import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import converter
import pygame
import threading
import time
import numpy as np

class MidiEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Portable MIDI to Arduino Editor")
        self.root.geometry("1000x600")

        self.converter = converter.MidiConverter()

        # Audio Setup
        self.audio_thread = None
        self.is_playing = False
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
        except Exception as e:
            print(f"Audio init failed: {e}")

        # UI Constants
        self.zoom_x = 0.1 # pixels per ms
        self.zoom_y = 10  # pixels per semitone
        self.base_pitch = 120 # Highest pitch to display at top
        self.min_pitch = 20
        self.row_height = 14

        self.setup_ui()
        self.selected_note_index = None
        self.drag_data = None

    def setup_ui(self):
        # Toolbar
        toolbar = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_load = tk.Button(toolbar, text="Load MIDI", command=self.load_midi)
        btn_load.pack(side=tk.LEFT, padx=2, pady=2)

        btn_save = tk.Button(toolbar, text="Export Arduino", command=self.save_arduino)
        btn_save.pack(side=tk.LEFT, padx=2, pady=2)

        tk.Frame(toolbar, width=20).pack(side=tk.LEFT) # Spacer

        btn_play = tk.Button(toolbar, text="Play Preview", command=self.toggle_play)
        btn_play.pack(side=tk.LEFT, padx=2, pady=2)

        tk.Label(toolbar, text=" | Instructions: Click to Select, Drag to Move. Del to Remove.").pack(side=tk.LEFT, padx=10)

        # Main Editor Area
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)

        self.canvas = tk.Canvas(self.canvas_frame, bg='white',
                                xscrollcommand=self.h_scroll.set,
                                yscrollcommand=self.v_scroll.set)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Event Bindings
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click) # Right click to create
        self.root.bind("<Delete>", self.delete_selection)

    def load_midi(self):
        filepath = filedialog.askopenfilename(filetypes=[("MIDI Files", "*.mid *.midi")])
        if filepath:
            try:
                self.converter.load_midi(filepath)
                self.redraw()
                messagebox.showinfo("Success", f"Loaded {len(self.converter.notes)} notes.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load MIDI: {e}")

    def save_arduino(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".ino", filetypes=[("Arduino Sketch", "*.ino")])
        if filepath:
            try:
                self.converter.export_arduino(filepath)
                messagebox.showinfo("Success", f"Exported to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

    def redraw(self):
        self.canvas.delete("all")
        notes = self.converter.get_notes()
        if not notes:
            return

        # Calculate canvas size
        max_time = self.converter.total_duration
        width = int(max_time * self.zoom_x) + 100
        height = (128 * self.row_height)

        self.canvas.config(scrollregion=(0, 0, width, height))

        # Draw Grid (Horizontal lines for pitches)
        for i in range(128):
            y = (127 - i) * self.row_height
            color = "#f0f0f0"
            if i % 12 == 0: color = "#d0d0d0" # C notes
            self.canvas.create_line(0, y, width, y, fill=color)

            # Label C notes
            if i % 12 == 0:
                self.canvas.create_text(5, y + self.row_height/2, text=f"C{i//12 - 1}", anchor=tk.W, font=("Arial", 8))

        # Draw Notes
        for i, note in enumerate(notes):
            x1 = note['start'] * self.zoom_x
            w = note['duration'] * self.zoom_x
            y1 = (127 - note['pitch']) * self.row_height

            color = "blue"
            if i == self.selected_note_index:
                color = "red"

            tag = f"note_{i}"
            self.canvas.create_rectangle(x1, y1, x1+w, y1+self.row_height, fill=color, outline="black", tags=(tag, "note"))

    def get_note_at(self, x, y):
        # Simple hit detection
        notes = self.converter.get_notes()
        for i, note in enumerate(notes):
            x1 = note['start'] * self.zoom_x
            w = note['duration'] * self.zoom_x
            y1 = (127 - note['pitch']) * self.row_height

            if x1 <= x <= x1+w and y1 <= y <= y1+self.row_height:
                return i
        return None

    def on_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        index = self.get_note_at(x, y)
        if index is not None:
            self.selected_note_index = index

            # Check if clicked near right edge for resize
            note = self.converter.notes[index]
            note_x1 = note['start'] * self.zoom_x
            note_x2 = note_x1 + note['duration'] * self.zoom_x

            is_resize = (x > note_x2 - 10) # Click within 10px of right edge

            self.drag_data = {'index': index, 'start_x': x, 'start_y': y,
                              'orig_start': note['start'],
                              'orig_pitch': note['pitch'],
                              'orig_duration': note['duration'],
                              'is_resize': is_resize}
        else:
            self.selected_note_index = None

        self.redraw()

    def on_drag(self, event):
        if self.drag_data:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            dx = x - self.drag_data['start_x']
            dy = y - self.drag_data['start_y']
            index = self.drag_data['index']

            if self.drag_data['is_resize']:
                # Resize logic
                dt_ms = dx / self.zoom_x
                new_duration = max(50, self.drag_data['orig_duration'] + dt_ms) # Minimum 50ms
                self.converter.notes[index]['duration'] = int(new_duration)
            else:
                # Move logic
                # Time change
                dt_ms = dx / self.zoom_x
                new_start = max(0, self.drag_data['orig_start'] + dt_ms)

                # Pitch change
                d_pitch = int(-dy / self.row_height)
                new_pitch = min(127, max(0, self.drag_data['orig_pitch'] + d_pitch))

                self.converter.notes[index]['start'] = int(new_start)
                self.converter.notes[index]['pitch'] = int(new_pitch)

            self.redraw()

    def on_release(self, event):
        if self.drag_data:
            # Sort notes again just in case order changed
            self.converter.set_notes(self.converter.notes)
            self.drag_data = None
            self.redraw()

    def on_right_click(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Determine pitch from y
        pitch = int(127 - (y / self.row_height))
        pitch = max(0, min(127, pitch))

        # Determine start time from x
        start = int(x / self.zoom_x)

        # Create new note
        new_note = {'start': start, 'duration': 500, 'pitch': pitch}
        self.converter.notes.append(new_note)
        self.converter.set_notes(self.converter.notes)
        self.redraw()

    def delete_selection(self, event):
        if self.selected_note_index is not None:
            del self.converter.notes[self.selected_note_index]
            self.selected_note_index = None
            self.redraw()

    def toggle_play(self):
        if self.is_playing:
            self.is_playing = False
        else:
            self.is_playing = True
            self.audio_thread = threading.Thread(target=self.play_audio_loop)
            self.audio_thread.start()

    def generate_square_wave(self, freq, duration_ms, sample_rate=44100):
        if freq <= 0:
            return np.zeros(int(sample_rate * duration_ms / 1000), dtype=np.int16)

        t = np.linspace(0, duration_ms / 1000, int(sample_rate * duration_ms / 1000), False)
        # Generate square wave: sign(sin(2*pi*f*t))
        wave = 0.5 * np.sign(np.sin(2 * np.pi * freq * t))
        # Convert to 16-bit PCM
        audio = (wave * 32767).astype(np.int16)
        return audio

    def play_audio_loop(self):
        # We need to flatten the notes for playback similar to export
        # But we can just iterate our notes list and sleep.
        # However, to handle Polyphony correctly (monophonic for preview to match arduino),
        # we should use the export logic's flattening.

        # Let's verify what the user hears is what they get.
        # So we should run the "export" logic in memory.

        # Hacky: Reuse export logic or just re-implement flattening here
        # Let's re-implement a simple version or add a method to converter to get 'segments'

        # For now, let's just iterate time.

        sample_rate = 44100
        pygame.mixer.stop()

        # Get segments
        # To reuse the logic, let's add a method to Converter
        pass
        # Since I can't easily edit Converter class from here without re-writing file,
        # I will just replicate the logic briefly.

        notes = self.converter.notes
        if not notes:
            self.is_playing = False
            return

        events = []
        for n in notes:
            events.append((n['start'], 1, n['pitch']))
            events.append((n['start'] + n['duration'], -1, n['pitch']))
        events.sort(key=lambda x: (x[0], x[1]))

        current_time = 0
        active_pitches = []

        for time_ms, type, pitch in events:
            if not self.is_playing: break

            duration = time_ms - current_time
            if duration > 0:
                freq = 0
                if active_pitches:
                    freq = self.converter.note_to_freq(active_pitches[-1])

                # Play sound
                if freq > 0:
                    sound_data = self.generate_square_wave(freq, duration)
                    sound = pygame.sndarray.make_sound(sound_data)
                    sound.play()
                    # Wait for duration
                    pygame.time.wait(int(duration))
                    sound.stop()
                else:
                    pygame.time.wait(int(duration))

            current_time = time_ms
            if type == 1:
                active_pitches.append(pitch)
            else:
                if pitch in active_pitches:
                    active_pitches.remove(pitch)

        self.is_playing = False

if __name__ == "__main__":
    root = tk.Tk()
    app = MidiEditorApp(root)
    root.mainloop()
