import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfiguracja strony
st.set_page_config(page_title="Steam Warehouse Pro Analytics", layout="wide", initial_sidebar_state="expanded")

# Inicjalizacja stanu sesji dla autoryzacji
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- SIDEBAR: PANEL STEROWANIA ---
st.sidebar.title("🛠️ Panel Sterowania")
db_user = "dashuser"

if not st.session_state['authenticated']:
    with st.sidebar.form("login_form"):
        st.subheader("Autoryzacja")
        pwd = st.text_input("Hasło dla dashuser", type="password")
        submit_button = st.form_submit_button("Zaloguj")

    if submit_button:
        try:
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER=NORMANDY\\SQLEXPRESS;'
                f'DATABASE=db_dw_project_steam;'
                f'UID={db_user};'
                f'PWD={pwd};'
                f'TrustServerCertificate=yes;'
            )
            test_conn = pyodbc.connect(conn_str)
            test_conn.close()
            st.session_state['authenticated'] = True
            st.session_state['password'] = pwd
            st.rerun()
        except Exception:
            st.sidebar.error("❌ Błąd logowania - sprawdź hasło")
else:
    if st.sidebar.button("Wyloguj"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- LOGIKA DANYCH ---
if st.session_state['authenticated']:
    
    @st.cache_data(ttl=600)
    def load_full_data(pwd):
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER=NORMANDY\\SQLEXPRESS;'
            f'DATABASE=db_dw_project_steam;'
            f'UID={db_user};'
            f'PWD={pwd};'
            f'TrustServerCertificate=yes;'
        )
        conn = pyodbc.connect(conn_str)
        query = """
        SELECT 
            dg.Name, dd.Year, dd.Quarter, dp.PlatformName, 
            dar.AgeCategory, dsl.SupportDescription, dcs.AchievementsTier,
            f.Price, f.MetacriticScore, f.UserScore, f.PeakCCU, f.PlaytimeForever,
            dgn.GenreList
        FROM Fact_GameMetrics f
        JOIN Dim_Game dg ON f.GameKey = dg.GameKey
        JOIN Dim_Date dd ON f.DateKey = dd.DateKey
        JOIN Dim_Platform dp ON f.PlatformKey = dp.PlatformKey
        JOIN Dim_AgeRating dar ON f.AgeKey = dar.AgeKey
        JOIN Dim_SupportLevel dsl ON f.SupportKey = dsl.SupportKey
        JOIN Dim_ContentStats dcs ON f.ContentKey = dcs.ContentKey
        JOIN Dim_Genres dgn ON f.GenreKey = dgn.GenreKey
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    try:
        df = load_full_data(st.session_state['password'])

        # --- FILTRY SIDEBAR ---
        st.sidebar.subheader("🔍 Filtrowanie")
        f_years = st.sidebar.multiselect("📅 Lata wydania", options=sorted(df['Year'].unique(), reverse=True))
        f_platform = st.sidebar.multiselect("💻 Platforma", options=df['PlatformName'].unique())
        f_age = st.sidebar.multiselect("🔞 Kat. wiekowa", options=df['AgeCategory'].unique())
        f_support = st.sidebar.multiselect("🛠️ Poziom wsparcia", options=df['SupportDescription'].unique())
        
        # Poprawione nazwy filtrów osiągnięć z liczbami
        ach_map = {"Brak": "Brak (0)", "Mało": "Mało (1-9)", "Średnio": "Średnio (10-49)", "Bardzo dużo": "Dużo (50+)"}
        f_achieve = st.sidebar.multiselect("🏆 Osiągnięcia", options=df['AchievementsTier'].unique())
        
        all_genres = sorted(list(set(df['GenreList'].str.split(', ').explode())))
        f_genre = st.sidebar.multiselect("🧬 Gatunek", options=all_genres)

        # Aplikowanie filtrów
        f_df = df.copy()
        if f_years: f_df = f_df[f_df['Year'].isin(f_years)]
        if f_platform: f_df = f_df[f_df['PlatformName'].isin(f_platform)]
        if f_age: f_df = f_df[f_df['AgeCategory'].isin(f_age)]
        if f_support: f_df = f_df[f_df['SupportDescription'].isin(f_support)]
        if f_achieve: f_df = f_df[f_df['AchievementsTier'].isin(f_achieve)]
        if f_genre: f_df = f_df[f_df['GenreList'].apply(lambda x: any(g in x for g in f_genre))]

        st.title("📊 Steam Data Warehouse Pro Dashboard")

        # --- KPI ---
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Liczba Gier", f"{len(f_df):,}")
        kpi2.metric("Śr. Cena", f"{f_df['Price'].mean():.2f} $")
        kpi3.metric("Śr. Metascore", f"{f_df[f_df['MetacriticScore']>0]['MetacriticScore'].mean():.1f}")
        kpi4.metric("Suma Peak CCU", f"{int(f_df['PeakCCU'].sum()):,}", help="Concurrent Connected Users")

        st.divider()

        # --- SEKCJA WYKRESÓW 1 ---
        row1_1, row1_2 = st.columns(2)
        with row1_1:
            st.subheader("📈 Dynamika Premier (Liczba gier na rok)")
            trend = f_df.groupby('Year').size().reset_index(name='Ilość')
            st.plotly_chart(px.line(trend, x='Year', y='Ilość', markers=True, template="plotly_dark"), use_container_width=True)
        
        with row1_2:
            st.subheader("📊 Popularność Gatunków")
            genres = f_df['GenreList'].str.split(', ').explode().value_counts().head(10).reset_index()
            st.plotly_chart(px.bar(genres, x='count', y='GenreList', orientation='h', color='count', color_continuous_scale='Blues'), use_container_width=True)

        # --- SEKCJA WYKRESÓW 2 ---
        row2_1, row2_2 = st.columns(2)
        with row2_1:
            st.subheader("🎯 Struktura Kategorii Wiekowych")
            st.plotly_chart(px.pie(f_df, names='AgeCategory', hole=0.5), use_container_width=True)
        
        with row2_2:
            st.subheader("💰 Popularność vs Cena (Suma CCU)")
            price_ccu = f_df.groupby('Price')['PeakCCU'].sum().reset_index().head(40)
            st.plotly_chart(px.area(price_ccu, x='Price', y='PeakCCU', color_discrete_sequence=['#00CC96']), use_container_width=True)

        # --- SEKCJA WYKRESÓW 3 ---
        row3_1, row3_2 = st.columns(2)
        with row3_1:
            # Dodano liczby w nawiasach do wykresu lejkowego
            st.subheader("🏆 Rozkład Osiągnięć (Liczbowo)")
            ach_data = f_df['AchievementsTier'].value_counts().reset_index()
            ach_data['AchievementsTier'] = ach_data['AchievementsTier'].map({
                'Brak': 'Brak (0)', 'Mało': 'Mało (1-9)', 
                'Średnio': 'Średnio (10-49)', 'Bardzo dużo': 'Dużo (50+)'
            })
            st.plotly_chart(px.funnel(ach_data, x='count', y='AchievementsTier'), use_container_width=True)
        
        with row3_2:
            st.subheader("🔧 Deklarowane Wsparcie Techniczne")
            supp_data = f_df['SupportDescription'].value_counts().reset_index()
            st.plotly_chart(px.bar(supp_data, x='SupportDescription', y='count', color='SupportDescription', text_auto=True), use_container_width=True)

        # --- SEKCJA WYKRESÓW 4 ---
        row4_1, row4_2 = st.columns(2)
        with row4_1:
            st.subheader("🎮 Udział Platform Systemowych")
            plat_data = f_df['PlatformName'].value_counts().reset_index()
            st.plotly_chart(px.bar(plat_data, x='PlatformName', y='count', color='count', color_continuous_scale='Viridis'), use_container_width=True)
        
        with row4_2:
            st.subheader("🕒 Czas Gry vs Oceny Recenzentów")
            play_df = f_df[f_df['MetacriticScore'] > 0].groupby('MetacriticScore')['PlaytimeForever'].mean().reset_index()
            st.plotly_chart(px.scatter(play_df, x='MetacriticScore', y='PlaytimeForever', trendline="ols"), use_container_width=True)

        # --- POPRAWIONY I ROZBUDOWANY SŁOWNICZEK NA DOLE ---
        st.divider()
        with st.expander("Dokumentacja Metryk"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("### 📈 Metryki Popularności")
                st.write("**Peak CCU (Concurrent Connected Users)**")
                st.caption("Najwyższa odnotowana liczba graczy online jednocześnie w historii tytułu. Główny wskaźnik sukcesu komercyjnego i aktywności społeczności.")
                
                st.write("**Metascore vs User Score**")
                st.caption("Metascore to ocena krytyków (0-100), natomiast User Score to ocena samych graczy. Rozbieżność między nimi często wskazuje na kontrowersje wokół tytułu.")

                st.write("**Playtime Forever**")
                st.caption("Uśredniony całkowity czas spędzony w grze przez użytkowników (wyrażony w minutach). Pozwala ocenić 'grywalność' i długowieczność tytułu.")

            with col_b:
                st.markdown("### 🏆 Klasyfikacja Danych")
                st.write("**Progi Osiągnięć (Achievements Tier)**")
                st.markdown("""
                * **Brak**: 0 osiągnięć.
                * **Mało**: 1 - 9 osiągnięć (proste gry indie).
                * **Średnio**: 10 - 49 osiągnięć (standard rynkowy).
                * **Dużo**: 50+ osiągnięć (gry nastawione na długą retencję).
                """)
                
                st.write("**Poziomy Wsparcia (Support Level)**")
                st.caption("Klasyfikacja bazująca na istnieniu dedykowanej strony WWW oraz adresu e-mail do pomocy technicznej w metadanych Steam.")

                st.write("**Data Warehouse (Model Gwiazdy)**")
                st.caption("Dane pochodzą z 9 tabel wymiarów połączonych z centralną tabelą faktów (Fact_GameMetrics), co zapewnia najwyższą wydajność zapytań analitycznych.")

    except Exception as e:
        st.error(f"Błąd krytyczny aplikacji: {e}")
else:
    st.info("👈 Dashboard zablokowany. Zaloguj się jako 'dashuser' w panelu bocznym.")