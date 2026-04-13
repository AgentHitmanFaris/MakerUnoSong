import sys
import os
import time
import threading
import winsound

# Ensure current working directory is in sys path securely
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import converter

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QGraphicsView,
                             QGraphicsScene, QGraphicsRectItem, QLabel, QMessageBox,
                             QLineEdit, QFormLayout, QCheckBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPen

class PianoRollView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(QColor(20, 20, 25)))
        
        self.ZOOM_X = 0.2  # pixels per ms
        self.ROW_H = 14    # pixels per pitch
        self.MAX_PITCH = 127
        
        # Draw base grid roughly
        self.draw_grid()

    def draw_grid(self):
        self.scene.clear()
        pen = QPen(QColor(50, 50, 50))
        pen.setWidth(1)
        # Just draw horizontal lines for some notes
        for i in range(128):
            y = i * self.ROW_H
            self.scene.addLine(0, y, 5000, y, pen)

    def load_notes(self, notes):
        self.draw_grid()
        if not notes: return
        
        for n in notes:
            x = n['start'] * self.ZOOM_X
            y = (self.MAX_PITCH - n['pitch']) * self.ROW_H
            w = n['duration'] * self.ZOOM_X
            h = self.ROW_H
            
            rect = QGraphicsRectItem(x, y, w, h)
            rect.setBrush(QBrush(QColor(0, 242, 255)))
            rect.setPen(QPen(QColor(0, 0, 0)))
            self.scene.addItem(rect)
            
        # Update scene rect to fit notes
        max_x = max([(n['start'] + n['duration']) * self.ZOOM_X for n in notes])
        self.setSceneRect(0, 0, max_x + 500, 128 * self.ROW_H)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MakerUnoSong | Pro Desktop Editor (PyQt6)")
        self.resize(1000, 600)
        self.converter = converter.MidiConverter()
        self.playing = False
        self.play_thread = None
        
        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        btn_load = QPushButton("Load MIDI")
        btn_load.clicked.connect(self.load_midi)
        
        self.btn_play = QPushButton("▶ Play Preview")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("background-color: #00f2ff; color: #000; font-weight: bold;")
        
        btn_export = QPushButton("Export .INO")
        btn_export.clicked.connect(self.export_arduino)
        
        self.lbl_stats = QLabel("No file loaded.")
        self.lbl_stats.setStyleSheet("color: #888;")
        
        toolbar.addWidget(btn_load)
        toolbar.addWidget(self.btn_play)
        toolbar.addWidget(btn_export)
        toolbar.addStretch()
        toolbar.addWidget(self.lbl_stats)
        
        layout.addLayout(toolbar)
        
        # Metadata Form
        form_layout = QFormLayout()
        self.input_song = QLineEdit()
        self.input_song.setPlaceholderText("Enter Song Name")
        self.input_artist = QLineEdit()
        self.input_artist.setPlaceholderText("Enter Artist Name")
        
        form_layout.addRow("Song Name:", self.input_song)
        form_layout.addRow("Artist:", self.input_artist)
        
        self.chk_drums = QCheckBox("Enable Drums")
        self.chk_drums.setChecked(True)
        self.combo_drums = QComboBox()
        self.combo_drums.addItems(["Use MIDI Track", "Auto-Gen: Pop", "Auto-Gen: Rock", "Auto-Gen: Metal", 
                                   "Auto-Gen: Funk", "Auto-Gen: Disco", "Auto-Gen: Hip-Hop", "Auto-Gen: Reggae"])
        
        drum_layout = QHBoxLayout()
        drum_layout.addWidget(self.chk_drums)
        drum_layout.addWidget(self.combo_drums)
        form_layout.addRow("Drums:", drum_layout)
        
        layout.addLayout(form_layout)
        
        # Piano Roll
        self.piano_roll = PianoRollView()
        layout.addWidget(self.piano_roll)

    def load_midi(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load MIDI", "", "MIDI Files (*.mid *.midi)")
        if path:
            try:
                self.converter.load_midi(path)
                self.input_song.setText(getattr(self.converter, 'song_name', 'Unknown'))
                self.input_artist.setText(getattr(self.converter, 'artist', 'Unknown'))
                self.piano_roll.load_notes(self.converter.notes)
                self.lbl_stats.setText(f"Loaded {len(self.converter.notes)} notes.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load MIDI: {e}")

    def export_arduino(self):
        if not self.converter.notes:
            QMessageBox.warning(self, "Warning", "Please load a MIDI file first.")
            return

        # Prepare metadata metadata for naming
        self.converter.song_name = self.input_song.text().strip()
        self.converter.artist = self.input_artist.text().strip()
        project_name = self.converter.get_project_name()

        # Ask for root directory (default to Songs)
        default_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Songs")
        if not os.path.exists(default_root):
            os.makedirs(default_root)
            
        # Target folder and filename
        target_folder = os.path.join(default_root, project_name)
        target_file = os.path.join(target_folder, f"{project_name}.ino")
        
        # Confirmation Dialog
        reply = QMessageBox.question(self, "Export Confirmation", 
                                   f"This will export to:\n{target_file}\n\nProceed?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                    
                self.converter.enable_drums = self.chk_drums.isChecked()
                self.converter.drum_mode = self.combo_drums.currentText()
                self.converter.export_arduino(target_file)
                
                QMessageBox.information(self, "Success", f"Exported successfully to:\n{target_folder}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def toggle_play(self):
        if self.playing:
            self.playing = False
            self.btn_play.setText("▶ Play Preview")
        else:
            if not self.converter.notes: return
            self.playing = True
            self.btn_play.setText("⏸ Stop")
            self.play_thread = threading.Thread(target=self.play_audio_loop, daemon=True)
            self.play_thread.start()

    def play_audio_loop(self):
        # We use winsound to simulate Arduino tone() perfectly
        start_time = time.time()
        for idx, note in enumerate(self.converter.notes):
            if not self.playing: break
            
            # Wait until it's time for this note
            time_to_play = note['start'] / 1000.0
            
            while True:
                time_to_wait = time_to_play - (time.time() - start_time)
                if time_to_wait <= 0: break
                if not self.playing: return
                # Optimized waiting: sleep in larger chunks to reduce CPU wakeups
                time.sleep(min(time_to_wait, 0.05))
                
            freq = self.converter.note_to_freq(note['pitch'])
            # WinSound requires freq between 37 and 32767
            if 37 <= freq <= 32767:
                winsound.Beep(freq, max(10, note['duration']))
            else:
                time.sleep(note['duration'] / 1000.0)
                
        self.playing = False
        self.btn_play.setText("▶ Play Preview")

if __name__ == "__main__":
    app = QApplication(sys.path)
    # Force dark fusion theme
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(40, 44, 52))
    palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Base, QColor(20, 20, 25))
    palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Button, QColor(50, 54, 62))
    palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
