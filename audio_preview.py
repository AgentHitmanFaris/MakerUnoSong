"""
Audio Preview & Synthesizer Engine for Maker UNO.
Build by AgentHitmanFaris (NC-Engineering).

Generates real-time PCM WAV audio matching the Maker UNO ATmega328P buzzer & white-noise drum engine:
- Monophonic square-wave / buzzer tone emulation with smooth articulation.
- White noise drum synthesis: Kick (low pitch sweep blip), Snare (noise burst), Hi-Hat (crisp tick).
- High-performance in-memory WAV generation via standard library (struct, wave, io).
- Non-blocking asynchronous playback via Windows winsound (SND_ASYNC | SND_MEMORY) with zero UI lag.
- Playhead tracking, seeking, tempo scaling, and live LED frame evaluation.
- WAV audio file export for CLI and offline preview.
"""

import math
import struct
import io
import wave
import time
import random
import bisect

import os
import tempfile

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

class AudioPreviewEngine:
    SAMPLE_RATE = 22050  # 22.05 kHz provides crisp audio with fast synthesis speed

    def __init__(self):
        self.wav_bytes = None
        self.total_duration_ms = 0
        self.is_playing = False
        self.play_start_epoch = 0.0
        self.start_offset_ms = 0.0
        self.tempo_multiplier = 1.0
        self.segments = [] # [(freq, dur_ms), ...]
        self._timeline_starts = []
        self._timeline_states = []
        self._temp_wav_file = None

    @staticmethod
    def _clamp16(val: float) -> int:
        return max(-32767, min(32767, int(val)))

    def synthesize(self, segments: list, tempo_multiplier: float = 1.0) -> bytes:
        """
        Synthesizes a list of (freq, duration_ms) segments into 16-bit PCM WAV bytes.
        Special markers:
          freq > 0  : Maker UNO Buzzer tone (square wave)
          freq == 0 : Rest / Silence
          freq == -1: Snare White Noise burst
          freq == -2: Hi-Hat crisp white noise tick
          freq == 28: Kick blip (frequency glide 130Hz -> 45Hz)
        """
        self.segments = list(segments)
        self.tempo_multiplier = max(0.2, min(3.0, float(tempo_multiplier)))
        sample_rate = self.SAMPLE_RATE

        total_ms = 0
        for f, d in self.segments:
            total_ms += int(d / self.tempo_multiplier)
        self.total_duration_ms = total_ms

        total_samples = int((total_ms / 1000.0) * sample_rate) + sample_rate // 2
        # Use bytearray buffer for rapid synthesis
        raw_samples = bytearray(total_samples * 2)

        write_idx = 0
        rand_seed = 12345
        def _fast_random():
            nonlocal rand_seed
            rand_seed = (1103515245 * rand_seed + 12345) & 0x7FFFFFFF
            return (rand_seed / 0x7FFFFFFF) * 2.0 - 1.0

        self._timeline_starts = []
        self._timeline_states = []
        accum_time_ms = 0

        for freq, duration_ms in self.segments:
            adj_dur_ms = int(duration_ms / self.tempo_multiplier)
            num_samples = int((adj_dur_ms / 1000.0) * sample_rate)
            if num_samples <= 0:
                continue

            # Build O(log N) timeline index for LED state and frequency lookup
            if freq in (-1, -2, 28):
                t_pin = 13 if freq == 28 else 7
            elif freq > 0:
                norm = max(0.0, min(1.0, (freq - 130.0) / 1870.0))
                t_pin = 3 + int(norm * 10)
            else:
                t_pin = 0
            self._timeline_starts.append(accum_time_ms)
            self._timeline_states.append((t_pin, freq, accum_time_ms + adj_dur_ms))
            accum_time_ms += adj_dur_ms

            if freq == 28:
                # Kick Drum: Frequency downward sweep 135Hz -> 42Hz + punch
                vol = 22000.0
                kick_len = min(num_samples, int(0.09 * sample_rate))
                phase = 0.0
                for i in range(num_samples):
                    if i < kick_len:
                        decay = math.exp(-i / (sample_rate * 0.03))
                        cur_freq = 42.0 + (135.0 - 42.0) * math.exp(-i / (sample_rate * 0.015))
                        phase += (2.0 * math.pi * cur_freq) / sample_rate
                        val = math.sin(phase) * vol * decay
                    else:
                        val = 0.0
                    pos = (write_idx + i) * 2
                    if pos + 1 < len(raw_samples):
                        s = self._clamp16(val)
                        raw_samples[pos] = s & 0xFF
                        raw_samples[pos + 1] = (s >> 8) & 0xFF

            elif freq > 0:
                # Maker UNO Piezo Buzzer: Square wave with 50% duty cycle and slight low-pass softening
                period = sample_rate / float(freq)
                vol = 14000.0
                tone_len = int(num_samples * 0.92) # Slight staccato articulation like Arduino tone()
                for i in range(num_samples):
                    if i < tone_len:
                        phase = (i % period) / period
                        val = vol if phase < 0.5 else -vol
                    else:
                        val = 0.0
                    pos = (write_idx + i) * 2
                    if pos + 1 < len(raw_samples):
                        s = self._clamp16(val)
                        raw_samples[pos] = s & 0xFF
                        raw_samples[pos + 1] = (s >> 8) & 0xFF

            elif freq == -1:
                # Snare Drum: White noise burst with exponential decay
                vol = 18000.0
                snare_len = min(num_samples, int(0.12 * sample_rate))
                for i in range(num_samples):
                    if i < snare_len:
                        decay = math.exp(-i / (sample_rate * 0.035))
                        noise = _fast_random() * vol * decay
                        # Add a low resonant pop around 180Hz
                        body = math.sin(2.0 * math.pi * 180.0 * (i / sample_rate)) * (vol * 0.4) * decay
                        val = noise + body
                    else:
                        val = 0.0
                    pos = (write_idx + i) * 2
                    if pos + 1 < len(raw_samples):
                        s = self._clamp16(val)
                        raw_samples[pos] = s & 0xFF
                        raw_samples[pos + 1] = (s >> 8) & 0xFF

            elif freq == -2:
                # Hi-Hat: Crisp, short metallic high-frequency noise
                vol = 12000.0
                hihat_len = min(num_samples, int(0.045 * sample_rate))
                prev_noise = 0.0
                for i in range(num_samples):
                    if i < hihat_len:
                        decay = math.exp(-i / (sample_rate * 0.012))
                        raw_n = _fast_random()
                        # High-pass filter simulation (difference)
                        hp_noise = (raw_n - prev_noise) * vol * decay
                        prev_noise = raw_n
                        val = hp_noise
                    else:
                        val = 0.0
                    pos = (write_idx + i) * 2
                    if pos + 1 < len(raw_samples):
                        s = self._clamp16(val)
                        raw_samples[pos] = s & 0xFF
                        raw_samples[pos + 1] = (s >> 8) & 0xFF

            else:
                # Rest / Silence (0)
                pass

            write_idx += num_samples

        # Package into standard WAV container
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, 'wb') as wf:
            wf.setnchannels(1) # Mono
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(raw_samples[:write_idx * 2])

        self.wav_bytes = wav_buf.getvalue()
        return self.wav_bytes

    def play(self, start_ms: int = 0):
        """Starts asynchronous non-blocking audio preview playback."""
        if not self.wav_bytes or not HAS_WINSOUND:
            self.is_playing = True
            self.play_start_epoch = time.time()
            self.start_offset_ms = float(start_ms)
            return

        self.stop()
        self.start_offset_ms = float(start_ms)

        # Slice WAV audio if starting from offset
        if start_ms > 0 and self.total_duration_ms > 0:
            sample_rate = self.SAMPLE_RATE
            start_sample = int((start_ms / 1000.0) * sample_rate)
            start_byte = start_sample * 2
            # Read header and slice raw frames
            try:
                with wave.open(io.BytesIO(self.wav_bytes), 'rb') as wf:
                    n_channels = wf.getnchannels()
                    samp_width = wf.getsampwidth()
                    fr = wf.getframerate()
                    total_frames = wf.getnframes()
                    if start_sample >= total_frames:
                        self.is_playing = False
                        return
                    wf.setpos(start_sample)
                    sliced_frames = wf.readframes(total_frames - start_sample)

                sub_buf = io.BytesIO()
                with wave.open(sub_buf, 'wb') as wf_out:
                    wf_out.setnchannels(n_channels)
                    wf_out.setsampwidth(samp_width)
                    wf_out.setframerate(fr)
                    wf_out.writeframes(sliced_frames)
                play_bytes = sub_buf.getvalue()
            except Exception:
                play_bytes = self.wav_bytes
        else:
            play_bytes = self.wav_bytes

        if HAS_WINSOUND:
            try:
                if not self._temp_wav_file or not os.path.exists(self._temp_wav_file):
                    tf = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                    self._temp_wav_file = tf.name
                    tf.close()

                with open(self._temp_wav_file, 'wb') as f:
                    f.write(play_bytes)

                winsound.PlaySound(self._temp_wav_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

        self.is_playing = True
        self.play_start_epoch = time.time()

    def stop(self):
        """Stops audio preview playback."""
        self.is_playing = False
        if HAS_WINSOUND:
            try:
                winsound.PlaySound(None, winsound.SND_PURGE)
            except Exception:
                pass

    def cleanup(self):
        """Releases audio resources and cleans up temporary audio preview files."""
        self.stop()
        if hasattr(self, '_temp_wav_file') and self._temp_wav_file:
            try:
                if os.path.exists(self._temp_wav_file):
                    os.remove(self._temp_wav_file)
            except Exception:
                pass
            self._temp_wav_file = None

    def __del__(self):
        self.cleanup()

    def get_current_time_ms(self) -> float:
        """Returns current playback position in milliseconds."""
        if not self.is_playing:
            return self.start_offset_ms

        elapsed_ms = (time.time() - self.play_start_epoch) * 1000.0
        cur_pos = self.start_offset_ms + elapsed_ms
        if self.total_duration_ms > 0 and cur_pos >= self.total_duration_ms:
            self.is_playing = False
            return self.total_duration_ms
        return cur_pos

    def get_led_state_at_ms(self, time_ms: float) -> tuple[int, int]:
        """
        Determines which Maker UNO LED (Pins 2 to 13) and buzzer are active at time_ms.
        Returns (active_led_pin, current_freq).
        """
        if not self.segments or time_ms < 0:
            return 0, 0

        # Fast O(log N) lookup if timeline precomputed
        if self._timeline_starts and len(self._timeline_starts) == len(self._timeline_states):
            idx = bisect.bisect_right(self._timeline_starts, time_ms) - 1
            if 0 <= idx < len(self._timeline_states):
                pin, freq, end_ms = self._timeline_states[idx]
                if time_ms < end_ms:
                    return pin, freq
            return 0, 0

        # Fallback linear search
        accum_ms = 0
        for freq, dur in self.segments:
            adj_dur = int(dur / self.tempo_multiplier)
            if accum_ms <= time_ms < (accum_ms + adj_dur):
                if freq in (-1, -2, 28):
                    return 13 if freq == 28 else 7, freq
                elif freq > 0:
                    norm = max(0.0, min(1.0, (freq - 130.0) / (2000.0 - 130.0)))
                    pin = 3 + int(norm * 10)
                    return pin, freq
                else:
                    return 0, 0
            accum_ms += adj_dur

        return 0, 0

    def export_wav(self, filepath: str) -> bool:
        """Exports the synthesized preview audio to a WAV file."""
        if not self.wav_bytes:
            return False
        with open(filepath, 'wb') as f:
            f.write(self.wav_bytes)
        return True
