import requests
import pandas as pd
import time

def get_steam_api_details():
    # Wczytujemy AppID z pliku SteamSpy
    try:
        df_spy = pd.read_csv('stg_steamspy_top1000.csv')
        app_ids = df_spy['appid'].tolist()
    except FileNotFoundError:
        print("Błąd: Brak pliku stg_steamspy_top1000.csv. Uruchom najpierw Skrypt 1.")
        return

    details_list = []
    print(f"Rozpoczynam pobieranie detali dla 1000 gier. Szacowany czas: ~25 min.")

    for i, app_id in enumerate(app_ids):
        url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&l=polish"
        
        try:
            res = requests.get(url)
            if res.status_code == 200:
                data = res.json()
                if data and data[str(app_id)]['success']:
                    g = data[str(app_id)]['data']
                    
                    details_list.append({
                        'appid': app_id,
                        'name': g.get('name'),
                        'release_date': g.get('release_date', {}).get('date'),
                        'genres': ";".join([gen['description'] for gen in g.get('genres', [])]),
                        'developers': ";".join(g.get('developers', [])),
                        'price_pln': g.get('price_overview', {}).get('final_formatted'),
                        'description': g.get('short_description')
                    })
            
            # Monitoring postępu
            if (i + 1) % 50 == 0:
                print(f"Pobrano {i + 1}/1000...")
            
            time.sleep(1.5) # Ochrona przed banem IP
            
        except Exception as e:
            print(f"Błąd przy {app_id}: {e}")
            continue

    # Zapis do drugiego pliku CSV
    df_details = pd.DataFrame(details_list)
    df_details.to_csv('stg_steamapi_top1000.csv', index=False, encoding='utf-8-sig')
    print("Zakończono! Dane zapisane w stg_steamapi_top1000.csv")

if __name__ == "__main__":
    get_steam_api_details()