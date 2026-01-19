# src/pages/ev_ratio.py
import streamlit as st
import pandas as pd
import MySQLdb
import altair as alt

from ..config import DB_CONFIG
from ..constants import ZCODE_TO_SHORT  # 이미 같은 매핑이 있음 :contentReference[oaicite:3]{index=3}

def render():
    # st.set_page_config(
    #     page_title="지역별 차량 대비 충전 인프라 현황",
    #     page_icon="🔌",
    #     layout="wide"
    # )

    # =============================
    # DB 연결
    # =============================
    conn = MySQLdb.connect(connect_timeout=50, **DB_CONFIG)

    # =============================
    # 1. 지역별 누적 차량 등록 대수
    # =============================
    car_query = """
    SELECT region, SUM(reg_count) AS vehicle_total
    FROM car_register
    GROUP BY region
    """
    car_df = pd.read_sql(car_query, conn)

    # =============================
    # 2. 지역별 충전기 개수
    # =============================
    charger_query = """
    SELECT zcode, COUNT(*) AS charger_total
    FROM ev_charger
    WHERE del_yn IS NULL OR del_yn = 'N'
    GROUP BY zcode
    """
    charger_df = pd.read_sql(charger_query, conn)
    conn.close()

    charger_df["region"] = charger_df["zcode"].astype(str).str.strip().str[:2].map(ZCODE_TO_SHORT)
    charger_df = charger_df.dropna(subset=["region"])

    # =============================
    # 3. 병합 + 지표 계산
    # =============================
    df = pd.merge(
        car_df,
        charger_df[["region", "charger_total"]],
        on="region",
        how="inner"
    )

    df["충전기 1대당 차량 수"] = df["vehicle_total"] / df["charger_total"]

    df = (
        df.rename(columns={
            "region": "지역",
            "vehicle_total": "누적 차량 등록 대수",
            "charger_total": "충전기 개수"
        })
        .sort_values("충전기 1대당 차량 수", ascending=False)
        .reset_index(drop=True)
    )

    df.index = df.index + 1

    # =============================
    # 상단 요약
    # =============================
    worst = df.iloc[0]
    best = df.sort_values("충전기 1대당 차량 수").iloc[0]
    avg_value = df["충전기 1대당 차량 수"].mean()

    st.title("🔌 지역별 전기·하이브리드 차량 대비 충전 인프라 현황")
    st.caption("※ 누적 기준 : 차량 등록 대수 ÷ 충전기 개수")

    st.markdown("## 📌 요약")
    c1, c2, c3 = st.columns(3)

    c1.metric("🚨 충전 인프라 가장 부족한 지역", worst["지역"], f"{worst['충전기 1대당 차량 수']:.2f} 대")
    c2.metric("✅ 충전 인프라 가장 여유로운 지역", best["지역"], f"{best['충전기 1대당 차량 수']:.2f} 대")
    c3.metric("📊 전체 평균", f"{avg_value:.2f}", "대 / 충전기")

    st.markdown("---")

    # =============================
    # 📊 가로 막대그래프 (그라데이션 적용)
    # =============================
    st.subheader("📊 충전기 1대당 차량 수 (지역별 · 누적)")

    chart_df = df.copy()

    bar = (
        alt.Chart(chart_df)
        .mark_bar()
        .encode(
            y=alt.Y("지역:N", sort="-x", title="지역"),
            x=alt.X("충전기 1대당 차량 수:Q", title="충전기 1대당 차량 수"),
            color=alt.Color(
                "충전기 1대당 차량 수:Q",
                scale=alt.Scale(scheme="reds"),
                legend=None
            ),
            tooltip=["지역", alt.Tooltip("충전기 1대당 차량 수:Q", format=".2f")]
        )
    )

    text = (
        alt.Chart(chart_df)
        .mark_text(
            align="left",
            baseline="middle",
            dx=4,
            color="black",
            fontSize=12
        )
        .encode(
            y=alt.Y("지역:N", sort="-x"),
            x=alt.X("충전기 1대당 차량 수:Q"),
            text=alt.Text("충전기 1대당 차량 수:Q", format=".2f")
        )
    )

    st.altair_chart(
        (bar + text).properties(height=420),
        use_container_width=True
    )

    st.markdown("---")

    # =============================
    # 📋 전체 테이블
    # =============================
    st.subheader("📋 지역별 차량 등록 대비 충전 인프라 현황 (전체 · 누적)")

    df_display = df.copy()
    df_display["누적 차량 등록 대수"] = df_display["누적 차량 등록 대수"].map(lambda x: f"{int(x):,}")
    df_display["충전기 개수"] = df_display["충전기 개수"].map(lambda x: f"{int(x):,}")
    df_display["충전기 1대당 차량 수"] = df_display["충전기 1대당 차량 수"].round(2)

    styled_df = (
        df_display.style
        .set_properties(**{"text-align": "left"})
        .set_table_styles([
            {"selector": "th", "props": [("text-align", "left")]},
            {"selector": "td", "props": [("text-align", "left")]}
        ])
        .background_gradient(
            subset=["충전기 1대당 차량 수"],
            cmap="Reds"
        )
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=650
    )