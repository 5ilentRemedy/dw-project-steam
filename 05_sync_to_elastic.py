import pyodbc
from elasticsearch import Elasticsearch, helpers
import getpass

def sync_sql_to_elastic():
    # --- KONFIGURACJA SQL ---
    server = 'NORMANDY\\SQLEXPRESS'
    database = 'db_dw_project_steam'
    
    # --- KONFIGURACJA ELASTIC ---
    es_host = "https://localhost:9200"
    es_user = "elastic"
    es_pass = getpass.getpass("Podaj hasło do Elasticsearch: ")

    # Połączenie z Elastic (ignorujemy certyfikat na lokalnym devie)
    es = Elasticsearch(
        es_host,
        basic_auth=(es_user, es_pass),
        verify_certs=False
    )

    # Połączenie z SQL
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;')
    cursor = conn.cursor()

    # POBIERAMY DANE (Łączymy Fact z Wymiarami w jeden dokument JSON)
    query = """
    SELECT 
        f.FactKey, dg.Name, dd.FullDate, dp.PlatformName, 
        f.Price, f.MetacriticScore, dgn.GenreList, dpb.PublisherList
    FROM Fact_GameMetrics f
    JOIN Dim_Game dg ON f.GameKey = dg.GameKey
    JOIN Dim_Date dd ON f.DateKey = dd.DateKey
    JOIN Dim_Platform dp ON f.PlatformKey = dp.PlatformKey
    JOIN Dim_Genres dgn ON f.GenreKey = dgn.GenreKey
    JOIN Dim_Publishers dpb ON f.PublisherKey = dpb.PublisherKey
    """
    
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]

    print("Przygotowywanie dokumentów...")
    actions = []
    for row in cursor.fetchall():
        doc = dict(zip(columns, row))
        action = {
            "_index": "steam_games",
            "_id": doc['FactKey'],
            "_source": doc
        }
        actions.append(action)

    print(f"Wysyłanie {len(actions)} dokumentów do Elasticsearch...")
    helpers.bulk(es, actions)
    print("Synchronizacja zakończona!")

if __name__ == "__main__":
    sync_sql_to_elastic()