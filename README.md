<div align="center">

# MakerUnoSong Studio v3.5.0

<p align="center">
  <b>Advanced MIDI to Maker UNO Studio with Intelligent Beat Structuring, Built-in Audio & Hardware Preview, 1-Click Fully Automated Pipeline & Real-Time Board Diagnostics!</b>
</p>

</div>

---

Designed specifically for the **Maker UNO** (by Cytron Technologies) and standard **Arduino UNO** (ATmega328P).

## What's New in v3.5.0

### 1. Intelligent Structural Beat Engine (Beyond Static Presets)
- **Rhythm Thinking, Not Just Looping**: Analyzes musical energy, note density, tempo, and measure cadences rather than mechanically repeating static presets.
- **Section-Aware Drum Synthesis**: Automatically classifies songs into structural phases:
  - `INTRO`: Subtle downbeat kick, delicate hi-hat ticks.
  - `VERSE`: Steady foundational groove supporting the melody.
  - `PRE-CHORUS`: Rising energy, driving four-on-the-floor kicks, building snare rolls.
  - `CHORUS / CLIMAX`: Dynamic syncopated kicks locking in with melodic accents, crisp backbeat snares, open hi-hat drive.
  - `BRIDGE / BREAKDOWN`: Dramatic contrast, half-time snares, kick dropouts.
  - `OUTRO`: Decelerating groove resolving to final chord.
- **Context-Aware Cadence Fills**: Detects 4-bar and 8-bar boundaries and structural section transitions, inserting authentic drum fills (16th-note snare rolls and syncopated kick turnarounds).
- **Musical Key & Harmonic Intelligence**: Uses Krumhansl-Schmuckler pitch class profiling to automatically detect the song's key and mode (e.g. C Major, A Minor).

### 2. Built-in Audio & Real-Time Virtual Hardware Preview
- **High-Performance Audio Synthesizer**: Generates authentic in-memory 16-bit PCM WAV audio:
  - Monophonic square-wave piezo buzzer tone.
  - Sub-bass kick transients (135Hz → 42Hz frequency downward glide).
  - White noise snare bursts with resonant body.
  - Crisp high-pass filtered metallic hi-hats.
- **Non-Blocking Asynchronous Playback**: Uses zero-lag audio streaming with instant play/pause/seek controls and tempo scaling (0.5x to 2.0x).
- **Virtual Maker UNO Hardware Visualizer**: Real-time simulated onboard hardware panel featuring:
  - 12 Dynamic Status LEDs (Pins 2 to 13) glowing in sync with playback.
  - Pin 8 Piezo Buzzer frequency ripple display.
  - Pin 2 Button state indicator.
- **Interactive Piano Roll with Zoom & Auto-Scroll**: Multi-colored register/drum tracks with animated playhead, horizontal time-axis Zoom (buttons + Ctrl+Wheel), horizontal panning (Shift/Alt+Wheel), 1:1 reset, and real-time Auto-Scroll tracking.
- **WAV Audio Export**: Export synthesized preview audio directly to `.wav` files via GUI or CLI (`--preview-wav`).

### 3. Fully Automated 1-Click Pipeline
- **Zero-Configuration Workflow**:
  - **In GUI**: Click **"⚡ 1-Click Auto Pipeline"** to auto-analyze structure, generate adaptive beats, detect connected Maker UNO port, compile, and flash directly.
  - **In CLI**: Run `python midi_to_arduino.py "song.mid" --auto` for hands-free compilation and upload.
- **Batch Processing**: Convert entire directories of MIDI files in one command (`--batch <DIR>`).
- **4 Selectable LED Visualizer Modes**:
  - `Frequency Mapped` (Default): Frequency-to-pin mapping (130Hz - 2000Hz).
  - `VU Meter`: Dynamic bar-graph volume/pitch meter across pins 2–13.
  - `Knight Rider Scanner`: High-speed Larson Scanner chasing across LEDs on musical beats.
  - `Drum Reactive`: Dedicated split (Pins 3–5 Kick, Pins 6–8 Snare, Pins 10–12 Hi-Hat).

### 4. Real-Time Board Health & Life Monitor
- **Internal 1.1V Bandgap Vcc Voltage Reference**: Detects USB voltage sags (<4.75V).
- **ATmega328P Core Die Temperature**: Monitors internal MCU temperature via ADC channel 8.
- **Dynamic SRAM Headroom**: Tracks available memory out of 2048 bytes of SRAM to prevent stack collision.
- **Non-Volatile EEPROM Integrity Check**: Validates memory cell retention without excessive wear.
- **16MHz Oscillator Latency & Jitter**: Measures real-time loop timing and crystal stability.
- **Interactive Peripheral Self-Test**: Test 12x LEDs (pins 2–13), Buzzer sweep (pin 8), and Button responses (pin 2).
- **Board Health Life Score**: 0–100% health score (Grade A/B/C/F) with telemetry logs.

---

## Technologies Used

- **[Python 3.11+](https://www.python.org/)** - Core engine, MIDI parsing, and synthesis algorithms.
- **[PySide6 / PyQt6](https://pypi.org/project/PySide6/)** - Modern dark-themed cyber desktop GUI.
- **[pyserial](https://pypi.org/project/pyserial/)** - Serial communication and telemetry protocol.
- **[mido](https://mido.readthedocs.io/)** - High-precision MIDI track and meta-event parsing.

---

## Getting Started

### 1. Installation
Install the required dependencies:
```powershell
pip install -r requirements.txt
```

### 2. Launching the Desktop Studio
Run the GUI application:
```powershell
python main.py
```

### 3. CLI Usage

#### ⚡ Fully Automated Pipeline (Analyze, Smart Beat, Auto-Detect Port & Flash):
```powershell
python midi_to_arduino.py "MySong (Artist).mid" --auto
```

#### Analyze Musical Structure & Export Audio Preview (.WAV):
```powershell
python midi_to_arduino.py "MySong (Artist).mid" --analyze --preview-wav "preview.wav"
```

#### Batch Convert All MIDI Files in a Folder:
```powershell
python midi_to_arduino.py --batch "C:\Path\To\Midis"
```

#### Choose Custom LED Mode:
```powershell
python midi_to_arduino.py "MySong (Artist).mid" --led-mode "Knight Rider Scanner" --upload COM3
```

#### Run Real-Time Board Health Diagnostics:
```powershell
python midi_to_arduino.py --health-check COM3
```

---

## Running Unit Tests
To verify all 34 unit tests:
```powershell
python -m unittest discover -v
```

---

## Changelog
- **v3.5.0** - **Major Boost Release**:
  - **Intelligent Beat Structuring Engine (`smart_beat.py`)**: Musical energy curve analysis, section classification (Intro, Verse, Chorus, Bridge, Outro), melody-locked kicks, and context-aware cadence fills.
  - **Built-in Audio Preview Engine (`audio_preview.py`)**: High-performance PCM WAV synthesizer for melody square wave and white noise drum kits (kick, snare, hi-hat), with non-blocking playback, seeking, and WAV export.
  - **Virtual Maker UNO Hardware Visualizer**: Real-time simulated 12x LEDs, Pin 8 buzzer, and Pin 2 button animation in GUI.
  - **Interactive Piano Roll**: Animated playhead cursor, note scrubbing, and color-coded pitch registers.
  - **1-Click Auto Pipeline**: Fully automated 1-click execution in GUI and `--auto` in CLI.
  - **Batch Conversion & Analysis**: `--batch <DIR>` and `--analyze` flags.
  - **4 LED Visualizer Modes**: Frequency Mapped, VU Meter, Knight Rider Scanner, and Drum Reactive.
  - Complete test suite expanded from 17 to 34 tests passing.
- **v3.0.0**: Standalone Direct Uploader, Board Health Diagnostics, Maker UNO 12x LED Sync.
- **v2.2.0**: Single-pass MIDI parsing, LRU-cached frequency calculations.

---
*Maintained by AgentHitmanFaris (NC-Engineering).*
