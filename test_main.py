import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Create a robust mock for PyQt6 to allow class inheritance
class MockQtWidget:
    def __init__(self, *args, **kwargs): pass
    def setWindowTitle(self, *args): pass
    def setFixedSize(self, *args): pass
    def setLayout(self, *args): pass
    def setCentralWidget(self, *args): pass
    def isChecked(self): return False
    def text(self): return ""
    def currentText(self): return ""
    def setText(self, *args): pass

# Mock the entire PyQt6 hierarchy
mock_qt = MagicMock()
mock_qt.QtWidgets.QMainWindow = MockQtWidget
mock_qt.QtWidgets.QWidget = MockQtWidget
mock_qt.QtWidgets.QVBoxLayout = MagicMock
mock_qt.QtWidgets.QHBoxLayout = MagicMock
mock_qt.QtWidgets.QPushButton = MockQtWidget
mock_qt.QtWidgets.QFileDialog = MagicMock
mock_qt.QtWidgets.QGraphicsView = MockQtWidget
mock_qt.QtWidgets.QGraphicsScene = MagicMock
mock_qt.QtWidgets.QGraphicsRectItem = MagicMock
mock_qt.QtWidgets.QLabel = MockQtWidget
mock_qt.QtWidgets.QMessageBox = MagicMock
mock_qt.QtWidgets.QLineEdit = MockQtWidget
mock_qt.QtWidgets.QFormLayout = MagicMock
mock_qt.QtWidgets.QCheckBox = MockQtWidget
mock_qt.QtWidgets.QComboBox = MockQtWidget
mock_qt.QtCore.Qt.AlignmentFlag.AlignCenter = 0

sys.modules['PyQt6'] = mock_qt
sys.modules['PyQt6.QtWidgets'] = mock_qt.QtWidgets
sys.modules['PyQt6.QtCore'] = mock_qt.QtCore
sys.modules['PyQt6.QtGui'] = MagicMock()

# Inject QMessageBox buttons needed for export_arduino logic
from PyQt6.QtWidgets import QMessageBox
QMessageBox.StandardButton = MagicMock()
QMessageBox.StandardButton.Yes = 16384
QMessageBox.StandardButton.No = 65536

# Now import App from main
import main
from main import App

class TestMainApp(unittest.TestCase):
    @patch('main.MidiConverter')
    @patch('main.os.makedirs')
    @patch('main.os.path.exists')
    def setUp(self, mock_exists, mock_makedirs, mock_converter_class):
        # Prevent __init__ from doing too much if necessary, 
        # but here we'll just let it run with mocks
        self.app = App()
        self.app.converter = mock_converter_class.return_value
        
        # Re-mock UI elements to control their return values
        self.app.input_song = MagicMock()
        self.app.input_artist = MagicMock()
        self.app.chk_drums = MagicMock()
        self.app.combo_drums = MagicMock()

    @patch('main.QMessageBox')
    def test_export_arduino_no_notes(self, mock_msgbox):
        self.app.converter.notes = []
        self.app.export_arduino()
        mock_msgbox.warning.assert_called_with(self.app, "Warning", "Please load a MIDI file first.")

    @patch('main.QMessageBox')
    def test_export_arduino_success(self, mock_msgbox):
        # Setup state
        self.app.converter.notes = [{'pitch': 60, 'duration': 500}]
        self.app.input_song.text.return_value = "Test Song"
        self.app.input_artist.text.return_value = "Test Artist"
        self.app.converter.get_project_name.return_value = "Test_Project"
        self.app.chk_drums.isChecked.return_value = True
        self.app.combo_drums.currentText.return_value = "Auto-Gen: Rock"
        
        # Mock confirmation dialog to say 'Yes'
        mock_msgbox.StandardButton.Yes = 16384
        mock_msgbox.question.return_value = 16384
        
        with patch('main.os.path.exists', return_value=True):
            with patch('main.os.makedirs'):
                self.app.export_arduino()
                
                # Verify metadata was pushed to converter
                self.assertEqual(self.app.converter.song_name, "Test Song")
                self.assertEqual(self.app.converter.artist, "Test Artist")
                
                # Verify converter settings were applied
                self.assertEqual(self.app.converter.enable_drums, True)
                self.assertEqual(self.app.converter.drum_mode, "Auto-Gen: Rock")
                
                # Verify converter export was triggered
                self.app.converter.export_arduino.assert_called()
                
                # Verify success message
                mock_msgbox.information.assert_called()

if __name__ == '__main__':
    unittest.main()
