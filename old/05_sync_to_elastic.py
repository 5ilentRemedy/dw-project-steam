import pyodbc
from elasticsearch import Elasticsearch, helpers
import urllib3

# Wyłączamy ostrzeżenia o braku weryfikacji certyfikatu SSL na localhost
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def sync_sql_to_elastic():
    # --- KONFIGURACJA SQL ---
    server = 'NORMANDY\\SQLEXPRESS'
    database = 'db_dw_project_steam'
    
    # --- KONFIGURACJA ELASTIC ---
    es_host = "https://localhost:9200"
    es_user = "elastic"
    # TUTAJ WPISZ HASŁO Z TWOJEGO LOGU:
    es_pass = "UILUa5h1gVTy6YGLTmtY" 

    # Połączenie z Elastic (verify_certs=False pozwala na pracę z lokalnym SSL)
    es = Elasticsearch(
        es_host,
        basic_auth=(es_user, es_pass),
        verify_certs=False 
    )

    # Połączenie z SQL Server (Windows Auth)
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Wyciągamy dane z Twojej Gwiazdy (wszystko w jednym zapytaniu!)
# Zmieniamy JOIN na LEFT JOIN, żeby nie zgubić danych przy brakujących relacjach
    query = """
    SELECT 
        f.FactKey, 
        dg.Name, 
        dd.FullDate, 
        dp.PlatformName, 
        f.Price, 
        f.MetacriticScore, 
        f.UserScore, 
        f.PeakCCU,
        ISNULL(dgn.GenreList, 'Brak') as GenreList, 
        ISNULL(dpb.PublisherList, 'Brak') as PublisherList, 
        ISNULL(dlg.LanguageList, 'Brak') as LanguageList
    FROM Fact_GameMetrics f
    LEFT JOIN Dim_Game dg ON f.GameKey = dg.GameKey
    LEFT JOIN Dim_Date dd ON f.DateKey = dd.DateKey
    LEFT JOIN Dim_Platform dp ON f.PlatformKey = dp.PlatformKey
    LEFT JOIN Dim_Genres dgn ON f.GenreKey = dgn.GenreKey
    LEFT JOIN Dim_Publishers dpb ON f.PublisherKey = dpb.PublisherKey
    LEFT JOIN Dim_Language dlg ON f.LanguageKey = dlg.LanguageKey
    """
    
    print("Pobieranie danych z SQL Server...")
    cursor.execute(query)
    columns = [column[0] for column in cursor.description]

    actions = []
    for row in cursor.fetchall():
        doc = dict(zip(columns, row))
        # Elastic nie lubi typu 'decimal' z Pythona, zamieniamy na float
        if doc['Price']: doc['Price'] = float(doc['Price'])
        
        action = {
            "_index": "steam_games",
            "_id": doc['FactKey'],
            "_source": doc
        }
        actions.append(action)

    print(f"Wysyłanie {len(actions)} dokumentów do Elasticsearch...")
    helpers.bulk(es, actions)
    print("\n[SUKCES] Dane są już w Elasticsearch!")

if __name__ == "__main__":
    sync_sql_to_elastic()