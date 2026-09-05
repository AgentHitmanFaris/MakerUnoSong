import unittest
import os
import io
import wave
import tempfile
from audio_preview import AudioPreviewEngine

class TestAudioPreviewEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AudioPreviewEngine()

    def test_synthesize_segments_and_wav_format(self):
        # Segments: tone (440Hz), silence (0Hz), kick (28), snare (-1), hihat (-2)
        segments = [
            (440, 200),  # 440 Hz for 200ms
            (0, 100),    # Rest for 100ms
            (28, 100),   # Kick blip for 100ms
            (-1, 100),   # Snare noise for 100ms
            (-2, 50),    # Hi-hat tick for 50ms
        ]
        wav_data = self.engine.synthesize(segments, tempo_multiplier=1.0)
        self.assertIsNotNone(wav_data)
        self.assertTrue(len(wav_data) > 44) # WAV header is at least 44 bytes

        # Read back with wave module to verify container validity
        with wave.open(io.BytesIO(wav_data), 'rb') as wf:
            self.assertEqual(wf.getnchannels(), 1)
            self.assertEqual(wf.getsampwidth(), 2)
            self.assertEqual(wf.getframerate(), AudioPreviewEngine.SAMPLE_RATE)
            self.assertTrue(wf.getnframes() > 0)

    def test_tempo_multiplier_duration_scaling(self):
        segments = [(440, 500)]
        # Normal speed
        self.engine.synthesize(segments, tempo_multiplier=1.0)
        dur_1x = self.engine.total_duration_ms
        self.assertEqual(dur_1x, 500)

        # 2x speed -> half duration
        self.engine.synthesize(segments, tempo_multiplier=2.0)
        dur_2x = self.engine.total_duration_ms
        self.assertEqual(dur_2x, 250)

        # 0.5x speed -> double duration
        self.engine.synthesize(segments, tempo_multiplier=0.5)
        dur_half = self.engine.total_duration_ms
        self.assertEqual(dur_half, 1000)

    def test_get_led_state_at_ms(self):
        segments = [
            (440, 200), # 0 to 200ms -> buzzer frequency mapped
            (0, 100),   # 200 to 300ms -> silence
            (28, 100),  # 300 to 400ms -> kick drum (Pin 13)
            (-1, 100),  # 400 to 500ms -> snare (Pin 7)
        ]
        self.engine.synthesize(segments)

        # At 50ms: 440 Hz
        pin, freq = self.engine.get_led_state_at_ms(50)
        self.assertEqual(freq, 440)
        self.assertTrue(3 <= pin <= 13)

        # At 250ms: rest
        pin, freq = self.engine.get_led_state_at_ms(250)
        self.assertEqual(freq, 0)
        self.assertEqual(pin, 0)

        # At 350ms: kick (Pin 13)
        pin, freq = self.engine.get_led_state_at_ms(350)
        self.assertEqual(freq, 28)
        self.assertEqual(pin, 13)

        # At 450ms: snare (Pin 7)
        pin, freq = self.engine.get_led_state_at_ms(450)
        self.assertEqual(freq, -1)
        self.assertEqual(pin, 7)

    def test_export_wav_file(self):
        segments = [(440, 100), (-1, 100)]
        self.engine.synthesize(segments)

        temp_dir = tempfile.gettempdir()
        out_wav = os.path.join(temp_dir, "test_preview_out.wav")
        try:
            ok = self.engine.export_wav(out_wav)
            self.assertTrue(ok)
            self.assertTrue(os.path.exists(out_wav))
            self.assertTrue(os.path.getsize(out_wav) > 100)
        finally:
            if os.path.exists(out_wav):
                os.remove(out_wav)

if __name__ == '__main__':
    unittest.main()
