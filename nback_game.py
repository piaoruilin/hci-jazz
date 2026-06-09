import os
import sys
import time
import random
import pygame
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

from audio_engine import AudioEngine

class AuditoryNBack:
    def __init__(self, participant_id):
        pygame.init()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Auditory N-Back Cognitive Task")
        self.clock = pygame.time.Clock()
        
        self.participant_id = participant_id
        self.alarm_engine = AudioEngine()
        
        self.N_BACK = 2
        
        self.LETTER_SEQUENCE = [
            "B", "G", "B", "G", "D", "D", "C", "B", "F", "C", 
            "G", "F", "G", "B", "B", "B", "B", "C", "F", "D", "C", "D"
        ]
        
        # FIXED: Speed up pacing to 2.5 seconds per letter turn
        self.STEP_INTERVAL_MS = 2500  
        
        # FIXED: Dynamic schedule generator utilizes ALL available sound assets
        self.alarm_schedule = self.generate_unlimited_random_schedule()
        
        self.letter_sounds = {}
        for letter in set(self.LETTER_SEQUENCE):
            path = os.path.join("assets", "sounds", "letters", f"{letter}.wav")
            if os.path.exists(path):
                self.letter_sounds[letter] = pygame.mixer.Sound(path)
            else:
                print(f"❌ Missing letter file: {path}. Please generate it first.")
                sys.exit(1)

        self.telemetry = []
        self.font = pygame.font.SysFont("arial", 28)
        self.font_center = pygame.font.SysFont("arial", 96)

    def generate_unlimited_random_schedule(self):
        """
        Gathers every single file inside your consonant/dissonant folders 
        and schedules them randomly across available sequence steps.
        """
        consonant_dir = "assets/sounds/consonant/"
        dissonant_dir = "assets/sounds/dissonant/"
        
        all_consonants = [f for f in os.listdir(consonant_dir) if f.endswith('.wav')] if os.path.exists(consonant_dir) else []
        all_dissonants = [f for f in os.listdir(dissonant_dir) if f.endswith('.wav')] if os.path.exists(dissonant_dir) else []
        
        # Combine everything you have stored in your directory layers
        total_available_pool = all_consonants + all_dissonants
        random.shuffle(total_available_pool)
        
        # Isolate indices where it's safe to fire background audio (steps 2 through 20)
        possible_steps = list(range(2, len(self.LETTER_SEQUENCE) - 1))
        
        # We can dynamically scale up the density. Let's aim to fill up to 8 of those steps with audio.
        max_sounds_to_trigger = min(len(total_available_pool), len(possible_steps), 9)
        selected_steps = sorted(random.sample(possible_steps, max_sounds_to_trigger))
        
        schedule = {step: chord for step, chord in zip(selected_steps, total_available_pool)}
        print(f"🎲 Full-Pool Dynamic Schedule Generated ({max_sounds_to_trigger} sounds active): {schedule}")
        return schedule

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

        print("\n🖥️ Pygame Window Operational. Click inside and tap SPACEBAR to launch.")

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
                        self.letter_sounds[self.LETTER_SEQUENCE[current_idx]].play()
                    elif event.key == pygame.K_m and started and not pressed_match_this_step:
                        pressed_match_this_step = True
                        reaction_time = current_tick - step_start_time
                        screen_color = (210, 230, 255)
                        if alarm_time > 0:
                            latency_from_alarm = current_tick - alarm_time

            if not started:
                msg1 = self.font.render("Auditory 2-Back Memory Task", True, (50, 50, 50))
                msg2 = self.font.render("Listen closely. Press 'M' if the spoken letter matches", True, (80, 80, 80))
                msg3 = self.font.render("the one you heard exactly 2 steps ago.", True, (80, 80, 80))
                msg4 = self.font.render("Press SPACEBAR to start", True, (0, 123, 255))
                self.screen.blit(msg1, (400 - msg1.get_width()//2, 200))
                self.screen.blit(msg2, (400 - msg2.get_width()//2, 260))
                self.screen.blit(msg3, (400 - msg3.get_width()//2, 300))
                self.screen.blit(msg4, (400 - msg4.get_width()//2, 400))
            else:
                fixation_cross = self.font_center.render("+", True, (180, 180, 180))
                self.screen.blit(fixation_cross, (400 - fixation_cross.get_width()//2, 250))
                
                # Injects the background audio chord 400ms into the tighter interval window
                if current_idx in self.alarm_schedule and not alarm_fired_this_step:
                    if current_tick - step_start_time >= 400:
                        target_file = self.alarm_schedule[current_idx]
                        alarm_file_played = self.alarm_engine.play_chord_by_filename(target_file)
                        alarm_time = pygame.time.get_ticks()
                        alarm_fired_this_step = True
                        screen_color = (245, 230, 230)

                # Progression Threshold Monitor
                if current_tick - step_start_time >= self.STEP_INTERVAL_MS:
                    self.telemetry.append({
                        "Participant_ID": self.participant_id,
                        "step_index": current_idx,
                        "heard_letter": self.LETTER_SEQUENCE[current_idx],
                        "pressed_match": pressed_match_this_step,
                        "reaction_time_ms": reaction_time,
                        "alarm_file": alarm_file_played,
                        "latency_from_alarm_ms": latency_from_alarm
                    })
                    
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
                        self.letter_sounds[self.LETTER_SEQUENCE[current_idx]].play()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        self.process_results()

    def process_results(self):
        print("\n[SUCCESS] Compiling results dataframe matrix...")
        df = pd.DataFrame(self.telemetry)
        
        df['is_target'] = False
        for i in range(len(self.LETTER_SEQUENCE)):
            if i >= self.N_BACK:
                df.loc[i, 'is_target'] = self.LETTER_SEQUENCE[i] == self.LETTER_SEQUENCE[i - self.N_BACK]
                
        df['correct'] = df['pressed_match'] == df['is_target']
        
        print("\n=== HIGH-PACE EXPERIMENT RUN LOGS ===")
        print(df[['step_index', 'heard_letter', 'is_target', 'pressed_match', 'correct', 'alarm_file', 'reaction_time_ms']].to_string())
        
        os.makedirs("data/raw_behavioral", exist_ok=True)
        export_path = f"data/raw_behavioral/{self.participant_id}.csv"
        df.to_csv(export_path, index=False)
        print(f"\n📁 File saved to disk: {export_path}")

if __name__ == "__main__":
    print("\n==========================================")
    print("      HCI AUDIO EXPERIMENT LAUNCHER       ")
    print("==========================================")
    print("1. Run PRACTICE Mode (No Chord Interruption)")
    print("2. Run ACTUAL Experiment (Data Recorded)")
    choice = input("Select mode (1 or 2): ").strip()
    
    if choice == "1":
        # Launch practice with a placeholder ID
        experiment = AuditoryNBack(participant_id="PRACTICE_SESSION")
        
        # MUTE ALL ALARMS: Empty out the schedule array so NO chords play
        experiment.alarm_schedule = {} 
        print("\n🧪 PRACTICE MODE INITIATED: No background chords will play.")
        experiment.run()
        
        # Optional: Delete the file right after so it doesn't clutter your data folder
        practice_file = "data/raw_behavioral/PRACTICE_SESSION.csv"
        if os.path.exists(practice_file):
            os.remove(practice_file)
            
    else:
        input_id = input("\nEnter Assigned Participant ID (e.g., U01): ").strip()
        if not input_id:
            input_id = f"sandbox_run_{int(time.time())}"
            
        experiment = AuditoryNBack(participant_id=input_id)
        experiment.run()