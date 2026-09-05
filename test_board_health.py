import unittest
from board_health import BoardHealthEngine

class TestBoardHealthEngine(unittest.TestCase):
    def setUp(self):
        self.engine = BoardHealthEngine()

    def test_generate_diagnostic_sketch(self):
        sketch = BoardHealthEngine.generate_diagnostic_sketch()
        self.assertIn("readVcc()", sketch)
        self.assertIn("readMcuTemp()", sketch)
        self.assertIn("getFreeRam()", sketch)
        self.assertIn("testEepromIntegrity()", sketch)
        self.assertIn("sweepLeds", sketch)
        self.assertIn("testBuzzer", sketch)
        self.assertIn("BUZZER_PIN 8", sketch)
        self.assertIn("BUTTON_PIN 2", sketch)

    def test_calculate_health_score_optimal(self):
        telemetry = {
            "type": "HEALTH",
            "vcc_v": 5.02,
            "temp_c": 28.5,
            "free_ram": 1720,
            "eeprom_ok": True,
            "uptime_ms": 5000,
            "jitter_ms": 0.05
        }
        res = self.engine.calculate_health_score(telemetry)
        self.assertEqual(res["score"], 100)
        self.assertEqual(res["grade"], "A (EXCELLENT)")
        self.assertEqual(res["status_vcc"], "Optimal")
        self.assertEqual(res["status_temp"], "Normal")
        self.assertEqual(res["status_eeprom"], "Verified")
        self.assertEqual(len(res["issues"]), 0)

    def test_calculate_health_score_low_voltage(self):
        telemetry = {
            "type": "HEALTH",
            "vcc_v": 4.30, # Critical under-voltage
            "temp_c": 30.0,
            "free_ram": 1600,
            "eeprom_ok": True,
            "uptime_ms": 1000,
            "jitter_ms": 0.1
        }
        res = self.engine.calculate_health_score(telemetry)
        self.assertTrue(res["score"] < 75)
        self.assertIn("Critical Low", res["status_vcc"])
        self.assertTrue(len(res["issues"]) > 0)

    def test_calculate_health_score_eeprom_failure(self):
        telemetry = {
            "type": "HEALTH",
            "vcc_v": 5.00,
            "temp_c": 28.0,
            "free_ram": 1700,
            "eeprom_ok": False, # Failed
            "uptime_ms": 2000,
            "jitter_ms": 0.0
        }
        res = self.engine.calculate_health_score(telemetry)
        self.assertEqual(res["score"], 75)
        self.assertIn("Failed", res["status_eeprom"])

    def test_parse_serial_line_json(self):
        line = '{"type":"HEALTH","vcc_v":4.980,"temp_c":29.1,"free_ram":1680,"total_ram":2048,"eeprom_ok":true,"btn_pressed":false,"uptime_ms":3000,"jitter_ms":0.02}'
        res = self.engine.parse_serial_line(line)
        self.assertEqual(res["vcc_v"], 4.98)
        self.assertEqual(res["temp_c"], 29.1)
        self.assertEqual(res["free_ram"], 1680)
        self.assertEqual(res["score"], 100)

if __name__ == '__main__':
    unittest.main()
