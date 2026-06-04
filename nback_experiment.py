import time
import random
import pandas as pd
import pygame


N_BACK = 2
LETTER_SEQUENCE = ["B", "C", "B", "D", "B", "D", "F", "D", "F", "G", "B", "G", "C", "C"]
TRIAL_DURATION_MS = 2500  # How long each letter stays on screen

ALARM_SCHEDULE = {
    4: "consonant.mp3",
    8: "dissonant.mp3"
}

pygame.init()
pygame.mixer.init()


# Setup a clean visual display window
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cognitive Load N-Back Task")
clock = pygame.time.Clock()

# Fonts and Colors
FONT_LETTER = pygame.font.SysFont("arial", 120, bold=True)
FONT_TEXT = pygame.font.SysFont("arial", 24)
COLOR_BG = (245, 245, 245)
COLOR_TEXT = (50, 50, 50)
COLOR_FEEDBACK = (0, 123, 255)

def draw_text(text, font, color, y_offset=0):
    """Utility to center text on screen."""
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
    screen.blit(surface, rect)

# Preload Audio Sounds safely
sounds = {}
for idx, filename in ALARM_SCHEDULE.items():
    try:
        sounds[filename] = pygame.mixer.Sound(filename)
    except pygame.error:
        print(f"Warning: Could not load {filename}. Playing silent fallback.")
        sounds[filename] = None

# ==========================================
# 3. EXPERIMENT LOOP
# ==========================================
results = []
running = True
started = False

print("Click on the Pygame window and press SPACE to start.")

trial_idx = 0
letter_start_time = 0
alarm_trigger_time = 0
pressed_this_trial = False
reaction_time = None
latency_from_alarm = None
current_color = COLOR_TEXT

while running:
    screen.fill(COLOR_BG)
    current_time = pygame.time.get_ticks() # Millisecond-level clock ticks
    
    # Handle OS inputs and keystrokes
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            elif event.key == pygame.K_SPACE and not started:
                started = True
                letter_start_time = pygame.time.get_ticks()
                
            elif event.key == pygame.K_m and started and not pressed_this_trial:
                # Capture accurate reaction timestamp metrics
                pressed_this_trial = True
                reaction_time = current_time - letter_start_time
                current_color = COLOR_FEEDBACK # Flash blue on success registration
                
                if alarm_trigger_time > 0:
                    latency_from_alarm = current_time - alarm_trigger_time

    # Display Welcome Screen
    if not started:
        draw_text(f"{N_BACK}-Back Task", FONT_TEXT, COLOR_TEXT, -80)
        draw_text("Press 'M' if the letter matches the one seen 2 steps ago.", FONT_TEXT, COLOR_TEXT, -20)
        draw_text("Press SPACE to Begin", FONT_TEXT, COLOR_FEEDBACK, 60)
    
    # Process Ongoing Trial Timeline
    else:
        # Check if current trial time window has expired
        if current_time - letter_start_time >= TRIAL_DURATION_MS:
            # Log metrics for completed trial
            results.append({
                "trial_index": trial_idx,
                "letter": LETTER_SEQUENCE[trial_idx],
                "alarm_played": ALARM_SCHEDULE.get(trial_idx, "none"),
                "pressed_match": pressed_this_trial,
                "reaction_time_ms": reaction_time,
                "latency_from_alarm_ms": latency_from_alarm
            })
            
            # Step forward to next trial configuration
            trial_idx += 1
            pressed_this_trial = False
            reaction_time = None
            latency_from_alarm = None
            alarm_trigger_time = 0
            current_color = COLOR_TEXT
            letter_start_time = current_time # Reset timestamp for new letter
            
            # End experiment loop if sequence finishes
            if trial_idx >= len(LETTER_SEQUENCE):
                running = False
                break
                
            # Intercept and trigger auditory alarm asynchronously if scheduled
            if trial_idx in ALARM_SCHEDULE:
                alarm_file = ALARM_SCHEDULE[trial_idx]
                if sounds[alarm_file]:
                    sounds[alarm_file].play()
                alarm_trigger_time = pygame.time.get_ticks()

        # Render the letters dynamically on active trials
        if trial_idx < len(LETTER_SEQUENCE):
            draw_text(LETTER_SEQUENCE[trial_idx], FONT_LETTER, current_color)

    pygame.display.flip()
    clock.tick(60) # Frame rate limiting to preserve CPU overhead

pygame.quit()

# ==========================================
# 4. POST-PROCESSING DATA EXPORT
# ==========================================
print("\n[SUCCESS] Experiment concluded. Processing telemetry...")
df = pd.DataFrame(results)

# Append ground truth N-back expectations
df['is_target'] = False
for i in range(len(LETTER_SEQUENCE)):
    if i >= N_BACK:
        df.loc[i, 'is_target'] = LETTER_SEQUENCE[i] == LETTER_SEQUENCE[i - N_BACK]

df['correct'] = df['pressed_match'] == df['is_target']

# Output results nicely to the terminal terminal
print("\n=== EXPERIMENT RESULTS SUMMARY ===")
print(df[['trial_index', 'letter', 'is_target', 'pressed_match', 'correct', 'alarm_played', 'reaction_time_ms', 'latency_from_alarm_ms']])

# Automatically dump telemetry run directly to local storage csv
df.to_csv("jazz_thesis_pilot_data.csv", index=False)
print("\nTelemetry saved successfully to 'jazz_thesis_pilot_data.csv'")