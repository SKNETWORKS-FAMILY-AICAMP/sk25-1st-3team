# src/pages/ev_map.py
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

from ..db import load_chargers_min
from ..constants import (
    regions,
    SIDO_FULL_KO,
    SIDO_FULL_EN,
    ZCODE_TO_SHORT,
)
from ..utils import has_hangul, normalize_addr_to_short


@st.cache_data(ttl=60 * 60 * 24)
def load_korea_sido_geojson() -> dict:
    urls = [
        "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2018/json/skorea-provinces-2018-geo.json",
        "https://cdn.jsdelivr.net/gh/southkorea/southkorea-maps@master/kostat/2018/json/skorea-provinces-2018-geo.json",
        "https://fastly.jsdelivr.net/gh/southkorea/southkorea-maps@master/kostat/2018/json/skorea-provinces-2018-geo.json",
    ]
    last_err = None
    for url in urls:
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            continue
    raise last_err


def infer_name_key(geojson: dict) -> str:
    feats = geojson.get("features", [])
    if not feats:
        raise ValueError("geojson features가 비어있습니다.")
    props = feats[0].get("properties", {})
    keys = list(props.keys())
    candidates = [
        "CTP_KOR_NM",
        "CTPRVN_NM",
        "NAME_1",
        "name",
        "NAME",
        "province",
        "sido",
        "adm_nm",
    ]
    for c in candidates:
        if c in keys:
            return c
    if keys:
        return keys[0]
    raise ValueError("geojson properties가 비어있습니다.")


def render():
    with st.sidebar:
        st.markdown("---")
        region = st.selectbox("지역 선택", regions, index=0, key="region_select_map")

    st.title("전국 전기차 충전소 지도")

    charger_df = load_chargers_min()

    if "addr" not in charger_df.columns:
        st.error("충전소 테이블에서 addr 컬럼을 찾을 수 없습니다.")
        st.write("현재 컬럼:", list(charger_df.columns))
        st.stop()

    if "zcode" not in charger_df.columns:
        charger_df["zcode"] = ""

    tmp = charger_df.copy()
    tmp["addr"] = tmp["addr"].astype(str)
    tmp["zcode"] = tmp["zcode"].astype(str)

    # 1) addr에서 먼저 시도 추정
    tmp["region_short"] = tmp["addr"].map(normalize_addr_to_short)

    # 2) addr에서 못 뽑으면 zcode 앞 2자리로 보완
    mask_none = tmp["region_short"].isna()
    if mask_none.any():
        tmp.loc[mask_none, "region_short"] = tmp.loc[mask_none, "zcode"].map(
            lambda z: ZCODE_TO_SHORT.get(str(z).strip()[:2])
        )

    tmp = tmp[tmp["region_short"].isin([r for r in regions if r != "전국"])].copy()

    if tmp.empty:
        st.error("addr/zcode로 시도 매핑이 하나도 안 됐습니다.")
        st.stop()

    df_region = tmp.groupby("region_short", as_index=False).size().rename(columns={"size": "charger_count"})
    df_region["region_short"] = df_region["region_short"].astype(str).str.strip()

    geojson = load_korea_sido_geojson()
    name_key = infer_name_key(geojson)

    feat_names = []
    for f in geojson.get("features", []):
        feat_names.append(str(f.get("properties", {}).get(name_key, "")).strip())
    feat_names = [x for x in feat_names if x]
    if not feat_names:
        st.error("GeoJSON에서 시도명 속성을 못 읽었습니다.")
        st.stop()

    geo_is_ko = any(has_hangul(x) for x in feat_names)

    def short_to_geo_name(short: str) -> str | None:
        if geo_is_ko:
            return SIDO_FULL_KO.get(short)
        return SIDO_FULL_EN.get(short)

    df_region["geo_name"] = df_region["region_short"].map(short_to_geo_name)
    df_region = df_region.dropna(subset=["geo_name"]).copy()

    known = set(feat_names)
    df_region = df_region[df_region["geo_name"].isin(known)].copy()

    if df_region.empty:
        st.error("GeoJSON의 시도명과 DB 시도명이 매칭이 안 됩니다.")
        st.stop()

    st.subheader("시도별 충전소 개수")
    st.dataframe(
        df_region[["region_short", "charger_count"]].sort_values("charger_count", ascending=False),
        use_container_width=True,
    )

    global_min = int(df_region["charger_count"].min())
    global_max = int(df_region["charger_count"].max())

    fig_all = px.choropleth(
        df_region,
        geojson=geojson,
        locations="geo_name",
        featureidkey=f"properties.{name_key}",
        color="charger_count",
        hover_name="region_short",
        hover_data={"charger_count": True, "geo_name": False},
        labels={"charger_count": "충전소 수"},
        color_continuous_scale="Blues",
        range_color=(global_min, global_max),
    )
    fig_all.update_geos(fitbounds="locations", visible=False)
    fig_all.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=650)
    fig_all.update_traces(marker_line_width=1)

    st.markdown("## 전국 분포")
    st.plotly_chart(fig_all, width="stretch")

    # 선택 지역 확대
    if region != "전국":
        target_full = short_to_geo_name(region)
        if target_full and (target_full in known):
            sub_geo = {
                "type": "FeatureCollection",
                "features": [
                    f for f in geojson.get("features", [])
                    if str(f.get("properties", {}).get(name_key, "")).strip() == target_full
                ],
            }
            df_one = df_region[df_region["region_short"] == region].copy()
            if df_one.empty:
                df_one = pd.DataFrame([{"region_short": region, "geo_name": target_full, "charger_count": 0}])

            fig_one = px.choropleth(
                df_one,
                geojson=sub_geo,
                locations="geo_name",
                featureidkey=f"properties.{name_key}",
                color="charger_count",
                hover_name="region_short",
                hover_data={"charger_count": True, "geo_name": False},
                labels={"charger_count": "충전소 수"},
                color_continuous_scale="Blues",
                range_color=(global_min, global_max),
            )
            fig_one.update_geos(fitbounds="locations", visible=False)
            fig_one.update_layout(margin=dict(l=0, r=0, t=40, b=0), height=650)
            fig_one.update_traces(marker_line_width=1)

            st.markdown(f"## {region}")
            st.plotly_chart(fig_one, width="stretch")
        else:
            st.warning(f"{region}을(를) GeoJSON에서 찾지 못해서 확대지도를 못 그렸습니다.")