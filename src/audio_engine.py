import os
import wave
import pygame

class AudioEngine:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        self.consonant_dir = "assets/sounds/consonant/"
        self.dissonant_dir = "assets/sounds/dissonant/"
        self.temp_dir = "assets/sounds/temp/"
        
        os.makedirs(self.temp_dir, exist_ok=True)

    def play_chord_by_filename(self, filename):
        """
        Finds a chord file, slices it down to exactly 3 seconds 
        without changing the pitch or speed, and plays it.
        """
        pygame.mixer.stop() # Kill any previous sounds instantly
        
        # Locate the source file
        source_path = os.path.join(self.consonant_dir, filename)
        if not os.path.exists(source_path):
            source_path = os.path.join(self.dissonant_dir, filename)
            
        if not os.path.exists(source_path):
            print(f"⚠️ Warning: Could not find audio asset file: {filename}")
            return "none"

        temp_output_path = os.path.join(self.temp_dir, f"sliced_{filename}")

        try:
            with wave.open(source_path, 'rb') as source_wave:
                params = source_wave.getparams()
                framerate = params.framerate
                sampwidth = params.sampwidth
                nchannels = params.nchannels
                
                # Calculate exactly how many frames are in 3 seconds
                # Number of frames = Frame Rate (e.g., 44100) * Seconds (3)
                frames_to_read = int(framerate * 3.0)
                
                # Read only up to the 3-second mark
                sliced_frames = source_wave.readframes(frames_to_read)
                
            # Write the sliced frames into a temporary file
            with wave.open(temp_output_path, 'wb') as temp_wave:
                temp_wave.setparams((nchannels, sampwidth, framerate, 
                                     len(sliced_frames) // (sampwidth * nchannels), 
                                     params.comptype, params.compname))
                temp_wave.writeframes(sliced_frames)
            
            # Play the perfectly trimmed audio clip
            chord = pygame.mixer.Sound(temp_output_path)
            chord.play()
            return filename
            
        except Exception as e:
            print(f"⚠️ Audio trimming failed: {e}. Playing standard clip.")
            chord = pygame.mixer.Sound(source_path)
            chord.play()
            return filename