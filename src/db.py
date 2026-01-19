import pandas as pd
import MySQLdb
import streamlit as st
from .config import DB_CONFIG, EV_CHARGER_TABLE, CAR_MODEL_TABLE

@st.cache_data(ttl=600)
def load_faq() -> pd.DataFrame:
    conn = MySQLdb.connect(connect_timeout=50, **DB_CONFIG)
    df = pd.read_sql_query("SELECT * FROM faq;", conn).fillna("")
    conn.close()
    return df

@st.cache_data(ttl=600)
def load_car_model() -> pd.DataFrame:
    conn = MySQLdb.connect(connect_timeout=50, **DB_CONFIG)
    df = pd.read_sql_query(f"SELECT * FROM {CAR_MODEL_TABLE};", conn).fillna("")
    conn.close()
    return df

@st.cache_data(ttl=600)
def load_ev_register(region: str) -> pd.DataFrame:
    conn = MySQLdb.connect(connect_timeout=50, **DB_CONFIG)
    if region == "전국":
        sql = """
        select c.reg_year, c.fuel_type, sum(c.reg_count) as reg_count
        from car_register c
        where c.fuel_type in ('전기', '하이브리드(휘발유+전기)')
          and c.reg_year between 2021 and 2024
        group by c.reg_year, c.fuel_type
        order by c.reg_year, c.fuel_type
        """
        df = pd.read_sql_query(sql, conn)
    else:
        sql = """
        select c.reg_year, c.fuel_type, sum(c.reg_count) as reg_count
        from car_register c
        where c.region = %s
          and c.fuel_type in ('전기', '하이브리드(휘발유+전기)')
          and c.reg_year between 2021 and 2024
        group by c.reg_year, c.fuel_type
        order by c.reg_year, c.fuel_type
        """
        df = pd.read_sql_query(sql, conn, params=[region])
    conn.close()
    return df

@st.cache_data(ttl=600)
def load_chargers_min() -> pd.DataFrame:
    conn = MySQLdb.connect(connect_timeout=50, **DB_CONFIG)
    df = pd.read_sql_query(
        f"SELECT addr, zcode FROM {EV_CHARGER_TABLE};",
        conn,
    ).fillna("")
    conn.close()
    return df
