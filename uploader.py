"""
Standalone Uploader & Toolchain Manager for Maker UNO / Arduino UNO.
Build by AgentHitmanFaris (NC-Engineering).

Allows direct 1-click compiling and uploading of .ino sketches without needing Arduino IDE.
"""

import os
import sys
import subprocess
import glob
import zipfile
import urllib.request
import threading
import serial.tools.list_ports

class ArduinoUploader:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tools_dir = os.path.join(self.base_dir, ".tools")
        self.cli_path = self._find_arduino_cli()

    def _find_arduino_cli(self) -> str | None:
        """Finds arduino-cli executable on the system or in local .tools."""
        # 1. Local tools folder
        local_cli = os.path.join(self.tools_dir, "bin", "arduino-cli.exe")
        if os.path.exists(local_cli):
            return local_cli

        # 2. Check PATH
        try:
            res = subprocess.run(["arduino-cli", "version"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                return "arduino-cli"
        except Exception:
            pass

        # 3. Check common Arduino IDE 2.x and standard locations
        search_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Arduino15\arduino-cli.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Arduino IDE\resources\app\node_modules\arduino-ide-extension\build\arduino-cli.exe"),
            r"C:\ProgramData\chocolatey\bin\arduino-cli.exe",
            os.path.expandvars(r"%USERPROFILE%\bin\arduino-cli.exe"),
        ]
        for p in search_paths:
            if os.path.exists(p):
                return p

        # Check glob inside Arduino IDE or LocalAppData
        ide_matches = glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Arduino IDE\**\arduino-cli.exe"), recursive=True)
        if ide_matches:
            return ide_matches[0]

        return None

    @staticmethod
    def list_ports():
        """
        Discovers all available serial/COM ports and highlights Maker UNO / Arduino compatible boards.
        Returns a list of dicts: [{'port': 'COM3', 'desc': '...', 'is_maker_uno': bool}]
        """
        ports = []
        for p in serial.tools.list_ports.comports():
            desc = p.description or ""
            hwid = p.hwid or ""
            is_uno = False
            
            # Common USB-to-UART chips on Maker UNO and Arduino UNO:
            # - Silicon Labs CP210x (10C4:EA60) - Standard Maker UNO
            # - CH340 / CH341 (1A86:7523) - Maker UNO Plus / Clones
            # - FTDI FT232R (0403:6001)
            # - ATmega16U2 (2341:0043 / 2341:0001) - Official Uno
            lower_desc = desc.lower()
            lower_hw = hwid.lower()

            if any(k in lower_desc for k in ["maker uno", "arduino", "ch340", "cp210", "ft232", "usb-serial", "usb serial"]):
                is_uno = True
            elif any(v in lower_hw for v in ["10c4:ea60", "1a86:7523", "0403:6001", "2341:0043", "2341:0001"]):
                is_uno = True

            ports.append({
                "port": p.device,
                "desc": desc,
                "hwid": hwid,
                "is_maker_uno": is_uno,
                "display": f"{p.device} ({desc})" + (" ⭐ [Maker UNO]" if is_uno else "")
            })
        return ports

    def ensure_toolchain(self, progress_callback=None) -> bool:
        """
        Ensures arduino-cli and the arduino:avr core (for ATmega328P) are installed.
        Downloads portable CLI if not found.
        """
        if self.cli_path and os.path.exists(self.cli_path):
            # Check if avr core is installed
            return self._ensure_avr_core(progress_callback)

        if progress_callback:
            progress_callback("Setting up standalone Arduino toolchain...")

        bin_dir = os.path.join(self.tools_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        local_cli = os.path.join(bin_dir, "arduino-cli.exe")

        # Download portable arduino-cli Windows 64-bit
        url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip"
        zip_dest = os.path.join(self.tools_dir, "arduino-cli.zip")

        try:
            if progress_callback:
                progress_callback("Downloading portable arduino-cli compiler...")
            urllib.request.urlretrieve(url, zip_dest)

            if progress_callback:
                progress_callback("Extracting toolchain...")
            with zipfile.ZipFile(zip_dest, 'r') as z:
                z.extractall(bin_dir)

            if os.path.exists(zip_dest):
                os.remove(zip_dest)

            self.cli_path = local_cli
            return self._ensure_avr_core(progress_callback)
        except Exception as e:
            if progress_callback:
                progress_callback(f"Failed to setup toolchain: {e}")
            return False

    def _ensure_avr_core(self, progress_callback=None) -> bool:
        """Checks and installs arduino:avr core for ATmega328P."""
        try:
            # Check core list
            res = subprocess.run([self.cli_path, "core", "list"], capture_output=True, text=True, timeout=15)
            if "arduino:avr" in res.stdout:
                return True

            if progress_callback:
                progress_callback("Updating core index & installing Arduino AVR platform...")
            
            subprocess.run([self.cli_path, "core", "update-index"], capture_output=True, text=True, timeout=30)
            install_res = subprocess.run([self.cli_path, "core", "install", "arduino:avr"], capture_output=True, text=True, timeout=120)
            return install_res.returncode == 0
        except Exception as e:
            if progress_callback:
                progress_callback(f"Core install notice: {e}")
            return False

    def compile(self, sketch_path: str, progress_callback=None) -> tuple[bool, str]:
        """
        Compiles an .ino sketch for Maker UNO / Arduino Uno (FQBN: arduino:avr:uno).
        Returns (success: bool, log: str).
        """
        if not self.ensure_toolchain(progress_callback):
            return False, "Failed to initialize Arduino toolchain."

        sketch_dir = os.path.dirname(os.path.abspath(sketch_path)) if os.path.isfile(sketch_path) else sketch_path
        
        if progress_callback:
            progress_callback(f"Compiling sketch {os.path.basename(sketch_path)} for ATmega328P...")

        cmd = [
            self.cli_path, "compile",
            "--fqbn", "arduino:avr:uno",
            sketch_dir
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = res.stdout + "\\n" + res.stderr
            if res.returncode == 0:
                if progress_callback:
                    progress_callback("Compilation successful!")
                return True, output
            else:
                if progress_callback:
                    progress_callback("Compilation failed.")
                return False, output
        except Exception as e:
            return False, f"Execution error: {e}"

    def upload(self, sketch_path: str, port: str, progress_callback=None) -> tuple[bool, str]:
        """
        Uploads compiled sketch to Maker UNO / Arduino UNO over specified COM port.
        Returns (success: bool, log: str).
        """
        if not self.ensure_toolchain(progress_callback):
            return False, "Failed to initialize Arduino toolchain."

        sketch_dir = os.path.dirname(os.path.abspath(sketch_path)) if os.path.isfile(sketch_path) else sketch_path

        if progress_callback:
            progress_callback(f"Flashing to Maker UNO on {port}...")

        cmd = [
            self.cli_path, "upload",
            "-p", port,
            "--fqbn", "arduino:avr:uno",
            sketch_dir
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            output = res.stdout + "\\n" + res.stderr
            if res.returncode == 0:
                if progress_callback:
                    progress_callback("Upload completed successfully! Maker UNO is now playing.")
                return True, output
            else:
                if progress_callback:
                    progress_callback("Upload failed.")
                return False, output
        except Exception as e:
            return False, f"Upload error: {e}"

    def compile_and_upload(self, sketch_path: str, port: str, progress_callback=None) -> tuple[bool, str]:
        """Convenience method to compile and immediately upload."""
        ok, comp_log = self.compile(sketch_path, progress_callback)
        if not ok:
            return False, comp_log

        ok, up_log = self.upload(sketch_path, port, progress_callback)
        return ok, comp_log + "\\n" + up_log
