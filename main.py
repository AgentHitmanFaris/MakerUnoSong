"""
MakerUnoSong - Desktop Editor & Board Health Life Monitor.
Build by AgentHitmanFaris (NC-Engineering).

Compatible with PySide6 & PyQt6.
Features:
- MIDI to Maker UNO Arpeggiator & Adaptive White Noise Drum Synthesis
- Intelligent Structural Beat Engine (AI/Heuristic section thinking & cadence fills)
- Built-in Non-Blocking Audio Preview Synthesizer (Buzzer square wave + Kick + Snare + Hi-Hat)
- Real-Time Virtual Maker UNO Hardware Visualizer (12x Onboard LEDs, Pin 8 Buzzer, Pin 2 Button)
- Interactive Piano Roll with Live Animated Playhead & Scrubbing
- 1-Click Fully Automated Pipeline (Auto Beat Structuring + Auto Port Detection + Direct Flash)
- Standalone 1-Click Direct Sketch Upload (No Arduino IDE required)
- Real-Time Maker UNO Board Health & Life-Span Telemetry Dashboard
"""

import sys
import os
import time
import threading
import tempfile

# Ensure current working directory is in sys path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import converter
import uploader
import board_health
import smart_beat
import audio_preview

# Adaptive Qt Import Layer (PySide6 / PyQt6)
try:
    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                   QHBoxLayout, QPushButton, QFileDialog, QGraphicsView,
                                   QGraphicsScene, QGraphicsRectItem, QLabel, QMessageBox,
                                   QLineEdit, QFormLayout, QCheckBox, QComboBox, QTabWidget,
                                   QProgressBar, QTextEdit, QGroupBox, QGridLayout, QFrame,
                                   QSlider, QScrollArea)
    from PySide6.QtCore import Qt, QTimer, Signal, QObject
    from PySide6.QtGui import QBrush, QColor, QPen, QFont
except ImportError:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                   QHBoxLayout, QPushButton, QFileDialog, QGraphicsView,
                                   QGraphicsScene, QGraphicsRectItem, QLabel, QMessageBox,
                                   QLineEdit, QFormLayout, QCheckBox, QComboBox, QTabWidget,
                                   QProgressBar, QTextEdit, QGroupBox, QGridLayout, QFrame,
                                   QSlider, QScrollArea)
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal as Signal, QObject
    from PyQt6.QtGui import QBrush, QColor, QPen, QFont

class PianoRollView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setBackgroundBrush(QBrush(QColor(18, 20, 26)))
        
        self.ZOOM_X = 0.2  # pixels per ms
        self.ROW_H = 12    # pixels per pitch
        self.MAX_PITCH = 127
        self.playhead_line = None
        self.total_length_px = 6000
        self.on_seek_callback = None
        self.autoscroll = True
        self._zoom_factor = 1.0

        anchor = None
        if hasattr(QGraphicsView, 'ViewportAnchor'):
            anchor = getattr(QGraphicsView.ViewportAnchor, 'AnchorUnderMouse', None)
        elif hasattr(QGraphicsView, 'AnchorUnderMouse'):
            anchor = getattr(QGraphicsView, 'AnchorUnderMouse', None)
        if anchor is not None and hasattr(self, 'setTransformationAnchor'):
            try:
                self.setTransformationAnchor(anchor)
            except Exception:
                pass
        self.draw_grid()

    def zoom_in(self):
        """Zoom in time axis (horizontal)."""
        if self._zoom_factor < 8.0:
            self._zoom_factor *= 1.25
            self.scale(1.25, 1.0)

    def zoom_out(self):
        """Zoom out time axis (horizontal)."""
        if self._zoom_factor > 0.12:
            self._zoom_factor /= 1.25
            self.scale(0.8, 1.0)

    def reset_zoom(self):
        """Resets zoom level to 100%."""
        self.resetTransform()
        self._zoom_factor = 1.0

    def wheelEvent(self, event):
        modifiers = event.modifiers()
        ctrl_flag = Qt.KeyboardModifier.ControlModifier if hasattr(Qt, 'KeyboardModifier') else Qt.ControlModifier
        if modifiers & ctrl_flag:
            # Ctrl + Wheel = Zoom in / out
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            elif delta < 0:
                self.zoom_out()
            event.accept()
        else:
            shift_flag = Qt.KeyboardModifier.ShiftModifier if hasattr(Qt, 'KeyboardModifier') else Qt.ShiftModifier
            alt_flag = Qt.KeyboardModifier.AltModifier if hasattr(Qt, 'KeyboardModifier') else Qt.AltModifier
            if modifiers & (shift_flag | alt_flag):
                # Shift / Alt + Wheel = Horizontal scroll
                delta = event.angleDelta().y() or event.angleDelta().x()
                self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
                event.accept()
            else:
                super().wheelEvent(event)

    def draw_grid(self):
        self.scene.clear()
        self.playhead_line = None
        pen = QPen(QColor(32, 36, 46))
        pen.setWidth(1)
        for i in range(128):
            y = i * self.ROW_H
            self.scene.addLine(0, y, self.total_length_px, y, pen)

    def load_notes(self, notes):
        self.draw_grid()
        if not notes: return
        
        pitches = []
        for n in notes:
            x = n['start'] * self.ZOOM_X
            p = n.get('pitch', 60)
            if p > 0:
                pitches.append(p)
            y = (self.MAX_PITCH - p) * self.ROW_H
            w = max(4, n['duration'] * self.ZOOM_X)
            h = self.ROW_H
            
            rect = QGraphicsRectItem(x, y, w, h)
            # Sophisticated multi-channel coloring
            if n.get('channel', 0) == 9 or p in (28, 128, 129):
                if p == 28:
                    rect.setBrush(QBrush(QColor(255, 60, 60)))   # Kick: Neon Red
                elif p == 128:
                    rect.setBrush(QBrush(QColor(255, 170, 0)))  # Snare: Amber Orange
                else:
                    rect.setBrush(QBrush(QColor(255, 220, 50)))  # Hi-Hat: Gold
            elif p < 48:
                rect.setBrush(QBrush(QColor(160, 100, 255)))      # Bass: Purple
            elif p > 74:
                rect.setBrush(QBrush(QColor(0, 255, 200)))        # High Register: Aquamarine
            else:
                rect.setBrush(QBrush(QColor(0, 242, 255)))        # Main Melody: Cyan
            rect.setPen(QPen(QColor(10, 12, 16)))
            self.scene.addItem(rect)
            
        max_x = max([(n['start'] + n['duration']) * self.ZOOM_X for n in notes])
        self.total_length_px = max(6000, max_x + 500)
        self.setSceneRect(0, 0, self.total_length_px, 128 * self.ROW_H)

        # Create Playhead Indicator Line
        pen_cursor = QPen(QColor(255, 45, 85))
        pen_cursor.setWidth(2)
        self.playhead_line = self.scene.addLine(0, 0, 0, 128 * self.ROW_H, pen_cursor)
        self.playhead_line.setZValue(100)

        # Center vertically around the active melody range
        if pitches:
            avg_pitch = sum(pitches) / len(pitches)
            center_y = (self.MAX_PITCH - avg_pitch) * self.ROW_H
            self.centerOn(0, center_y)

    def set_playhead_pos_ms(self, time_ms: float):
        if self.playhead_line:
            x = time_ms * self.ZOOM_X
            self.playhead_line.setLine(x, 0, x, 128 * self.ROW_H)
            if self.autoscroll:
                viewport_center_y = self.mapToScene(0, self.viewport().height() // 2).y()
                self.centerOn(x, viewport_center_y)
            else:
                self.ensureVisible(x, 64 * self.ROW_H, 60, 60)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        pos = self.mapToScene(event.pos())
        ms = int(pos.x() / self.ZOOM_X)
        if self.on_seek_callback and ms >= 0:
            self.on_seek_callback(ms)

class VirtualMakerUnoWidget(QFrame):
    """
    Realistic visual representation of the Cytron Maker UNO board:
    12 Onboard status LEDs (Pins 2 to 13), Buzzer (Pin 8), and Button (Pin 2).
    """
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background: #141720;
                border: 1px solid #2d3444;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        self.led_labels = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        # Top Silkscreen Banner
        top_bar = QHBoxLayout()
        title = QLabel("CYTRON MAKER UNO (VIRTUAL HARDWARE VISUALIZER)")
        title.setStyleSheet("color: #00f2ff; font-weight: bold; font-size: 11px; letter-spacing: 0.5px;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self.lbl_buzzer = QLabel("🔊 BUZZER (PIN 8): Standby")
        self.lbl_buzzer.setStyleSheet("color: #8892b0; font-size: 11px; font-weight: bold;")
        top_bar.addWidget(self.lbl_buzzer)

        self.lbl_btn = QLabel("🔘 BUTTON (PIN 2): Standby")
        self.lbl_btn.setStyleSheet("color: #8892b0; font-size: 11px; font-weight: bold; margin-left: 12px;")
        top_bar.addWidget(self.lbl_btn)
        layout.addLayout(top_bar)

        # 12 Onboard LEDs row (Pins 2 to 13)
        led_row = QHBoxLayout()
        led_row.setSpacing(6)
        align_center = Qt.AlignmentFlag.AlignCenter if hasattr(Qt, 'AlignmentFlag') else Qt.AlignCenter

        pins = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        for p in pins:
            col = QVBoxLayout()
            col.setSpacing(2)

            role_tag = " (BTN)" if p == 2 else (" (BUZZ)" if p == 8 else (" (LED)" if p == 13 else ""))
            lbl_pin = QLabel(f"D{p}{role_tag}")
            lbl_pin.setAlignment(align_center)
            lbl_pin.setStyleSheet("color: #616e88; font-size: 9px; font-weight: bold;")

            led = QLabel()
            led.setFixedSize(20, 20)
            led.setStyleSheet("background: #20242e; border: 1px solid #333945; border-radius: 10px;")
            self.led_labels[p] = led

            col.addWidget(led, alignment=align_center)
            col.addWidget(lbl_pin, alignment=align_center)
            led_row.addLayout(col)

        layout.addLayout(led_row)

    def update_visuals(self, active_pin: int, freq: int, btn_pressed: bool = False):
        for p, led in self.led_labels.items():
            if p == active_pin:
                if p == 13:
                    glow = "background: #ff0055; border: 2px solid #ffffff; border-radius: 10px;"
                elif p == 8:
                    glow = "background: #ffcc00; border: 2px solid #ffffff; border-radius: 10px;"
                elif p == 2:
                    glow = "background: #00ff88; border: 2px solid #ffffff; border-radius: 10px;"
                else:
                    glow = "background: #00f2ff; border: 2px solid #ffffff; border-radius: 10px;"
                led.setStyleSheet(glow)
            else:
                led.setStyleSheet("background: #20242e; border: 1px solid #333945; border-radius: 10px;")

        # Buzzer update
        if freq > 0:
            self.lbl_buzzer.setText(f"🔊 BUZZER (PIN 8): {freq} Hz")
            self.lbl_buzzer.setStyleSheet("color: #00f2ff; font-size: 11px; font-weight: bold;")
        elif freq == -1:
            self.lbl_buzzer.setText("🔊 BUZZER (PIN 8): 🥁 SNARE NOISE")
            self.lbl_buzzer.setStyleSheet("color: #ffaa00; font-size: 11px; font-weight: bold;")
        elif freq == -2:
            self.lbl_buzzer.setText("🔊 BUZZER (PIN 8): 🎵 HI-HAT TICK")
            self.lbl_buzzer.setStyleSheet("color: #ffff00; font-size: 11px; font-weight: bold;")
        elif freq == 28:
            self.lbl_buzzer.setText("🔊 BUZZER (PIN 8): 💥 KICK SUB-BASS")
            self.lbl_buzzer.setStyleSheet("color: #ff4444; font-size: 11px; font-weight: bold;")
        else:
            self.lbl_buzzer.setText("🔊 BUZZER (PIN 8): Rest")
            self.lbl_buzzer.setStyleSheet("color: #616e88; font-size: 11px; font-weight: bold;")

        # Button update
        if btn_pressed:
            self.lbl_btn.setText("🔘 BUTTON (PIN 2): PRESSED")
            self.lbl_btn.setStyleSheet("color: #00ff88; font-size: 11px; font-weight: bold;")
        else:
            self.lbl_btn.setText("🔘 BUTTON (PIN 2): Idle")
            self.lbl_btn.setStyleSheet("color: #616e88; font-size: 11px; font-weight: bold;")

    def reset(self):
        for p, led in self.led_labels.items():
            led.setStyleSheet("background: #20242e; border: 1px solid #333945; border-radius: 10px;")
        self.lbl_buzzer.setText("🔊 BUZZER (PIN 8): Standby")
        self.lbl_buzzer.setStyleSheet("color: #8892b0; font-size: 11px; font-weight: bold;")
        self.lbl_btn.setText("🔘 BUTTON (PIN 2): Standby")
        self.lbl_btn.setStyleSheet("color: #8892b0; font-size: 11px; font-weight: bold;")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MakerUnoSong Studio | Pro Editor, Direct Uploader & Health Monitor")
        self.resize(1180, 780)
        
        self.converter = converter.MidiConverter()
        self.uploader = uploader.ArduinoUploader()
        self.health_engine = board_health.BoardHealthEngine()
        
        self.playing = False
        self.preview_engine = None
        self.tempo_multiplier = 1.0
        self.slider_dragging = False
        
        # Audio Preview Timer for Playhead & Hardware Visualizer
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.on_preview_tick)

        self.setup_ui()
        self.refresh_ports()

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Tabs: Song Studio & Board Health Monitor
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3d4450; background: #1a1d24; border-radius: 4px; }
            QTabBar::tab { background: #252a34; color: #aaa; padding: 8px 18px; font-weight: bold; }
            QTabBar::tab:selected { background: #00f2ff; color: #000; }
        """)

        # Tab 1: Song Studio
        self.tab_studio = QWidget()
        self.setup_studio_tab()
        self.tabs.addTab(self.tab_studio, "🎵 Song Studio & Direct Flasher")

        # Tab 2: Board Health Monitor
        self.tab_health = QWidget()
        self.setup_health_tab()
        self.tabs.addTab(self.tab_health, "🩺 Board Health & Life Monitor")

        main_layout.addWidget(self.tabs)

        # Global Bottom Status & Progress Bar
        status_bar = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #333; border-radius: 3px; background: #222; }
            QProgressBar::chunk { background: #00f2ff; }
        """)
        self.progress_bar.setVisible(False)

        self.lbl_global_status = QLabel("Ready.")
        self.lbl_global_status.setStyleSheet("color: #8892b0; font-size: 11px;")
        
        status_bar.addWidget(self.lbl_global_status)
        status_bar.addStretch()
        status_bar.addWidget(self.progress_bar)
        main_layout.addLayout(status_bar)

    def setup_studio_tab(self):
        layout = QVBoxLayout(self.tab_studio)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Top Action Toolbar
        toolbar = QHBoxLayout()
        
        btn_load = QPushButton("📂 Load MIDI")
        btn_load.clicked.connect(self.load_midi)
        btn_load.setStyleSheet("padding: 6px 12px; font-weight: bold; background: #2b3240; color: #fff;")
        
        # 1-Click Fully Automated Pipeline Button
        self.btn_auto_pipeline = QPushButton("⚡ 1-Click Auto Pipeline")
        self.btn_auto_pipeline.setToolTip("Auto-analyze structure, generate smart beat, detect port, and flash Maker UNO")
        self.btn_auto_pipeline.clicked.connect(self.run_auto_pipeline)
        self.btn_auto_pipeline.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #00ff88; color: #000;")

        self.btn_play = QPushButton("▶ Play Preview")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #00f2ff; color: #000;")

        btn_stop = QPushButton("⏹")
        btn_stop.setFixedWidth(30)
        btn_stop.setToolTip("Stop Audio Preview")
        btn_stop.clicked.connect(self.stop_play)
        btn_stop.setStyleSheet("padding: 6px; font-weight: bold; background: #2b3240; color: #fff;")

        btn_export = QPushButton("💾 Export .INO")
        btn_export.clicked.connect(self.export_arduino)
        btn_export.setStyleSheet("padding: 6px 12px; font-weight: bold; background: #2b3240; color: #fff;")

        self.btn_export_wav = QPushButton("🎵 Export WAV")
        self.btn_export_wav.setToolTip("Export Synthesized Audio Preview as WAV file")
        self.btn_export_wav.clicked.connect(self.export_preview_wav)
        self.btn_export_wav.setStyleSheet("padding: 6px 12px; font-weight: bold; background: #2b3240; color: #fff;")

        # Direct Flash to Maker UNO Controls
        self.combo_ports_studio = QComboBox()
        self.combo_ports_studio.setMinimumWidth(180)
        self.combo_ports_studio.setStyleSheet("padding: 5px; background: #252a34; color: #fff;")
        
        btn_refresh_ports = QPushButton("🔄")
        btn_refresh_ports.setToolTip("Scan COM Ports")
        btn_refresh_ports.setFixedWidth(30)
        btn_refresh_ports.clicked.connect(self.refresh_ports)
        
        self.btn_direct_upload = QPushButton("⚡ Direct Upload")
        self.btn_direct_upload.clicked.connect(self.direct_upload_song)
        self.btn_direct_upload.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #ffaa00; color: #000;")
        
        toolbar.addWidget(btn_load)
        toolbar.addWidget(self.btn_auto_pipeline)
        toolbar.addWidget(self.btn_play)
        toolbar.addWidget(btn_stop)
        toolbar.addWidget(btn_export)
        toolbar.addWidget(self.btn_export_wav)
        toolbar.addSpacing(10)
        toolbar.addWidget(QLabel("Port:"))
        toolbar.addWidget(self.combo_ports_studio)
        toolbar.addWidget(btn_refresh_ports)
        toolbar.addWidget(self.btn_direct_upload)
        toolbar.addStretch()

        self.lbl_stats = QLabel("No MIDI loaded.")
        self.lbl_stats.setStyleSheet("color: #8892b0; font-size: 11px;")
        toolbar.addWidget(self.lbl_stats)

        layout.addLayout(toolbar)

        # Musical Intelligence & Song Settings Group
        form_group = QGroupBox("Song Settings, Intelligent Beat & Maker UNO Hardware Visualizer")
        form_group.setStyleSheet("QGroupBox { color: #00f2ff; font-weight: bold; border: 1px solid #333; margin-top: 4px; padding-top: 8px; }")
        grid_form = QGridLayout(form_group)
        grid_form.setSpacing(6)
        
        self.input_song = QLineEdit()
        self.input_song.setPlaceholderText("Enter Song Name")
        self.input_song.setStyleSheet("background: #252a34; color: #fff; padding: 4px;")
        
        self.input_artist = QLineEdit()
        self.input_artist.setPlaceholderText("Enter Artist Name")
        self.input_artist.setStyleSheet("background: #252a34; color: #fff; padding: 4px;")

        self.chk_drums = QCheckBox("Enable Drums")
        self.chk_drums.setChecked(True)
        self.combo_drums = QComboBox()
        self.combo_drums.addItems([
            "🧠 Smart Adaptive AI",
            "🧠 Smart Adaptive: High Energy",
            "🧠 Smart Adaptive: Chill / Acoustic",
            "🧠 Smart Adaptive: Rock / Live Band",
            "Use MIDI Track",
            "Auto-Gen: Pop", "Auto-Gen: Rock", "Auto-Gen: Metal", 
            "Auto-Gen: Funk", "Auto-Gen: Disco", "Auto-Gen: Hip-Hop", "Auto-Gen: Reggae"
        ])
        self.combo_drums.setStyleSheet("background: #252a34; color: #fff; padding: 3px;")
        self.combo_drums.currentIndexChanged.connect(self.on_settings_changed)

        self.chk_led_sync = QCheckBox("Maker UNO 12x LED Sync")
        self.chk_led_sync.setChecked(True)
        self.combo_led_mode = QComboBox()
        self.combo_led_mode.addItems([
            "Frequency Mapped",
            "VU Meter",
            "Knight Rider Scanner",
            "Drum Reactive"
        ])
        self.combo_led_mode.setStyleSheet("background: #252a34; color: #fff; padding: 3px;")

        self.chk_button_ctrl = QCheckBox("Maker UNO Button (Pin 2 Pause/Resume)")
        self.chk_button_ctrl.setChecked(True)

        grid_form.addWidget(QLabel("Song:"), 0, 0)
        grid_form.addWidget(self.input_song, 0, 1)
        grid_form.addWidget(QLabel("Artist:"), 0, 2)
        grid_form.addWidget(self.input_artist, 0, 3)

        drum_box = QHBoxLayout()
        drum_box.addWidget(self.chk_drums)
        drum_box.addWidget(self.combo_drums)
        grid_form.addLayout(drum_box, 1, 0, 1, 2)

        feat_box = QHBoxLayout()
        feat_box.addWidget(self.chk_led_sync)
        feat_box.addWidget(self.combo_led_mode)
        feat_box.addWidget(self.chk_button_ctrl)
        grid_form.addLayout(feat_box, 1, 2, 1, 2)

        layout.addWidget(form_group)

        # Musical Intelligence Dashboard Ribbon
        self.lbl_music_intel = QLabel("🎼 Key: -- | ⏱️ -- BPM | 📊 Measures: 0 | ⚡ Density: 0 n/s | 💾 Flash: 0%")
        self.lbl_music_intel.setStyleSheet("color: #00ff88; font-weight: bold; font-size: 11px; padding: 2px 4px;")
        layout.addWidget(self.lbl_music_intel)

        # Song Structure Section Badges Bar (Scrollable for complex songs)
        self.sec_scroll = QScrollArea()
        self.sec_scroll.setWidgetResizable(True)
        self.sec_scroll.setFixedHeight(34)
        h_policy = Qt.ScrollBarPolicy.ScrollBarAsNeeded if hasattr(Qt, 'ScrollBarPolicy') else Qt.ScrollBarAsNeeded
        v_policy = Qt.ScrollBarPolicy.ScrollBarAlwaysOff if hasattr(Qt, 'ScrollBarPolicy') else Qt.ScrollBarAlwaysOff
        self.sec_scroll.setHorizontalScrollBarPolicy(h_policy)
        self.sec_scroll.setVerticalScrollBarPolicy(v_policy)
        self.sec_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.sec_bar_widget = QWidget()
        self.sec_bar_layout = QHBoxLayout(self.sec_bar_widget)
        self.sec_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.sec_bar_layout.setSpacing(4)
        self.sec_scroll.setWidget(self.sec_bar_widget)
        layout.addWidget(self.sec_scroll)

        # Real-Time Virtual Maker UNO Hardware Visualizer Panel
        self.virtual_board = VirtualMakerUnoWidget()
        layout.addWidget(self.virtual_board)

        # Audio Scrubbing & Controls Bar
        audio_bar = QHBoxLayout()
        self.lbl_time_pos = QLabel("00:00 / 00:00")
        self.lbl_time_pos.setStyleSheet("color: #8892b0; font-family: monospace; font-size: 11px;")
        
        self.slider_pos = QSlider(Qt.Orientation.Horizontal if hasattr(Qt, 'Orientation') else Qt.Horizontal)
        self.slider_pos.setRange(0, 1000)
        self.slider_pos.sliderPressed.connect(self.on_slider_pressed)
        self.slider_pos.sliderReleased.connect(self.on_slider_released)

        lbl_tempo = QLabel("Speed:")
        lbl_tempo.setStyleSheet("color: #8892b0; font-size: 10px;")
        self.combo_tempo = QComboBox()
        self.combo_tempo.addItems(["0.5x", "0.75x", "1.0x (Normal)", "1.25x", "1.5x", "2.0x"])
        self.combo_tempo.setCurrentText("1.0x (Normal)")
        self.combo_tempo.currentIndexChanged.connect(self.on_tempo_changed)
        self.combo_tempo.setStyleSheet("background: #252a34; color: #fff; padding: 2px;")

        # Timeline Zoom & Autoscroll Controls
        self.btn_zoom_out = QPushButton("🔍 -")
        self.btn_zoom_out.setToolTip("Zoom Out Timeline (Ctrl + Mouse Wheel Down)")
        self.btn_zoom_out.setFixedWidth(34)
        self.btn_zoom_out.setStyleSheet("padding: 3px; font-weight: bold; background: #252a34; color: #fff;")
        self.btn_zoom_out.clicked.connect(self.on_zoom_out)

        self.btn_zoom_in = QPushButton("🔍 +")
        self.btn_zoom_in.setToolTip("Zoom In Timeline (Ctrl + Mouse Wheel Up)")
        self.btn_zoom_in.setFixedWidth(34)
        self.btn_zoom_in.setStyleSheet("padding: 3px; font-weight: bold; background: #252a34; color: #fff;")
        self.btn_zoom_in.clicked.connect(self.on_zoom_in)

        self.btn_zoom_reset = QPushButton("1:1")
        self.btn_zoom_reset.setToolTip("Reset Zoom to 100%")
        self.btn_zoom_reset.setFixedWidth(34)
        self.btn_zoom_reset.setStyleSheet("padding: 3px; font-weight: bold; background: #252a34; color: #fff;")
        self.btn_zoom_reset.clicked.connect(self.on_zoom_reset)

        self.chk_autoscroll = QCheckBox("🔄 Auto-Scroll")
        self.chk_autoscroll.setChecked(True)
        self.chk_autoscroll.setToolTip("Keep playhead centered and visible during playback")
        self.chk_autoscroll.setStyleSheet("color: #00f2ff; font-size: 11px; font-weight: bold;")
        self.chk_autoscroll.toggled.connect(self.on_autoscroll_toggled)

        audio_bar.addWidget(self.lbl_time_pos)
        audio_bar.addWidget(self.slider_pos)
        audio_bar.addWidget(lbl_tempo)
        audio_bar.addWidget(self.combo_tempo)
        audio_bar.addSpacing(6)
        audio_bar.addWidget(self.btn_zoom_out)
        audio_bar.addWidget(self.btn_zoom_in)
        audio_bar.addWidget(self.btn_zoom_reset)
        audio_bar.addWidget(self.chk_autoscroll)
        layout.addLayout(audio_bar)

        # Piano Roll View
        self.piano_roll = PianoRollView()
        self.piano_roll.on_seek_callback = self.seek_to_ms
        layout.addWidget(self.piano_roll)

    def setup_health_tab(self):
        layout = QVBoxLayout(self.tab_health)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Diagnostics Connection Toolbar
        conn_bar = QHBoxLayout()
        conn_bar.addWidget(QLabel("Target Maker UNO Port:"))
        
        self.combo_ports_health = QComboBox()
        self.combo_ports_health.setMinimumWidth(200)
        self.combo_ports_health.setStyleSheet("padding: 5px; background: #252a34; color: #fff;")
        conn_bar.addWidget(self.combo_ports_health)
        
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedWidth(32)
        btn_refresh.clicked.connect(self.refresh_ports)
        conn_bar.addWidget(btn_refresh)
        
        self.btn_flash_diag = QPushButton("⚡ 1-Click Flash Diagnostic Firmware")
        self.btn_flash_diag.clicked.connect(self.flash_diagnostic_firmware)
        self.btn_flash_diag.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #00f2ff; color: #000;")
        conn_bar.addWidget(self.btn_flash_diag)

        self.btn_monitor_toggle = QPushButton("🩺 Connect & Read Health")
        self.btn_monitor_toggle.clicked.connect(self.toggle_health_monitoring)
        self.btn_monitor_toggle.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #00ff88; color: #000;")
        conn_bar.addWidget(self.btn_monitor_toggle)
        
        conn_bar.addStretch()
        layout.addLayout(conn_bar)

        # Big Health Score Badge Card
        self.card_score = QFrame()
        self.card_score.setStyleSheet("QFrame { background: #20242e; border: 2px solid #00f2ff; border-radius: 8px; padding: 12px; }")
        score_layout = QHBoxLayout(self.card_score)
        
        self.lbl_score_num = QLabel("100%")
        self.lbl_score_num.setStyleSheet("font-size: 38px; font-weight: bold; color: #00f2ff;")
        
        score_details = QVBoxLayout()
        self.lbl_score_grade = QLabel("BOARD HEALTH: EXCELLENT (GRADE A)")
        self.lbl_score_grade.setStyleSheet("font-size: 16px; font-weight: bold; color: #00ff88;")
        self.lbl_score_summary = QLabel("Board diagnostics standby. Flash diagnostic firmware or connect to monitor.")
        self.lbl_score_summary.setStyleSheet("color: #8892b0; font-size: 12px;")
        score_details.addWidget(self.lbl_score_grade)
        score_details.addWidget(self.lbl_score_summary)
        
        score_layout.addWidget(self.lbl_score_num)
        score_layout.addSpacing(20)
        score_layout.addLayout(score_details)
        score_layout.addStretch()
        layout.addWidget(self.card_score)

        # 6 Metric Diagnostic Telemetry Cards
        grid_metrics = QGridLayout()
        grid_metrics.setSpacing(10)

        self.card_vcc = self._create_metric_card("⚡ Supply Voltage (Vcc)", "5.000 V", "Nominal Rail (Internal 1.1V Bandgap)")
        self.card_temp = self._create_metric_card("🌡️ MCU Core Temp", "28.5 °C", "Internal ATmega328P ADC8 Sensor")
        self.card_ram = self._create_metric_card("💾 Free SRAM Headroom", "1,720 / 2,048 B", "84% Dynamic Memory Free")
        self.card_eeprom = self._create_metric_card("💾 EEPROM Integrity", "Verified OK", "Non-Volatile Storage Retention")
        self.card_jitter = self._create_metric_card("⏱️ Crystal Timing / Jitter", "0.00 ms", "16MHz Oscillator Stability")
        self.card_button = self._create_metric_card("🔘 Maker UNO Button (Pin 2)", "IDLE", "Press button to test live reaction")

        grid_metrics.addWidget(self.card_vcc, 0, 0)
        grid_metrics.addWidget(self.card_temp, 0, 1)
        grid_metrics.addWidget(self.card_ram, 0, 2)
        grid_metrics.addWidget(self.card_eeprom, 1, 0)
        grid_metrics.addWidget(self.card_jitter, 1, 1)
        grid_metrics.addWidget(self.card_button, 1, 2)

        layout.addLayout(grid_metrics)

        # Interactive Hardware Test Bar
        test_group = QGroupBox("Interactive Maker UNO Hardware Peripherals Test")
        test_group.setStyleSheet("QGroupBox { color: #ffaa00; font-weight: bold; border: 1px solid #333; margin-top: 4px; padding-top: 10px; }")
        test_bar = QHBoxLayout(test_group)

        btn_test_leds = QPushButton("💡 Sweep 12x LEDs (Pins 2-13)")
        btn_test_leds.clicked.connect(lambda: self.health_engine.send_command("TEST_LEDS"))
        btn_test_leds.setStyleSheet("padding: 6px 12px; font-weight: bold; background: #2b3240; color: #fff;")

        btn_test_buzzer = QPushButton("🔊 Test Buzzer (Pin 8 Sweep)")
        btn_test_buzzer.clicked.connect(lambda: self.health_engine.send_command("TEST_BUZZER"))
        btn_test_buzzer.setStyleSheet("padding: 6px 12px; font-weight: bold; background: #2b3240; color: #fff;")

        btn_ping = QPushButton("🏓 Ping MCU")
        btn_ping.clicked.connect(lambda: self.health_engine.send_command("PING"))
        btn_ping.setStyleSheet("padding: 6px 12px; font-weight: bold; background: #2b3240; color: #fff;")

        test_bar.addWidget(btn_test_leds)
        test_bar.addWidget(btn_test_buzzer)
        test_bar.addWidget(btn_ping)
        test_bar.addStretch()
        layout.addWidget(test_group)

        # Raw Telemetry Log
        self.txt_health_log = QTextEdit()
        self.txt_health_log.setReadOnly(True)
        self.txt_health_log.setMaximumHeight(100)
        self.txt_health_log.setStyleSheet("background: #11141a; color: #00ff88; font-family: Consolas, monospace; font-size: 10px; border: 1px solid #222;")
        layout.addWidget(self.txt_health_log)

    def _create_metric_card(self, title: str, value: str, sub: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background: #222630; border: 1px solid #333945; border-radius: 6px; padding: 8px; }")
        v = QVBoxLayout(frame)
        v.setContentsMargins(6, 6, 6, 6)
        
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #8892b0; font-size: 11px; font-weight: bold;")
        
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet("color: #ffffff; font-size: 17px; font-weight: bold;")
        
        lbl_sub = QLabel(sub)
        lbl_sub.setStyleSheet("color: #00f2ff; font-size: 10px;")
        
        v.addWidget(lbl_t)
        v.addWidget(lbl_val)
        v.addWidget(lbl_sub)
        
        frame.lbl_val = lbl_val
        frame.lbl_sub = lbl_sub
        return frame

    def refresh_ports(self):
        """Scans COM ports and updates selectors."""
        ports = self.uploader.list_ports()
        self.combo_ports_studio.clear()
        self.combo_ports_health.clear()
        
        best_idx = 0
        for idx, p in enumerate(ports):
            self.combo_ports_studio.addItem(p['display'], p['port'])
            self.combo_ports_health.addItem(p['display'], p['port'])
            if p.get('is_maker_uno'):
                best_idx = idx

        if ports:
            self.combo_ports_studio.setCurrentIndex(best_idx)
            self.combo_ports_health.setCurrentIndex(best_idx)
            self.lbl_global_status.setText(f"Detected {len(ports)} serial port(s).")
        else:
            self.combo_ports_studio.addItem("No COM Ports Found", "")
            self.combo_ports_health.addItem("No COM Ports Found", "")
            self.lbl_global_status.setText("No serial devices detected.")

    def get_selected_port(self, tab: str = "studio") -> str:
        combo = self.combo_ports_studio if tab == "studio" else self.combo_ports_health
        return combo.currentData() or combo.currentText().split()[0]

    def load_midi(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load MIDI", "", "MIDI Files (*.mid *.midi)")
        if path:
            try:
                self.stop_play()
                self.preview_engine = None
                self.converter.load_midi(path)
                self.input_song.setText(getattr(self.converter, 'song_name', 'Untitled'))
                self.input_artist.setText(getattr(self.converter, 'artist', 'Unknown'))
                
                # Apply current drum settings
                self.converter.enable_drums = self.chk_drums.isChecked()
                self.converter.drum_mode = self.combo_drums.currentText()
                processed_notes = self.converter._process_drums()
                self.piano_roll.load_notes(processed_notes)

                self.update_musical_intelligence_ui()

                self.lbl_stats.setText(f"Loaded: {len(self.converter.notes)} notes | {self.converter.bpm} BPM")
                self.lbl_global_status.setText(f"Loaded {os.path.basename(path)} successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load MIDI: {e}")

    def update_musical_intelligence_ui(self):
        analysis = self.converter.analyze_song_structure()
        if not isinstance(analysis, dict):
            analysis = {}
        flash = self.converter.get_flash_usage_estimate()
        if not isinstance(flash, dict):
            flash = {}

        key = analysis.get('key_detected', 'C Major')
        measures = analysis.get('total_measures', 0)
        density = analysis.get('avg_density', 0)
        flash_pct = flash.get('percent', 0)
        flash_bytes = flash.get('progmem_bytes', 0)
        bpm = getattr(self.converter, 'bpm', 120)
        time_sig = getattr(self.converter, 'time_signature', '4/4')

        self.lbl_music_intel.setText(
            f"🎼 Key: {key}  |  ⏱️ {bpm} BPM ({time_sig})  |  "
            f"📊 Measures: {measures}  |  ⚡ Density: {density} notes/s  |  "
            f"💾 Flash: {flash_pct}% (~{flash_bytes} B)"
        )

        # Clear previous section badges
        if hasattr(self.sec_bar_layout, 'count'):
            while self.sec_bar_layout.count() > 0:
                item = self.sec_bar_layout.takeAt(0)
                if not item:
                    break
                if hasattr(item, 'widget') and item.widget():
                    item.widget().deleteLater()

        # Render color-coded section badges
        sections = analysis.get('sections', []) if isinstance(analysis.get('sections'), list) else []
        colors = {
            "INTRO": "#2e7d32",
            "VERSE": "#1565c0",
            "PRE-CHORUS": "#6a1b9a",
            "CHORUS": "#c2185b",
            "BRIDGE": "#ef6c00",
            "OUTRO": "#00838f"
        }

        for s in sections:
            s_name = str(s.get('name', 'SECTION'))
            s_bar_start = s.get('start_bar', 0)
            s_bar_end = s.get('end_bar', 0)
            sec_btn = QPushButton(f"{s_name} (b{s_bar_start}-{s_bar_end})")
            sec_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {colors.get(s_name, '#37474f')};
                    color: #fff;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 3px;
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    border: 1px solid #00f2ff;
                }}
            """)
            sec_start_ms = s.get('start_ms', 0)
            sec_btn.clicked.connect(lambda checked=False, ms=sec_start_ms: self.seek_to_ms(ms))
            self.sec_bar_layout.addWidget(sec_btn)
        self.sec_bar_layout.addStretch()

    def on_settings_changed(self):
        if self.converter.notes:
            self.preview_engine = None
            self.converter.enable_drums = self.chk_drums.isChecked()
            self.converter.drum_mode = self.combo_drums.currentText()
            processed_notes = self.converter._process_drums()
            self.piano_roll.load_notes(processed_notes)
            self.update_musical_intelligence_ui()

    def on_tempo_changed(self):
        text = self.combo_tempo.currentText().split()[0]
        try:
            self.tempo_multiplier = float(text.replace('x', ''))
        except Exception:
            self.tempo_multiplier = 1.0
        if self.playing:
            cur_ms = self.preview_engine.get_current_time_ms() if self.preview_engine else 0
            self.stop_play()
            self.start_play(start_pos_ms=int(cur_ms))

    def on_slider_pressed(self):
        self.slider_dragging = True

    def on_slider_released(self):
        self.slider_dragging = False
        val = self.slider_pos.value()
        if self.preview_engine and self.preview_engine.total_duration_ms > 0:
            target_ms = int((val / 1000.0) * self.preview_engine.total_duration_ms)
            self.seek_to_ms(target_ms)

    def on_zoom_in(self):
        self.piano_roll.zoom_in()

    def on_zoom_out(self):
        self.piano_roll.zoom_out()

    def on_zoom_reset(self):
        self.piano_roll.reset_zoom()

    def on_autoscroll_toggled(self, checked):
        self.piano_roll.autoscroll = bool(checked)

    def seek_to_ms(self, time_ms: int):
        was_playing = self.playing
        if was_playing:
            self.stop_play()
        self.piano_roll.set_playhead_pos_ms(time_ms)
        if was_playing:
            self.start_play(start_pos_ms=time_ms)

    def toggle_play(self):
        if self.playing:
            self.stop_play()
        else:
            self.start_play()

    def start_play(self, start_pos_ms: int = 0):
        if not self.converter.notes:
            return

        self.converter.song_name = self.input_song.text().strip()
        self.converter.artist = self.input_artist.text().strip()
        self.converter.enable_drums = self.chk_drums.isChecked()
        self.converter.drum_mode = self.combo_drums.currentText()
        self.converter.enable_led_sync = self.chk_led_sync.isChecked()
        self.converter.enable_button_control = self.chk_button_ctrl.isChecked()
        if hasattr(self, 'combo_led_mode'):
            self.converter.led_mode = self.combo_led_mode.currentText()

        if not self.preview_engine or abs(getattr(self.preview_engine, 'tempo_multiplier', 1.0) - self.tempo_multiplier) > 0.01:
            self.lbl_global_status.setText("Synthesizing audio preview...")
            self.preview_engine = self.converter.get_preview_engine(tempo_multiplier=self.tempo_multiplier)
        if not self.preview_engine:
            return

        self.playing = True
        self.btn_play.setText("⏸ Pause")
        self.btn_play.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #ffaa00; color: #000;")
        self.preview_engine.play(start_ms=start_pos_ms)
        self.preview_timer.start(33)
        self.lbl_global_status.setText(f"Playing Maker UNO preview (Tempo: {self.tempo_multiplier:.2f}x)...")

    def stop_play(self):
        self.playing = False
        if self.preview_engine:
            self.preview_engine.stop()
        self.preview_timer.stop()
        self.btn_play.setText("▶ Play Preview")
        self.btn_play.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #00f2ff; color: #000;")
        self.virtual_board.reset()
        self.lbl_global_status.setText("Playback stopped.")

    def on_preview_tick(self):
        if not self.preview_engine:
            return
        cur_ms = self.preview_engine.get_current_time_ms()
        total_ms = self.preview_engine.total_duration_ms

        if not self.preview_engine.is_playing or (total_ms > 0 and cur_ms >= total_ms):
            self.stop_play()
            if self.slider_pos:
                self.slider_pos.setValue(0)
            self.piano_roll.set_playhead_pos_ms(0)
            return

        self.piano_roll.set_playhead_pos_ms(cur_ms)
        pin, freq = self.preview_engine.get_led_state_at_ms(cur_ms)
        self.virtual_board.update_visuals(pin, freq)

        if total_ms > 0 and self.slider_pos and not self.slider_dragging:
            self.slider_pos.setValue(int((cur_ms / total_ms) * 1000))
        cur_sec = int(cur_ms / 1000)
        tot_sec = int(total_ms / 1000)
        self.lbl_time_pos.setText(f"{cur_sec // 60:02d}:{cur_sec % 60:02d} / {tot_sec // 60:02d}:{tot_sec % 60:02d}")

    def run_auto_pipeline(self):
        """Fully automated 1-click pipeline: loads/structures beat, detects port, and flashes Maker UNO."""
        if not self.converter.notes:
            self.load_midi()
            if not self.converter.notes:
                return

        # 1. Select intelligent beat thinking
        self.combo_drums.setCurrentText("🧠 Smart Adaptive AI")
        self.converter.drum_mode = "🧠 Smart Adaptive AI"
        self.converter.enable_drums = True
        self.chk_drums.setChecked(True)

        processed_notes = self.converter._process_drums()
        self.piano_roll.load_notes(processed_notes)
        self.update_musical_intelligence_ui()

        # 2. Detect Maker UNO port
        ports = self.uploader.list_ports()
        maker_port = None
        for p in ports:
            if p.get('is_maker_uno'):
                maker_port = p['port']
                break
        if not maker_port and ports:
            maker_port = ports[0]['port']

        if not maker_port:
            song_title = self.input_song.text().strip() or getattr(self.converter, 'song_name', 'MakerUno_Song')
            artist_name = self.input_artist.text().strip() or getattr(self.converter, 'artist', 'Unknown')
            self.converter.song_name = song_title
            self.converter.artist = artist_name
            proj_name = self.converter.get_project_name()
            default_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Songs")
            target_folder = os.path.join(default_root, proj_name)
            target_file = os.path.join(target_folder, f"{proj_name}.ino")
            try:
                self.converter.export_arduino(target_file)
                export_msg = f"Exported .ino sketch to:\n{target_file}\n\n"
            except Exception:
                export_msg = ""

            QMessageBox.information(
                self, "Auto Pipeline Complete",
                f"Song '{self.converter.song_name}' processed with Smart Adaptive AI beat!\n\n"
                f"{export_msg}Connect your Maker UNO to a COM port for direct hardware flashing."
            )
            return

        self.combo_ports_studio.setCurrentText(maker_port)
        self.direct_upload_song()

    def export_preview_wav(self):
        """Synthesizes and exports audio preview as WAV file."""
        if not self.converter.notes:
            QMessageBox.warning(self, "Warning", "Please load a MIDI file first.")
            return

        proj_name = self.converter.get_project_name()
        default_name = f"{proj_name}_Preview.wav"
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Audio Preview WAV", default_name, "WAV Audio (*.wav)")
        if save_path:
            try:
                engine = self.converter.get_preview_engine(tempo_multiplier=self.tempo_multiplier)
                if engine and engine.export_wav(save_path):
                    QMessageBox.information(self, "Success", f"Preview audio saved successfully to:\n{save_path}")
                else:
                    QMessageBox.critical(self, "Error", "Failed to render preview audio.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export WAV: {e}")

    def export_arduino(self):
        if not self.converter.notes:
            QMessageBox.warning(self, "Warning", "Please load a MIDI file first.")
            return

        self.converter.song_name = self.input_song.text().strip()
        self.converter.artist = self.input_artist.text().strip()
        project_name = self.converter.get_project_name()

        default_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Songs")
        target_folder = os.path.join(default_root, project_name)
        target_file = os.path.join(target_folder, f"{project_name}.ino")
        
        reply = QMessageBox.question(self, "Export Confirmation", 
                                   f"Export to:\n{target_file}\n\nProceed?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.converter.enable_drums = self.chk_drums.isChecked()
                self.converter.drum_mode = self.combo_drums.currentText()
                self.converter.enable_led_sync = self.chk_led_sync.isChecked()
                self.converter.enable_button_control = self.chk_button_ctrl.isChecked()
                if hasattr(self, 'combo_led_mode'):
                    self.converter.led_mode = self.combo_led_mode.currentText()

                self.converter.export_arduino(target_file)
                QMessageBox.information(self, "Success", f"Exported successfully to:\n{target_folder}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def direct_upload_song(self):
        """Compiles and flashes the song directly to Maker UNO without Arduino IDE."""
        if not self.converter.notes:
            QMessageBox.warning(self, "Warning", "Please load a MIDI file first.")
            return

        port = self.get_selected_port("studio")
        if not port:
            QMessageBox.warning(self, "Warning", "Please select a valid COM port.")
            return

        self.converter.song_name = self.input_song.text().strip()
        self.converter.artist = self.input_artist.text().strip()
        self.converter.enable_drums = self.chk_drums.isChecked()
        self.converter.drum_mode = self.combo_drums.currentText()
        self.converter.enable_led_sync = self.chk_led_sync.isChecked()
        self.converter.enable_button_control = self.chk_button_ctrl.isChecked()
        if hasattr(self, 'combo_led_mode'):
            self.converter.led_mode = self.combo_led_mode.currentText()
        
        temp_dir = os.path.join(tempfile.gettempdir(), "MakerUno_Upload")
        sketch_name = "MakerUno_Upload"
        sketch_folder = os.path.join(temp_dir, sketch_name)
        sketch_file = os.path.join(sketch_folder, f"{sketch_name}.ino")
        
        self.converter.export_arduino(sketch_file)

        self.btn_direct_upload.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.lbl_global_status.setText("Compiling and uploading to Maker UNO...")

        def _worker():
            def _cb(msg):
                self.lbl_global_status.setText(msg)

            self.health_engine.stop_monitoring()
            ok, log = self.uploader.compile_and_upload(sketch_file, port, progress_callback=_cb)
            
            def _finish():
                self.btn_direct_upload.setEnabled(True)
                self.progress_bar.setVisible(False)
                if ok:
                    QMessageBox.information(self, "Upload Success", f"Song flashed successfully to Maker UNO on {port}!\nPlaying now...")
                else:
                    QMessageBox.critical(self, "Upload Failed", f"Upload error:\n{log}")
            QTimer.singleShot(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    def flash_diagnostic_firmware(self):
        port = self.get_selected_port("health")
        if not port:
            QMessageBox.warning(self, "Warning", "Please select a valid COM port.")
            return

        temp_dir = os.path.join(tempfile.gettempdir(), "MakerUno_HealthCheck")
        sketch_name = "MakerUno_HealthCheck"
        sketch_folder = os.path.join(temp_dir, sketch_name)
        os.makedirs(sketch_folder, exist_ok=True)
        sketch_file = os.path.join(sketch_folder, f"{sketch_name}.ino")

        with open(sketch_file, 'w') as f:
            f.write(self.health_engine.generate_diagnostic_sketch())

        self.btn_flash_diag.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.lbl_global_status.setText("Flashing Health Diagnostics firmware...")

        def _worker():
            def _cb(msg):
                self.lbl_global_status.setText(msg)

            self.health_engine.stop_monitoring()
            ok, log = self.uploader.compile_and_upload(sketch_file, port, progress_callback=_cb)

            def _finish():
                self.btn_flash_diag.setEnabled(True)
                self.progress_bar.setVisible(False)
                if ok:
                    QMessageBox.information(self, "Diagnostic Firmware Flashed", 
                                            f"Diagnostics installed on {port}!\nConnecting telemetry stream...")
                    self.start_health_monitoring(port)
                else:
                    QMessageBox.critical(self, "Diagnostic Upload Failed", f"Error:\n{log}")
            QTimer.singleShot(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    def toggle_health_monitoring(self):
        if self.health_engine.is_monitoring:
            self.health_engine.stop_monitoring()
            self.btn_monitor_toggle.setText("🩺 Connect & Read Health")
            self.btn_monitor_toggle.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #00ff88; color: #000;")
            self.lbl_global_status.setText("Health monitoring disconnected.")
        else:
            port = self.get_selected_port("health")
            if not port:
                QMessageBox.warning(self, "Warning", "Please select a COM port.")
                return
            self.start_health_monitoring(port)

    def start_health_monitoring(self, port: str):
        self.btn_monitor_toggle.setText("⏹ Stop Telemetry")
        self.btn_monitor_toggle.setStyleSheet("padding: 6px 14px; font-weight: bold; background: #ff4444; color: #fff;")
        self.lbl_global_status.setText(f"Listening to Maker UNO health telemetry on {port}...")

        def _on_telemetry(data):
            QTimer.singleShot(0, lambda: self.update_health_ui(data))

        self.health_engine.start_monitoring(port, callback=_on_telemetry)

    def update_health_ui(self, data: dict):
        if "error" in data:
            self.txt_health_log.append(f"[ERROR] {data['error']}")
            return

        if "raw" in data:
            self.txt_health_log.append(f">> {data['raw']}")
            return

        if "score" in data:
            score = data['score']
            grade = data['grade']
            self.lbl_score_num.setText(f"{score}%")
            self.lbl_score_grade.setText(f"BOARD HEALTH: {grade}")
            
            if score >= 90:
                color = "#00ff88"
            elif score >= 75:
                color = "#00f2ff"
            elif score >= 50:
                color = "#ffaa00"
            else:
                color = "#ff4444"

            self.lbl_score_num.setStyleSheet(f"font-size: 38px; font-weight: bold; color: {color};")
            self.lbl_score_summary.setText(data.get('summary', ''))

            vcc = data.get('vcc_v', 5.0)
            self.card_vcc.lbl_val.setText(f"{vcc:.3f} V")
            self.card_vcc.lbl_sub.setText(data.get('status_vcc', ''))

            temp = data.get('temp_c', 28.0)
            self.card_temp.lbl_val.setText(f"{temp:.1f} °C")
            self.card_temp.lbl_sub.setText(data.get('status_temp', ''))

            free_ram = data.get('free_ram', 1700)
            ram_pct = data.get('ram_percent', 83.0)
            self.card_ram.lbl_val.setText(f"{free_ram} / 2,048 B")
            self.card_ram.lbl_sub.setText(f"{ram_pct}% Dynamic SRAM Free")

            eeprom_ok = data.get('eeprom_ok', True)
            self.card_eeprom.lbl_val.setText("Verified OK" if eeprom_ok else "FAILED")
            self.card_eeprom.lbl_sub.setText("Retention Test Passed" if eeprom_ok else "Integrity Degraded")

            jitter = data.get('jitter_ms', 0.0)
            self.card_jitter.lbl_val.setText(f"{jitter:.2f} ms")
            self.card_jitter.lbl_sub.setText(data.get('status_clock', ''))

            btn_pressed = data.get('btn_pressed', False)
            self.card_button.lbl_val.setText("🔴 PRESSED" if btn_pressed else "IDLE")
            self.card_button.lbl_val.setStyleSheet("color: #00ff88; font-size: 17px; font-weight: bold;" if btn_pressed else "color: #ffffff; font-size: 17px; font-weight: bold;")

            self.txt_health_log.append(f"[HEALTH] Vcc={vcc:.3f}V | Temp={temp:.1f}C | RAM={free_ram}B | Score={score}% | Uptime={data.get('uptime_s', 0)}s")

    def closeEvent(self, event):
        self.stop_play()
        self.health_engine.stop_monitoring()
        event.accept()

App = MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(26, 29, 36))
    palette.setColor(palette.ColorRole.WindowText, QColor(240, 240, 240))
    palette.setColor(palette.ColorRole.Base, QColor(17, 20, 26))
    palette.setColor(palette.ColorRole.Text, QColor(240, 240, 240))
    palette.setColor(palette.ColorRole.Button, QColor(37, 42, 52))
    palette.setColor(palette.ColorRole.ButtonText, QColor(240, 240, 240))
    palette.setColor(palette.ColorRole.Highlight, QColor(0, 242, 255))
    palette.setColor(palette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
