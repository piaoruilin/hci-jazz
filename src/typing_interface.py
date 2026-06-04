import os
import time
import random
import pygame
from audio_engine import AudioEngine

class TypingInterface:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("HCI Jazz Cognitive Load Simulator")
        self.clock = pygame.time.Clock()
        
        # Initialize your custom audio engine
        self.audio = AudioEngine()
        
        # Load Text Prompts
        self.prompts = self.load_prompts()
        self.current_prompt_idx = 0
        self.user_input = ""
        
        # Telemetry Logging Cache
        self.keystroke_log = []
        
        # Fonts & Styling
        self.font_huge = pygame.font.SysFont("mono", 72, bold=True)
        self.font_sub = pygame.font.SysFont("arial", 28)
        
        # State Control
        self.experiment_running = True
        self.current_target_text = self.prompts[self.current_prompt_idx]
        self.trial_start_time = pygame.time.get_ticks()
        
        # Alarm Trigger Variables
        self.alarm_fired_this_trial = False
        self.alarm_time = 0
        self.active_alarm_file = "none"
        self.alarm_condition = "none"

    def load_prompts(self):
        """Loads non-word strings from your assets folder."""
        path = os.path.join("assets", "text_prompts", "prompt_1.txt")
        if os.path.exists(path):
            with open(path, "r") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return ["XKFZ", "WQMB", "RTVN", "PLHY"] # Fallback hardcoded strings

    def run(self):
        while self.experiment_running:
            current_tick = pygame.time.get_ticks()
            self.screen.fill((240, 242, 245)) # Clean grey/blue background
            
            # --- 1. RANDOM ALARM INJECTION LOGIC ---
            # If a trial has been active for more than 1 second, randomly fire an alarm condition
            if not self.alarm_fired_this_trial and (current_tick - self.trial_start_time > 1000):
                if random.random() < 0.01: # Roll dice per frame execution loop
                    self.alarm_condition = random.choice(['consonant', 'dissonant'])
                    self.active_alarm_file = self.audio.play_chord(self.alarm_condition)
                    self.alarm_time = pygame.time.get_ticks()
                    self.alarm_fired_this_trial = True

            # --- 2. OS INPUT EVENT CAPTURE ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.experiment_running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.experiment_running = False
                        
                    elif event.key == pygame.K_BACKSPACE:
                        self.user_input = self.user_input[:-1]
                        
                    elif event.unicode:
                        typed_char = event.unicode.upper()
                        target_char = self.current_target_text[len(self.user_input)] if len(self.user_input) < len(self.current_target_text) else ""
                        
                        # High-resolution timestamp registration
                        press_timestamp = pygame.time.get_ticks()
                        
                        # Calculate millisecond distance relative to alarm firing
                        latency_from_alarm = (press_timestamp - self.alarm_time) if self.alarm_fired_this_trial else None
                        
                        # Log Keystroke Metrics Payload
                        self.keystroke_log.append({
                            "timestamp": press_timestamp,
                            "expected": target_char,
                            "typed": typed_char,
                            "is_correct": typed_char == target_char,
                            "active_condition": self.alarm_condition,
                            "alarm_file": self.active_alarm_file,
                            "ms_since_alarm": latency_from_alarm
                        })
                        
                        # Update visual buffer string alignment
                        if len(self.user_input) < len(self.current_target_text):
                            self.user_input += typed_char

            # --- 3. TRIAL PROGRESSION MONITOR ---
            # Advance trial when the target word is completely typed out
            if self.user_input == self.current_target_text:
                self.current_prompt_idx += 1
                if self.current_prompt_idx >= len(self.prompts):
                    self.experiment_running = False # Sequence fully complete
                else:
                    # Clear state parameters for the upcoming next trial run
                    self.current_target_text = self.prompts[self.current_prompt_idx]
                    self.user_input = ""
                    self.alarm_fired_this_trial = False
                    self.alarm_condition = "none"
                    self.active_alarm_file = "none"
                    self.alarm_time = 0
                    self.trial_start_time = pygame.time.get_ticks()

            # --- 4. GRAPHICAL UI RENDERING ---
            # Render Target Word Prompt
            target_surface = self.font_huge.render(self.current_target_text, True, (50, 50, 50))
            self.screen.blit(target_surface, (400 - target_surface.get_width() // 2, 200))
            
            # Render Active Input Buffer directly below target
            input_surface = self.font_huge.render(self.user_input, True, (0, 123, 255))
            self.screen.blit(input_surface, (400 - input_surface.get_width() // 2, 300))
            
            # Context Guidelines
            guide_surface = self.font_sub.render("Type the letters sequence displayed above precisely.", True, (120, 120, 120))
            self.screen.blit(guide_surface, (400 - guide_surface.get_width() // 2, 450))
            
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        return self.keystroke_log

if __name__ == "__main__":
    interface = TypingInterface()
    log_data = interface.run()
    
    # Simple terminal output validation printout
    print("\nTelemetry Captured:")
    import pandas as pd
    df = pd.DataFrame(log_data)
    print(df.head(20))