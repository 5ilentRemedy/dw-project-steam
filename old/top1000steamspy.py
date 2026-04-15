import requests
import pandas as pd

def get_top_1000_steamspy():
    print("Pobieranie Top 1000 gier ze SteamSpy...")
    # Strona 0 zwraca pierwsze 1000 gier posortowanych domyślnie wg popularności/sprzedaży
    url = "https://steamspy.com/api.php?request=all&page=0"
    
    try:
        response = requests.get(url, timeout=30)
        data = response.json()
        
        # Konwersja słownika na listę
        games_list = list(data.values())
        
        # Sortowanie pomocnicze
        def get_min_owners(game):
            try:
                return int(str(game.get('owners', '0')).replace(',', '').split('..')[0])
            except:
                return 0
        
        games_list.sort(key=get_min_owners, reverse=True)
        top_1000 = games_list[:1000]
        
        # Zapis do CSV
        df = pd.DataFrame(top_1000)
        df.to_csv('stg_steamspy_top1000.csv', index=False, encoding='utf-8-sig')
        
        print(f"SUKCES: Zapisano {len(df)} gier do stg_steamspy_top1000.csv")
        return df['appid'].tolist()
        
    except Exception as e:
        print(f"Błąd: {e}")
        return []

if __name__ == "__main__":
    get_top_1000_steamspy()