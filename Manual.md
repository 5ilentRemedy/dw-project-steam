🎯 Kryteria i realizacja projektu
📊 Ocena 3.0: Projekt hurtowni + załadowanie danych
Gdzie tego szukać:

Definicja hurtowni (Schemat Gwiazdy): sql/01_database_objects.sql

Ładowanie danych: 03_load_initial_bulk_to_mssql.py oraz 04_load_update_to_mssql.py

Opis realizacji:
Projekt hurtowni został oparty na strukturze schematu gwiazdy, który jest budowany dynamicznie za pomocą procedury składowanej usp_BuildAndLoadStarSchema. W centrum znajduje się tabela faktów Fact_GameMetrics, przechowująca miary takie jak cena, wyniki z serwisu Metacritic, szczytowa liczba graczy czy recenzje. Wokół niej rozmieszczono tabele wymiarów (np. Dim_Game, Dim_Date, Dim_Platform, Dim_Genres).

Załadowanie danych odbywa się automatycznie z poziomu Pythona. Skrypt 03_load_initial_bulk_to_mssql.py z wykorzystaniem biblioteki pyodbc oraz mechanizmu fast_executemany wczytuje paczkę "Initial Bulk" (70% starszych danych) do tabeli stagingowej, a następnie uruchamia procedurę zasilającą docelową hurtownię.

⚙️ Ocena 3.5: Odpalenie procesu ETL
Gdzie tego szukać:

E (Extract): 01_download_from_kagglehub.py

T (Transform): 02_standardize_and_split_data.py

L (Load): 03_load_initial_bulk_to_mssql.py oraz 04_load_update_to_mssql.py

Opis realizacji:
Pełny proces ETL (Extract, Transform, Load) jest oskryptowany i możliwy do uruchomienia krok po kroku:

Ekstrakcja: Pobranie najświeższego zbioru danych steam-games-dataset bezpośrednio z platformy Kaggle przy użyciu biblioteki kagglehub i zapisanie ich do katalogu data/raw/.

Transformacja: Oczyszczenie formatów, usunięcie zbędnych kolumn, standaryzacja tekstów i dat (przy użyciu biblioteki pandas). Następnie dane są logicznie dzielone według daty premiery na paczkę inicjalną (70%) oraz paczkę aktualizacyjną (30%) w celu symulacji przyrostowego zasilania hurtowni (Incremental Load).

Ładowanie: Zasilenie bazy MS SQL Server przygotowanymi plikami .csv. Skrypt 04_load_update_to_mssql.py wykorzystuje mechanizm MERGE (winside procedury SQL) do bezkolizyjnego dopisywania oraz aktualizowania istniejących już faktów i wymiarów.

🖥️ Ocena 4.0: Przygotowanie dashboard-u (prezentacja danych)
Gdzie tego szukać:

Dashboard główny: 05_dashboard_streamlit.py

Uruchomienie: 06_run_dashboard.py

Opis realizacji:
Warstwa analityczna to interaktywna aplikacja webowa zbudowana w oparciu o framework Streamlit. Po udanym logowaniu do bazy danych z panelu bocznego, dashboard zaciąga zbudowany schemat gwiazdy i prezentuje:

Filtry interaktywne: rok wydania, platforma, kategoria wiekowa, poziom wsparcia, osiągnięcia, gatunki, które w czasie rzeczywistym zmieniają widok.

Główne wskaźniki KPI: takie jak łączna liczba unikalnych gier, średnia cena, średni wynik Metacritic oraz całkowita szczytowa liczba graczy (Peak CCU).

Sześć wykresów analitycznych: wygenerowanych za pomocą biblioteki plotly.express, m.in. trend gier wydawanych z biegiem lat, ranking najpopularniejszych gatunków, dystrybucja platform operacyjnych oraz korelacja ceny z ocenami graczy.

🏗️ Ocena 5.0: Backend + frontend
Gdzie tego szukać:

Backend: MS SQL Server, zapytania SQL, pyodbc, transformacje w pandas.

Frontend: Skrypty wykorzystujące UI Streamlit oraz Plotly.

Opis realizacji:
Projekt stanowi kompletną, end-to-end architekturę analityczną, gdzie odpowiedzialności są wyraźnie odseparowane:

Warstwa Backendowa (Logika i Składowanie Danych): W całości oparta o relacyjną bazę MS SQL Server, która utrzymuje złożoną strukturę schematu gwiazdy. Operacje CRUD i transformacje "ciężkie" wydelegowane są na warstwę bazy danych (procedury składowane, operatory MERGE). Python pełni tu rolę potężnego kontrolera procesu ETL zarządzającego cyklem życia danych (konfiguracja, pobieranie, połączenia bazodanowe autoryzowane w project_config.py).

Warstwa Frontendowa (Prezentacja): Reprezentowana przez responsywny interfejs użytkownika w Streamlit. Posiada wbudowany prosty formularz logowania zabezpieczający dostęp do hurtowni (zarządzanie stanem aplikacji – st.session_state). Aplikacja frontendowa posiada zoptymalizowany moduł @st.cache_data, który buforuje odpytywanie backendu SQL, znacząco przyspieszając przełączanie filtrów w interfejsie. Wykresy (Plotly) zapewniają bogate, interaktywne podpowiedzi (tzw. tooltips).

🚀 Instrukcja szybkiego uruchomienia projektu do weryfikacji
Aby udowodnić działanie całego stosu technologicznego (od punktu 3.0 do 5.0), wystarczy odpalić sekwencyjnie skrypty w konsoli PowerShell:

PowerShell
## 1. Konfiguracja środowiska (opcjonalnie)
python 00_setup_venv.py
.\.venv\Scripts\Activate.ps1

## 2. Test połączenia z lokalnym MS SQL
python 00_test_mssql_connection.py

## 3. Proces ETL (Ocena 3.5)
python 01_download_from_kagglehub.py
python 02_standardize_and_split_data.py

## 4. Ładowanie i hurtownia (Ocena 3.0)
python 03_load_initial_bulk_to_mssql.py
python 04_load_update_to_mssql.py

## 5. Uruchomienie Frontend / Dashboard (Ocena 4.0 i 5.0)
python 06_run_dashboard.py

# lub bezpośrednio:
# streamlit run 05_dashboard_streamlit.py
