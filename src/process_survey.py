import os
import pandas as pd

def clean_google_form_data(input_csv, output_csv="HCI-Jazz_Cleaned_Responses.csv"):
    """
    Cleans Google Form responses, maps columns, and duplicates rows 
    to match the behavioral telemetry IDs (e.g., mirroring U15 to U15-1).
    """
    print(f"Loading data from: {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # 1. Rename long Google Form questions to clean, data-science-friendly column names
    col_mapping = {
        'What is your Code? (Given by assessor)': 'participant_id',
        'Have you had experience in musical performances?': 'musical_background',
        'How many years of active musical experience do you have?': 'years_experience',
        'SOUND A': 'dissonance_Cmaj6',
        'Sound A - How distracting would this sound be if it played while you were trying to focus on a difficult task?': 'distraction_Cmaj6',
        'SOUND B': 'dissonance_Cmaj7_b9',
        'Sound B - How distracting would this sound be if it played while you were trying to focus on a difficult task?': 'distraction_Cmaj7_b9',
        'SOUND C': 'dissonance_min2nd_cluster',
        'Sound C - How distracting would this sound be if it played while you were trying to focus on a difficult task?': 'distraction_min2nd_cluster',
        'SOUND D': 'dissonance_Cmaj',
        'Sound D - How distracting would this sound be if it played while you were trying to focus on a difficult task?': 'distraction_Cmaj',
        'SOUND E': 'dissonance_stacked_tritones',
        'Sound E - How distracting would this sound be if it played while you were trying to focus on a difficult task?': 'distraction_stacked_tritones',
        'SOUND F': 'dissonance_C7_sharp_9',
        'Sound F - How distracting would this sound be if it played while you were trying to focus on a difficult task?': 'distraction_C7_sharp_9',
        'When you heard a complex or harsh chord, what was your immediate mental reaction? (Select all that apply) 복잡하거나 불편한 코드를 들었을 때, 직관적으로 든 반응은 무엇이었습니까? (해당되는 것을 모두 선택해 주세요)': 'mental_reaction',
        'Which of the following best describes your internal response when hearing the more complex or tense chords? 더 복잡하거나 긴장감이 높은 코드를 들었을 때, 자신의 내부 반응을 가장 잘 설명하는 것은 무엇입니까?': 'internal_response',
        'In your opinion, would the most complex/dissonant chords you heard today make an effective warning alarm in an urgent, high-stakes environment (e.g., a cockpit or a hospital operating room)? 오늘 들은 가장 복잡하고 불협화음적인 코드들이 긴박하고 위험도가 높은 환경(예: 비행기 조종석, 병원 수술실)에서 효과적인 경고음 역할을 할 수 있을 것이라 생각합니까?': 'effective_alarm_rating',
        'If you felt a difference in how your brain processed the simple (smooth) chords versus the complex (tense) chords, please briefly describe that experience. 단순한(부드러운) 코드를 들었을 때와 복잡한(긴장감 있는) 코드를 들었을 때 뇌가 정보를 처리하는 방식의 차이를 느끼셨다면, 그 경험을 간략히 기술해 주세요.': 'qualitative_experience'
    }
    df = df.rename(columns=col_mapping)
    
    # Drop the Timestamp column as it is unnecessary for statistical analysis
    df = df.drop(columns=['Timestamp'], errors='ignore')
    
    # 2. Duplicate rows for the "-1" behavioral logs
    # This ensures if U15 is a musician, U15-1 is automatically logged as a musician too
    df_sub = df.copy()
    df_sub['participant_id'] = df_sub['participant_id'].astype(str) + '-1'
    
    # Combine the original and the duplicated rows
    df_final = pd.concat([df, df_sub], ignore_index=True)
    
    # Sort so base IDs and their '-1' counterparts appear sequentially (e.g., U06, U06-1)
    df_final = df_final.sort_values(by='participant_id').reset_index(drop=True)
    
    # 3. Create the explicit 'group' column strictly based on musical background
    def categorize_group(bg):
        if 'Jazz' in str(bg):
            return 'musician'
        else:
            return 'non_musician'
            
    # Insert the 'group' column right after 'musical_background' (index 2)
    df_final.insert(2, 'group', df_final['musical_background'].apply(categorize_group))
    
    # 4. Export the clean dataset
    df_final.to_csv(output_csv, index=False)
    
    print(f"\n--- Processing Complete ---")
    print(f"Saved cleaned dataset to: {output_csv}")
    print(f"Total rows generated (including mirrored IDs): {len(df_final)}")
    
    return df_final

if __name__ == "__main__":
    # Ensure this matches the actual filename of your downloaded Google Form CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    INPUT_FILE = os.path.join(script_dir, "HCI-Jazz (Responses) - Form responses 1.csv")
    
    try:
        clean_google_form_data(INPUT_FILE)
    except FileNotFoundError:
        print(f"Error: Could not find '{INPUT_FILE}'. Please check the file path.")