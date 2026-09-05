import unittest
from unittest.mock import MagicMock, patch
import os
from uploader import ArduinoUploader

class TestArduinoUploader(unittest.TestCase):
    def setUp(self):
        self.uploader = ArduinoUploader()

    @patch('serial.tools.list_ports.comports')
    def test_list_ports(self, mock_comports):
        p1 = MagicMock()
        p1.device = "COM3"
        p1.description = "Silicon Labs CP210x USB to UART Bridge (COM3)"
        p1.hwid = "USB VID:PID=10C4:EA60"

        p2 = MagicMock()
        p2.device = "COM1"
        p2.description = "Communications Port (COM1)"
        p2.hwid = "ACPI\\PNP0501"

        mock_comports.return_value = [p1, p2]

        ports = ArduinoUploader.list_ports()
        self.assertEqual(len(ports), 2)
        self.assertEqual(ports[0]['port'], "COM3")
        self.assertTrue(ports[0]['is_maker_uno'])
        self.assertIn("Maker UNO", ports[0]['display'])

        self.assertEqual(ports[1]['port'], "COM1")
        self.assertFalse(ports[1]['is_maker_uno'])

    @patch('subprocess.run')
    def test_compile_sketch_success(self, mock_run):
        self.uploader.cli_path = "mock-arduino-cli"
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "Sketch uses 4500 bytes (13%) of program storage space."
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        with patch.object(self.uploader, 'ensure_toolchain', return_value=True):
            ok, output = self.uploader.compile("test/test.ino")
            self.assertTrue(ok)
            self.assertIn("4500 bytes", output)

if __name__ == '__main__':
    unittest.main()
