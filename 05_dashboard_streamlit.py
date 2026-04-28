import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px

# 1. Konfiguracja strony
st.set_page_config(page_title="Steam Data Warehouse", layout="wide")

# Inicjalizacja stanu sesji dla zalogowanego użytkownika
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# --- SIDEBAR: LOGOWANIE ---
st.sidebar.title("🔐 Autoryzacja")
db_user = "dashuser"

if not st.session_state['authenticated']:
    with st.sidebar.form("login_form"):
        pwd = st.text_input("Hasło dla dashuser", type="password")
        submit_button = st.form_submit_button("Zaloguj")

    if submit_button:
        try:
            # Dodajemy TrustServerCertificate=yes dla pewności połączenia
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
        except Exception as e:
            st.sidebar.error(f"❌ Błąd: {str(e)}")
else:
    if st.sidebar.button("Wyloguj"):
        st.session_state['authenticated'] = False
        st.rerun()

# --- GŁÓWNA TREŚĆ APLIKACJI ---
if st.session_state['authenticated']:
    st.title("🎮 Steam Data Warehouse Dashboard")
    st.success(f"Połączono jako {db_user}")

    @st.cache_data(ttl=600) # Cache na 10 minut
    def load_data(pwd):
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
            dg.Name,
            dd.FullDate,
            dd.Year,
            dp.PlatformName,
            dar.AgeCategory,
            f.Price,
            f.MetacriticScore,
            f.UserScore,
            f.PeakCCU,
            f.PlaytimeForever
        FROM Fact_GameMetrics f
        JOIN Dim_Game dg ON f.GameKey = dg.GameKey
        JOIN Dim_Date dd ON f.DateKey = dd.DateKey
        JOIN Dim_Platform dp ON f.PlatformKey = dp.PlatformKey
        JOIN Dim_AgeRating dar ON f.AgeKey = dar.AgeKey
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    try:
        df = load_data(st.session_state['password'])

        # KPI row
        c1, c2, c3 = st.columns(3)
        c1.metric("Łączna liczba gier", len(df))
        c2.metric("Średnia cena", f"{df['Price'].mean():.2f} $")
        c3.metric("Najwyższy Peak CCU", int(df['PeakCCU'].max()))

        # Wykresy
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Ceny gier według kategorii wiekowej")
            fig = px.box(df, x="AgeCategory", y="Price", color="AgeCategory")
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.subheader("Popularność (Peak CCU) vs Cena")
            fig2 = px.scatter(df[df['PeakCCU'] > 0], x="Price", y="PeakCCU", 
                              hover_name="Name", size="PeakCCU", color="MetacriticScore")
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"Błąd podczas pobierania danych: {e}")

else:
    st.warning("Proszę zalogować się w panelu bocznym.")
    st.info("💡 Wskazówka: Upewnij się, że użytkownik 'dashuser' ma uprawnienia SELECT do tabel w bazie.")