
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "incinerator.db"

st.set_page_config(
    page_title="INCINERATOR",
    page_icon="🔥",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp { background: #101114; color: #f5f5f5; }
    h1, h2, h3 { color: #f04444; }
    [data-testid="stMetric"] {
        background: #1c1d22;
        border: 1px solid #35363d;
        padding: 16px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data
def load_tables():
    if not DATABASE.exists():
        return {}

    # Open SQLite in read-only mode; this app cannot write to the DB.
    uri = DATABASE.resolve().as_uri() + "?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        names = pd.read_sql_query(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name",
            conn,
        )["name"].tolist()

        return {
            name: pd.read_sql_query(
                f'SELECT * FROM "{name.replace(chr(34), chr(34)*2)}"',
                conn,
            )
            for name in names
        }

st.title("🔥 INCINERATOR")
st.caption("CEW DATABASE • WRESTLER PROFILES • MATCH HISTORY")
st.divider()

try:
    tables = load_tables()
except Exception as exc:
    st.error("Could not read the database.")
    st.code(str(exc))
    st.stop()

if not tables:
    st.error("No database tables found. Check that incinerator.db is in this folder.")
    st.stop()

st.success("Database connected in read-only mode.")

table_names = list(tables)
profile_table = next(
    (n for n in table_names if n.lower() == "wrestler_profiles"),
    None,
)
history_table = next(
    (n for n in table_names if n.lower() == "wrestler_match_history"),
    None,
)

if profile_table:
    profiles = tables[profile_table]
    st.subheader("Roster overview")
    c1, c2 = st.columns(2)
    c1.metric("Wrestler profiles", len(profiles))
    c2.metric("Database tables", len(tables))

    search = st.text_input("🔎 Search wrestlers")
    filtered = profiles.copy()

    name_col = next(
        (c for c in filtered.columns if c.lower() in
         ("wrestler_name", "name", "profile_name", "wrestler")),
        None,
    )
    if search and name_col:
        filtered = filtered[
            filtered[name_col].astype(str).str.contains(
                search, case=False, na=False
            )
        ]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    if name_col and not filtered.empty:
        st.subheader("Wrestler profile")
        names = filtered[name_col].astype(str).tolist()
        selected = st.selectbox("Choose a wrestler", names)
        row = filtered[filtered[name_col].astype(str) == selected].iloc[0]

        left, right = st.columns(2)
        items = list(row.items())
        midpoint = (len(items) + 1) // 2

        with left:
            for key, value in items[:midpoint]:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        with right:
            for key, value in items[midpoint:]:
                st.write(f"**{key.replace('_', ' ').title()}:** {value}")

if history_table:
    history = tables[history_table]
    st.divider()
    st.subheader("Match history")
    st.metric("History records", len(history))
    st.dataframe(history, use_container_width=True, hide_index=True)

with st.expander("Database tables"):
    for name, frame in tables.items():
        st.write(f"**{name}** — {len(frame)} rows, {len(frame.columns)} columns")

st.caption("INCINERATOR • Public read-only edition")
