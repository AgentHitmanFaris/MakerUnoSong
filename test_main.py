import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Create a robust mock for PySide6 / PyQt6 to allow class inheritance and testing without GUI display
class MockQtWidget:
    def __init__(self, *args, **kwargs):
        self.lbl_val = MagicMock()
        self.lbl_sub = MagicMock()
        self._text = ""
        self._items = []

    def isChecked(self): return True
    def text(self): return self._text
    def setText(self, val): self._text = str(val)
    def currentText(self): return "COM3 (Silicon Labs)"
    def currentData(self): return "COM3"
    def count(self): return len(self._items)
    def addWidget(self, w, *args, **kwargs): self._items.append(w)
    def addStretch(self, *args): pass
    def takeAt(self, idx):
        if 0 <= idx < len(self._items):
            return self._items.pop(idx)
        return None
    
    def __getattr__(self, name):
        mock_func = MagicMock()
        setattr(self, name, mock_func)
        return mock_func

mock_qt = MagicMock()
for w in ['QMainWindow', 'QWidget', 'QVBoxLayout', 'QHBoxLayout', 'QPushButton', 'QFileDialog',
          'QGraphicsView', 'QGraphicsScene', 'QGraphicsRectItem', 'QLabel', 'QMessageBox',
          'QLineEdit', 'QFormLayout', 'QCheckBox', 'QComboBox', 'QTabWidget', 'QProgressBar',
          'QTextEdit', 'QGroupBox', 'QGridLayout', 'QFrame', 'QScrollArea']:
    setattr(mock_qt.QtWidgets, w, MockQtWidget)

mock_qt.QtCore.Qt.AlignmentFlag.AlignCenter = 0

sys.modules['PySide6'] = mock_qt
sys.modules['PySide6.QtWidgets'] = mock_qt.QtWidgets
sys.modules['PySide6.QtCore'] = mock_qt.QtCore
sys.modules['PySide6.QtGui'] = MagicMock()

sys.modules['PyQt6'] = mock_qt
sys.modules['PyQt6.QtWidgets'] = mock_qt.QtWidgets
sys.modules['PyQt6.QtCore'] = mock_qt.QtCore
sys.modules['PyQt6.QtGui'] = MagicMock()

from main import MainWindow, App

class TestMainApp(unittest.TestCase):
    @patch('main.board_health.BoardHealthEngine')
    @patch('main.uploader.ArduinoUploader')
    @patch('main.converter.MidiConverter')
    @patch('main.os.makedirs')
    @patch('main.os.path.exists')
    def setUp(self, mock_exists, mock_makedirs, mock_converter, mock_uploader, mock_health):
        self.app = MainWindow()
        self.app.converter = mock_converter.return_value
        self.app.uploader = mock_uploader.return_value
        self.app.health_engine = mock_health.return_value

    @patch('main.QMessageBox')
    def test_export_arduino_no_notes(self, mock_msgbox):
        self.app.converter.notes = []
        self.app.export_arduino()
        mock_msgbox.warning.assert_called_with(self.app, "Warning", "Please load a MIDI file first.")

    @patch('main.QMessageBox')
    def test_export_arduino_success(self, mock_msgbox):
        self.app.converter.notes = [{'pitch': 60, 'duration': 500}]
        self.app.input_song = MagicMock()
        self.app.input_song.text.return_value = "Test Song"
        self.app.input_artist = MagicMock()
        self.app.input_artist.text.return_value = "Test Artist"
        self.app.converter.get_project_name.return_value = "Test_Project"
        
        self.app.chk_drums = MagicMock()
        self.app.chk_drums.isChecked.return_value = True
        self.app.combo_drums = MagicMock()
        self.app.combo_drums.currentText.return_value = "Auto-Gen: Rock"
        self.app.chk_led_sync = MagicMock()
        self.app.chk_led_sync.isChecked.return_value = True
        self.app.chk_button_ctrl = MagicMock()
        self.app.chk_button_ctrl.isChecked.return_value = True

        mock_msgbox.StandardButton.Yes = 16384
        mock_msgbox.StandardButton.No = 65536
        mock_msgbox.question.return_value = 16384

        with patch('main.os.path.exists', return_value=True):
            with patch('main.os.makedirs'):
                self.app.export_arduino()
                self.assertEqual(self.app.converter.song_name, "Test Song")
                self.assertEqual(self.app.converter.artist, "Test Artist")
                self.app.converter.export_arduino.assert_called()

    def test_health_ui_update(self):
        data = {
            "score": 98,
            "grade": "A (EXCELLENT)",
            "summary": "All systems nominal",
            "vcc_v": 5.01,
            "temp_c": 29.0,
            "free_ram": 1720,
            "ram_percent": 84.0,
            "eeprom_ok": True,
            "jitter_ms": 0.01,
            "btn_pressed": False,
            "uptime_s": 10.0,
            "status_vcc": "Optimal",
            "status_temp": "Normal",
            "status_clock": "Stable"
        }
        self.app.update_health_ui(data)
        self.assertEqual(self.app.lbl_score_num.text(), "98%")

    def test_virtual_board_visuals(self):
        self.app.virtual_board.update_visuals(active_pin=13, freq=440, btn_pressed=True)
        self.assertIn("440 Hz", self.app.virtual_board.lbl_buzzer.text())
        self.assertIn("PRESSED", self.app.virtual_board.lbl_btn.text())

        self.app.virtual_board.reset()
        self.assertIn("Standby", self.app.virtual_board.lbl_buzzer.text())

    @patch('main.QMessageBox')
    def test_auto_pipeline_execution(self, mock_msgbox):
        self.app.converter.notes = [{'pitch': 60, 'start': 0, 'duration': 400}]
        self.app.converter._process_drums.return_value = [{'pitch': 60, 'start': 0, 'duration': 400}]
        self.app.uploader.list_ports.return_value = [{'port': 'COM4', 'is_maker_uno': True, 'display': 'COM4'}]
        with patch.object(self.app, 'direct_upload_song') as mock_upload:
            self.app.run_auto_pipeline()
            self.assertEqual(self.app.converter.drum_mode, "🧠 Smart Adaptive AI")
            mock_upload.assert_called_once()

    def test_piano_roll_zoom_and_autoscroll(self):
        roll = self.app.piano_roll
        init_zoom = roll._zoom_factor
        self.app.on_zoom_in()
        self.assertGreater(roll._zoom_factor, init_zoom)
        self.app.on_zoom_out()
        self.assertAlmostEqual(roll._zoom_factor, init_zoom, places=2)
        self.app.on_zoom_reset()
        self.assertEqual(roll._zoom_factor, 1.0)
        
        self.assertTrue(roll.autoscroll)
        self.app.on_autoscroll_toggled(False)
        self.assertFalse(roll.autoscroll)
        self.app.on_autoscroll_toggled(True)
        self.assertTrue(roll.autoscroll)

if __name__ == '__main__':
    unittest.main()
