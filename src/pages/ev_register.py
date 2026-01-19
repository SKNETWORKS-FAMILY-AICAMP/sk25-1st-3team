import pandas as pd
import streamlit as st
import plotly.express as px

from ..db import load_ev_register
from ..constants import regions


def render():
    with st.sidebar:
        st.markdown("---")
        region = st.selectbox(
            "지역 선택",
            regions,
            index=0,
            key="region_select_ev",
        )

    st.title("전국 전기/하이브리드 등록 현황")

    df_table = load_ev_register(region)

    st.markdown("### 연도별 전기 vs 하이브리드 등록 대수")

    df_plot = df_table.copy()
    df_plot["fuel_type"] = df_plot["fuel_type"].replace(
        {"하이브리드(휘발유+전기)": "하이브리드"}
    )
    df_plot["reg_year"] = df_plot["reg_year"].astype(str)

    fig = px.bar(
        df_plot,
        x="reg_year",
        y="reg_count",
        color="fuel_type",
        barmode="group",
        labels={
            "reg_year": "연도",
            "reg_count": "등록 대수",
            "fuel_type": "연료",
        },
    )
    fig.update_traces(
        hovertemplate="연도=%{x}<br>등록=%{y:,}대<extra></extra>"
    )
    fig.update_layout(xaxis_tickangle=0, height=450)

    st.plotly_chart(fig, width="stretch")

    st.subheader("요약 지표")

    years = sorted(df_plot["reg_year"].unique().tolist())
    if years:
        selected_year = st.selectbox(
            "기준 연도 선택",
            years,
            index=len(years) - 1,
            key="year_select_metrics",
        )

        tmp = df_plot[df_plot["reg_year"] == selected_year]
        ev = tmp.loc[tmp["fuel_type"] == "전기", "reg_count"].sum()
        hy = tmp.loc[tmp["fuel_type"] == "하이브리드", "reg_count"].sum()
        diff = hy - ev
        ratio = (hy / ev * 100) if ev != 0 else None

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("전기 등록 대수", f"{int(ev):,}대")
        with c2:
            st.metric("하이브리드 등록 대수", f"{int(hy):,}대")
        with c3:
            st.metric(
                "차이(하이브리드-전기)",
                f"{int(diff):+,}대",
                delta=(f"{ratio:.1f}%" if ratio is not None else None),
            )

    st.subheader("등록 현황 표")
    st.caption(f"선택 지역: {region}")

    df_show = df_table.rename(
        columns={
            "reg_year": "등록 연도",
            "fuel_type": "연료 유형",
            "reg_count": "등록 대수",
        }
    ).copy()

    df_show["등록 연도"] = df_show["등록 연도"].astype(str)

    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
    )