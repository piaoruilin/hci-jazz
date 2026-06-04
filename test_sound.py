import os
import time
import platform
import fluidsynth
import sys
print(sys.executable)

# ==========================================
# 🎹 EDIT YOUR CHORD HERE
# ==========================================
# Change these MIDI numbers to test out different combinations!
# (Examples: C7#9 = [60, 64, 70, 75] | Minor 2nd Cluster = [60, 61, 62, 63])
MY_CHORD = [60, 61, 71, 72]

# Velocity handles volume/intensity (0 to 127)
VOLUME = 110 

# How long the chord rings out in seconds
DURATION = 3.0 


# ==========================================
# 🛠️ SYNTHESIZER INITIALIZATION LOGIC
# ==========================================
def run_audio_test():
    # Automatically locate your SoundFont inside your project directory structure
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sf2_path = os.path.join(base_dir, "assets", "sounds", "FluidR3_GM.sf2")
    
    # Fallback to local directory if you are running outside your project environment
    if not os.path.exists(sf2_path):
        sf2_path = "FluidR3_GM.sf2"

    if not os.path.exists(sf2_path):
        print(f"❌ Error: Cannot find your SoundFont file ('FluidR3_GM.sf2').")
        print(f"Please ensure it is dropped into: {os.path.abspath(sf2_path)}")
        return

    # Initialize FluidSynth using the installed pyfluidsynth API
    settings = fluidsynth.new_fluid_settings()
    sys_os = platform.system().lower()
    if sys_os == "darwin":
        fluidsynth.fluid_settings_setstr(settings, b"audio.driver", b"coreaudio")
    elif sys_os == "windows":
        fluidsynth.fluid_settings_setstr(settings, b"audio.driver", b"dsound")
    else:
        fluidsynth.fluid_settings_setstr(settings, b"audio.driver", b"alsa")

    synth = fluidsynth.new_fluid_synth(settings)
    audio_driver = fluidsynth.new_fluid_audio_driver(settings, synth)
    sfid = fluidsynth.fluid_synth_sfload(synth, sf2_path.encode(), True)
    fluidsynth.fluid_synth_program_select(synth, 0, sfid, 0, 0)  # Track 0: Acoustic Grand Piano

    print(f"\n⚡ Playing MIDI Chord Array: {MY_CHORD}")
    
    # Trigger all notes simultaneously 
    for note in MY_CHORD:
        fluidsynth.fluid_synth_noteon(synth, 0, note, VOLUME)
        
    # Let the chord ring out so you can listen for sensory roughness/dissonance
    time.sleep(DURATION)
    
    # Dampen the notes smoothly
    for note in MY_CHORD:
        fluidsynth.fluid_synth_noteoff(synth, 0, note)
        
    # Give the audio buffer a moment to clear out before closing down resources
    time.sleep(0.2)
    fluidsynth.delete_fluid_audio_driver(audio_driver)
    fluidsynth.delete_fluid_synth(synth)
    print("⏹️ Playback Finished.")

if __name__ == "__main__":
    run_audio_test()