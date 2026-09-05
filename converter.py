"""
Midi to Maker UNO Arduino Converter.
Build by AgentHitmanFaris (NC-Engineering).

Optimized for ATmega328P with:
- Single-pass MIDI track parsing
- Melody-weighted polyphonic arpeggiator
- White noise drum synthesis (Snare, Hi-Hat, Kick)
- Multi-genre auto-drum loop generation
- Synchronized Maker UNO 12x LED visualizer (Pins 2-13)
- Maker UNO Pin 2 onboard button control (Pause / Resume / Restart)
- PROGMEM memory optimization with safety limits
"""

import mido
import functools
import os
import re

try:
    from smart_beat import SmartBeatEngine
except ImportError:
    SmartBeatEngine = None

@functools.lru_cache(maxsize=128)
def note_to_freq(note):
    if note is None or note == 0:
        return 0
    if note == 28: return 28 # Kick Drum Sub-Bass / Glissando Marker
    if note == 128: return -1 # Snare White Noise Marker
    if note == 129: return -2 # Hi-Hat White Noise Marker
    return int(440 * (2 ** ((note - 69) / 12)))

class MidiConverter:
    def __init__(self):
        # notes is a list of dictionaries: {'start': ms, 'duration': ms, 'pitch': midi_note_number, 'channel': ch}
        self.notes = []
        self.total_duration = 0
        self.bpm = 120
        self.time_signature = "4/4"
        self.key_signature = "C"
        self.song_name = "Untitled"
        self.artist = "Unknown"
        self.enable_drums = True
        self.drum_mode = "🧠 Smart Adaptive AI"
        self.enable_led_sync = True
        self.enable_button_control = True
        self.led_mode = "Frequency Mapped"
        self.structure_analysis = {}
        self.detected_key = "C Major"

    def note_to_freq(self, note):
        return note_to_freq(note)

    @staticmethod
    def sanitize_str(text):
        """Sanitize strings for C++ comments and identifiers."""
        if not text:
            return "Unknown"
        sanitized = re.sub(r'[\r\n\*\/\\]', ' ', str(text))
        return sanitized.strip() or "Unknown"

    def load_midi(self, filepath):
        """
        Loads a MIDI file and converts it into a monophonic list of note events.
        Optimized single-pass parsing extracting metadata, tempo, and notes simultaneously.
        """
        mid = mido.MidiFile(filepath)

        # Extract Meta information first from filename
        base_filename = os.path.splitext(os.path.basename(filepath))[0]
        self.song_name = self.sanitize_str(base_filename)
        self.artist = "Unknown"
        
        # Check for "Song (Artist)" pattern in filename
        match = re.match(r"(.*)\s*\((.*)\)", base_filename)
        filename_found = False
        if match:
            self.song_name = self.sanitize_str(match.group(1))
            self.artist = self.sanitize_str(match.group(2))
            filename_found = True

        self.notes = []
        temp_notes = []
        active_starts = {} # (pitch, channel) -> start_time_ms
        abs_time_ms = 0.0

        for msg in mid:
            dt_ms = msg.time * 1000.0
            abs_time_ms += dt_ms

            if msg.is_meta:
                if msg.type == 'set_tempo':
                    self.bpm = round(mido.tempo2bpm(msg.tempo))
                elif msg.type == 'time_signature':
                    self.time_signature = f"{msg.numerator}/{msg.denominator}"
                elif msg.type == 'key_signature':
                    self.key_signature = msg.key
                elif msg.type == 'track_name':
                    if not filename_found and msg.name.strip():
                        name = msg.name.strip()
                        if not name.lower().endswith(('.mid', '.midi')):
                            self.song_name = self.sanitize_str(name)
                elif msg.type == 'text' and "artist" in msg.text.lower():
                    self.artist = self.sanitize_str(msg.text)
                elif msg.type == 'copyright' and (self.artist == "Unknown" or not filename_found):
                    self.artist = self.sanitize_str(msg.text)
            
            elif msg.type == 'note_on' and msg.velocity > 0:
                key = (msg.note, getattr(msg, 'channel', 0))
                if key not in active_starts:
                    active_starts[key] = abs_time_ms

            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.note, getattr(msg, 'channel', 0))
                if key in active_starts:
                    start_t = active_starts.pop(key)
                    duration = abs_time_ms - start_t
                    if duration > 0:
                        temp_notes.append({
                            'start': int(start_t),
                            'duration': int(duration),
                            'pitch': msg.note,
                            'channel': key[1]
                        })

        self.notes = sorted(temp_notes, key=lambda x: x['start'])
        self.update_duration()
        if SmartBeatEngine and self.notes:
            self.analyze_song_structure()

    def get_project_name(self):
        """Returns a safe, filesystem-friendly name."""
        name = f"{self.song_name}_{self.artist}"
        safe = re.sub(r'[^\w\s]', '', name)
        return safe.replace(" ", "_").strip("_") or "MakerUno_Melody"

    def update_duration(self):
        if not self.notes:
            self.total_duration = 0
        else:
            self.total_duration = max(n['start'] + n['duration'] for n in self.notes)

    def get_notes(self):
        return self.notes

    def set_notes(self, notes):
        self.notes = sorted(notes, key=lambda x: x['start'])
        self.update_duration()

    def analyze_song_structure(self):
        """Analyzes musical structure, energy, and key of the loaded song."""
        if not SmartBeatEngine or not self.notes:
            return {}
        self.structure_analysis = SmartBeatEngine.analyze_structure(self.notes, self.bpm, self.time_signature)
        if self.structure_analysis.get('key_detected'):
            self.detected_key = self.structure_analysis['key_detected']
            if self.key_signature == "C":
                self.key_signature = self.detected_key
        return self.structure_analysis

    def get_flash_usage_estimate(self, segments=None):
        """Calculates PROGMEM and ATmega328P Flash usage statistics."""
        if segments is None:
            filtered = self._process_drums()
            raw_seg = self._generate_segments(filtered)
            segments = self._optimize_segments(raw_seg)
        num_seg = len(segments)
        progmem_bytes = num_seg * 4
        base_sketch_bytes = 4500
        total_estimated = base_sketch_bytes + progmem_bytes
        total_flash = 32256
        pct = round((total_estimated / total_flash) * 100.0, 1)
        return {
            "segments": num_seg,
            "progmem_bytes": progmem_bytes,
            "total_estimated_flash": total_estimated,
            "flash_capacity": total_flash,
            "percent": pct
        }

    def get_preview_engine(self, tempo_multiplier=1.0):
        """Builds and returns an AudioPreviewEngine with synthesized WAV audio."""
        try:
            from audio_preview import AudioPreviewEngine
        except ImportError:
            return None
        filtered = self._process_drums()
        segments = self._generate_segments(filtered)
        final_segments = self._optimize_segments(segments)
        engine = AudioPreviewEngine()
        engine.synthesize(final_segments, tempo_multiplier=tempo_multiplier)
        return engine

    def _process_drums(self):
        enable_drums = getattr(self, 'enable_drums', True)
        drum_mode = getattr(self, 'drum_mode', '🧠 Smart Adaptive AI')
        
        if not enable_drums:
            return [n for n in self.notes if n.get('channel', 0) != 9]

        is_smart_adaptive = ("Smart Adaptive" in drum_mode) or ("🧠" in drum_mode) or (drum_mode == "Adaptive AI")
        if is_smart_adaptive and SmartBeatEngine:
            drum_notes = SmartBeatEngine.generate_intelligent_beat(
                self.notes, self.bpm, self.time_signature, style=drum_mode
            )
            mel_notes = [n for n in self.notes if n.get('channel', 0) != 9]
            combined = mel_notes + drum_notes
            return sorted(combined, key=lambda x: x['start'])

        filtered_notes = []
        for n in self.notes:
            if n.get('channel', 0) == 9: # MIDI Channel 10 (drums)
                if drum_mode != 'Use MIDI Track': 
                    continue # Drop MIDI drums if disabled or overwritten by Auto-Gen
                
                p = n['pitch']
                if p in (35, 36, 1, 2): n_p = 28 # Kick (low frequency blip)
                elif p in (38, 40, 3, 4): n_p = 128 # Snare (white noise)
                elif p in (42, 44, 46, 5): n_p = 129 # Hi-hat (short noise)
                else: n_p = 128
                
                filtered_notes.append({
                    'start': n['start'], 'duration': min(40, n['duration']), 'pitch': n_p, 'channel': 9
                })
            else:
                filtered_notes.append(n)
                
        # Handle Auto-Generated Drums
        if enable_drums and drum_mode.startswith('Auto-Gen'):
            beat_ms = 60000.0 / self.bpm if self.bpm > 0 else 500
            t = 0
            beat_idx = 0
            while t < self.total_duration:
                is_kick = False
                is_snare = False
                is_hihat = False
                
                if drum_mode not in ("Auto-Gen: Disco", "Auto-Gen: Funk") and beat_idx % 0.5 == 0:
                    is_hihat = True
                
                if drum_mode == "Auto-Gen: Pop":
                    if beat_idx % 4 in (0, 2): is_kick = True
                    if beat_idx % 4 in (1, 3): is_snare = True
                elif drum_mode == "Auto-Gen: Rock":
                    if beat_idx % 4 in (0, 1.5, 2.5): is_kick = True
                    if beat_idx % 4 in (1, 3): is_snare = True
                elif drum_mode == "Auto-Gen: Metal":
                    if beat_idx % 0.5 == 0: is_kick = True
                    if beat_idx % 4 in (1, 3): 
                        is_snare = True
                        is_kick = False
                elif drum_mode == "Auto-Gen: Funk":
                    if beat_idx % 4 in (0, 0.75, 2.5): is_kick = True
                    if beat_idx % 4 in (1, 3, 3.75): is_snare = True
                    if beat_idx % 0.25 == 0: is_hihat = True
                elif drum_mode == "Auto-Gen: Disco":
                    if beat_idx % 1 == 0: is_kick = True
                    if beat_idx % 4 in (1, 3): is_snare = True
                    if beat_idx % 1 == 0.5: is_hihat = True
                elif drum_mode == "Auto-Gen: Hip-Hop":
                    if beat_idx % 4 in (0, 2.5): is_kick = True
                    if beat_idx % 4 in (1, 3): is_snare = True
                elif drum_mode == "Auto-Gen: Reggae":
                    if beat_idx % 4 == 2:
                        is_kick = True
                        is_snare = True
                        
                if is_hihat:
                    filtered_notes.append({'start': int(t), 'duration': 15, 'pitch': 129, 'channel': 9})
                if is_kick:
                    filtered_notes.append({'start': int(t), 'duration': 40, 'pitch': 28, 'channel': 9})
                if is_snare:
                    filtered_notes.append({'start': int(t), 'duration': 40, 'pitch': 128, 'channel': 9})
                
                t += 60000.0 / self.bpm / 4.0 if self.bpm > 0 else 125
                beat_idx += 0.25
        return sorted(filtered_notes, key=lambda x: x['start'])

    def _generate_segments(self, filtered_notes):
        events = []
        for n in filtered_notes:
            events.append((n['start'], 1, n['pitch']))
            events.append((n['start'] + n['duration'], -1, n['pitch']))

        events.sort(key=lambda x: (x[0], x[1])) 

        segments = []
        current_time = 0
        active_pitches = [] 
        arp_index = 0

        for time_pt, type_val, pitch in events:
            duration = time_pt - current_time

            if duration > 0:
                if active_pitches:
                    drum_active = [p for p in active_pitches if p in (28, 128, 129)]
                    mel_active = [p for p in active_pitches if p not in (28, 128, 129)]

                    if drum_active:
                        # Percussion transient priority: Kick (28) / Snare (128) > Hi-Hat (129)
                        if 128 in drum_active:
                            drum_p = 128
                        elif 28 in drum_active:
                            drum_p = 28
                        else:
                            drum_p = 129
                        segments.append((self.note_to_freq(drum_p), int(duration)))
                    elif mel_active:
                        sorted_mel = sorted(mel_active)
                        if len(sorted_mel) == 1:
                            segments.append((self.note_to_freq(sorted_mel[0]), int(duration)))
                        else:
                            highest_pitch = sorted_mel[-1]
                            lowest_pitch = sorted_mel[0]
                            rem_dur = duration
                            while rem_dur > 0:
                                if arp_index % 2 == 0:
                                    step_dur = min(60, rem_dur)
                                    segments.append((self.note_to_freq(highest_pitch), int(step_dur)))
                                else:
                                    step_dur = min(30, rem_dur)
                                    segments.append((self.note_to_freq(lowest_pitch), int(step_dur)))
                                rem_dur -= step_dur
                                arp_index += 1
                    else:
                        segments.append((0, int(duration)))
                        arp_index = 0
                else:
                    segments.append((0, int(duration)))
                    arp_index = 0

            current_time = time_pt

            if type_val == 1:
                active_pitches.append(pitch)
            else:
                if pitch in active_pitches:
                    active_pitches.remove(pitch) 
        return segments

    def _optimize_segments(self, segments):
        # 1. Merge adjacent segments with identical frequencies
        optimized_segments = []
        for freq, duration in segments:
            if duration <= 0: continue
            if optimized_segments and optimized_segments[-1][0] == freq:
                optimized_segments[-1] = (freq, optimized_segments[-1][1] + duration)
            else:
                optimized_segments.append((freq, duration))

        # 2. Filter out inaudibly short segments (< 6ms)
        final_segments = []
        for freq, duration in optimized_segments:
            if duration < 6 and final_segments:
                prev_f, prev_d = final_segments[-1]
                final_segments[-1] = (prev_f, prev_d + duration)
            else:
                final_segments.append((freq, duration))

        # 3. Memory Safety Cap: ATmega328P has 32KB flash (~7000 entries max)
        MAX_SEGMENTS = 7000
        if len(final_segments) > MAX_SEGMENTS:
            final_segments = final_segments[:MAX_SEGMENTS]
        
        return final_segments

    def _build_arduino_code(self, final_segments):
        san_song = self.sanitize_str(self.song_name)
        san_artist = self.sanitize_str(self.artist)
        san_bpm = self.sanitize_str(self.bpm)
        san_time_sig = self.sanitize_str(self.time_signature)
        san_key = self.sanitize_str(self.key_signature)
        led_mode = getattr(self, 'led_mode', 'Frequency Mapped')
        flash_info = self.get_flash_usage_estimate(final_segments)

        sec_summary = "N/A"
        if self.structure_analysis and self.structure_analysis.get('sections'):
            sec_list = [f"{s['name']} (Bar {s['start_bar']}-{s['end_bar']})" for s in self.structure_analysis['sections']]
            sec_summary = " -> ".join(sec_list[:6])

        header = f"""/*
  Maker UNO Melody & Visualizer
  Generated by MakerUnoSong Studio
  Build by AgentHitmanFaris (NC-Engineering)
  -------------------------------------------------------------
  Song: {san_song}
  Artist: {san_artist}
  Tempo: {san_bpm} BPM | Time Sig: {san_time_sig} | Key: {san_key}
  Total Segments: {len(final_segments)} (PROGMEM: {flash_info['progmem_bytes']} B / {flash_info['percent']}% flash)
  Structural Flow: {sec_summary}
  Features:
    - Maker UNO Buzzer on Pin 8
    - Maker UNO 12x LED Sync on Pins 2-13 (Mode: {led_mode})
    - Maker UNO Push Button on Pin 2 (Click to Pause/Play)
  -------------------------------------------------------------
*/

#include <avr/pgmspace.h>

#define BUZZER_PIN 8
#define BUTTON_PIN 2

// 12 Status LEDs on Maker UNO (Pins 2 to 13)
const uint8_t LED_PINS[] = {{2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}};
const uint8_t NUM_LEDS = sizeof(LED_PINS) / sizeof(LED_PINS[0]);

"""
        melody_array = "const int16_t melody[] PROGMEM = {\n"
        duration_array = "const uint16_t noteDurations[] PROGMEM = {\n"

        melody_rows = []
        duration_rows = []
        for i in range(0, len(final_segments), 10):
            chunk = final_segments[i : i + 10]
            melody_rows.append("  " + ", ".join(str(f) for f, d in chunk))
            duration_rows.append("  " + ", ".join(str(d) for f, d in chunk))

        melody_array += ",\n".join(melody_rows) + "\n};\n"
        duration_array += ",\n".join(duration_rows) + "\n};\n"

        if not self.enable_led_sync:
            led_sync_code = """
void updateLeds(int freq) {
  // LED Sync Disabled
}
"""
        elif led_mode == "VU Meter":
            led_sync_code = """
void updateLeds(int freq) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    if (LED_PINS[i] != BUTTON_PIN) digitalWrite(LED_PINS[i], LOW);
  }
  if (freq == 0) return;
  int level;
  if (freq == 28) {
    level = 4;
  } else if (freq == -1) {
    level = 8;
  } else if (freq == -2) {
    level = 11;
  } else {
    level = map(constrain(freq, 130, 2000), 130, 2000, 1, NUM_LEDS);
  }
  for (uint8_t i = 0; i < level; i++) {
    if (LED_PINS[i] != BUTTON_PIN) digitalWrite(LED_PINS[i], HIGH);
  }
}
"""
        elif led_mode == "Knight Rider Scanner":
            led_sync_code = """
int scanPos = 0;
int scanDir = 1;
void updateLeds(int freq) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    if (LED_PINS[i] != BUTTON_PIN) digitalWrite(LED_PINS[i], LOW);
  }
  if (freq != 0) {
    scanPos += scanDir;
    if (scanPos >= NUM_LEDS - 1) { scanPos = NUM_LEDS - 1; scanDir = -1; }
    else if (scanPos <= 0) { scanPos = 0; scanDir = 1; }
    if (LED_PINS[scanPos] != BUTTON_PIN) digitalWrite(LED_PINS[scanPos], HIGH);
  }
}
"""
        elif led_mode == "Drum Reactive":
            led_sync_code = """
void updateLeds(int freq) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    if (LED_PINS[i] != BUTTON_PIN) digitalWrite(LED_PINS[i], LOW);
  }
  if (freq == 28) {
    // Kick: Bottom LEDs (Pins 3, 4, 5)
    digitalWrite(LED_PINS[1], HIGH); digitalWrite(LED_PINS[2], HIGH); digitalWrite(LED_PINS[3], HIGH);
  } else if (freq == -1) {
    // Snare: Mid LEDs (Pins 6, 7, 8)
    digitalWrite(LED_PINS[4], HIGH); digitalWrite(LED_PINS[5], HIGH); digitalWrite(LED_PINS[6], HIGH);
  } else if (freq == -2) {
    // Hi-Hat: High LEDs (Pins 10, 11, 12)
    digitalWrite(LED_PINS[8], HIGH); digitalWrite(LED_PINS[9], HIGH); digitalWrite(LED_PINS[10], HIGH);
  } else if (freq > 0) {
    int idx = map(constrain(freq, 130, 2000), 130, 2000, 0, NUM_LEDS - 1);
    if (LED_PINS[idx] != BUTTON_PIN) digitalWrite(LED_PINS[idx], HIGH);
  }
}
"""
        else: # Frequency Mapped (Default)
            led_sync_code = """
void updateLeds(int freq) {
  if (freq <= 0 || freq == 28) {
    for (uint8_t i = 0; i < NUM_LEDS; i++) {
      if (LED_PINS[i] != BUTTON_PIN) {
        digitalWrite(LED_PINS[i], LOW);
      }
    }
    if (freq == 28) {
      digitalWrite(LED_PINS[1], HIGH);
      digitalWrite(LED_PINS[2], HIGH);
    } else if (freq < 0) {
      digitalWrite(LED_PINS[3], HIGH);
      digitalWrite(LED_PINS[7], HIGH);
      digitalWrite(LED_PINS[11], HIGH);
    }
    return;
  }
  
  int ledIdx = map(constrain(freq, 130, 2000), 130, 2000, 0, NUM_LEDS - 1);
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    if (LED_PINS[i] != BUTTON_PIN) {
      digitalWrite(LED_PINS[i], (i == ledIdx) ? HIGH : LOW);
    }
  }
}
"""

        button_code = """
bool isPaused = false;
unsigned long lastBtnPress = 0;

void checkButton() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    if (millis() - lastBtnPress > 300) { // Debounce
      isPaused = !isPaused;
      lastBtnPress = millis();
      noTone(BUZZER_PIN);
      while (isPaused) {
        // Blink LED 13 slowly while paused
        digitalWrite(13, (millis() / 500) % 2);
        if (digitalRead(BUTTON_PIN) == LOW && millis() - lastBtnPress > 300) {
          isPaused = false;
          lastBtnPress = millis();
          digitalWrite(13, LOW);
          break;
        }
        delay(20);
      }
    }
  }
}
""" if self.enable_button_control else """
void checkButton() {
  // Button Control Disabled
}
"""

        setup_loop = f"""
// --- TO ADJUST TEMPO: Increase for FASTER (>1.0), decrease for SLOWER (<1.0) ---
float tempoMultiplier = 1.0;

const uint16_t noteCount = sizeof(melody) / sizeof(melody[0]);

{led_sync_code}
{button_code}

void setup() {{
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  for (uint8_t i = 0; i < NUM_LEDS; i++) {{
    if (LED_PINS[i] != BUTTON_PIN) {{
      pinMode(LED_PINS[i], OUTPUT);
      digitalWrite(LED_PINS[i], LOW);
    }}
  }}
}}

void loop() {{
  for (uint16_t i = 0; i < noteCount; i++) {{
    checkButton();
    
    int freq = (int16_t)pgm_read_word_near(melody + i);
    int duration = (uint16_t)pgm_read_word_near(noteDurations + i);
    
    int finalDuration = (int)(duration / tempoMultiplier);
    unsigned long noteStart = millis();
    
    updateLeds(freq);
    
    if (freq == 28) {{
      // Kick Drum: Rapid downward pitch glide (140Hz -> 40Hz)
      for (int kf = 140; kf >= 40; kf -= 10) {{
        tone(BUZZER_PIN, kf, 4);
        delay(3);
      }}
      noTone(BUZZER_PIN);
    }} else if (freq > 0) {{
      tone(BUZZER_PIN, freq, (int)(finalDuration * 0.9));
    }} else if (freq < 0) {{
      // White Noise Synthesizer (-1 = Snare, -2 = HiHat)
      int maxDel = (freq == -1) ? 800 : 150;
      while (millis() - noteStart < (unsigned long)(finalDuration * 0.85)) {{
        digitalWrite(BUZZER_PIN, random(2));
        delayMicroseconds(random(50, maxDel));
      }}
      digitalWrite(BUZZER_PIN, LOW);
    }} else {{
      noTone(BUZZER_PIN);
    }}
    
    // Maintain precise tempo timing
    while (millis() - noteStart < (unsigned long)finalDuration) {{
      checkButton();
      delay(1);
    }}
    noTone(BUZZER_PIN);
  }}
  
  // Turn off all LEDs during end pause
  for (uint8_t i = 0; i < NUM_LEDS; i++) {{
    if (LED_PINS[i] != BUTTON_PIN) {{
      digitalWrite(LED_PINS[i], LOW);
    }}
  }}
  delay(2000); // 2 second pause before replay
}}
"""
        return header + melody_array + "\n" + duration_array + "\n" + setup_loop

    def export_arduino(self, output_filepath):
        """Generates and writes Arduino C++ sketch."""
        filtered_notes = self._process_drums()
        segments = self._generate_segments(filtered_notes)
        final_segments = self._optimize_segments(segments)
        full_code = self._build_arduino_code(final_segments)

        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
        with open(output_filepath, 'w') as f:
            f.write(full_code)

        return True