# Portable MIDI to Arduino Converter
**One-Click Windows Application**

## Usage
1. Download the **Windows x86-64 embeddable zip** package from Python.org (e.g., Python 3.11.x).
2. Extract the zip file to a folder.
3. Place the contents of this repository (all files) into the **same folder** as the extracted Python files (where `python.exe` is located).
4. Double-click `run_portable.bat`.

## What happens next?
- The script will automatically detect if `pip` is missing and download it.
- It will install necessary libraries (`pygame`, `mido`, `numpy`) directly into the local folder.
- It will launch the application.
- **No administrative privileges required.**
- **No changes to your system drive.**

## Features
- **Load MIDI**: Open standard `.mid` files using native Windows dialogs.
- **Editor**:
  - Visual Piano Roll interface.
  - **Left Click**: Select Note.
  - **Right Click**: Create Note.
  - **Drag**: Move notes (Time/Pitch).
  - **Drag Edge**: Resize notes (Duration).
  - **Delete**: Remove selected notes.
  - **Scroll**: Use Mouse Wheel (Vertical) or drag.
- **Preview**: Real-time audio playback simulation of the Arduino buzzer.
- **Export**: Generates `.ino` code compatible with Maker UNO / Arduino (Tone library).

## Requirements (for Manual Run)
- Python 3.x
- `pip install -r requirements.txt`
- Windows (for native file dialogs)
