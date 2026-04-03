<div align="center">

# MakerUnoSong

<p align="center">
  A fun project converting MIDI to Arduino code specifically for Maker UNO's built-in buzzer!
</p>

</div>

---

Guess what? I just stumbled upon the Maker UNO by Cytron Technologies—a snazzy replacement for the classic Arduino Uno! and guess what makes it even cooler? It's got a built-in buzzer! So, naturally, my brain went into creative overdrive, and voila, the birth of this super fun project! 

## Features

- **MIDI to Arduino Conversion**: Flattens polyphonic MIDI files into a monophonic stream (Last-Note-Priority) specifically tailored for the `tone()` function on Arduino.
- **Audio Preview**: Includes a built-in audio preview mechanism using NumPy and Pygame with dynamic crossfading to eliminate audio clicking.
- **Portable Architecture**: Designed to run cleanly in portable environments, utilizing standard CLI inputs as fallback options when native OS dialogs are unavailable.
- **Strict Compliance**: Fully avoids Tkinter and adheres strictly to environment boundaries and operational guidelines.

## Technologies Used

- **[Python 3.12](https://www.python.org/)** - Core programming language.
- **[mido](https://mido.readthedocs.io/en/latest/)** - For parsing standard MIDI files.
- **[pygame](https://www.pygame.org/)** - For graphical user interface components and audio rendering.
- **[numpy](https://numpy.org/)** - For programmatic audio synthesis (generating sine waves).

## Getting Started

To get started with the MakerUnoSong project locally, run the following commands:

```bash
# Install required dependencies
pip install -r requirements.txt

# Run the main application
python3 main.py
```

## Changelog

- **v1.1.0** - Added modern centered hero section to README, improved audio smoothing, refactored dialogs, and hardened overall system stability.
- **v1.0.0** - Initial release featuring MIDI parsing and basic Arduino code generation targeting digital pin 8.

---
*Maintained under clinical security audit logging protocols.*
