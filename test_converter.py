from unittest.mock import MagicMock, patch
import sys

# Mock mido before importing MidiConverter
sys.modules['mido'] = MagicMock()
import mido

from converter import MidiConverter

class TestMidiConverter(unittest.TestCase):
    def setUp(self):
        self.converter = MidiConverter()

    def test_note_to_freq(self):
        # Edge cases
        self.assertEqual(self.converter.note_to_freq(None), 0)
        self.assertEqual(self.converter.note_to_freq(0), 0)
        
        # Special drum markers
        self.assertEqual(self.converter.note_to_freq(128), -1)
        self.assertEqual(self.converter.note_to_freq(129), -2)
        
        # Standard notes
        self.assertEqual(self.converter.note_to_freq(69), 440)
        self.assertEqual(self.converter.note_to_freq(60), 261)
        self.assertEqual(self.converter.note_to_freq(21), 27)
        self.assertEqual(self.converter.note_to_freq(108), 4186)

    @patch('mido.MidiFile')
    def test_load_midi_metadata_from_filename(self, mock_midi_file_class):
        # Setup mock behavior
        mock_mid = mock_midi_file_class.return_value
        mock_mid.tracks = []
        mock_mid.__iter__.return_value = [] # For the second pass in load_midi
        
        # Verify "(Artist)" pattern in filename
        self.converter.load_midi("Die On This Hill (NC-Dance).mid")
        self.assertEqual(self.converter.song_name, "Die On This Hill")
        self.assertEqual(self.converter.artist, "NC-Dance")

    @patch('mido.MidiFile')
    def test_load_midi_metadata_from_messages(self, mock_midi_file_class):
        # Setup mock messages for meta info pass
        mock_mid = mock_midi_file_class.return_value
        
        # Mocking messages
        msg_tempo = MagicMock(type='set_tempo', tempo=500000) # 120 BPM
        msg_time_sig = MagicMock(type='time_signature', numerator=3, denominator=4)
        msg_key_sig = MagicMock(type='key_signature', key='G')
        msg_track_name = MagicMock(type='track_name', name='Piano Solo')
        
        mock_mid.tracks = [[msg_tempo, msg_time_sig, msg_key_sig, msg_track_name]]
        mock_mid.__iter__.return_value = []
        
        # Mock tempo2bpm (which we use in converter.py)
        mido.tempo2bpm.return_value = 120
        
        self.converter.load_midi("simple.mid")
        self.assertEqual(self.converter.bpm, 120)
        self.assertEqual(self.converter.time_signature, "3/4")
        self.assertEqual(self.converter.key_signature, "G")
        self.assertEqual(self.converter.song_name, "Piano Solo")

    @patch('mido.MidiFile')
    def test_load_midi_notes_parsing(self, mock_midi_file_class):
        mock_mid = mock_midi_file_class.return_value
        mock_mid.tracks = []
        
        # Mocking the iterator for note parsing
        # (msg.time is in fractional seconds in the iterator)
        msg_on = MagicMock(type='note_on', note=60, velocity=64, time=0.0) # Start at 0ms
        msg_off = MagicMock(type='note_off', note=60, velocity=0, time=0.5) # 500ms duration
        msg_snare = MagicMock(type='note_on', note=38, velocity=64, time=0.1, channel=9) # Drum channel
        
        mock_mid.__iter__.return_value = [msg_on, msg_off, msg_snare]
        
        self.converter.load_midi("test.mid")
        
        # Should have 1 note (the snare is note_on but lacks note_off in this short mock, 
        # actually let's just check the note parsing logic)
        # Note: load_midi appends to self.notes
        self.assertTrue(len(self.converter.notes) >= 1)
        self.assertEqual(self.converter.notes[0]['pitch'], 60)
        self.assertEqual(self.converter.notes[0]['duration'], 500)

if __name__ == '__main__':
    unittest.main()
