import mido
import math

class MidiConverter:
    def __init__(self):
        # notes is a list of dictionaries: {'start': ms, 'duration': ms, 'pitch': midi_note_number}
        self.notes = []
        self.total_duration = 0
        self.bpm = 120
        self.time_signature = "4/4"
        self.key_signature = "C"

    def note_to_freq(self, note):
        if note is None or note == 0:
            return 0
        if note == 128: return -1 # Snare White Noise Marker
        if note == 129: return -2 # Hi-Hat White Noise Marker
        return int(440 * (2 ** ((note - 69) / 12)))

    def load_midi(self, filepath):
        """
        Loads a MIDI file and converts it into a monophonic list of note events.
        Prioritizes the highest note if multiple are playing at once (simple monophonic conversion).
        Filters to only "read the treble clef" by taking the first track with notes.
        """
        mid = mido.MidiFile(filepath)
        
        # Extract Meta information first before any destructive filtering
        import os
        self.song_name = os.path.basename(filepath)
        self.artist = "Unknown"

        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    self.bpm = round(mido.tempo2bpm(msg.tempo))
                elif msg.type == 'time_signature':
                    self.time_signature = f"{msg.numerator}/{msg.denominator}"
                elif msg.type == 'key_signature':
                    self.key_signature = msg.key
                elif msg.type == 'track_name':
                    if self.song_name.endswith('.mid') or self.song_name.endswith('.midi'):
                        self.song_name = msg.name
                elif msg.type == 'text' and "artist" in msg.text.lower():
                    self.artist = msg.text
                elif msg.type == 'copyright' and self.artist == "Unknown":
                    self.artist = msg.text
        


        self.notes = []

        temp_notes = []
        active_starts = {} # pitch -> start_time_ms
        abs_time_ms = 0.0

        for msg in mid:
            dt_ms = msg.time * 1000
            abs_time_ms += dt_ms

            if msg.type == 'note_on' and msg.velocity > 0:
                if msg.note not in active_starts:
                    active_starts[msg.note] = abs_time_ms

            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_starts:
                    start_t = active_starts.pop(msg.note)
                    duration = abs_time_ms - start_t
                    if duration > 0:
                        temp_notes.append({
                            'start': int(start_t),
                            'duration': int(duration),
                            'pitch': msg.note,
                            'channel': getattr(msg, 'channel', 0)
                        })

        self.notes = sorted(temp_notes, key=lambda x: x['start'])
        self.update_duration()

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

    def export_arduino(self, output_filepath):
        """
        Generates the Arduino code.
        Converts the overlapping/gap-filled note list into a continuous stream of (freq, duration).
        """
        # Handle Drum Filtering & Generation
        filtered_notes = []
        enable_drums = getattr(self, 'enable_drums', False)
        drum_mode = getattr(self, 'drum_mode', 'Use MIDI Track')
        
        for n in self.notes:
            if n.get('channel', 0) == 9: # MIDI Channel 10
                if not enable_drums or drum_mode != 'Use MIDI Track': 
                    continue # Drop MIDI drums if disabled or overwritten by Auto-Gen
                
                # Map drum pitch to Buzzer frequencies
                p = n['pitch']
                if p in (35, 36, 1, 2): n_p = 28 # Kick
                elif p in (38, 40, 3, 4): n_p = 128 # Snare
                elif p in (42, 44, 46, 5): n_p = 129 # Hi-hat
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
                
                # Default hi-hat pattern
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
                    if beat_idx % 0.25 == 0: is_hihat = True  # Tight 16th note hats
                elif drum_mode == "Auto-Gen: Disco":
                    if beat_idx % 1 == 0: is_kick = True  # Four on the floor
                    if beat_idx % 4 in (1, 3): is_snare = True
                    if beat_idx % 1 == 0.5: is_hihat = True  # Off-beat hats
                elif drum_mode == "Auto-Gen: Hip-Hop":
                    if beat_idx % 4 in (0, 2.5): is_kick = True
                    if beat_idx % 4 in (1, 3): is_snare = True
                elif drum_mode == "Auto-Gen: Reggae":
                    if beat_idx % 4 == 2:  # Classic 'One Drop' on the 3rd beat
                        is_kick = True
                        is_snare = True
                        
                if is_hihat:
                    filtered_notes.append({'start': int(t), 'duration': 15, 'pitch': 129, 'channel': 9})
                if is_kick:
                    filtered_notes.append({'start': int(t), 'duration': 40, 'pitch': 28, 'channel': 9})
                if is_snare:
                    filtered_notes.append({'start': int(t), 'duration': 40, 'pitch': 128, 'channel': 9})
                
                t += 60000.0 / self.bpm / 4.0 if self.bpm > 0 else 125 # step by 16th notes
                beat_idx += 0.25

        # Build events from filtered notes
        events = []
        for n in filtered_notes:
            events.append((n['start'], 1, n['pitch']))
            events.append((n['start'] + n['duration'], -1, n['pitch']))

        events.sort(key=lambda x: (x[0], x[1])) 

        segments = []
        current_time = 0
        active_pitches = [] 

        arp_time_ms = 90 # 90ms per arpeggio note (reduces memory usage dramatically while keeping effect)
        arp_index = 0

        for time, type, pitch in events:
            duration = time - current_time

            if duration > 0:
                if active_pitches:
                    # Sort active pitches so we always arpeggiate cleanly (e.g., lowest to highest)
                    sorted_pitches = sorted(active_pitches)
                    
                    if len(sorted_pitches) == 1:
                        # Only one note, just play it
                        segments.append((self.note_to_freq(sorted_pitches[0]), int(duration)))
                    else:
                        # Multiple notes: Give priority to highest note (melody) so it doesn't get lost
                        highest_pitch = sorted_pitches[-1]
                        lowest_pitch = sorted_pitches[0]
                        rem_dur = duration
                        while rem_dur > 0:
                            if arp_index % 2 == 0:
                                # Melody stands out longer
                                step_dur = min(60, rem_dur)
                                segments.append((self.note_to_freq(highest_pitch), int(step_dur)))
                            else:
                                # Harmony is just a quick blip
                                step_dur = min(30, rem_dur)
                                segments.append((self.note_to_freq(lowest_pitch), int(step_dur)))
                            rem_dur -= step_dur
                            arp_index += 1
                else:
                    segments.append((0, int(duration)))
                    arp_index = 0 # reset arpeggiator on silence

            current_time = time

            if type == 1:
                active_pitches.append(pitch)
            else:
                if pitch in active_pitches:
                    active_pitches.remove(pitch) 

        # Generate Code
        header = f"""/*
  Maker UNO Melody
  Generated by Portable MIDI to Arduino Converter
  Build by AgentHitmanFaris (NC-Engineering)
  Detected Info -> BPM: {self.bpm} | Time Sig: {self.time_signature} | Key: {self.key_signature}
  Song Name: {self.song_name}
  Artist: {self.artist}
*/

#include <avr/pgmspace.h>

#define BUZZER_PIN 8

"""
        melody_array = "const int melody[] PROGMEM = {\n"
        duration_array = "const int noteDurations[] PROGMEM = {\n"

        # Memory Optimization: Merge adjacent segments with identical frequencies (especially adjacent rests)
        optimized_segments = []
        for freq, duration in segments:
            if duration <= 0: continue
            if optimized_segments and optimized_segments[-1][0] == freq:
                optimized_segments[-1] = (freq, optimized_segments[-1][1] + duration)
            else:
                optimized_segments.append((freq, duration))

        count = 0
        note_count = 0
        for freq, duration in optimized_segments:

            melody_array += f"  {freq}, "
            duration_array += f"  {duration}, "
            count += 1
            note_count += 1
            if count % 10 == 0:
                melody_array += "\n"
                duration_array += "\n"

        melody_array = melody_array.rstrip(", \n") + "\n};\n"
        duration_array = duration_array.rstrip(", \n") + "\n};\n"

        setup_loop = f"""
// --- TO ADJUST TEMPO: Increase for FASTER, decrease for SLOWER ---
float tempoMultiplier = 1.0;

const int noteCount = sizeof(melody) / sizeof(melody[0]);

void setup() {{
  pinMode(BUZZER_PIN, OUTPUT);
}}

void loop() {{
  for (int i = 0; i < noteCount; i++) {{
    int freq = pgm_read_word_near(melody + i);
    int duration = pgm_read_word_near(noteDurations + i);
    
    // Apply Tempo Multiplier
    int finalDuration = (int)(duration / tempoMultiplier);
    
    unsigned long noteStart = millis();
    if (freq > 0) {{
      // Articulation: Play for 90% of duration, 10% silence
      tone(BUZZER_PIN, freq, finalDuration * 0.9);
    }} else if (freq < 0) {{
      // White Noise Drum Mode (-1 = Snare, -2 = HiHat)
      int maxDel = (freq == -1) ? 800 : 150;
      while (millis() - noteStart < finalDuration * 0.9) {{
        digitalWrite(BUZZER_PIN, random(2));
        delayMicroseconds(random(50, maxDel));
      }}
      digitalWrite(BUZZER_PIN, LOW);
    }} else {{
      noTone(BUZZER_PIN);
    }}
    
    // Wait exactly the rest of the required duration length to maintain sync
    while (millis() - noteStart < finalDuration) {{
      delay(1);
    }}
    noTone(BUZZER_PIN);
  }}
  delay(2000); // Wait 2 seconds before repeating
}}
"""
        full_code = header + melody_array + "\n" + duration_array + "\n" + setup_loop

        with open(output_filepath, 'w') as f:
            f.write(full_code)

        return True