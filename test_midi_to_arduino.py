import unittest
from unittest.mock import MagicMock
import sys

# Mock mido before importing midi_to_arduino
sys.modules['mido'] = MagicMock()

from midi_to_arduino import note_to_freq

class TestMidiToArduino(unittest.TestCase):
    def test_note_to_freq(self):
        # A4 = 440Hz
        self.assertEqual(note_to_freq(69), 440)
        # C4 = 261.63... -> 261
        self.assertEqual(note_to_freq(60), 261)
        # A0 = 27.5Hz -> 27
        self.assertEqual(note_to_freq(21), 27)
        # C8 = 4186.01... -> 4186
        self.assertEqual(note_to_freq(108), 4186)

if __name__ == '__main__':
    unittest.main()
