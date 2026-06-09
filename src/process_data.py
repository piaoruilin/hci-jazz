import argparse
import glob
import os
import re
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats


def extract_base_participant_id(filename: str) -> str:
    """Normalize names like U01.csv and U01-1.csv to U01."""
    base_name = os.path.basename(str(filename)).replace('.csv', '')
    clean_id = re.split(r'[-_]', base_name)[0]
    return clean_id.strip().upper()


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_raw_behavioral_files(raw_dir: str) -> List[str]:
    pattern = os.path.join(raw_dir, '*.csv')
    return sorted(glob.glob(pattern))


def clean_behavioral_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()

    if 'reaction_time_ms' in df.columns:
        df = df[df['reaction_time_ms'].notna()]
        df = df[df['reaction_time_ms'] >= 200]

    return df


def calculate_participant_metrics(participant_id: str, df: pd.DataFrame) -> Dict[str, float]:
    valid = clean_behavioral_dataframe(df)
    baseline = valid.loc[valid['alarm_file'] == 'none', 'reaction_time_ms']
    chord = valid.loc[valid['alarm_file'] != 'none', 'reaction_time_ms']

    metrics = {
        'Participant_ID': participant_id,
        'Runs_Combined': df['run_id'].nunique() if 'run_id' in df.columns else np.nan,
        'Total_Rows': len(df),
        'Keepable_Rows': len(valid),
        'Baseline_Mean_RT_ms': baseline.mean() if not baseline.empty else np.nan,
        'Chord_Mean_RT_ms': chord.mean() if not chord.empty else np.nan,
        'Accuracy_Rate': df['correct'].mean() if 'correct' in df.columns else np.nan,
    }
    metrics['RT_Penalty_ms'] = metrics['Chord_Mean_RT_ms'] - metrics['Baseline_Mean_RT_ms']
    return metrics


def combine_raw_sessions(raw_dir: str, participant_raw_out: str, save_combined_raw: bool) -> pd.DataFrame:
    raw_files = load_raw_behavioral_files(raw_dir)
    if not raw_files:
        raise FileNotFoundError(f'No raw CSV files found in {raw_dir}')

    grouped_dfs: Dict[str, List[pd.DataFrame]] = {}

    for path in raw_files:
        base_id = extract_base_participant_id(path)
        df = pd.read_csv(path)
        grouped_dfs.setdefault(base_id, []).append(df)

    summary_records = []

    for participant_id, dfs in grouped_dfs.items():
        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.insert(0, 'Participant_ID', participant_id)

        if save_combined_raw:
            ensure_directory(participant_raw_out)
            combined_path = os.path.join(participant_raw_out, f'{participant_id}.csv')
            combined_df.to_csv(combined_path, index=False)

        summary_records.append(calculate_participant_metrics(participant_id, combined_df))

    return pd.DataFrame(summary_records)


def find_survey_columns(df: pd.DataFrame) -> Tuple[str, str]:
    cleaned = [col.strip() for col in df.columns]
    participant_candidates = [col for col in cleaned if 'participant' in col.lower()]
    rating_candidates = [col for col in cleaned if any(token in col.lower() for token in ['uncomfort', 'discomfort', 'chord', 'rating'])]

    if not participant_candidates:
        raise ValueError('Could not detect a participant ID column in the survey CSV.')
    if not rating_candidates:
        raise ValueError('Could not detect a chord discomfort/rating column in the survey CSV.')

    return participant_candidates[0], rating_candidates[0]


def merge_summary_with_survey(
    df_summary: pd.DataFrame,
    survey_path: str,
    participant_col: Optional[str] = None,
    rating_col: Optional[str] = None,
) -> Tuple[pd.DataFrame, str, str]:
    survey = pd.read_csv(survey_path)
    survey.columns = survey.columns.str.strip()

    if participant_col is None or rating_col is None:
        participant_col, rating_col = find_survey_columns(survey)

    survey['Participant_ID'] = survey[participant_col].astype(str).apply(extract_base_participant_id)
    merged = df_summary.merge(
        survey[['Participant_ID', rating_col]],
        on='Participant_ID',
        how='inner',
    )

    if merged.empty:
        raise ValueError('No overlapping Participant_ID values were found between behavior summary and survey CSV.')

    return merged, participant_col, rating_col


def run_statistical_tests(df_merged: pd.DataFrame, rating_col: str) -> pd.DataFrame:
    df = df_merged.copy()
    df[rating_col] = pd.to_numeric(df[rating_col], errors='coerce')
    df = df.dropna(subset=[rating_col, 'RT_Penalty_ms'])

    if df.empty:
        raise ValueError('No valid numeric survey ratings and RT penalty values were available for testing.')

    pearson = stats.pearsonr(df[rating_col], df['RT_Penalty_ms'])
    spearman = stats.spearmanr(df[rating_col], df['RT_Penalty_ms'])

    median_rating = df[rating_col].median()
    low_group = df.loc[df[rating_col] <= median_rating, 'RT_Penalty_ms']
    high_group = df.loc[df[rating_col] > median_rating, 'RT_Penalty_ms']
    ttest = stats.ttest_ind(low_group, high_group, equal_var=False, nan_policy='omit')

    report = pd.DataFrame(
        [
            {
                'Test': 'Pearson correlation',
                'Rating_Column': rating_col,
                'Metric': 'RT_Penalty_ms',
                'Statistic': pearson.statistic,
                'p_value': pearson.pvalue,
                'Notes': 'Linear relation',
            },
            {
                'Test': 'Spearman correlation',
                'Rating_Column': rating_col,
                'Metric': 'RT_Penalty_ms',
                'Statistic': spearman.correlation,
                'p_value': spearman.pvalue,
                'Notes': 'Rank-order relation',
            },
            {
                'Test': 'Welch t-test',
                'Rating_Column': rating_col,
                'Metric': 'RT_Penalty_ms',
                'Statistic': ttest.statistic,
                'p_value': ttest.pvalue,
                'Notes': f'Low vs high discomfort split at median ({median_rating})',
            },
        ]
    )

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description='Process N-back raw behavioral CSVs and optionally merge Google Form ratings.')
    parser.add_argument('--raw-dir', default='data/raw_behavioral', help='Folder containing the raw behavioral CSV files.')
    parser.add_argument('--processed-dir', default='data/processed', help='Folder to write combined and summary outputs.')
    parser.add_argument('--survey-path', default=None, help='Path to the Google Form survey CSV file.')
    parser.add_argument('--save-combined-raw', action='store_true', help='Save combined participant raw files under processed output.')
    args = parser.parse_args()

    ensure_directory(args.processed_dir)
    participant_raw_out = os.path.join(args.processed_dir, 'combined_raw_behavioral')
    if args.save_combined_raw:
        ensure_directory(participant_raw_out)

    print('Loading raw behavioral files...')
    df_summary = combine_raw_sessions(args.raw_dir, participant_raw_out, args.save_combined_raw)

    summary_path = os.path.join(args.processed_dir, 'behavioral_summary.csv')
    df_summary.to_csv(summary_path, index=False)
    print(f'Saved participant summary to {summary_path}')

    if args.survey_path:
        print('Loading survey CSV...')
        merged, participant_col, rating_col = merge_summary_with_survey(df_summary, args.survey_path)
        merged_path = os.path.join(args.processed_dir, 'behavioral_survey_merged.csv')
        merged.to_csv(merged_path, index=False)
        print(f'Saved merged behavioral + survey data to {merged_path}')

        report = run_statistical_tests(merged, rating_col)
        report_path = os.path.join(args.processed_dir, 'survey_statistics_report.csv')
        report.to_csv(report_path, index=False)
        print(f'Saved statistical report to {report_path}')
        print(report.to_string(index=False))
    else:
        print('No survey CSV path provided. Skipping survey merge and statistical tests.')


if __name__ == '__main__':
    main()
