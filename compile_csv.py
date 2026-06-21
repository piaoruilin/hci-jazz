import os
import glob
import pandas as pd

def compile_by_folder_structure(root_dir="."):
    raw_dir = os.path.join(root_dir, "data", "raw_behavioral")
    processed_dir = os.path.join(root_dir, "data", "processed")
    
    all_files = glob.glob(os.path.join(raw_dir, "*.csv"))
    if not all_files:
        print(f"No CSV files found in: {raw_dir}")
        return

    compiled_events = []
    
    for file_path in all_files:
        try:
            df = pd.read_csv(file_path)
            
            # Extract the pure participant token (e.g., 'U15')
            raw_pid = str(df['Participant_ID'].iloc[0]).split('-')[0].strip()
            
            # Keep only rows where an actual alarm went off
            active_trials = df[df['alarm_file'].notna() & (df['alarm_file'] != 'none')].copy()
            
            # Map conditions precisely based on your filename patterns or structure
            def get_condition(val):
                filename = str(val).lower()
                # Since your screenshots show these exact filenames:
                if 'major_6' in filename or filename == 'c_major.wav':
                    return 'Consonant'
                else:
                    return 'Dissonant'
            
            active_trials['Participant'] = raw_pid
            active_trials['Condition'] = active_trials['alarm_file'].apply(get_condition)
            
            compiled_events.append(active_trials)
        except Exception as e:
            print(f"Error processing {os.path.basename(file_path)}: {e}")
            
    if compiled_events:
        final_df = pd.concat(compiled_events, ignore_index=True)
        
        # Target layout for your downstream statistics
        target_columns = [
            'Participant', 'Condition', 'alarm_file', 
            'reaction_time_ms', 'step_index', 'pressed_match'
        ]
        
        valid_cols = [col for col in target_columns if col in final_df.columns]
        final_df = final_df[valid_cols]
        
        os.makedirs(processed_dir, exist_ok=True)
        output_path = os.path.join(processed_dir, "behavioral_events_master.csv")
        final_df.to_csv(output_path, index=False)
        
        print(f"Successfully compiled {len(final_df)} events into: {output_path}")
        print("\nCleaned Data Sample:")
        print(final_df.head(10))

if __name__ == "__main__":
    compile_by_folder_structure()