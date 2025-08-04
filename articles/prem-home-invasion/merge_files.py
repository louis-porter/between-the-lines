
import pandas as pd
import os
from datetime import datetime

# Update this to the directory containing your files
DATA_DIR = "articles/prem-home-invasion"

def parse_date_column(df):
    """
    Attempt to parse the 'Date' column using multiple common formats.
    Fallback to auto-inference if necessary.
    """
    original_dates = df['Date'].copy()

    # Try known common formats
    formats_to_try = ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%d-%m-%Y', '%d %b %Y']
    for fmt in formats_to_try:
        parsed = pd.to_datetime(df['Date'], format=fmt, errors='coerce')
        success_count = parsed.notna().sum()
        if success_count > 0 and success_count >= len(df) * 0.9:  # >=90% success
            df['Date'] = parsed
            return df

    # Final fallback: let pandas try to infer automatically
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)

    # Still nothing? Print a sample to investigate
    if df['Date'].isna().all():
        print("⚠ Date parsing failed completely. Sample values:")
        print(original_dates.head(5).to_list())

    return df


def merge_premier_league_data(data_dir):
    print("Premier League Data Merger")
    print("="*30)

    # List CSV files in the directory
    all_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    print(f"Files in directory: {data_dir}")
    for f in sorted(all_files):
        print(f"  {f}")
    print()

    dataframes = []

    # Attempt to load E0 (4).csv to E0 (36).csv
    for i in range(4, 37):
        filename = f"E0 ({i}).csv"
        path = os.path.join(data_dir, filename)
        
        if os.path.exists(path):
            print(f"Reading {filename}...")
            try:
                df = pd.read_csv(path)
                df = parse_date_column(df)
                dataframes.append(df)
                print(f"✓ Successfully read {filename} - {len(df)} rows")
            except Exception as e:
                print(f"✗ Error reading {filename}: {e}")
        else:
            print(f"⚠ File {filename} not found - skipping")

    if not dataframes:
        print("No data files loaded — exiting.")
        return None

    # Merge all DataFrames
    merged_df = pd.concat(dataframes, ignore_index=True)
    print(f"\n✓ Merged data: {len(merged_df)} total rows")

    # Drop rows with invalid dates
    invalid_dates = merged_df['Date'].isna().sum()
    if invalid_dates > 0:
        print(f"⚠ Dropping {invalid_dates} rows with invalid/missing dates")
        merged_df = merged_df.dropna(subset=['Date'])

    # Add Season column
    merged_df['Season'] = merged_df['Date'].apply(
        lambda x: x.year + 1 if x.month >= 8 else x.year
    )

    merged_df = merged_df.sort_values('Date').reset_index(drop=True)
    print(f"✓ Added Season column")
    print(f"Season range: {merged_df['Season'].min()} - {merged_df['Season'].max()}")
    print(f"Seasons covered: {sorted(merged_df['Season'].unique())}")

    # Save merged file
    output_path = os.path.join(data_dir, "premier_league_merged.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"✓ Saved merged data to {output_path}")

    return merged_df

def display_sample_data(df, n=5):
    print(f"\nSample data (first {n} rows):")
    print("="*50)
    key_cols = ['Date', 'Season', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
    cols = [c for c in key_cols if c in df.columns]
    print(df[cols].head(n).to_string(index=False))

    print(f"\nSeasons breakdown:")
    for season, count in df['Season'].value_counts().sort_index().items():
        print(f"  {season}: {count} matches")

if __name__ == "__main__":
    merged = merge_premier_league_data(DATA_DIR)
    if merged is not None:
        display_sample_data(merged)
        print(f"\nTotal columns: {len(merged.columns)}")
        print(f"Total matches: {len(merged)}")
    else:
        print("No data was merged.")
