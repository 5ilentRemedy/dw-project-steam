import os

import pandas as pd
import plotly.express as px
import pyodbc
import streamlit as st

from project_config import SQL_USER, SQL_PASSWORD, needs_sql_password, sql_connection_string
from logging_config import setup_logging

logger = setup_logging("05_dashboard_streamlit")

logger.info("=" * 80)
logger.info("DASHBOARD INITIALIZATION")
logger.info("=" * 80)

st.set_page_config(page_title="Steam Data Warehouse", layout="wide")
logger.debug("Streamlit page configured")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "sql_password" not in st.session_state:
    st.session_state.sql_password = SQL_PASSWORD

logger.info("Session state initialized")


@st.cache_data(ttl=600)
def load_data(password):
    logger.info("Loading data from SQL Server (cache timeout: 10 minutes)")
    query = """
    SELECT
        dg.AppID,
        dg.Name,
        dd.FullDate,
        dd.Year,
        dd.Quarter,
        dd.MonthName,
        dp.PlatformName,
        da.AgeCategory,
        ds.SupportDescription,
        dc.AchievementsTier,
        dge.GenreList,
        dpu.PublisherList,
        dl.LanguageList,
        f.Price,
        f.MetacriticScore,
        f.UserScore,
        f.PositiveReviews,
        f.NegativeReviews,
        f.PeakCCU,
        f.PlaytimeForever
    FROM dbo.Fact_GameMetrics f
    JOIN dbo.Dim_Game dg ON dg.GameKey = f.GameKey
    JOIN dbo.Dim_Date dd ON dd.DateKey = f.DateKey
    JOIN dbo.Dim_Platform dp ON dp.PlatformKey = f.PlatformKey
    JOIN dbo.Dim_AgeRating da ON da.AgeKey = f.AgeKey
    JOIN dbo.Dim_SupportLevel ds ON ds.SupportKey = f.SupportKey
    JOIN dbo.Dim_ContentStats dc ON dc.ContentKey = f.ContentKey
    JOIN dbo.Dim_Genres dge ON dge.GenreKey = f.GenreKey
    JOIN dbo.Dim_Publishers dpu ON dpu.PublisherKey = f.PublisherKey
    JOIN dbo.Dim_Language dl ON dl.LanguageKey = f.LanguageKey;
    """
    logger.debug("Executing data query...")
    try:
        with pyodbc.connect(sql_connection_string(password)) as conn:
            df = pd.read_sql(query, conn)
        logger.info(f"✓ Data loaded successfully: {len(df):,} rows")
        return df
    except Exception as e:
        logger.error(f"✗ Failed to load data: {e}")
        raise


def apply_filters(df):
    st.sidebar.header("Filters")
    filtered = df.copy()
    logger.debug(f"Starting filtering on {len(df):,} rows")

    years = st.sidebar.multiselect("Release year", sorted(df["Year"].dropna().astype(int).unique(), reverse=True))
    platforms = st.sidebar.multiselect("Platform", sorted(df["PlatformName"].dropna().unique()))
    ages = st.sidebar.multiselect("Age category", sorted(df["AgeCategory"].dropna().unique()))
    support = st.sidebar.multiselect("Support", sorted(df["SupportDescription"].dropna().unique()))
    achievements = st.sidebar.multiselect("Achievements", sorted(df["AchievementsTier"].dropna().unique()))
    genres = sorted(set(df["GenreList"].fillna("").str.split(", ").explode()) - {""})
    selected_genres = st.sidebar.multiselect("Genre", genres)

    filter_count = 0
    if years:
        filtered = filtered[filtered["Year"].isin(years)]
        filter_count += 1
        logger.debug(f"Applied year filter: {len(years)} year(s)")
    if platforms:
        filtered = filtered[filtered["PlatformName"].isin(platforms)]
        filter_count += 1
        logger.debug(f"Applied platform filter: {len(platforms)} platform(s)")
    if ages:
        filtered = filtered[filtered["AgeCategory"].isin(ages)]
        filter_count += 1
        logger.debug(f"Applied age filter: {len(ages)} category(ies)")
    if support:
        filtered = filtered[filtered["SupportDescription"].isin(support)]
        filter_count += 1
        logger.debug(f"Applied support filter: {len(support)} level(s)")
    if achievements:
        filtered = filtered[filtered["AchievementsTier"].isin(achievements)]
        filter_count += 1
        logger.debug(f"Applied achievements filter: {len(achievements)} tier(s)")
    if selected_genres:
        filtered = filtered[
            filtered["GenreList"].fillna("").apply(lambda value: any(genre in value for genre in selected_genres))
        ]
        filter_count += 1
        logger.debug(f"Applied genre filter: {len(selected_genres)} genre(s)")

    logger.info(f"Filters applied: {filter_count} active filter(s) | Result: {len(filtered):,} rows")
    return filtered


def main():
    st.title("Steam Data Warehouse Dashboard")
    logger.info("Dashboard UI initialized")

    if needs_sql_password() and not st.session_state.authenticated:
        logger.info("Authentication required and user not authenticated")
        with st.sidebar.form("login_form"):
            password = st.text_input(f"Password for {SQL_USER}", type="password")
            submitted = st.form_submit_button("Login")

        if not submitted:
            st.info("Enter SQL Server password in the sidebar.")
            logger.debug("Waiting for user to submit login form")
            return

        try:
            logger.info(f"Attempting authentication for user: {SQL_USER}")
            load_data.clear()
            load_data(password)
            st.session_state.sql_password = password
            st.session_state.authenticated = True
            logger.info("✓ Authentication successful")
            st.rerun()
        except Exception as error:
            logger.error(f"✗ Authentication failed: {error}")
            st.error(f"Could not connect to SQL Server: {error}")
            return

    if needs_sql_password() and st.session_state.authenticated:
        if st.sidebar.button("Logout"):
            logger.info("User clicked logout")
            st.session_state.authenticated = False
            st.session_state.sql_password = None
            load_data.clear()
            st.rerun()

    password = st.session_state.sql_password if needs_sql_password() else None

    try:
        logger.info("Loading data for dashboard display...")
        df = load_data(password)
    except Exception as error:
        logger.error(f"✗ Could not load data from SQL Server: {error}")
        st.error(f"Could not load data from SQL Server: {error}")
        return

    logger.info(f"Applying user filters...")
    filtered = apply_filters(df)
    unique_games = filtered.drop_duplicates("AppID")
    logger.info(f"Data ready for display: {len(unique_games):,} unique games")

    logger.debug("Rendering KPI metrics...")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Games", f"{unique_games['AppID'].nunique():,}")
    kpi2.metric("Average price", f"${unique_games['Price'].mean():.2f}" if len(unique_games) else "$0.00")
    metacritic = unique_games.loc[unique_games["MetacriticScore"] > 0, "MetacriticScore"].mean()
    kpi3.metric("Average Metascore", f"{metacritic:.1f}" if pd.notna(metacritic) else "0.0")
    kpi4.metric("Peak CCU total", f"{int(unique_games['PeakCCU'].sum()):,}")

    st.divider()

    logger.debug("Rendering visualization charts...")
    col1, col2 = st.columns(2)
    with col1:
        trend = unique_games.dropna(subset=["Year"]).groupby("Year")["AppID"].nunique().reset_index(name="Games")
        st.subheader("Games released by year")
        st.plotly_chart(px.line(trend, x="Year", y="Games", markers=True), use_container_width=True)

    with col2:
        genres = unique_games["GenreList"].fillna("").str.split(", ").explode()
        genres = genres[genres != ""].value_counts().head(10).reset_index()
        genres.columns = ["Genre", "Games"]
        st.subheader("Top genres")
        st.plotly_chart(px.bar(genres, x="Games", y="Genre", orientation="h"), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Age categories")
        st.plotly_chart(px.pie(unique_games, names="AgeCategory", hole=0.45), use_container_width=True)

    with col4:
        platforms = filtered.groupby("PlatformName")["AppID"].nunique().reset_index(name="Games")
        platforms.columns = ["Platform", "Games"]
        st.subheader("Platforms")
        st.plotly_chart(px.bar(platforms, x="Platform", y="Games"), use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        support = unique_games["SupportDescription"].value_counts().reset_index()
        support.columns = ["Support", "Games"]
        st.subheader("Support level")
        st.plotly_chart(px.bar(support, x="Support", y="Games"), use_container_width=True)

    with col6:
        score_price = unique_games[unique_games["MetacriticScore"] > 0]
        st.subheader("Price vs Metascore")
        st.plotly_chart(
            px.scatter(score_price, x="Price", y="MetacriticScore", size="PeakCCU", hover_name="Name"),
            use_container_width=True,
        )
    
    logger.info("✓ Dashboard rendered successfully")


if __name__ == "__main__":
    main()
