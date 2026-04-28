import pandas as pd
from pathlib import Path
import sys
import io
import json

# Wymuszenie kodowania UTF-8 dla konsoli Windows
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def prepare_for_sql():
    print("=" * 60)
    print("PRZYGOTOWANIE DANYCH DLA MS SQL")
    print("=" * 60)

    data_dir = Path(__file__).parent / "data"
    
    # Szukamy bezpiecznego pliku JSON zamiast wadliwego CSV
    json_files = sorted(list(data_dir.glob("games_*.json")))
    
    if not json_files:
        print("[!] BŁĄD: Nie znaleziono plików JSON z danymi.")
        print("Uruchom najpierw skrypt 01_download_data.py")
        return
        
    latest_file = json_files[-1]
    print(f"Wczytywanie danych z pliku: {latest_file.name}...")
    print("To może zająć kilkanaście sekund...")
    
    # Wczytywanie JSON
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Konwersja na pandas DataFrame
    df = pd.DataFrame.from_dict(data, orient='index')
    df.index.name = 'AppID'
    df = df.reset_index()
    
    print(f"Początkowy rozmiar: {df.shape[0]} wierszy, {df.shape[1]} kolumn")

    # W JSON kolumny są pisane małymi literami z podłogą
    json_columns = [
        'AppID', 'name', 'release_date', 'price', 
        'windows', 'mac', 'linux',
        'developers', 'publishers',
        'categories', 'genres', 
        'metacritic_score', 'achievements', 
        'positive', 'negative', 'estimated_owners'
    ]

    # Wyciągamy to co nas interesuje
    available_cols = [col for col in json_columns if col in df.columns]
    df = df[available_cols].copy()
    
    # Zmieniamy nazwy na czyste, aby skrypt nr 3 załadował je prawidłowo do bazy
    rename_map = {
        'name': 'Name',
        'release_date': 'Release date',
        'price': 'Price',
        'windows': 'Windows',
        'mac': 'Mac',
        'linux': 'Linux',
        'developers': 'Developers',
        'publishers': 'Publishers',
        'categories': 'Categories',
        'genres': 'Genres',
        'metacritic_score': 'Metacritic score',
        'achievements': 'Achievements',
        'positive': 'Positive',
        'negative': 'Negative',
        'estimated_owners': 'Estimated owners'
    }
    df = df.rename(columns=rename_map)

    print("Trwa czyszczenie formatowania (usuwanie znaków nowej linii, formatowanie dat)...")
    
    for col in df.columns:
        # JSON czasami przetrzymuje kategorie/gatunki jako listy. Zmieniamy je na tekst z przecinkami
        df[col] = df[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)
        
        if df[col].dtype == object:
            df[col] = df[col].fillna('')
            df[col] = df[col].astype(str).str.replace(r'[\n\r]+', ' ', regex=True)
            df[col] = df[col].str.replace(r'\s{2,}', ' ', regex=True).str.strip()

    # Standaryzacja daty
    if 'Release date' in df.columns:
        df['Release date'] = pd.to_datetime(df['Release date'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['Release date'] = df['Release date'].fillna('')

    # Standaryzacja cen
    if 'Price' in df.columns:
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0).round(2)

    # Zapis
    output_path = data_dir / "games_staging.csv"
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f"\n[SUKCES] Zapisano w 100% wyrównane dane do: {output_path.name}")
    print("Są gotowe do ponownego importu do MS SQL!")

if __name__ == "__main__":
    prepare_for_sql()