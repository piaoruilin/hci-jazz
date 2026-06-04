import os
import glob
import pandas as pd

def process_all_participants():
    compiled_behavioral = []
    
    # 1. Loop through every participant file in your directory
    file_paths = glob.glob("data/raw_behavioral/*.csv")
    
    for path in file_paths:
        # Extract filename to use as the join key (e.g., "p01_jazz")
        p_id = os.path.basename(path).replace(".csv", "")
        df = pd.read_csv(path)
        
        # --- FEATURE ENGINEERING ---
        # Calculate baseline accuracy vs accuracy when an alarm is playing
        baseline_accuracy = df[df['alarm_played'] == 'none']['correct'].mean()
        dissonant_accuracy = df[df['alarm_played'] == 'dissonant']['correct'].mean()
        
        # Calculate reaction time metrics (drop NaN values where no key was pressed)
        baseline_rt = df[df['alarm_played'] == 'none']['reaction_time_ms'].mean()
        dissonant_rt = df[df['alarm_played'] == 'dissonant']['reaction_time_ms'].mean()
        
        # Compute the specific "Dissonance Performance Penalty"
        rt_penalty = dissonant_rt - baseline_rt
        accuracy_drop = baseline_accuracy - dissonant_accuracy
        
        # Append this participant's summary vector to our compilation list
        compiled_behavioral.append({
            "Participant_ID": p_id,
            "Baseline_RT": baseline_rt,
            "Dissonant_RT": dissonant_rt,
            "RT_Penalty_ms": rt_penalty,
            "Accuracy_Drop": accuracy_drop
        })
        
    # Convert behavioral metrics to a summary dataframe
    df_behavioral = pd.DataFrame(compiled_behavioral)
    
    # 2. Load your Google Form CSV
    # Ensure your Google Form has a "Participant ID" column matching your filenames!
    df_survey = pd.read_csv("data/survey/google_form_responses.csv")
    
    # 3. MERGE BOTH DATASETS TOGETHER
    final_master_dataset = pd.merge(df_behavioral, df_survey, on="Participant_ID")
    
    # Save the consolidated matrix for modeling
    final_master_dataset.to_csv("data/master_analytics_dataset.csv", index=False)
    print("✅ Master dataset generated and compiled successfully!")

if __name__ == "__main__":
    process_all_participants()