import pandas as pd
from pathlib import Path
import os

def list_all_source_columns():
    data_dir = Path(__file__).parent / "data"
    
    # Szukamy surowego pliku CSV pobranego z Kaggle (ignorujemy staging)
    csv_files = sorted([f for f in data_dir.glob("games_*.csv") if "staging" not in f.name])
    
    if not csv_files:
        print("[!] BŁĄD: Nie znaleziono surowych plików w katalogu data/.")
        print("Upewnij się, że uruchomiłeś najpierw 01_download_data.py")
        return

    latest_file = csv_files[-1]
    print(f"--- ANALIZA PLIKU: {latest_file.name} ---")
    
    # Wczytujemy tylko pierwszy wiersz, żeby było szybko
    df_sample = pd.read_csv(latest_file, nrows=1)
    
    print(f"\nZnaleziono łącznie {len(df_sample.columns)} kolumn:\n")
    print(f"{'NR':<4} | {'NAZWA KOLUMNY':<30} | {'PRZYKŁADOWA WARTOŚĆ'}")
    print("-" * 70)
    
    for i, col in enumerate(df_sample.columns, 1):
        sample_val = str(df_sample[col].iloc[0])[:50] # Skracamy długie teksty
        print(f"{i:<4} | {col:<30} | {sample_val}")

if __name__ == "__main__":
    list_all_source_columns()