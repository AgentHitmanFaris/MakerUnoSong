import unittest
from smart_beat import SmartBeatEngine

class TestSmartBeatEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SmartBeatEngine()

    def test_detect_musical_key_c_major(self):
        # C Major scale notes: C (60), D (62), E (64), F (65), G (67), A (69), B (71)
        notes = []
        c_major_pitches = [60, 62, 64, 65, 67, 69, 71, 72]
        for idx, p in enumerate(c_major_pitches * 4):
            notes.append({'start': idx * 250, 'duration': 200, 'pitch': p, 'channel': 0})

        key, mode = SmartBeatEngine.detect_musical_key(notes)
        self.assertEqual(key, "C")
        self.assertEqual(mode, "Major")

    def test_detect_musical_key_a_minor(self):
        # A Minor scale notes: A (57, 69), B (59), C (60), D (62), E (64), F (65), G (67)
        # Heavily emphasizing A and C
        notes = []
        a_min_pitches = [69, 69, 60, 64, 69, 60, 64, 65, 69]
        for idx, p in enumerate(a_min_pitches * 4):
            notes.append({'start': idx * 250, 'duration': 200, 'pitch': p, 'channel': 0})

        key, mode = SmartBeatEngine.detect_musical_key(notes)
        self.assertEqual(key, "A")
        self.assertEqual(mode, "Minor")

    def test_analyze_structure_empty(self):
        res = SmartBeatEngine.analyze_structure([], 120)
        self.assertEqual(res["total_measures"], 0)
        self.assertEqual(len(res["sections"]), 0)

    def test_analyze_structure_and_sections(self):
        # Build 16 measures of varying energy
        # 120 BPM, 4/4 = 2000 ms per bar
        notes = []
        bar_ms = 2000

        # Bars 0-1: Intro (low density, 1 note per bar)
        notes.append({'start': 100, 'duration': 500, 'pitch': 60, 'channel': 0})
        notes.append({'start': bar_ms + 100, 'duration': 500, 'pitch': 60, 'channel': 0})

        # Bars 2-5: Verse (medium density, 4 notes per bar)
        for b in range(2, 6):
            for step in range(4):
                notes.append({'start': b * bar_ms + step * 500, 'duration': 400, 'pitch': 64, 'channel': 0})

        # Bars 6-9: Chorus (high density & high pitch, 8 notes per bar)
        for b in range(6, 10):
            for step in range(8):
                notes.append({'start': b * bar_ms + step * 250, 'duration': 200, 'pitch': 76, 'channel': 0})

        # Bars 10-11: Outro (low density)
        notes.append({'start': 10 * bar_ms, 'duration': 500, 'pitch': 60, 'channel': 0})
        notes.append({'start': 11 * bar_ms, 'duration': 500, 'pitch': 60, 'channel': 0})

        analysis = SmartBeatEngine.analyze_structure(notes, 120, "4/4")
        self.assertEqual(analysis["total_measures"], 12)
        self.assertTrue(len(analysis["sections"]) >= 3)
        section_names = [s["name"] for s in analysis["sections"]]
        self.assertIn("INTRO", section_names)
        self.assertIn("CHORUS", section_names)
        self.assertIn("OUTRO", section_names)

    def test_generate_intelligent_beat(self):
        # 8 measures of notes at 120 BPM
        notes = []
        for i in range(32):
            notes.append({'start': i * 500, 'duration': 400, 'pitch': 60 + (i % 8), 'channel': 0})

        drums = SmartBeatEngine.generate_intelligent_beat(notes, 120, "4/4", style="Adaptive AI")
        self.assertTrue(len(drums) > 0)

        # Check kick, snare, hi-hat presence
        pitches = {d['pitch'] for d in drums}
        self.assertIn(28, pitches)   # Kick
        self.assertIn(128, pitches)  # Snare
        self.assertIn(129, pitches)  # Hi-Hat

        # All events should be sorted chronologically
        starts = [d['start'] for d in drums]
        self.assertEqual(starts, sorted(starts))

    def test_smart_beat_cadence_fills(self):
        # Cadence fill should exist near bar transitions (e.g. bar 3 end or bar 7 end)
        notes = [{'start': i * 500, 'duration': 450, 'pitch': 60, 'channel': 0} for i in range(32)]
        drums = SmartBeatEngine.generate_intelligent_beat(notes, 120, "4/4", style="Adaptive AI")

        # In bar 3 (between 6000ms and 8000ms), there should be fill events (multiple fast snare hits)
        bar_3_snares = [d for d in drums if 6000 <= d['start'] < 8000 and d['pitch'] == 128]
        self.assertTrue(len(bar_3_snares) >= 4)

if __name__ == '__main__':
    unittest.main()
