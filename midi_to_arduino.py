"""
MakerUnoSong - CLI Converter, Direct Flasher & Health Diagnostics.
Build by AgentHitmanFaris (NC-Engineering).

CLI tool for converting MIDI files, intelligent beat structuring, audio preview synthesis,
direct flashing to Maker UNO without Arduino IDE, batch processing, and board health diagnostics.
"""

import sys
import os
import glob
import argparse
import time

# Ensure Windows command line handles UTF-8 safely without charmap crashes
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure module imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from converter import MidiConverter, note_to_freq
from uploader import ArduinoUploader
from board_health import BoardHealthEngine

def run_health_check_cli(port: str):
    print(f"\n🩺 Starting Maker UNO Health Diagnostics on {port}...")
    engine = BoardHealthEngine()
    
    received_count = 0
    def _on_telemetry(data):
        nonlocal received_count
        if "score" in data:
            received_count += 1
            print("\n" + "="*55)
            print(f"  Maker UNO Board Health: {data['score']}% [{data['grade']}]")
            print("="*55)
            print(f"  ⚡ Supply Voltage (Vcc) : {data['vcc_v']:.3f} V  ({data['status_vcc']})")
            print(f"  🌡️  MCU Core Temp        : {data['temp_c']:.1f} °C  ({data['status_temp']})")
            print(f"  💾 Free Dynamic SRAM    : {data['free_ram']} / 2048 Bytes ({data['ram_percent']}%)")
            print(f"  💾 EEPROM Storage       : {data['status_eeprom']}")
            print(f"  ⏱️  Loop Timing Jitter   : {data['jitter_ms']:.2f} ms ({data['status_clock']})")
            print(f"  🔘 Button State (Pin 2) : {'PRESSED' if data['btn_pressed'] else 'RELEASED'}")
            print(f"  ⏱️  Board Uptime         : {data['uptime_s']} s")
            print("-"*55)
            print(f"  Summary: {data['summary']}")
            if data['issues']:
                print(f"  ⚠️  Issues Detected:")
                for issue in data['issues']:
                    print(f"     - {issue}")
            print("="*55)
        elif "error" in data:
            print(f"  ❌ Error: {data['error']}")
        elif "raw" in data:
            print(f"  >> {data['raw']}")

    engine.start_monitoring(port, callback=_on_telemetry)
    print("Listening for telemetry packets (Press Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(1)
            if received_count >= 3:
                pass
    except KeyboardInterrupt:
        print("\nStopping health monitoring...")
    finally:
        engine.stop_monitoring()

def process_single_midi(midi_file: str, out_file: str = None, drum_mode: str = "Smart Adaptive AI",
                        no_drums: bool = False, led_mode: str = "Frequency Mapped",
                        preview_wav: str = None, analyze: bool = False):
    converter = MidiConverter()
    print(f"\n📂 Reading MIDI file: {midi_file}")
    converter.load_midi(midi_file)

    if no_drums:
        converter.enable_drums = False
    elif drum_mode == "Smart Adaptive AI" or "Smart" in drum_mode:
        converter.enable_drums = True
        converter.drum_mode = "🧠 Smart Adaptive AI"
    elif drum_mode != "Use MIDI Track":
        converter.enable_drums = True
        converter.drum_mode = f"Auto-Gen: {drum_mode}"
    else:
        converter.enable_drums = True
        converter.drum_mode = "Use MIDI Track"

    converter.led_mode = led_mode

    # Musical Analysis Output
    analysis = converter.analyze_song_structure()
    flash_info = converter.get_flash_usage_estimate()

    if analyze or True:
        print("="*58)
        print(f"  🎵 SONG ANALYSIS: '{converter.song_name}' by '{converter.artist}'")
        print("="*58)
        print(f"  Tempo / BPM      : {converter.bpm} BPM")
        print(f"  Time Signature   : {converter.time_signature}")
        print(f"  Detected Key     : {analysis.get('key_detected', 'C Major')}")
        print(f"  Total Measures   : {analysis.get('total_measures', 0)} bars")
        print(f"  Avg Note Density : {analysis.get('avg_density', 0)} notes/sec")
        print(f"  Flash Memory Est : {flash_info['segments']} segments (~{flash_info['progmem_bytes']} B / {flash_info['percent']}% of ATmega328P)")
        if analysis.get('sections'):
            print("  Structure Map    :")
            for s in analysis['sections']:
                print(f"    - [{s['name']:<10}] Bars {s['start_bar']:>2}-{s['end_bar']:<2} | Energy: {int(s['avg_energy']*100)}%")
        print("="*58)

    # Determine output path
    if out_file:
        out_path = out_file
    else:
        proj_name = converter.get_project_name()
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Songs", proj_name, f"{proj_name}.ino")

    print(f"Generating optimized Arduino code...")
    converter.export_arduino(out_path)
    print(f"✅ Generated: {out_path} ({len(converter.notes)} notes)")

    # Synthesize WAV Preview if requested
    if preview_wav:
        print(f"Rendering audio preview to '{preview_wav}'...")
        pe = converter.get_preview_engine()
        if pe:
            pe.export_wav(preview_wav)
            print(f"✅ Saved Preview Audio: {preview_wav}")

    return converter, out_path

def main():
    parser = argparse.ArgumentParser(description='MakerUnoSong: Convert MIDI to Arduino & Flash Maker UNO without Arduino IDE')
    parser.add_argument('input_file', nargs='?', help='Path to input MIDI file (.mid or .midi)')
    parser.add_argument('output_file', nargs='?', help='Path to output .ino file')
    parser.add_argument('--auto', '-a', action='store_true', help='Fully automated pipeline: auto-detect port, structure beat, compile, and flash')
    parser.add_argument('--upload', '-u', metavar='PORT', help='Directly compile and flash to Maker UNO COM port (e.g. COM3)')
    parser.add_argument('--batch', '-b', metavar='DIR', help='Batch convert all MIDI files in a directory')
    parser.add_argument('--preview-wav', '-w', metavar='OUT_WAV', help='Synthesize and export an audio preview (.wav)')
    parser.add_argument('--analyze', action='store_true', help='Print deep musical structure and energy analysis')
    parser.add_argument('--health-check', '-hc', metavar='PORT', help='Run real-time board health and life diagnostics on COM port')
    parser.add_argument('--list-ports', '-l', action='store_true', help='List all available serial COM ports')
    parser.add_argument('--no-drums', action='store_true', help='Disable drum synthesis')
    parser.add_argument('--led-mode', default='Frequency Mapped',
                        choices=['Frequency Mapped', 'VU Meter', 'Knight Rider Scanner', 'Drum Reactive'],
                        help='Visualizer pattern for Maker UNO 12x LEDs')
    parser.add_argument('--drum-genre', default='Smart Adaptive AI', 
                        choices=['Smart Adaptive AI', 'Use MIDI Track', 'Pop', 'Rock', 'Metal', 'Funk', 'Disco', 'Hip-Hop', 'Reggae'],
                        help='Drum synthesis mode: intelligent structure thinking or classic preset')
    args = parser.parse_args()

    # 1. List Ports
    if args.list_ports:
        ports = ArduinoUploader.list_ports()
        print("\nAvailable Serial Ports:")
        if not ports:
            print("  No serial devices detected.")
        for p in ports:
            print(f"  - {p['display']}")
        return

    # 2. Health Check
    if args.health_check:
        run_health_check_cli(args.health_check)
        return

    # 3. Batch Conversion Mode
    if args.batch:
        if not os.path.isdir(args.batch):
            print(f"❌ Error: Directory '{args.batch}' not found.")
            sys.exit(1)
        midi_files = glob.glob(os.path.join(args.batch, "*.mid")) + glob.glob(os.path.join(args.batch, "*.midi"))
        if not midi_files:
            print(f"No MIDI files found in '{args.batch}'.")
            return
        print(f"\n🚀 Batch processing {len(midi_files)} MIDI files from '{args.batch}'...")
        for mf in midi_files:
            try:
                process_single_midi(mf, drum_mode=args.drum_genre, no_drums=args.no_drums,
                                    led_mode=args.led_mode, analyze=args.analyze)
            except Exception as e:
                print(f"❌ Failed to process {mf}: {e}")
        print(f"\n🎉 Batch conversion completed! All sketches saved in 'Songs/' folder.")
        return

    # 4. Single MIDI Conversion
    if not args.input_file:
        parser.print_help()
        print("\nTip: Run 'python main.py' to launch the Desktop GUI Studio.")
        return

    converter, out_path = process_single_midi(
        args.input_file, out_file=args.output_file, drum_mode=args.drum_genre,
        no_drums=args.no_drums, led_mode=args.led_mode, preview_wav=args.preview_wav,
        analyze=args.analyze
    )

    # 5. Automated Pipeline or Explicit Upload
    target_port = args.upload
    if args.auto and not target_port:
        # Automatically detect connected Maker UNO
        ports = ArduinoUploader.list_ports()
        maker_ports = [p for p in ports if p.get('is_maker_uno')]
        if maker_ports:
            target_port = maker_ports[0]['port']
            print(f"\n⚡ Auto-detected Maker UNO on port: {target_port}")
        elif ports:
            target_port = ports[0]['port']
            print(f"\n⚡ Using detected serial port: {target_port}")
        else:
            print("\n⚠️ Auto mode: No serial ports detected. Exported .ino sketch ready for flashing.")

    if target_port:
        print(f"\n⚡ Uploading directly to Maker UNO on {target_port}...")
        uploader = ArduinoUploader()
        def _cb(msg):
            print(f"  [Uploader] {msg}")

        ok, log = uploader.compile_and_upload(out_path, target_port, progress_callback=_cb)
        if ok:
            print(f"\n🎉 SUCCESS: Flashed '{converter.song_name}' to Maker UNO on {target_port}!")
        else:
            print(f"\n❌ UPLOAD FAILED:\n{log}")
            sys.exit(1)

if __name__ == "__main__":
    main()