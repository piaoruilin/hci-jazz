import pygame
import os
import random

class AudioEngine:
    def __init__(self):
        # Initialize the mixer with high-quality settings
        # 44100Hz is standard for your rendered m4a exports
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        # Paths to your exported asset folders
        self.consonant_dir = "assets/sounds/consonant/"
        self.dissonant_dir = "assets/sounds/dissonant/"
        
        # Look for .m4a files instead of .wav files
        # Change lines 17 & 18 in src/audio_engine.py to this:
        self.consonant_files = [f for f in os.listdir(self.consonant_dir) if f.endswith('.wav')]
        self.dissonant_files = [f for f in os.listdir(self.dissonant_dir) if f.endswith('.wav')]
        
        # Absolute safety check to make sure the files are placed correctly
        if not self.consonant_files or not self.dissonant_files:
            print("⚠️ Warning: No .m4a files found in your asset directories!")
            print(f"Current Consonant Files found: {self.consonant_files}")
            print(f"Current Dissonant Files found: {self.dissonant_files}")

    def play_chord(self, category):
        """
        Plays a random chord from the specified category.
        :param category: 'consonant' or 'dissonant'
        :return: filename of the chord played (for telemetry data logging)
        """
        # Ensure any currently playing audio track is forcefully cleared 
        # so overlapping chords don't contaminate the trial data
        pygame.mixer.stop()

        if category == 'consonant':
            if not self.consonant_files:
                return None
            file_to_play = random.choice(self.consonant_files)
            path = os.path.join(self.consonant_dir, file_to_play)
        else:
            if not self.dissonant_files:
                return None
            file_to_play = random.choice(self.dissonant_files)
            path = os.path.join(self.dissonant_dir, file_to_play)
            
        # Load the physical file and play it asynchronously
        chord = pygame.mixer.Sound(path)
        chord.play()
        
        return file_to_play

# Quick Test Block
if __name__ == "__main__":
    # This part only runs if you run THIS file directly to audit your setup
    engine = AudioEngine()
    
    print("\n--- Audio Directory Audit ---")
    print(f"Available Consonant Files: {engine.consonant_files}")
    print(f"Available Dissonant Files: {engine.dissonant_files}\n")
    
    print("🔊 Testing Consonant Audio Track Trigger...")
    played_con = engine.play_chord('consonant')
    print(f"Playing: {played_con}")
    pygame.time.wait(3000) # Let it ring out for 3 seconds
    
    print("🔊 Testing Dissonant Audio Track Trigger...")
    played_dis = engine.play_chord('dissonant')
    print(f"Playing: {played_dis}")
    pygame.time.wait(3000) 
    
    print("⏹️ Audio Engine Check Concluded.")