import unittest
from unittest.mock import MagicMock, patch
import sys
import os

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

    @patch('converter.mido.MidiFile')
    def test_load_midi_metadata_from_filename(self, mock_midi_file_class):
        mock_mid = mock_midi_file_class.return_value
        mock_mid.__iter__.side_effect = lambda: iter([])
        
        self.converter.load_midi("Die On This Hill (NC-Dance).mid")
        self.assertEqual(self.converter.song_name, "Die On This Hill")
        self.assertEqual(self.converter.artist, "NC-Dance")

    @patch('converter.mido.tempo2bpm', return_value=120)
    @patch('converter.mido.MidiFile')
    def test_load_midi_metadata_from_messages(self, mock_midi_file_class, mock_tempo2bpm):
        mock_mid = mock_midi_file_class.return_value
        
        msg_tempo = MagicMock(type='set_tempo', tempo=500000, is_meta=True, time=0.0)
        msg_time_sig = MagicMock(type='time_signature', numerator=3, denominator=4, is_meta=True, time=0.0)
        msg_key_sig = MagicMock(type='key_signature', key='G', is_meta=True, time=0.0)
        msg_track_name = MagicMock(type='track_name', is_meta=True, time=0.0)
        msg_track_name.name = 'Piano Solo'
        
        mock_mid.__iter__.side_effect = lambda: iter([msg_tempo, msg_time_sig, msg_key_sig, msg_track_name])
        
        self.converter.load_midi("simple.mid")
        self.assertEqual(self.converter.bpm, 120)
        self.assertEqual(self.converter.time_signature, "3/4")
        self.assertEqual(self.converter.key_signature, "G")
        self.assertEqual(self.converter.song_name, "Piano Solo")

    @patch('converter.mido.MidiFile')
    def test_load_midi_notes_parsing(self, mock_midi_file_class):
        mock_mid = mock_midi_file_class.return_value
        
        msg_on = MagicMock(type='note_on', note=60, velocity=64, time=0.0, channel=0, is_meta=False)
        msg_off = MagicMock(type='note_off', note=60, velocity=0, time=0.5, channel=0, is_meta=False)
        
        mock_mid.__iter__.side_effect = lambda: iter([msg_on, msg_off])
        
        self.converter.load_midi("test.mid")
        self.assertTrue(len(self.converter.notes) >= 1)
        self.assertEqual(self.converter.notes[0]['pitch'], 60)
        self.assertEqual(self.converter.notes[0]['duration'], 500)

    def test_sanitize_str(self):
        self.assertEqual(MidiConverter.sanitize_str("Hello/*World*/"), "Hello  World")
        self.assertEqual(MidiConverter.sanitize_str(None), "Unknown")

    def test_drum_processing_and_optimization(self):
        self.converter.notes = [
            {'start': 0, 'duration': 200, 'pitch': 60, 'channel': 0},
            {'start': 200, 'duration': 200, 'pitch': 62, 'channel': 0},
        ]
        self.converter.update_duration()
        self.converter.enable_drums = True
        self.converter.drum_mode = "Auto-Gen: Rock"
        drums = self.converter._process_drums()
        self.assertTrue(len(drums) >= 2)

        segments = self.converter._generate_segments(drums)
        optimized = self.converter._optimize_segments(segments)
        self.assertTrue(len(optimized) > 0)

        code = self.converter._build_arduino_code(optimized)
        self.assertIn("BUZZER_PIN", code)
        self.assertIn("LED_PINS", code)
        self.assertIn("BUTTON_PIN", code)

    def test_smart_adaptive_beat_processing(self):
        self.converter.notes = [
            {'start': i * 500, 'duration': 400, 'pitch': 60 + (i % 8), 'channel': 0} for i in range(16)
        ]
        self.converter.update_duration()
        self.converter.enable_drums = True
        self.converter.drum_mode = "🧠 Smart Adaptive AI"
        processed = self.converter._process_drums()
        self.assertTrue(len(processed) > len(self.converter.notes))
        # Ensure drums exist
        drum_pitches = {n['pitch'] for n in processed if n.get('channel', 0) == 9}
        self.assertTrue(28 in drum_pitches or 128 in drum_pitches or 129 in drum_pitches)

    def test_flash_usage_estimate(self):
        self.converter.notes = [
            {'start': 0, 'duration': 200, 'pitch': 60, 'channel': 0},
            {'start': 200, 'duration': 200, 'pitch': 64, 'channel': 0}
        ]
        self.converter.update_duration()
        estimate = self.converter.get_flash_usage_estimate()
        self.assertIn("segments", estimate)
        self.assertIn("progmem_bytes", estimate)
        self.assertIn("percent", estimate)
        self.assertTrue(estimate["segments"] >= 2)
        self.assertTrue(0 < estimate["percent"] < 100)

    def test_analyze_song_structure(self):
        self.converter.notes = [
            {'start': i * 250, 'duration': 200, 'pitch': 60, 'channel': 0} for i in range(32)
        ]
        self.converter.update_duration()
        analysis = self.converter.analyze_song_structure()
        self.assertIn("total_measures", analysis)
        self.assertIn("sections", analysis)
        self.assertIn("key_detected", analysis)

    def test_led_modes_in_code_generation(self):
        segments = [(440, 200), (0, 100)]
        
        self.converter.led_mode = "VU Meter"
        code_vu = self.converter._build_arduino_code(segments)
        self.assertIn("level = map", code_vu)

        self.converter.led_mode = "Knight Rider Scanner"
        code_kr = self.converter._build_arduino_code(segments)
        self.assertIn("scanPos", code_kr)

        self.converter.led_mode = "Drum Reactive"
        code_dr = self.converter._build_arduino_code(segments)
        self.assertIn("Kick: Bottom LEDs", code_dr)

    def test_preview_engine_creation(self):
        self.converter.notes = [
            {'start': 0, 'duration': 100, 'pitch': 69, 'channel': 0}
        ]
        self.converter.update_duration()
        engine = self.converter.get_preview_engine(tempo_multiplier=1.2)
        self.assertIsNotNone(engine)
        self.assertIsNotNone(engine.wav_bytes)
        self.assertEqual(engine.tempo_multiplier, 1.2)

if __name__ == '__main__':
    unittest.main()
