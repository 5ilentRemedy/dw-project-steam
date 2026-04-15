import pandas as pd
import json
import os
import glob
import datetime

def extract_and_save_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")
    json_path = os.path.join(current_dir, "columns_to_extract.json")
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(data_dir, f"filtered_games_{timestamp}.csv")

    # Wczytywanie kolumn do wyciągnięcia z pliku JSON
    if not os.path.exists(json_path):
        print(f"Błąd: Nie znaleziono pliku konfiguracyjnego {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        columns_to_extract = config.get("columns_to_extract", [])

    if not columns_to_extract:
        print("Błąd: Lista kolumn do wyciągnięcia z pliku JSON jest pusta.")
        return

    # Szukanie pobranego pliku CSV z danymi w katalogu data/
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    
    # Pomijamy pliki wynikowe z poprzednich uruchomień
    csv_files = [f for f in csv_files if "filtered_games" not in os.path.basename(f)]

    if not csv_files:
        print(f"Błąd: Nie znaleziono pobranych plików źródłowych CSV w katalogu {data_dir}.")
        print("Upewnij się, że skrypt 'download_data.py' został poprawnie uruchomiony.")
        return

    # Sortowanie plików CSV według daty modyfikacji (najnowsze najpierw)
    csv_files.sort(key=os.path.getmtime, reverse=True)

    # Wybieramy najnowszy pobrany plik CSV
    source_file = csv_files[0]
    print(f"Wczytywanie danych źródłowych z najnowszego pliku: {source_file}...")

    try:
        # Wczytanie całego zbioru danych do pandas DataFrame
        df = pd.read_csv(source_file)
        
        # Opcjonalnie: Standaryzacja nazw kolumn, aby były pisane z małych liter i miały podkreślenia zamiast spacji
        # Pozwoli to na łatwiejsze mapowanie z pliku JSON
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]

        # Wczytanie docelowych kolumn z JSON i upewnienie się, że również są w tym samym formacie
        columns_to_extract = [col.lower().replace(' ', '_') for col in columns_to_extract]

        # Weryfikacja czy wszystkie kolumny z JSONa faktycznie istnieją w pobranym pliku
        missing_columns = [col for col in columns_to_extract if col not in df.columns]
        if missing_columns:
            print(f"Ostrzeżenie: Następujące kolumny zdefiniowane w JSON nie istnieją w danych źródłowych i zostaną pominięte: {missing_columns}")
            # Zawężenie listy kolumn tylko do tych, które faktycznie istnieją
            columns_to_extract = [col for col in columns_to_extract if col in df.columns]

        print(f"Wyciąganie {len(columns_to_extract)} kolumn...")
        
        # Ekstrakcja tylko wybranych kolumn
        filtered_df = df[columns_to_extract].copy()

        print("Trwa standaryzacja danych...")
        
        # Standaryzacja 1: Próba konwersji daty na spójny format
        if 'release_date' in filtered_df.columns:
            filtered_df['release_date'] = pd.to_datetime(filtered_df['release_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
        # Standaryzacja 2: Uzupełnianie braków w danych
        for col in filtered_df.columns:
            if filtered_df[col].dtype == 'object':
                filtered_df[col] = filtered_df[col].fillna('Brak')
            else:
                filtered_df[col] = filtered_df[col].fillna(0)
                
        # Zapisanie wyników do Excela (.xlsx), aby umożliwić podział na kolumny i włączenie filtrów
        excel_output_path = output_path.replace('.csv', '.xlsx')
        print(f"Zapisywanie danych do pliku Excel z dodaniem filtrów w nagłówkach: {excel_output_path}...")
        
        with pd.ExcelWriter(excel_output_path, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Games')
            
            workbook = writer.book
            worksheet = writer.sheets['Games']
            
            # Włączenie filtrów w nagłówkach (autofilter) dla całego zakresu danych
            max_row, max_col = filtered_df.shape
            worksheet.autofilter(0, 0, max_row, max_col - 1)
            
            # Dostosowanie szerokości kolumn
            for i, col in enumerate(filtered_df.columns):
                # max długość w kolumnie (ograniczamy do 40 znaków szerokości)
                max_len = min(40, max(filtered_df[col].astype(str).map(len).max(), len(col)) + 2)
                worksheet.set_column(i, i, max_len)

        print(f"Zakończono sukcesem! Zapisano przefiltrowane dane ({len(filtered_df)} wierszy) do pliku: {excel_output_path}")

    except Exception as e:
        print(f"Wystąpił błąd podczas przetwarzania danych: {e}")

if __name__ == "__main__":
    extract_and_save_data()