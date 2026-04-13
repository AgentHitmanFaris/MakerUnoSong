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
- **Melody-Weighted Arpeggiator**: Emulates polyphony on a monophonic buzzer by rapidly alternating between notes, giving double playtime to the melody so it always stands out over the harmony.
- **White Noise Drum Synthesis**: Snare and Hi-Hat hits are rendered as true white noise directly on the Arduino using rapid random-bit generation — not just simple beeps.
- **Auto-Gen Drum Loops**: Generate tempo-synced drum patterns in 7 genres: Pop, Rock, Metal, Funk, Disco, Hip-Hop, and Reggae. Or use the original MIDI percussion track.
- **Instant Preview**: Built-in `winsound` square-wave audio synthesis replicating the exact buzzer sound.
- **Smart Filename Parsing**: Automatically extracts Song Name and Artist from filenames like `Song Name (Artist).mid` and populates the UI fields.
- **Organized Export**: Exports `.ino` files into a structured `Songs/Song_Name_Artist/` folder hierarchy, ready for Arduino IDE.
- **Triple-Layer Memory Optimization**: Sequence merging, micro-segment filtering, and a hard 7000-entry safety cap ensure every song fits within the Arduino UNO's 32KB flash limit.
- **Performance Optimized Engine**: Single-pass MIDI parsing and LRU-cached frequency lookups provide near-instant processing, even for complex musical scores with thousands of notes.

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
- Files named like `Die On This Hill (Sienna Spiro).mid` will auto-fill **Song Name** and **Artist** fields.
- The Piano Roll will visualize all notes from every track.

### 3. Setting Song Properties
*   **Song Name & Artist**: Auto-detected from filename or MIDI metadata. Editable before export — values are embedded directly into the `.ino` header.
*   **Drums**: Choose how to handle rhythm!
    *   *Disable Drums*: Uncheck the box for a clean melodic-only export.
    *   *Use MIDI Track*: Maps MIDI Channel 10 percussion into white noise kick/snare/hi-hat.
    *   *Auto-Gen (7 genres)*: Pop, Rock, Metal, Funk, Disco, Hip-Hop, Reggae — fully synced to BPM.

### 4. Preview and Export
*   **Play Preview**: Hear a square-wave emulation of how the arpeggiated output will sound on the buzzer.
*   **Export .INO**: Automatically creates a `Songs/Song_Artist/Song_Artist.ino` folder structure. If the song exceeds memory, it auto-truncates with a warning.

## Changelog
- **v2.2.0** - Core performance overhaul: Single-pass MIDI parsing, LRU-cached frequency calculations, and linear string joining for massive speed boosts. Integrated modular test suite for core logic and GUI reliability.
- **v2.1.0** - Smart filename parsing for Song/Artist, organized `Songs/` export folder structure, triple-layer memory optimization with auto-truncation safety cap.
- **v2.0.0** - PyQt6 Desktop GUI, Melody-Weighted Arpeggiator, White Noise Drum Synthesis, Auto-Gen Drum Loops (7 genres).
- **v1.3.0** - Added Web Serial API support for hardware communication.
- **v1.2.0** - Transitioned interface to initial Web GUI rendering.

---
*Maintained under clinical security audit logging protocols.*
