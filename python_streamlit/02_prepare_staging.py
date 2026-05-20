import pandas as pd
from pathlib import Path
import sys
import io
import json
import numpy as np

# Wymuszenie kodowania UTF-8 dla konsoli Windows
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def prepare_for_sql():
    print("=" * 60)
    print("PRZYGOTOWANIE ROZSZERZONYCH DANYCH DLA MS SQL (9 WYMIARÓW)")
    print("=" * 60)

    data_dir = Path(__file__).parent / "data"
    json_files = sorted(list(data_dir.glob("games_*.json")))
    
    if not json_files:
        print("[!] BŁĄD: Nie znaleziono plików JSON.")
        return
        
    latest_file = json_files[-1]
    print(f"Wczytywanie: {latest_file.name}...")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index.name = 'AppID'
    df = df.reset_index()
    
    # --- ROZSZERZONA LISTA KOLUMN ---
    json_columns = [
        'AppID', 'name', 'release_date', 'price', 'required_age',
        'windows', 'mac', 'linux',
        'metacritic_score', 'user_score', 'positive', 'negative',
        'achievements', 'peak_ccu', 'average_playtime_forever',
        'developers', 'publishers', 'categories', 'genres', 'tags',
        'supported_languages', 'website', 'support_url', 'support_email',
        'estimated_owners'
    ]

    available_cols = [col for col in json_columns if col in df.columns]
    df = df[available_cols].copy()
    
    # Mapowanie nazw na czytelne dla SQL
    rename_map = {
        'name': 'Name',
        'release_date': 'Release date',
        'price': 'Price',
        'required_age': 'Required age',
        'windows': 'Windows',
        'mac': 'Mac',
        'linux': 'Linux',
        'metacritic_score': 'Metacritic score',
        'user_score': 'User score',
        'positive': 'Positive',
        'negative': 'Negative',
        'achievements': 'Achievements',
        'peak_ccu': 'Peak CCU',
        'average_playtime_forever': 'Playtime forever',
        'developers': 'Developers',
        'publishers': 'Publishers',
        'categories': 'Categories',
        'genres': 'Genres',
        'tags': 'Tags',
        'supported_languages': 'Languages',
        'website': 'Website',
        'support_url': 'Support URL',
        'support_email': 'Support Email',
        'estimated_owners': 'Estimated owners'
    }
    df = df.rename(columns=rename_map)

    print("Transformacja danych i czyszczenie...")

    # Obsługa list i czyszczenie tekstu
    for col in df.columns:
        # Konwersja list na stringi (np. języki, gatunki)
        df[col] = df[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)
        
        if df[col].dtype == object:
            df[col] = df[col].fillna('')
            df[col] = df[col].astype(str).str.replace(r'[\n\r\t]+', ' ', regex=True)
            df[col] = df[col].str.replace(r'\s{2,}', ' ', regex=True).str.strip()

    # Standaryzacja typów numerycznych (żeby SQL nie krzyczał)
    num_cols = ['Price', 'Required age', 'Metacritic score', 'User score', 
                'Positive', 'Negative', 'Achievements', 'Peak CCU', 'Playtime forever']
    
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Logika dla wymiaru Dim_Support (czy posiada jakiekolwiek dane kontaktowe)
    df['Has Website'] = df['Website'].apply(lambda x: 1 if len(str(x)) > 5 else 0)
    df['Has Support'] = df.apply(lambda row: 1 if len(str(row['Support URL'])) > 5 or len(str(row['Support Email'])) > 5 else 0, axis=1)

    # Formatowanie daty
    if 'Release date' in df.columns:
        df['Release date'] = pd.to_datetime(df['Release date'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['Release date'] = df['Release date'].fillna('')

    output_path = data_dir / "games_staging.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\n[SUKCES] Przygotowano {df.shape[0]} wierszy z bogatymi metadanymi.")
    print(f"Plik: {output_path.name}")

if __name__ == "__main__":
    prepare_for_sql()