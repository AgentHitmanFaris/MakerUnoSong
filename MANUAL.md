# MakerUnoSong - User Manual and Technical Reference

Version 3.5.0
Build by AgentHitmanFaris (NC-Engineering)
Target Hardware: Cytron Maker UNO / Standard Arduino UNO (ATmega328P)

---

## Table of Contents
1. Introduction and System Requirements
2. Part 1: Beginner and Non-Technical User Guide
   - 2.1 What is Maker UNO?
   - 2.2 Connecting Your Board
   - 2.3 Starting the Desktop Studio
   - 2.4 Loading a Song
   - 2.5 Using Built-in Preview and Virtual Visualizer
   - 2.6 Flashing Your Board in 1 Click
   - 2.7 Playing Music on Your Board
   - 2.8 Beginner Troubleshooting FAQ
3. Part 2: Professional and Advanced Technical Reference
   - 3.1 Architecture Overview
   - 3.2 ATmega328P Hardware Resource and Memory Optimization
   - 3.3 Musical Intelligence and Structural Beat Engine Algorithms
   - 3.4 PCM Audio Preview and Hardware Synthesis Model
   - 3.5 Command Line Interface and Batch Automation
   - 3.6 Hardware Health Monitoring and Telemetry Protocol
   - 3.7 Direct Toolchain Compilation and Avrdude Flashing
   - 3.8 Automated Testing and Continuous Verification

---

## 1. Introduction and System Requirements

MakerUnoSong is an advanced MIDI-to-microcontroller studio designed specifically for the Cytron Maker UNO and standard Arduino UNO boards powered by the ATmega328P 8-bit AVR microcontroller.

### Minimum System Requirements
* Operating System: Windows 10 or Windows 11 (64-bit), Linux, or macOS.
* Python Version: Python 3.10 or higher.
* Python Packages: mido, pyserial>=3.5, PySide6 (or PyQt6).
* Hardware: Cytron Maker UNO or Arduino UNO Rev3 with USB Type-B or Micro-USB cable.

---

## 2. Part 1: Beginner and Non-Technical User Guide

This section provides clear, step-by-step instructions for users who want to play songs on their Maker UNO without writing code or touching technical settings.

### 2.1 What is Maker UNO?
The Maker UNO is a beginner-friendly microcontroller board based on the Arduino UNO. It comes with built-in hardware features that make music projects simple:
* Built-in Piezo Buzzer on digital pin 8: Plays notes and tones without needing external speakers.
* 12 LED lights on digital pins 2 to 13: Light up automatically when pins are turned on.
* Programmable Push Button on digital pin 2: Used to pause, resume, or restart songs.

### 2.2 Connecting Your Board
1. Take a USB cable and connect your Maker UNO board to any open USB port on your computer.
2. A green power light on the board will turn on.
3. Your computer will automatically detect the board and assign it a communication port (for example, COM3 or COM4 on Windows).

### 2.3 Starting the Desktop Studio
1. Open a terminal or command prompt inside the project folder.
2. Run the application:
   ```powershell
   python main.py
   ```
3. The dark-themed MakerUnoSong Studio window will appear on your screen.

### 2.4 Loading a Song
1. Click the "Load MIDI" button in the top toolbar.
2. Select any standard .mid or .midi file from your computer (such as a piano track or full song).
3. The song title, artist name, tempo (BPM), and notes will automatically load into the interactive Piano Roll.
4. The Musical Intelligence ribbon will display the detected musical key (such as C Major) and note density.

### 2.5 Using Built-in Preview and Virtual Visualizer
Before sending the song to your physical board, you can preview exactly how it will sound and look:
1. Click the "Play Preview" button in the top toolbar.
2. You will hear the authentic buzzer melody along with synthesized drums (kick, snare, and hi-hat).
3. Watch the "Virtual Maker UNO" panel in the center of the window:
   - All 12 virtual LEDs light up in real time to match the melody and beat.
   - The buzzer monitor shows the current sound frequency in Hertz.
4. Navigation and View Controls:
   - Click the timeline slider or click directly inside the Piano Roll to jump to any part of the song.
   - Use the "Speed" dropdown to slow down (0.5x) or speed up (2.0x) the playback.
   - Use the Zoom buttons ("Zoom +", "Zoom -", or "1:1") to view individual notes or the entire composition.
   - Hold Ctrl and scroll your mouse wheel to zoom in and out smoothly.
   - Keep the "Auto-Scroll" checkbox checked so the screen follows along with the music as it plays.
5. Click "Stop" to stop playback.

### 2.6 Flashing Your Board in 1 Click
Once you are satisfied with the song preview:
1. Ensure your Maker UNO board is plugged into your computer.
2. Click the green "1-Click Auto Pipeline" button in the top toolbar.
3. The program will automatically:
   - Analyze the song structure and attach intelligent drum patterns.
   - Scan your computer's USB ports to find your Maker UNO.
   - Compile the Arduino code.
   - Upload the program directly to your board.
4. A confirmation message will appear when the upload is complete.

### 2.7 Playing Music on Your Board
* As soon as uploading completes, your Maker UNO will begin playing the song immediately through its built-in buzzer.
* The 12 onboard LEDs will dance in sync with the music.
* Press the built-in push button (Pin 2) at any time to pause the music.
* Press the button again to resume playback.
* When the song finishes, it pauses for 2 seconds and then loops automatically.

### 2.8 Beginner Troubleshooting FAQ

#### Q: The program says "No connected Maker UNO board found." What should I do?
* Verify that the USB cable is firmly plugged into both your computer and the board.
* Make sure your USB cable supports data transfer (some cables only provide power).
* Click the refresh icon next to the "Port" dropdown menu in the toolbar.
* If your board uses a CH340 or CP210x USB chip, ensure the driver is installed on your computer.

#### Q: How do I change the drum style?
* In the "Song Settings" section, click the "Drums" dropdown menu.
* Select "Smart Adaptive AI" for the intelligent dynamic beat that changes across Intro, Verse, and Chorus.
* Alternatively, choose classic presets like "Auto-Gen: Rock", "Auto-Gen: Pop", or "Auto-Gen: Disco".

#### Q: Can I turn off the LEDs or change how they flash?
* Yes. In the "Song Settings" section, you can uncheck "Maker UNO 12x LED Sync" or choose an alternative visualizer pattern such as "VU Meter", "Knight Rider Scanner", or "Drum Reactive".

---

## 3. Part 2: Professional and Advanced Technical Reference

This section provides comprehensive technical documentation for developers, audio engineers, and embedded systems programmers.

### 3.1 Architecture Overview
The system follows a modular, decoupled architecture:
* converter.py: Single-pass MIDI parser, polyphonic note arpeggiator, and Arduino C++ code generator.
* smart_beat.py: Musical intelligence engine providing section segmentation, Krumhansl-Schmuckler key detection, and cadence fills.
* audio_preview.py: Real-time 16-bit linear PCM WAV synthesizer emulating ATmega328P piezo square-wave output and white-noise drums.
* uploader.py: Direct microcontroller compilation and avrdude flashing layer with automatic DTR reset.
* board_health.py: Embedded diagnostic telemetry engine reading ADC sensors and EEPROM integrity at 115,200 baud.
* main.py: PySide6 / PyQt6 desktop graphical interface with interactive piano roll and virtual hardware visualizer.

### 3.2 ATmega328P Hardware Resource and Memory Optimization

The ATmega328P features 32 KB of flash memory (with 0.5 KB reserved for the bootloader, leaving 31.5 KB available) and 2 KB (2,048 bytes) of static RAM.

#### PROGMEM Melody Packing
Storing audio note arrays in dynamic RAM quickly causes stack-heap collisions. MakerUnoSong packs all melody frequencies and note durations into flash memory using the PROGMEM attribute:
* Frequencies: Array of int16_t (2 bytes per segment).
* Durations: Array of uint16_t (2 bytes per segment).
* Total memory per segment: Exactly 4 bytes.
* Memory capacity formula:
  Max Segments = (Available Flash - Base Sketch Size) / 4 = (32,256 - 4,500) / 4 = 6,939 segments
* The get_flash_usage_estimate() method in converter.py calculates exact byte consumption and flags warnings if memory usage approaches 90% capacity.

#### Frequency Calculation Caching
Frequency conversions rely on the equal temperament tuning formula:
f = 440 * 2^((d - 69) / 12)
The note_to_freq() function utilizes an LRU cache (@functools.lru_cache(maxsize=128)) to eliminate redundant floating-point calculations during MIDI parsing.

### 3.3 Musical Intelligence and Structural Beat Engine Algorithms

The SmartBeatEngine class in smart_beat.py processes raw MIDI note lists into cohesive musical structures.

#### 1. Measure and Beat Grid Construction
Using the song BPM and time signature (N/D), measure boundaries are calculated:
Beat Duration (ms) = (60,000 / BPM) * (4 / D)
Bar Duration (ms) = Beat Duration * N

#### 2. Krumhansl-Schmuckler Key Detection
Melodic pitch durations are aggregated modulo 12 into a 12-element pitch-class distribution vector P. The vector is correlated against standard empirical major and minor probe-tone profiles for all 24 chromatic rotations using the Pearson product-moment correlation coefficient. The key profile yielding the maximum coefficient determines the tonality and mode.

#### 3. Section Classification Heuristic
Measures are assigned structural classifications based on normalized energy E_m and relative chronological position:
* Normalized Energy: Weighted combination of note density and pitch register elevation:
  Weight = 1.0 + max(0, (Pitch - 60) / 48)
* State Transitions:
  - INTRO: Progress < 12% and E_m < 0.45.
  - OUTRO: Progress > 88% and E_m < 0.40.
  - CHORUS / CLIMAX: E_m >= 0.70.
  - PRE-CHORUS: E_m >= 0.45 with an immediately following Chorus (E_{m+1} >= 0.70).
  - BRIDGE: 55% <= Progress <= 75% with E_m < 0.35.
  - VERSE: Baseline energy measures.

#### 4. Cadence Turnarounds and Melody-Locked Accents
* Section boundary detection: Measures satisfying (m % 4 == 3) or marking the terminal bar of a section trigger 16th-note snare fills and syncopated kick turnarounds.
* Syncopation locking: The engine indexes off-beat melodic onsets (e.g. eighth-note subdivisions 1.5, 2.5) and anchors supplemental kick events to these exact millisecond offsets.

### 3.4 PCM Audio Preview and Hardware Synthesis Model

The AudioPreviewEngine in audio_preview.py synthesizes authentic 16-bit linear PCM mono audio at 22,050 Hz.

#### 1. Buzzer Square-Wave Synthesis
Simulates the microcontroller tone() output:
y(t) = A * sgn(sin(2 * pi * f * t))
To prevent speaker pop and digital clipping, high-pass transitions apply exponential attack and decay windowing across the initial and final 8 milliseconds of each note segment.

#### 2. White-Noise Percussion Modeling
Because the ATmega328P lacks a dedicated DAC, drums are rendered through microsecond timing pulses:
* Kick Drum (pitch = 28): Generates a sub-bass downward frequency sweep from 135 Hz down to 42 Hz with exponential amplitude decay over 90 milliseconds.
* Snare Drum (pitch = 128): Combines uniform white noise with a 180 Hz resonant sine wave body decaying over 120 milliseconds.
* Hi-Hat (pitch = 129): Synthesizes high-pass filtered white noise differences decaying over 45 milliseconds.

#### 3. Asynchronous Streaming Architecture
Audio is written to an ephemeral WAV container and played using winsound.SND_FILENAME | winsound.SND_ASYNC. This decouples audio synthesis from the GUI event loop, preventing UI thread blockage and supporting real-time playhead scrub seeking.

### 3.5 Command Line Interface and Batch Automation

The midi_to_arduino.py script provides headless automation for scripting, continuous integration, and batch compilation.

#### Common CLI Commands
* Hands-Free 1-Click Pipeline:
  ```powershell
  python midi_to_arduino.py "song.mid" --auto
  ```
* Analyze Structure and Export Audio Preview:
  ```powershell
  python midi_to_arduino.py "song.mid" --analyze --preview-wav "preview.wav"
  ```
* Batch Convert Entire Directories:
  ```powershell
  python midi_to_arduino.py --batch "C:\MidiLibrary"
  ```
* Direct Hardware Flashing:
  ```powershell
  python midi_to_arduino.py "song.mid" --upload COM3
  ```
* Custom Visualizer Mode:
  ```powershell
  python midi_to_arduino.py "song.mid" --led-mode "Drum Reactive" --upload COM3
  ```

### 3.6 Hardware Health Monitoring and Telemetry Protocol

The BoardHealthEngine in board_health.py pairs with an onboard diagnostic firmware sketch to sample internal ATmega328P analog channels at 115,200 baud.

#### Telemetry Metrics
1. Supply Voltage (Vcc): Measures the internal 1.1V bandgap voltage reference against Vcc using the analog multiplexer:
   Vcc = (1.1 * 1023) / ADC Reading
   Detects USB voltage droop (< 4.75V) under high current loads.
2. Core Die Temperature: Reads internal ADC Channel 8 against the 1.1V reference to calculate MCU junction temperature in Celsius.
3. Free SRAM Headroom: Traverses dynamic memory to locate the difference between the heap break and the stack pointer.
4. Non-Volatile EEPROM Verification: Performs safe checksum verification on non-volatile cells without exceeding the 100,000 write cycle limit.
5. Clock Jitter: Measures loop interval variation against the 16 MHz external crystal oscillator.

### 3.7 Direct Toolchain Compilation and Avrdude Flashing

The ArduinoUploader in uploader.py bypasses the external Arduino IDE GUI:
1. Detects serial devices via USB VID/PID filtering (0x10C4 Silicon Labs CP210x, 0x1A86 WCH CH340, 0x2341 Arduino SA).
2. Locates installed AVR toolchains (arduino-cli or avrdude).
3. Invokes avrdude using the STK500v1 protocol:
   avrdude -C avrdude.conf -v -p atmega328p -c arduino -P COM3 -b 115200 -D -U flash:w:firmware.hex:i
4. Handles automatic microcontroller reset by toggling the DTR serial control line.

### 3.8 Automated Testing and Continuous Verification

The project includes an automated test suite with 35 unit tests covering parsing, synthesis, compilation, and UI state machines:

```powershell
python -m unittest discover -v
```

* test_audio_preview.py: Validates WAV container header formatting, tempo scaling, and LED pin resolution.
* test_board_health.py: Validates telemetry packet decoding and health score algorithms.
* test_converter.py: Tests single-pass note extraction, string sanitization, flash estimation, and C++ code generation.
* test_smart_beat.py: Verifies harmonic key detection, structural section segmentation, and cadence fill generation.
* test_uploader.py: Validates COM port enumeration and compilation subroutines.
* test_main.py: Headless Qt GUI validation covering pipeline automation, virtual board telemetry, and timeline zooming.

---
Maintained by AgentHitmanFaris (NC-Engineering).
