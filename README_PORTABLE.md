# Portable MIDI to Arduino Converter - Build Instructions

## Requirements
To run the source code directly, you need:
- Python 3.x
- Dependencies: `pip install -r requirements.txt`

## Running with Python Embedded
If you are using the "Python Embedded" distribution (a zip file of Python):
1. Ensure the `python-3.x.x-embed-amd64.zip` is extracted.
2. By default, `tkinter` is NOT included in the embedded distribution. You must:
   - Copy the `tcl` folder and `tk` folder from a full Python installation to the embedded folder.
   - Copy `_tkinter.pyd`, `tcl86t.dll`, `tk86t.dll` (versions may vary) to the embedded folder or `Lib` folder.
3. **Important**: Open the `python3x._pth` file (e.g., `python311._pth`) in the embedded folder and uncomment the line `#import site`. This allows Python to load modules installed by pip.
4. Install dependencies (`mido`, `pygame`, `numpy`) into the embedded python environment.
   - Since `pip` is not installed by default, download `get-pip.py` and run `python get-pip.py`.
   - Then run `python -m pip install -r requirements.txt`.
5. Run the application:
   ```bash
   python main.py
   ```

## Creating a Portable Windows Executable (Recommended)
The easiest way to make a "portable" application that doesn't require the user to manage Python is to use PyInstaller.

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Build the EXE:
   ```bash
   pyinstaller --onefile --noconsole --name "MidiToArduino" main.py
   ```
   - `--onefile`: bundles everything into a single `.exe`.
   - `--noconsole`: hides the black command prompt window.
3. The result will be in the `dist` folder: `MidiToArduino.exe`.
   You can move this file anywhere (USB drive, another PC), and it will run without installation.

## Features
- **Load MIDI**: Import standard .mid files.
- **Editor**:
  - View notes on a Piano Roll.
  - **Select**: Click a note (turns red).
  - **Move**: Drag notes to change start time (X) or pitch (Y).
  - **Delete**: Press `Delete` key to remove selected note.
- **Preview**: Click "Play Preview" to hear the melody (simulated square wave).
- **Export**: Save as `.ino` file for Maker UNO.
