import os
import sys
import time
import random
import pygame
import pandas as pd

# Ensure system looks inside /src for dependencies
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.audio_engine import AudioEngine

class AuditoryNBack:
    def __init__(self):
        pygame.init()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Auditory N-Back Cognitive Task")
        self.clock = pygame.time.Clock()
        
        # Pull your existing background alarm engine
        self.alarm_engine = AudioEngine()
        
        # 2-Back Configuration Parameters
        self.N_BACK = 2
        self.LETTER_SEQUENCE = ["B", "C", "B", "D", "B", "D", "F", "D", "F", "G", "B", "G", "C", "C"]
        self.STEP_INTERVAL_MS = 3000  # 3 seconds window per auditory step
        
        # Dynamically map background alarms to specific progression indices
        self.alarm_schedule = {
            4: "consonant",
            8: "dissonant"
        }
        
        # Load the spoken letter files from assets
        self.letter_sounds = {}
        for letter in set(self.LETTER_SEQUENCE):
            path = f"assets/sounds/letters/{letter}.wav"
            if os.path.exists(path):
                self.letter_sounds[letter] = pygame.mixer.Sound(path)
            else:
                raise FileNotFoundError(f"Missing spoken letter asset: {path}. Run the 'say' commands first.")

        # Experiment Telemetry Storage
        self.telemetry = []
        self.font = pygame.font.SysFont("arial", 28)
        self.font_center = pygame.font.SysFont("arial", 96)

    def run(self):
        running = True
        started = False
        
        current_idx = 0
        step_start_time = 0
        pressed_match_this_step = False
        reaction_time = None
        latency_from_alarm = None
        alarm_fired_this_step = False
        alarm_file_played = "none"
        alarm_time = 0
        screen_color = (240, 242, 245)

        print("Click the window and press SPACE to start the Auditory Task.")

        while running:
            self.screen.fill(screen_color)
            current_tick = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        
                    elif event.key == pygame.K_SPACE and not started:
                        started = True
                        step_start_time = current_tick
                        # Trigger the first spoken letter immediately on launch
                        self.letter_sounds[self.LETTER_SEQUENCE[current_idx]].play()
                        
                    elif event.key == pygame.K_m and started and not pressed_match_this_step:
                        # Capture metric parameters instantly
                        pressed_match_this_step = True
                        reaction_time = current_tick - step_start_time
                        screen_color = (210, 230, 255) # Flash subtle blue feedback
                        
                        if alarm_time > 0:
                            latency_from_alarm = current_tick - alarm_time

            if not started:
                # Welcome Screen UI text layout
                msg1 = self.font.render("Auditory 2-Back Memory Task", True, (50, 50, 50))
                msg2 = self.font.render("Listen closely. Press 'M' if the spoken letter matches", True, (80, 80, 80))
                msg3 = self.font.render("the one you heard exactly 2 steps ago.", True, (80, 80, 80))
                msg4 = self.font.render("Press SPACE to activate", True, (0, 123, 255))
                self.screen.blit(msg1, (400 - msg1.get_width()//2, 200))
                self.screen.blit(msg2, (400 - msg2.get_width()//2, 260))
                self.screen.blit(msg3, (400 - msg3.get_width()//2, 300))
                self.screen.blit(msg4, (400 - msg4.get_width()//2, 400))
            else:
                # Keep target screen clean to force absolute focus on hearing
                fixation_cross = self.font_center.render("+", True, (180, 180, 180))
                self.screen.blit(fixation_cross, (400 - fixation_cross.get_width()//2, 250))
                
                # Asynchronous Interference Trigger Window (Plays background chord 800ms after speech starts)
                if current_idx in self.alarm_schedule and not alarm_fired_this_step:
                    if current_tick - step_start_time >= 800:
                        condition = self.alarm_schedule[current_idx]
                        alarm_file_played = self.alarm_engine.play_chord(condition)
                        alarm_time = pygame.time.get_ticks()
                        alarm_fired_this_step = True
                        screen_color = (245, 230, 230) # Visual hint that noise condition is active

                # Timeline boundary check for step progression
                if current_tick - step_start_time >= self.STEP_INTERVAL_MS:
                    # Append completed step data packet to log cache
                    self.telemetry.append({
                        "step_index": current_idx,
                        "heard_letter": self.LETTER_SEQUENCE[current_idx],
                        "pressed_match": pressed_match_this_step,
                        "reaction_time_ms": reaction_time,
                        "alarm_played": self.alarm_schedule.get(current_idx, "none"),
                        "alarm_file": alarm_file_played,
                        "latency_from_alarm_ms": latency_from_alarm
                    })
                    
                    # Advance state engine variables
                    current_idx += 1
                    pressed_match_this_step = False
                    reaction_time = None
                    latency_from_alarm = None
                    alarm_fired_this_step = False
                    alarm_file_played = "none"
                    alarm_time = 0
                    screen_color = (240, 242, 245)
                    step_start_time = current_tick
                    
                    if current_idx >= len(self.LETTER_SEQUENCE):
                        running = False
                    else:
                        # Play upcoming audio letter node entry
                        self.letter_sounds[self.LETTER_SEQUENCE[current_idx]].play()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        self.process_results()

    def process_results(self):
        print("\n[SUCCESS] Auditory session completed. Compiling matrix metrics...")
        df = pd.DataFrame(self.telemetry)
        
        # Establish structural ground truths for analysis verification
        df['is_target'] = False
        for i in range(len(self.LETTER_SEQUENCE)):
            if i >= self.N_BACK:
                df.loc[i, 'is_target'] = self.LETTER_SEQUENCE[i] == self.LETTER_SEQUENCE[i - self.N_BACK]
                
        df['correct'] = df['pressed_match'] == df['is_target']
        
        print("\n=== AUDITORY EXPERIMENT RESULTS ===")
        print(df[['step_index', 'heard_letter', 'is_target', 'pressed_match', 'correct', 'alarm_played', 'reaction_time_ms', 'latency_from_alarm_ms']].to_string())
        
        # Save output straight to raw folder logs
        os.makedirs("data/raw", exist_ok=True)
        df.to_csv("data/raw/auditory_nback_results.csv", index=False)
        print("\nTelemetry file logged successfully: 'data/raw/auditory_nback_results.csv'")

if __name__ == "__main__":
    experiment = AuditoryNBack()
    experiment.run()