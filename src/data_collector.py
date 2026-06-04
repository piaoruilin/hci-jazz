import time
import pandas as pd
import os

class DataCollector:
    def __init__(self, participant_id, is_musician):
        self.participant_id = participant_id
        self.is_musician = is_musician
        self.results = []
        self.current_alarm_time = None
        self.current_chord = None

    def mark_alarm_start(self, chord_name):
        """Records the exact nanosecond the alarm was triggered."""
        self.current_alarm_time = time.time_ns()
        self.current_chord = chord_name

    def record_response(self):
        """Calculates latency when the user hits a key after an alarm."""
        if self.current_alarm_time:
            response_time = time.time_ns()
            # Convert nanoseconds to milliseconds for easier analysis
            latency_ms = (response_time - self.current_alarm_time) / 1_000_000
            
            data_point = {
                "participant_id": self.participant_id,
                "is_musician": self.is_musician,
                "chord": self.current_chord,
                "latency_ms": latency_ms
            }
            self.results.append(data_point)
            
            # Reset the trigger so we don't record the same alarm twice
            self.current_alarm_time = None
            print(f"Captured Latency: {latency_ms:.2f} ms")

    def save_to_csv(self):
        if not self.results:
            print("No data captured to save.")
            return

        df = pd.DataFrame(self.results)
        filename = f"data/raw/subj_{self.participant_id}.csv"
        df.to_csv(filename, index=False)
        
        # --- NEW: Show Results Summary ---
        print("\n" + "="*30)
        print(f"RESULTS SUMMARY: SUBJECT {self.participant_id}")
        print(f"Total Alarms: {len(df)}")
        print(f"Average Latency: {df['latency_ms'].mean():.2f} ms")
        print(f"Max Latency: {df['latency_ms'].max():.2f} ms")
        print("="*30 + "\n")