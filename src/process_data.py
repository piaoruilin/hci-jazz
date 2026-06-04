import os
import glob
import numpy as np
import pandas as pd
from scipy import stats

def process_and_analyze():
    # -------------------------------------------------------------
    # STEP 1: LOAD AND AGGREGATE RAW BEHAVIORAL PYGAME TELEMETRY
    # -------------------------------------------------------------
    behavioral_files = glob.glob("data/raw_behavioral/*.csv")
    
    if not behavioral_files:
        print("❌ No behavioral CSV files found in data/raw_behavioral/.")
        return

    summary_records = []
    
    print(f"Parsing {len(behavioral_files)} participant log files...")
    for file_path in behavioral_files:
        df = pd.read_csv(file_path)
        
        # Extract ID metadata safely
        p_id = df['Participant_ID'].iloc[0] if 'Participant_ID' in df.columns else os.path.basename(file_path).replace(".csv", "")
        
        # --- DATA CLEANING & PREPROCESSING ---
        # 1. Isolate genuine active keypress responses (drop timeouts/NaN values)
        valid_responses = df[df['reaction_time_ms'].notna()].copy()
        
        # 2. Statistical Outlier Removal (Filter out mechanical keyboard blips < 200ms)
        valid_responses = valid_responses[valid_responses['reaction_time_ms'] >= 200]
        
        # --- METRIC FEATURE ENGINEERING ---
        # Calculate individual mean baseline reaction speed (Silence/None phases)
        baseline_rt = valid_responses[valid_responses['alarm_file'] == 'none']['reaction_time_ms'].mean()
        
        # Calculate individual mean reaction speed when ANY chord alarm is playing
        chord_rt = valid_responses[valid_responses['alarm_file'] != 'none']['reaction_time_ms'].mean()
        
        # Compute the specific metrics of interest
        rt_penalty_ms = chord_rt - baseline_rt
        overall_accuracy = df['correct'].mean()
        
        summary_records.append({
            "Participant_ID": str(p_id).strip(),
            "Baseline_Mean_RT_ms": baseline_rt,
            "Chord_Mean_RT_ms": chord_rt,
            "RT_Penalty_ms": rt_penalty_ms,
            "Accuracy_Rate": overall_accuracy
        })
        
    df_behavioral_summary = pd.DataFrame(summary_records)

# -------------------------------------------------------------
    # STEP 2: LOAD AND CLEAN SURVEY METADATA FROM GOOGLE FORM
    # -------------------------------------------------------------
    survey_path = "data/processed/google_form_responses.csv"
    if not os.path.exists(survey_path):
        print(f"❌ Missing survey metrics tracker file: '{survey_path}'")
        return
        
    df_survey = pd.read_csv(survey_path)
    df_survey.columns = df_survey.columns.str.strip()
    
    # 1. Map your EXACT column headers here
    id_col = "Participant ID" 
    group_col = "Have you had experience in musical performances?" # <--- EXACT QUESTION TEXT
    
    df_survey[id_col] = df_survey[id_col].astype(str).str.strip()
    
    # 2. DATA CLEANING: Clean long sentences into clean data science labels
    group_mapping = {
        "Yes, specifically in Jazz theory/performance.": "Jazz",
        "Yes, in Classical or other non-jazz genres.": "Classical",
        "No formal musical training (Non-musician).": "Non-Musician"
    }
    
    # Create a new, clean categorical column for calculations
    df_survey['Cohort'] = df_survey[group_col].str.strip().map(group_mapping)
    
    if id_col not in df_survey.columns:
        print(f"❌ Error: Column '{id_col}' not detected in Google Form CSV headers.")
        print(f"Available headers: {list(df_survey.columns)}")
        return

    df_survey[id_col] = df_survey[id_col].astype(str).str.strip()
    
    # -------------------------------------------------------------
    # STEP 3: CONSOLIDATED PARSING LAYER JOIN (BEHAVIORAL + SURVEY)
    # -------------------------------------------------------------
    df_master = pd.merge(df_behavioral_summary, df_survey, left_on="Participant_ID", right_on=id_col, how="inner")
    
    if df_master.empty:
        print("⚠️ Warning: Combined matrix join resulted in an empty frame.")
        print("Verify your file name IDs match your Google Form ID entries precisely.")
        return

    # Export compiled dataset back into your tracking directory
    master_output_path = "data/processed/master_analytics_dataset.csv"
    df_master.to_csv(master_output_path, index=False)
    print(f"✅ Integrated matrix written safely to disk: '{master_output_path}'")

    # -------------------------------------------------------------
    # STEP 4: HYPOTHESIS TESTING (ONE-WAY ANOVA FOR 3 GROUPS)
    # -------------------------------------------------------------
    print("\n==========================================")
    print("       STATISTICAL HYPOTHESIS TESTING       ")
    print("==========================================")
    
    # Isolate data arrays for our 3 cleaned groups
    jazz_group = df_master[df_master['Cohort'] == 'Jazz']['RT_Penalty_ms'].dropna()
    classical_group = df_master[df_master['Cohort'] == 'Classical']['RT_Penalty_ms'].dropna()
    non_music_group = df_master[df_master['Cohort'] == 'Non-Musician']['RT_Penalty_ms'].dropna()
    
    print(f"Jazz Group:       Sample Size = {len(jazz_group)}, Mean RT Penalty = {jazz_group.mean():.2f} ms")
    print(f"Classical Group:  Sample Size = {len(classical_group)}, Mean RT Penalty = {classical_group.mean():.2f} ms")
    print(f"Non-Musician:     Sample Size = {len(non_music_group)}, Mean RT Penalty = {non_music_group.mean():.2f} ms")
    
    if len(jazz_group) < 2 or len(classical_group) < 2 or len(non_music_group) < 2:
        print("\nℹ️ Waiting for more data. Need at least 2 entries per group to execute ANOVA.")
        return

    # Run One-Way ANOVA across all three distributions
    f_stat, p_value = stats.f_oneway(jazz_group, classical_group, non_music_group)
    
    print(f"\nCalculated F-Statistic: {f_stat:.4f}")
    print(f"Calculated ANOVA P-value: {p_value:.6f}")
    
    print("\n------------------------------------------")
    if p_value < 0.05:
        print("🎉 STATISTICALLY SIGNIFICANT RESULT!")
        print("The dissonance performance penalty is significantly different across the 3 cohorts.")
        print("You can now run a Post-Hoc Tukey HSD test to see if Jazz holds flat compared to Classical!")
    else:
        print("⚖️ RETAIN NULL HYPOTHESIS")
        print("No statistically significant group performance delta detected across cohorts.")
    print("==========================================")

if __name__ == "__main__":
    process_and_analyze()