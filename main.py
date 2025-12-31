import pygame
import converter
import sys
import numpy as np
import time

# Attempt to import native dialogs; fallback or error if on non-Windows (though requirements say Windows)
try:
    import windows_dialogs
except ImportError:
    windows_dialogs = None

class Button:
    def __init__(self, rect, text, callback, color=(100, 100, 100), hover_color=(150, 150, 150), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.font = pygame.font.SysFont("Arial", 16)

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 1) # Border

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.callback()
                return True
        return False

class MidiEditorApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Portable MIDI to Arduino Editor")
        self.screen_width = 1000
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.converter = converter.MidiConverter()

        # UI State
        self.scroll_x = 0
        self.scroll_y = 0 # In pixels, 0 is top (High pitch)
        self.zoom_x = 0.1 # pixels per ms
        self.row_height = 14
        self.header_height = 50
        self.keyboard_width = 40

        self.selected_note_index = None
        self.drag_state = None # None, 'move', 'resize', 'scroll'
        self.drag_start_pos = (0, 0)

        self.playing = False
        self.last_play_time = 0

        # Colors
        self.bg_color = (255, 255, 255)
        self.grid_color = (240, 240, 240)
        self.grid_dark = (200, 200, 200)
        self.note_color = (100, 149, 237) # Cornflower Blue
        self.note_selected_color = (220, 20, 60) # Crimson
        self.playhead_color = (0, 255, 0)

        # Audio
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            self.audio_end_event = pygame.USEREVENT + 1
            pygame.mixer.set_endevent(self.audio_end_event)
        except Exception as e:
            print(f"Warning: Audio init failed. Preview will be disabled. Error: {e}")
            self.playing = False # Ensure we don't try to play

        self.buttons = []
        self.setup_ui()

    def setup_ui(self):
        self.buttons = [
            Button((10, 10, 100, 30), "Load MIDI", self.load_midi),
            Button((120, 10, 120, 30), "Export Arduino", self.export_arduino),
            Button((250, 10, 100, 30), "Play/Stop", self.toggle_play),
            Button((360, 10, 100, 30), "Clear All", self.clear_all),
        ]

    def load_midi(self):
        if not windows_dialogs:
            print("Native dialogs not available.")
            return

        path = windows_dialogs.open_file_dialog("Load MIDI", "MIDI Files", "*.mid;*.midi")
        if path:
            try:
                self.converter.load_midi(path)
                self.scroll_x = 0
                print(f"Loaded {len(self.converter.notes)} notes.")
            except Exception as e:
                print(f"Error loading MIDI: {e}")

    def export_arduino(self):
        if not windows_dialogs:
            return

        path = windows_dialogs.save_file_dialog("Export Arduino", "Arduino Sketch", "*.ino", "ino")
        if path:
            try:
                # Ensure extension
                if not path.lower().endswith(".ino"):
                    path += ".ino"
                self.converter.export_arduino(path)
                print(f"Exported to {path}")
            except Exception as e:
                print(f"Error exporting: {e}")

    def clear_all(self):
        self.converter.notes = []
        self.converter.update_duration()
        self.selected_note_index = None
        self.stop_play()

    def toggle_play(self):
        if self.playing:
            self.stop_play()
        else:
            self.start_play()

    def start_play(self):
        self.playing = True
        self.play_start_time = time.time()
        # Flatten logic for playback
        # We will use a generator or simple index tracker in the update loop
        # But pygame mixer is not a synth. We need to feed it buffers or play generated sounds.
        # Generating a single long buffer is memory intensive.
        # Scheduling events is better.

        # Simple approach: Pre-generate the whole song? No.
        # Queue approach: Generate small chunks? Complex.

        # Let's use the same logic as the "preview" in Tkinter version but non-blocking?
        # The Tkinter version used `pygame.time.wait` which BLOCKS. We can't block here.

        # Solution: Use a tracking index and check `time.time()` in `update()`.
        # When time > note_start, play sound. When time > note_end, stop sound.

        self.play_cursor_ms = 0
        self.active_sounds = [] # (end_time, channel)

        # Prepare event list
        self.play_events = []
        for n in self.converter.notes:
            self.play_events.append({'time': n['start'], 'type': 'on', 'pitch': n['pitch'], 'id': id(n)})
            self.play_events.append({'time': n['start'] + n['duration'], 'type': 'off', 'pitch': n['pitch'], 'id': id(n)})

        self.play_events.sort(key=lambda x: x['time'])
        self.play_event_index = 0
        self.last_wall_time = time.time()

    def stop_play(self):
        self.playing = False
        pygame.mixer.stop()

    def update_audio(self):
        if not self.playing:
            return

        now = time.time()
        dt_ms = (now - self.last_wall_time) * 1000
        self.last_wall_time = now
        self.play_cursor_ms += dt_ms

        # Process events
        while self.play_event_index < len(self.play_events):
            evt = self.play_events[self.play_event_index]
            if evt['time'] <= self.play_cursor_ms:
                if evt['type'] == 'on':
                    freq = self.converter.note_to_freq(evt['pitch'])
                    if freq > 0:
                        # We need to play this indefinitely until 'off'
                        # But we don't know when 'off' is relative to now easily without lookahead?
                        # Actually we do know duration.
                        # But monophonic synth logic?
                        # Let's just play overlapping sounds for preview, it sounds okay.
                        # Construct a sound.
                        # How long? Until the note off?
                        # We can just play a sound and stop it later.
                        # Or better: generate a sound of exact duration.

                        # Find duration
                        duration = 0
                        # Look ahead for the off event with same id?
                        # Optimization: store duration in 'on' event.
                        pass
                self.play_event_index += 1
            else:
                break

        if self.play_cursor_ms > self.converter.total_duration + 1000:
            self.stop_play()

    # Re-implementing audio strategy:
    # Since we are in a game loop, we can just check what SHOULD be playing right now (Monophonic).
    # This matches Arduino logic perfectly.

    def update_audio_monophonic(self):
        if not self.playing:
            return

        now = time.time()
        dt_ms = (now - self.last_wall_time) * 1000
        self.last_wall_time = now
        self.play_cursor_ms += dt_ms

        # Find active note (Priority: Last started or Highest?)
        # Let's stick to the Arduino export logic: "Last Note Priority" or similar.
        # Actually export logic sorts segments.

        # Simple check: what note is under the cursor?
        active_note = None
        # Iterate all notes (naive, optimize if slow)
        candidates = []
        for n in self.converter.notes:
            if n['start'] <= self.play_cursor_ms < n['start'] + n['duration']:
                candidates.append(n)

        freq = 0
        if candidates:
            # Pick one. Max pitch? Or Start time?
            # Let's pick max start time (most recently started), then max pitch.
            candidates.sort(key=lambda x: (x['start'], x['pitch']))
            active_note = candidates[-1]
            freq = self.converter.note_to_freq(active_note['pitch'])

        # Manage Sound
        # If freq changed, stop old, start new.
        if not hasattr(self, 'current_freq'):
            self.current_freq = 0
            self.sound_channel = None

        if freq != self.current_freq:
            if self.sound_channel:
                self.sound_channel.stop()
                self.sound_channel = None

            if freq > 0:
                # Generate a short buffer (e.g. 100ms) and loop it?
                # Or just a long one?
                # Square wave
                arr = self.generate_square_wave(freq, 500) # 0.5s buffer
                snd = pygame.sndarray.make_sound(arr)
                self.sound_channel = snd.play(loops=-1) # Loop indefinitely

            self.current_freq = freq

        # If cursor passed end
        if self.play_cursor_ms > self.converter.total_duration + 500:
            if self.sound_channel: self.sound_channel.stop()
            self.playing = False
            self.current_freq = 0

    def generate_square_wave(self, freq, duration_ms, sample_rate=44100):
        t = np.linspace(0, duration_ms / 1000, int(sample_rate * duration_ms / 1000), False)
        wave = 0.5 * np.sign(np.sin(2 * np.pi * freq * t))
        return (wave * 32767).astype(np.int16)

    def run(self):
        while True:
            self.handle_events()
            self.update_audio_monophonic()
            self.draw()
            self.clock.tick(60) # 60 FPS

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle Buttons
            handled = False
            for btn in self.buttons:
                if btn.handle_event(event):
                    handled = True
                    break
            if handled: continue

            # Handle Editor
            self.handle_editor_event(event)

    def get_note_at_pos(self, pos):
        mx, my = pos
        # Adjust for scroll and offset
        grid_x = mx - self.keyboard_width + self.scroll_x
        grid_y = my - self.header_height + self.scroll_y

        # Check notes
        for i, n in enumerate(self.converter.notes):
            nx = n['start'] * self.zoom_x
            ny = (127 - n['pitch']) * self.row_height
            nw = n['duration'] * self.zoom_x
            nh = self.row_height

            if nx <= grid_x <= nx + nw and ny <= grid_y <= ny + nh:
                return i, (nx, ny, nw, nh)
        return None, None

    def screen_to_grid(self, pos):
        mx, my = pos
        time_ms = (mx - self.keyboard_width + self.scroll_x) / self.zoom_x
        pitch = 127 - int((my - self.header_height + self.scroll_y) / self.row_height)
        return time_ms, pitch

    def handle_editor_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                # Check for Note Click
                index, rect_info = self.get_note_at_pos(event.pos)
                if index is not None:
                    self.selected_note_index = index
                    # Check resize (right edge)
                    nx, ny, nw, nh = rect_info
                    grid_x = event.pos[0] - self.keyboard_width + self.scroll_x
                    if grid_x > nx + nw - 10:
                        self.drag_state = 'resize'
                    else:
                        self.drag_state = 'move'

                    self.drag_start_pos = event.pos
                    n = self.converter.notes[index]
                    self.drag_orig_data = {'start': n['start'], 'pitch': n['pitch'], 'duration': n['duration']}
                else:
                    # Click on empty space - Deselect
                    self.selected_note_index = None
                    # Or scroll?

            elif event.button == 3: # Right Click - Create
                if event.pos[0] > self.keyboard_width and event.pos[1] > self.header_height:
                    t, p = self.screen_to_grid(event.pos)
                    if 0 <= p <= 127:
                        start = max(0, int(t))
                        # Align to grid? Optional.
                        new_note = {'start': start, 'duration': 500, 'pitch': p}
                        self.converter.notes.append(new_note)
                        self.converter.set_notes(self.converter.notes)
                        self.selected_note_index = self.converter.notes.index(new_note)

            elif event.button == 4: # Scroll Up (Wheel)
                self.scroll_y = max(0, self.scroll_y - 30)
            elif event.button == 5: # Scroll Down (Wheel)
                self.scroll_y += 30

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if self.drag_state:
                    self.drag_state = None
                    self.converter.set_notes(self.converter.notes) # Sort

        elif event.type == pygame.MOUSEMOTION:
            if self.drag_state == 'move':
                dx = event.pos[0] - self.drag_start_pos[0]
                dy = event.pos[1] - self.drag_start_pos[1]

                dt = dx / self.zoom_x
                dp = -int(dy / self.row_height)

                n = self.converter.notes[self.selected_note_index]
                n['start'] = max(0, int(self.drag_orig_data['start'] + dt))
                n['pitch'] = min(127, max(0, int(self.drag_orig_data['pitch'] + dp)))

            elif self.drag_state == 'resize':
                dx = event.pos[0] - self.drag_start_pos[0]
                dt = dx / self.zoom_x

                n = self.converter.notes[self.selected_note_index]
                n['duration'] = max(50, int(self.drag_orig_data['duration'] + dt))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DELETE:
                if self.selected_note_index is not None:
                    del self.converter.notes[self.selected_note_index]
                    self.selected_note_index = None
                    self.converter.update_duration()

    def draw(self):
        self.screen.fill(self.bg_color)

        # Draw Toolbar
        pygame.draw.rect(self.screen, (220, 220, 220), (0, 0, self.screen_width, self.header_height))
        for btn in self.buttons:
            btn.draw(self.screen)

        # Editor Area Clip
        editor_rect = pygame.Rect(0, self.header_height, self.screen_width, self.screen_height - self.header_height)
        self.screen.set_clip(editor_rect)

        # Draw Piano Keys (Left)
        # We need to account for scroll_y
        # Visible range
        start_pitch = 127 - int(self.scroll_y / self.row_height)
        end_pitch = 127 - int((self.scroll_y + editor_rect.height) / self.row_height)

        # Draw Grid
        grid_surface = self.screen

        # Grid Lines (Horizontal)
        for i in range(128):
            y = self.header_height + (127 - i) * self.row_height - self.scroll_y
            if y < self.header_height or y > self.screen_height: continue

            color = self.grid_color
            if i % 12 == 0: color = self.grid_dark # C notes

            pygame.draw.line(grid_surface, color, (self.keyboard_width, y), (self.screen_width, y))

            # Draw Key
            key_color = (255, 255, 255)
            is_black = (i % 12) in [1, 3, 6, 8, 10]
            if is_black: key_color = (0, 0, 0)

            pygame.draw.rect(grid_surface, key_color, (0, y, self.keyboard_width, self.row_height))
            pygame.draw.rect(grid_surface, (150, 150, 150), (0, y, self.keyboard_width, self.row_height), 1)

            if i % 12 == 0:
                font = pygame.font.SysFont("Arial", 10)
                txt = font.render(f"C{i//12 - 1}", True, (255, 0, 0))
                grid_surface.blit(txt, (2, y + 1))

        # Notes
        for i, n in enumerate(self.converter.notes):
            x = self.keyboard_width - self.scroll_x + n['start'] * self.zoom_x
            y = self.header_height + (127 - n['pitch']) * self.row_height - self.scroll_y
            w = n['duration'] * self.zoom_x
            h = self.row_height

            if x + w < self.keyboard_width: continue
            if x > self.screen_width: continue
            if y + h < self.header_height: continue
            if y > self.screen_height: continue

            color = self.note_selected_color if i == self.selected_note_index else self.note_color

            r = pygame.Rect(x, y, w, h)
            # Clamp to visible area for drawing cleanliness? Not strictly needed with set_clip
            pygame.draw.rect(self.screen, color, r)
            pygame.draw.rect(self.screen, (0, 0, 0), r, 1)

        # Playhead
        if self.playing:
            ph_x = self.keyboard_width - self.scroll_x + self.play_cursor_ms * self.zoom_x
            if ph_x > self.keyboard_width:
                pygame.draw.line(self.screen, self.playhead_color, (ph_x, self.header_height), (ph_x, self.screen_height), 2)

        self.screen.set_clip(None)
        pygame.display.flip()

if __name__ == "__main__":
    MidiEditorApp().run()
