<div align="center">

# MakerUnoSong

<p align="center">
  A highly optimized MIDI to Arduino converter specifically designed for the Maker UNO's built-in buzzer!
</p>

</div>

---

Guess what? I just stumbled upon the Maker UNO by Cytron Technologies—a snazzy replacement for the classic Arduino Uno! And guess what makes it even cooler? It's got a built-in buzzer! So, naturally, my brain went into creative overdrive, and voila, the birth of this project!

## Features

- **Pro Desktop Editor**: A sleek PyQt6 desktop application with an interactive graphical Piano Roll.
- **Polyphonic Emulation**: Automatically translates multi-track overlapping MIDI files into a perfectly weighted arpeggio segment, letting you hear both harmony and melody simultaneously on a monophonic buzzer.
- **Auto-Generating Drum Engine**: Automatically maps standard MIDI percussion tracks to Arduino square-wave white noise sequences, OR bypass the track completely to dynamically generate tempo-synced drum beats in genres like Pop, Rock, Metal, Funk, Disco, Hip-Hop, and Reggae.
- **Instant Preview**: Built-in square-wave audio synthesis perfectly replicating the exact buzzer sound timing.
- **Extreme Architecture Compression**: Sequence merging logic slashes Arduino Flash Memory usage drastically, ensuring large songs fit within the UNO's 32KB constraint.
- **Metadata Management**: Automatically pulls and dynamically embeds Song Name and Artist Name into your generated code's headers.

## Technologies Used

- **[Python 3.12](https://www.python.org/)** - Core launcher, arpeggiator calculation, and memory optimization.
- **[PyQt6](https://pypi.org/project/PyQt6/)** - Native, lightning-fast cross-platform desktop UI framework.
- **[mido](https://mido.readthedocs.io/)** - For seamless, precision track, channel, and tempo parsing from raw Standard MIDI Files.

## Getting Started & Walkthrough

### 1. Launching the App
Ensure you have Python installed along with `mido` and `PyQt6`, then simply run the launcher script from the root directory:
```powershell
python main.py
```
This will open the dark-mode Fusion styled desktop application.

### 2. Loading a MIDI File
Click the **Load MIDI** button and choose any Standard MIDI File (.mid or .midi). 
The app will dynamically render the notes onto the Piano Roll, calculate total ticks, and naturally lock onto the BPM and Key Signatures natively.

### 3. Setting Song Properties
*   **Song Name & Artist**: Overwrite or tweak the automatically resolved Song and Artist title fields in the UI. Anything put in these boxes will be natively compiled into the top of your final `.ino` file for sharing.
*   **Drums**: Choose how to handle rhythm!
    *   *Disable Drums*: Uncheck the box to maintain a perfectly clean melodic loop.
    *   *Use MIDI Track*: Pulls and cleans percussion mappings directly from MIDI Channel 10.
    *   *Auto-Gen*: Ignore the original drum track and generate an infinite, perfectly synced groove directly over your song structure (Choose from Pop, Rock, Metal, Funk, Disco, Hip-Hop, or Reggae).

### 4. Preview and Export
*   **Play Preview**: Click to use native `winsound` audio synthesis to get a square-wave emulation of how your arpeggiated script will actually sound on the Arduino.
*   **Export .INO**: Click to export a perfectly crafted sketch. Open the `.ino` in Arduino IDE and Upload it directly to your Maker UNO!

## Changelog
- **v2.0.0** - Transitioned to PyQt6 Native Desktop GUI. Built Melody-Weighted Arpeggiator and Integrated Custom Drum Tracks. Implemented native white-noise generator.
- **v1.3.0** - Added Web Serial API support for hardware communication.
- **v1.2.0** - Transitioned interface to initial Web GUI rendering.

---
*Maintained under clinical security audit logging protocols.*
