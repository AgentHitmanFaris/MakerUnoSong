"""
Smart Adaptive Beat & Musical Intelligence Engine for Maker UNO.
Build by AgentHitmanFaris (NC-Engineering).

This engine moves beyond static looping presets by "thinking" about song structure:
- Analyzes musical energy, note density, velocity, and cadence across bars.
- Identifies structural sections: INTRO, VERSE, PRE-CHORUS, CHORUS/CLIMAX, BRIDGE, OUTRO.
- Synthesizes intelligent drum patterns that adapt to the song's energy and melody:
    * Intro: atmospheric, gentle hi-hat ticks, soft kick on bar downbeat.
    * Verse: foundational steady groove supporting melody.
    * Pre-Chorus: building tension, rising snare velocity and density.
    * Chorus/Drop: full driving dynamic groove, syncopated kick locking to melody accents.
    * Bridge/Breakdown: half-time snare, kick dropouts for dramatic contrast.
    * Fills: generates musical drum fills (snare rolls, triplet bursts) every 4/8 bars.
- Key and scale detection using pitch class profile analysis.
"""

import math
from collections import Counter

class SmartBeatEngine:
    """
    Intelligent musical analyzer and adaptive drum synthesizer.
    """

    PITCH_CLASS_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Krumhansl-Schmuckler Key Profiles (Major and Minor)
    MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

    def __init__(self):
        pass

    @classmethod
    def detect_musical_key(cls, notes: list) -> tuple[str, str]:
        """
        Analyzes pitch class distribution using Krumhansl-Schmuckler harmonic correlation.
        Returns (key_name, scale_type), e.g. ("C", "Major") or ("A", "Minor").
        """
        if not notes:
            return "C", "Major"

        # Calculate pitch class duration weights
        pc_weights = [0.0] * 12
        for n in notes:
            if n.get('channel', 0) == 9:
                continue # Skip drums
            pitch = n.get('pitch', 0)
            if pitch in (0, 28, 128, 129):
                continue
            pc = pitch % 12
            dur = max(20, n.get('duration', 100))
            pc_weights[pc] += dur

        total_weight = sum(pc_weights)
        if total_weight <= 0:
            return "C", "Major"

        best_corr = -999.0
        best_key = "C"
        best_mode = "Major"

        def _pearson_corr(x, y):
            n = len(x)
            mean_x = sum(x) / n
            mean_y = sum(y) / n
            num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
            den_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
            den_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))
            if den_x * den_y == 0:
                return 0.0
            return num / (den_x * den_y)

        for tonic in range(12):
            # Rotated profiles
            major_rot = [cls.MAJOR_PROFILE[(i - tonic) % 12] for i in range(12)]
            minor_rot = [cls.MINOR_PROFILE[(i - tonic) % 12] for i in range(12)]

            corr_maj = _pearson_corr(pc_weights, major_rot)
            corr_min = _pearson_corr(pc_weights, minor_rot)

            if corr_maj > best_corr:
                best_corr = corr_maj
                best_key = cls.PITCH_CLASS_NAMES[tonic]
                best_mode = "Major"

            if corr_min > best_corr:
                best_corr = corr_min
                best_key = cls.PITCH_CLASS_NAMES[tonic]
                best_mode = "Minor"

        return best_key, best_mode

    @classmethod
    def analyze_structure(cls, notes: list, bpm: float, time_signature: str = "4/4") -> dict:
        """
        Segments song into musical measures, evaluates note density & energy,
        and assigns structural section labels (INTRO, VERSE, PRE-CHORUS, CHORUS, BRIDGE, OUTRO).
        """
        if not notes:
            return {
                "total_measures": 0,
                "sections": [],
                "avg_density": 0.0,
                "peak_energy": 0.0,
                "key_detected": "C Major",
                "pitch_range": (0, 0),
            }

        # Parse time signature
        try:
            num, den = map(int, time_signature.split('/'))
        except Exception:
            num, den = 4, 4

        safe_bpm = bpm if bpm > 0 else 120.0
        # Duration of one beat in ms
        beat_ms = (60000.0 / safe_bpm) * (4.0 / den)
        bar_ms = beat_ms * num

        total_dur_ms = max(n['start'] + n.get('duration', 0) for n in notes)
        num_measures = max(1, math.ceil(total_dur_ms / bar_ms))

        # Filter melody/harmony notes (exclude channel 9)
        mel_notes = [n for n in notes if n.get('channel', 0) != 9 and n.get('pitch', 0) not in (28, 128, 129)]
        if not mel_notes:
            mel_notes = notes

        pitches = [n['pitch'] for n in mel_notes if n.get('pitch', 0) > 0]
        min_pitch = min(pitches) if pitches else 60
        max_pitch = max(pitches) if pitches else 72

        # Measure energy calculation: count notes and note coverage in each bar
        measure_energy = [0.0] * num_measures
        measure_note_count = [0] * num_measures

        for n in mel_notes:
            start_m = int(n['start'] // bar_ms)
            if 0 <= start_m < num_measures:
                measure_note_count[start_m] += 1
                # Weight by pitch height (higher pitch often correlates with vocal/chorus climax)
                pitch_factor = 1.0 + max(0, (n.get('pitch', 60) - 60) / 48.0)
                measure_energy[start_m] += pitch_factor

        # Normalize energy 0.0 to 1.0
        max_e = max(measure_energy) if max(measure_energy) > 0 else 1.0
        norm_energy = [e / max_e for e in measure_energy]

        # Classify measures into sections
        sections = []
        cur_sec_type = None
        sec_start_bar = 0

        for m_idx in range(num_measures):
            progress = m_idx / float(num_measures)
            e = norm_energy[m_idx]

            # Heuristic section classification
            if progress < 0.12 and e < 0.45:
                stype = "INTRO"
            elif progress > 0.88 and e < 0.40:
                stype = "OUTRO"
            elif e >= 0.70:
                stype = "CHORUS"
            elif e >= 0.45:
                # If preceding a chorus and rising, pre-chorus
                if m_idx + 1 < num_measures and norm_energy[m_idx + 1] >= 0.70:
                    stype = "PRE-CHORUS"
                else:
                    stype = "VERSE"
            elif progress > 0.55 and progress < 0.75 and e < 0.35:
                stype = "BRIDGE"
            else:
                stype = "VERSE"

            if cur_sec_type is None:
                cur_sec_type = stype
                sec_start_bar = m_idx
            elif stype != cur_sec_type:
                # Flush previous section
                sections.append({
                    "name": cur_sec_type,
                    "start_bar": sec_start_bar,
                    "end_bar": m_idx - 1,
                    "start_ms": int(sec_start_bar * bar_ms),
                    "end_ms": int(m_idx * bar_ms),
                    "avg_energy": round(sum(norm_energy[sec_start_bar:m_idx]) / max(1, m_idx - sec_start_bar), 2)
                })
                cur_sec_type = stype
                sec_start_bar = m_idx

        # Flush final section
        if cur_sec_type is not None:
            sections.append({
                "name": cur_sec_type,
                "start_bar": sec_start_bar,
                "end_bar": num_measures - 1,
                "start_ms": int(sec_start_bar * bar_ms),
                "end_ms": int(total_dur_ms),
                "avg_energy": round(sum(norm_energy[sec_start_bar:num_measures]) / max(1, num_measures - sec_start_bar), 2)
            })

        key_name, key_mode = cls.detect_musical_key(notes)
        avg_density = round(len(mel_notes) / (total_dur_ms / 1000.0), 1) if total_dur_ms > 0 else 0.0

        return {
            "total_measures": num_measures,
            "bar_ms": bar_ms,
            "beat_ms": beat_ms,
            "sections": sections,
            "measure_energy": norm_energy,
            "avg_density": avg_density,
            "peak_energy": round(max_e, 2),
            "key_detected": f"{key_name} {key_mode}",
            "pitch_range": (min_pitch, max_pitch),
            "time_signature": f"{num}/{den}",
            "bpm": safe_bpm
        }

    @classmethod
    def generate_intelligent_beat(cls, notes: list, bpm: float, time_signature: str = "4/4",
                                  style: str = "Adaptive AI") -> list:
        """
        Main Intelligent Beat Generator.
        Instead of a preset loop, it examines the structural analysis and melody accents
        to compose a dynamic drum arrangement for the Maker UNO.
        Returns a list of note dicts: {'start': ms, 'duration': ms, 'pitch': p, 'channel': 9}
        where pitch is:
          28  = Kick (low blip)
          128 = Snare (white noise burst)
          129 = Hi-Hat (crisp white noise tick)
        """
        analysis = cls.analyze_structure(notes, bpm, time_signature)
        num_measures = analysis["total_measures"]
        bar_ms = analysis["bar_ms"]
        beat_ms = analysis["beat_ms"]
        norm_energy = analysis["measure_energy"]
        sections = analysis["sections"]

        try:
            num_beats = int(time_signature.split('/')[0])
        except Exception:
            num_beats = 4

        # Precompute melody onset timestamps per bar for accent synchronization
        melody_onsets_by_bar = {}
        for n in notes:
            if n.get('channel', 0) != 9 and n.get('pitch', 0) not in (28, 128, 129):
                b_idx = int(n['start'] // bar_ms)
                if b_idx not in melody_onsets_by_bar:
                    melody_onsets_by_bar[b_idx] = []
                offset_in_bar = (n['start'] - (b_idx * bar_ms)) / bar_ms
                melody_onsets_by_bar[b_idx].append(offset_in_bar)

        # Style modifiers
        energy_boost = 1.2 if "High Energy" in style else (0.8 if "Chill" in style else 1.0)
        is_rock = "Rock" in style

        drum_notes = []

        def get_sec_for_bar(bar):
            for s in sections:
                if s["start_bar"] <= bar <= s["end_bar"]:
                    return s["name"]
            return "VERSE"

        for b in range(num_measures):
            sec_name = get_sec_for_bar(b)
            energy = (norm_energy[b] * energy_boost) if b < len(norm_energy) else 0.5
            bar_start_ms = b * bar_ms
            is_section_last_bar = False
            for s in sections:
                if s["end_bar"] == b:
                    is_section_last_bar = True
                    break

            is_cadence_bar = (b % 4 == 3) or is_section_last_bar
            mel_accents = melody_onsets_by_bar.get(b, [])

            # --- 1. INTRO SECTION ---
            if sec_name == "INTRO":
                # Subtle beat 1 kick, gentle hi-hat groove
                drum_notes.append({'start': int(bar_start_ms), 'duration': 35, 'pitch': 28, 'channel': 9})
                for beat in range(num_beats):
                    drum_notes.append({'start': int(bar_start_ms + beat * beat_ms), 'duration': 12, 'pitch': 129, 'channel': 9})
                    if energy > 0.35:
                        drum_notes.append({'start': int(bar_start_ms + (beat + 0.5) * beat_ms), 'duration': 10, 'pitch': 129, 'channel': 9})

            # --- 2. OUTRO SECTION ---
            elif sec_name == "OUTRO":
                # Fading rhythm: downbeat kick and soft backbeat snare
                drum_notes.append({'start': int(bar_start_ms), 'duration': 35, 'pitch': 28, 'channel': 9})
                if num_beats >= 4:
                    drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})
                elif num_beats == 3:
                    drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 30, 'pitch': 128, 'channel': 9})
                elif num_beats == 6:
                    drum_notes.append({'start': int(bar_start_ms + 3 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})

                for beat in range(num_beats):
                    drum_notes.append({'start': int(bar_start_ms + beat * beat_ms), 'duration': 10, 'pitch': 129, 'channel': 9})

            # --- 3. BRIDGE / BREAKDOWN SECTION ---
            elif sec_name == "BRIDGE":
                # Half-time feel: kick only on 1, snare on half-bar, 8th hi-hats
                drum_notes.append({'start': int(bar_start_ms), 'duration': 40, 'pitch': 28, 'channel': 9})
                if num_beats >= 4:
                    drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 40, 'pitch': 128, 'channel': 9})
                elif num_beats == 3:
                    drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})
                elif num_beats == 6:
                    drum_notes.append({'start': int(bar_start_ms + 3 * beat_ms), 'duration': 40, 'pitch': 128, 'channel': 9})

                for beat in range(num_beats):
                    drum_notes.append({'start': int(bar_start_ms + beat * beat_ms), 'duration': 12, 'pitch': 129, 'channel': 9})
                    drum_notes.append({'start': int(bar_start_ms + (beat + 0.5) * beat_ms), 'duration': 10, 'pitch': 129, 'channel': 9})

            # --- 4. PRE-CHORUS BUILD-UP ---
            elif sec_name == "PRE-CHORUS":
                # 4-on-the-floor driving kick, accelerating snare build-up
                for beat in range(num_beats):
                    drum_notes.append({'start': int(bar_start_ms + beat * beat_ms), 'duration': 40, 'pitch': 28, 'channel': 9})
                    drum_notes.append({'start': int(bar_start_ms + beat * beat_ms), 'duration': 12, 'pitch': 129, 'channel': 9})
                    drum_notes.append({'start': int(bar_start_ms + (beat + 0.5) * beat_ms), 'duration': 10, 'pitch': 129, 'channel': 9})

                if is_cadence_bar or energy > 0.5:
                    for s_step in range(4):
                        drum_notes.append({
                            'start': int(bar_start_ms + (num_beats - 1 + s_step * 0.25) * beat_ms),
                            'duration': 25,
                            'pitch': 128,
                            'channel': 9
                        })
                else:
                    if num_beats >= 4:
                        drum_notes.append({'start': int(bar_start_ms + 1 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})
                        drum_notes.append({'start': int(bar_start_ms + 3 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})
                    elif num_beats == 3:
                        drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})
                    elif num_beats == 6:
                        drum_notes.append({'start': int(bar_start_ms + 3 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})

            # --- 5. CHORUS / CLIMAX & VERSE (DYNAMIC GROOVE) ---
            else:
                is_chorus = (sec_name == "CHORUS")

                # KICK PLACEMENT
                drum_notes.append({'start': int(bar_start_ms), 'duration': 40, 'pitch': 28, 'channel': 9})

                if num_beats >= 4:
                    if is_chorus or is_rock:
                        drum_notes.append({'start': int(bar_start_ms + 2.5 * beat_ms), 'duration': 40, 'pitch': 28, 'channel': 9})
                        if energy > 0.75:
                            drum_notes.append({'start': int(bar_start_ms + 1.75 * beat_ms), 'duration': 35, 'pitch': 28, 'channel': 9})
                    else:
                        drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 40, 'pitch': 28, 'channel': 9})
                elif num_beats == 6:
                    # 6/8 compound time: secondary kick on beat 4 (dotted-quarter 2)
                    if is_chorus or energy > 0.6:
                        drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 35, 'pitch': 28, 'channel': 9})
                        drum_notes.append({'start': int(bar_start_ms + 4 * beat_ms), 'duration': 35, 'pitch': 28, 'channel': 9})
                elif num_beats == 3:
                    if is_chorus and energy > 0.7:
                        drum_notes.append({'start': int(bar_start_ms + 1.5 * beat_ms), 'duration': 35, 'pitch': 28, 'channel': 9})

                # Melody-locked kick accents (prevent overlapping within 80ms)
                for acc in mel_accents:
                    if 0.55 <= acc <= 0.88:
                        t_acc = bar_start_ms + acc * bar_ms
                        if not any(abs(d['start'] - t_acc) < 80 and d['pitch'] == 28 for d in drum_notes):
                            drum_notes.append({'start': int(t_acc), 'duration': 35, 'pitch': 28, 'channel': 9})
                            break

                # SNARE PLACEMENT
                if not (is_cadence_bar or is_section_last_bar):
                    if num_beats >= 4:
                        drum_notes.append({'start': int(bar_start_ms + 1 * beat_ms), 'duration': 40, 'pitch': 128, 'channel': 9})
                        drum_notes.append({'start': int(bar_start_ms + 3 * beat_ms), 'duration': 40, 'pitch': 128, 'channel': 9})
                    elif num_beats == 3:
                        drum_notes.append({'start': int(bar_start_ms + 1 * beat_ms), 'duration': 30, 'pitch': 128, 'channel': 9})
                        drum_notes.append({'start': int(bar_start_ms + 2 * beat_ms), 'duration': 30, 'pitch': 128, 'channel': 9})
                    elif num_beats == 6:
                        drum_notes.append({'start': int(bar_start_ms + 3 * beat_ms), 'duration': 40, 'pitch': 128, 'channel': 9})
                else:
                    # SMART DRUM FILL ON CADENCE
                    if num_beats >= 4:
                        drum_notes.append({'start': int(bar_start_ms + 1 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})
                        fill_times = [2.0, 2.5, 3.0, 3.25, 3.5, 3.75]
                        for f_beat in fill_times:
                            drum_notes.append({
                                'start': int(bar_start_ms + f_beat * beat_ms),
                                'duration': 25,
                                'pitch': 128,
                                'channel': 9
                            })
                            if f_beat in (3.0, 3.5):
                                drum_notes.append({
                                    'start': int(bar_start_ms + f_beat * beat_ms),
                                    'duration': 30,
                                    'pitch': 28,
                                    'channel': 9
                                })
                    elif num_beats == 3:
                        drum_notes.append({'start': int(bar_start_ms + 1 * beat_ms), 'duration': 30, 'pitch': 128, 'channel': 9})
                        for f_beat in [1.5, 2.0, 2.25, 2.5, 2.75]:
                            drum_notes.append({'start': int(bar_start_ms + f_beat * beat_ms), 'duration': 22, 'pitch': 128, 'channel': 9})
                    elif num_beats == 6:
                        drum_notes.append({'start': int(bar_start_ms + 3 * beat_ms), 'duration': 35, 'pitch': 128, 'channel': 9})
                        for f_beat in [4.0, 4.5, 5.0, 5.25, 5.5, 5.75]:
                            drum_notes.append({'start': int(bar_start_ms + f_beat * beat_ms), 'duration': 22, 'pitch': 128, 'channel': 9})

                # HI-HAT PLACEMENT
                for beat in range(num_beats):
                    drum_notes.append({'start': int(bar_start_ms + beat * beat_ms), 'duration': 14, 'pitch': 129, 'channel': 9})
                    drum_notes.append({'start': int(bar_start_ms + (beat + 0.5) * beat_ms), 'duration': 12, 'pitch': 129, 'channel': 9})
                    if is_chorus and energy > 0.8:
                        drum_notes.append({'start': int(bar_start_ms + (beat + 0.25) * beat_ms), 'duration': 10, 'pitch': 129, 'channel': 9})
                        drum_notes.append({'start': int(bar_start_ms + (beat + 0.75) * beat_ms), 'duration': 10, 'pitch': 129, 'channel': 9})

        drum_notes.sort(key=lambda x: x['start'])
        return drum_notes
