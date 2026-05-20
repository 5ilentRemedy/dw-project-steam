import os
import shutil
import kagglehub
import datetime

def download_and_move_dataset():
    # Ustalanie katalogu docelowego w projekcie
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, "data")

    # ID zbioru danych na Kaggle
    dataset_id = "fronkongames/steam-games-dataset"
    print(f"Pobieranie zbioru danych: {dataset_id}...")
    
    # Pobieranie przez kagglehub (najpierw zapisuje w lokalnym cache)
    cache_path = kagglehub.dataset_download(dataset_id)
    print(f"Pliki zapisane wstępnie w cache: {cache_path}")

    # Tworzenie katalogu 'data', jeśli jeszcze nie istnieje w naszym projekcie
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Utworzono katalog docelowy: {data_dir}")

    # Generowanie znacznika czasu (timestamp), np. 20260428_190500
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Przenoszenie (kopiowanie) plików z ukrytego cache do naszego widocznego katalogu data/
    for root, dirs, files in os.walk(cache_path):
        for file in files:
            source_path = os.path.join(root, file)
            
            # Dodanie znacznika czasu do nazwy pliku dla ułatwienia wersjonowania
            filename, ext = os.path.splitext(file)
            new_filename = f"{filename}_{timestamp}{ext}"
            destination_path = os.path.join(data_dir, new_filename)
            
            shutil.copy2(source_path, destination_path)
            print(f"Skopiowano: {new_filename} do katalogu data/")

    print(f"\nZakończono pobieranie i przenoszenie danych do: {data_dir}")

if __name__ == "__main__":
    download_and_move_dataset()