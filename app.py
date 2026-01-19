import os
import math
import re
import json
import requests
import streamlit as st
import MySQLdb
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Load environment variables from .env (local development)
load_dotenv()

st.set_page_config(page_title="EV Dashboard", layout="wide")

try:
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

DB_CONFIG = dict(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    charset=os.getenv("DB_CHARSET", "utf8mb4"),
)

FAQ_PAGE_SIZE = int(os.getenv("FAQ_PAGE_SIZE", 10))
EV_PAGE_SIZE = int(os.getenv("EV_PAGE_SIZE", 50))

EV_CHARGER_TABLE = "ev_charger"
CAR_MODEL_TABLE = "car_model"

regions = [
    "전국",
    "서울",
    "부산",
    "대구",
    "인천",
    "광주",
    "대전",
    "울산",
    "세종",
    "경기",
    "강원",
    "충북",
    "충남",
    "전북",
    "전남",
    "경북",
    "경남",
    "제주",
]

CAT_COL = "sword"
BRAND_COL_CANDIDATES = ["brand", "브랜드", "BRAND"]
QUESTION_CANDIDATES = ["question", "질문", "frontFaqTitlSbc", "frontFaqTitl", "title", "제목"]
ANSWER_CANDIDATES = ["answer", "답변", "frontFaqSbc", "content", "내용"]

CAR_BRAND_CANDIDATES = ["brand", "브랜드", "maker", "manufacturer"]
CAR_NAME_CANDIDATES = ["model", "car_name", "name", "차종", "모델명"]
CAR_IMG_CANDIDATES = ["image_url", "img_url", "img", "image", "photo", "thumbnail", "link", "url"]
CAR_PRICE_CANDIDATES = ["price", "가격", "msrp", "starting_price", "base_price", "min_price", "startingPrice"]

FAQ_EV_KEYWORDS = ["전기차", "EV", "ev", "충전", "배터리"]

SIDO_FULL_KO = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전라북도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}

SIDO_FULL_EN = {
    "서울": "Seoul",
    "부산": "Busan",
    "대구": "Daegu",
    "인천": "Incheon",
    "광주": "Gwangju",
    "대전": "Daejeon",
    "울산": "Ulsan",
    "세종": "Sejong",
    "경기": "Gyeonggi",
    "강원": "Gangwon",
    "충북": "North Chungcheong",
    "충남": "South Chungcheong",
    "전북": "North Jeolla",
    "전남": "South Jeolla",
    "경북": "North Gyeongsang",
    "경남": "South Gyeongsang",
    "제주": "Jeju",
}

ZCODE_TO_SHORT = {
    "11": "서울",
    "26": "부산",
    "27": "대구",
    "28": "인천",
    "29": "광주",
    "30": "대전",
    "31": "울산",
    "36": "세종",
    "41": "경기",
    "42": "강원",
    "43": "충북",
    "44": "충남",
    "45": "전북",
    "46": "전남",
    "47": "경북",
    "48": "경남",
    "50": "제주",
}


def pick_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def brand_ko(v: str) -> str:
    s = str(v).strip().lower()
    if s == "hyundai":
        return "현대"
    if s == "kia":
        return "기아"
    return str(v).strip()


def parse_price_to_num(v: str):
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    s2 = s.replace(",", "")
    nums = re.findall(r"\d+", s2)
    return int(nums[0]) if nums else None


def has_hangul(s: str) -> bool:
    return bool(re.search(r"[가-힣]", str(s)))


def normalize_addr_to_short(addr: str) -> str | None:
    s = str(addr).strip()
    if not s:
        return None
    first = s.split()[0]
    first = (
        first.replace("특별시", "")
        .replace("광역시", "")
        .replace("특별자치시", "")
        .replace("특별자치도", "")
        .replace("도", "")
    )
    if first == "충청북":
        return "충북"
    if first == "충청남":
        return "충남"
    if first == "전라북":
        return "전북"
    if first == "전라남":
        return "전남"
    if first == "경상북":
        return "경북"
    if first == "경상남":
        return "경남"
    if first == "강원":
        return "강원"
    if first == "경기":
        return "경기"
    if first in {"서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "제주"}:
        return first
    return None


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
        select
            c.reg_year,
            c.fuel_type,
            sum(c.reg_count) as reg_count
        from car_register c
        where c.fuel_type in ('전기', '하이브리드(휘발유+전기)')
        and c.reg_year between 2021 and 2024
        group by c.reg_year, c.fuel_type
        order by c.reg_year, c.fuel_type
        """
        df = pd.read_sql_query(sql, conn)
    else:
        sql = """
        select
            c.reg_year,
            c.fuel_type,
            sum(c.reg_count) as reg_count
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


def set_page(p: int, total_pages: int):
    st.session_state.page = max(1, min(total_pages, p))


def render_pagination(total_pages: int, window: int = 9, key_prefix: str = "pg"):
    if total_pages <= 1:
        return
    cur = st.session_state.page
    half = window // 2
    start = max(1, cur - half)
    end = min(total_pages, start + window - 1)
    start = max(1, end - window + 1)
    pages = list(range(start, end + 1))

    st.markdown('<div class="pager">', unsafe_allow_html=True)
    outer = st.columns([2, 8, 2])
    with outer[1]:
        widths = [1, 1] + [1] * len(pages) + [1, 1]
        row = st.columns(widths, gap="small")
        i = 0
        with row[i]:
            if st.button("≪", key=f"{key_prefix}_first", use_container_width=True, disabled=(cur == 1), type="secondary"):
                set_page(1, total_pages)
                st.rerun()
        i += 1
        with row[i]:
            if st.button("‹", key=f"{key_prefix}_prev", use_container_width=True, disabled=(cur == 1), type="secondary"):
                set_page(cur - 1, total_pages)
                st.rerun()
        i += 1
        for p in pages:
            with row[i]:
                if st.button(str(p), key=f"{key_prefix}_{p}", use_container_width=True, type="primary" if p == cur else "secondary"):
                    set_page(p, total_pages)
                    st.rerun()
            i += 1
        with row[i]:
            if st.button("›", key=f"{key_prefix}_next", use_container_width=True, disabled=(cur == total_pages), type="secondary"):
                set_page(cur + 1, total_pages)
                st.rerun()
        i += 1
        with row[i]:
            if st.button("≫", key=f"{key_prefix}_last", use_container_width=True, disabled=(cur == total_pages), type="secondary"):
                set_page(total_pages, total_pages)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


if "page" not in st.session_state:
    st.session_state.page = 1
if "selected_cat" not in st.session_state:
    st.session_state.selected_cat = "전체"
if "ev_sort_opt" not in st.session_state:
    st.session_state.ev_sort_opt = "가격 낮은순"
if "ev_brand_label" not in st.session_state:
    st.session_state.ev_brand_label = "전체"
if "main_menu" not in st.session_state:
    st.session_state.main_menu = "전국 전기차 등록 현황"


with st.sidebar:
    st.header("메뉴")
    st.markdown('<div class="navbtn">', unsafe_allow_html=True)
    active = st.session_state.main_menu
    if st.button("전국 전기차 등록 현황", key="nav_ev_reg", use_container_width=True, type="primary" if active == "전국 전기차 등록 현황" else "secondary"):
        st.session_state.main_menu = "전국 전기차 등록 현황"
        st.session_state.page = 1
        st.rerun()
    if st.button("전국 전기차 충전소 지도", key="nav_ev_map", use_container_width=True, type="primary" if active == "전국 전기차 충전소 지도" else "secondary"):
        st.session_state.main_menu = "전국 전기차 충전소 지도"
        st.session_state.page = 1
        st.rerun()
    if st.button("기업 FAQ", key="nav_faq", use_container_width=True, type="primary" if active == "기업 FAQ" else "secondary"):
        st.session_state.main_menu = "기업 FAQ"
        st.session_state.page = 1
        st.rerun()
    if st.button("전기차 모델", key="nav_ev_model", use_container_width=True, type="primary" if active == "전기차 모델" else "secondary"):
        st.session_state.main_menu = "전기차 모델"
        st.session_state.page = 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


if st.session_state.main_menu == "전국 전기차 등록 현황":
    with st.sidebar:
        st.markdown("---")
        region = st.selectbox("지역 선택", regions, index=0, key="region_select_ev")

    st.title("전국 전기/하이브리드 등록 현황")
    df_table = load_ev_register(region)

    st.markdown("### 연도별 전기 vs 하이브리드 등록 대수")

    df_plot = df_table.copy()
    df_plot["fuel_type"] = df_plot["fuel_type"].replace({"하이브리드(휘발유+전기)": "하이브리드"})
    df_plot["reg_year"] = df_plot["reg_year"].astype(str)

    fig = px.bar(
        df_plot,
        x="reg_year",
        y="reg_count",
        color="fuel_type",
        barmode="group",
        labels={"reg_year": "연도", "reg_count": "등록 대수", "fuel_type": "연료"},
    )
    fig.update_traces(hovertemplate="연도=%{x}<br>등록=%{y:,}대<extra></extra>")
    fig.update_layout(xaxis_tickangle=0, height=450)
    st.plotly_chart(fig, width="stretch")

    st.subheader("요약 지표")
    years = sorted(df_plot["reg_year"].unique().tolist())
    if years:
        selected_year = st.selectbox("기준 연도 선택", years, index=len(years) - 1, key="year_select_metrics")
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
            st.metric("차이(하이브리드-전기)", f"{int(diff):+,}대", delta=(f"{ratio:.1f}%" if ratio is not None else None))

    st.subheader("등록 현황 표")
    st.caption(f"선택 지역: {region}")

    st.dataframe(
        df_table.rename(columns={
            "reg_year": "등록 연도",
            "fuel_type": "연료 유형",
            "reg_count": "등록 대수",
        }),
        use_container_width=True
    ) 


elif st.session_state.main_menu == "전국 전기차 충전소 지도":
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

    tmp["region_short"] = tmp["addr"].map(normalize_addr_to_short)
    mask_none = tmp["region_short"].isna()
    if mask_none.any():
        tmp.loc[mask_none, "region_short"] = tmp.loc[mask_none, "zcode"].map(lambda z: ZCODE_TO_SHORT.get(str(z).strip()[:2]))

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


elif st.session_state.main_menu == "기업 FAQ":
    st.title("FAQ")
    df = load_faq()

    brand_col = pick_col(df, BRAND_COL_CANDIDATES)
    q_col = pick_col(df, QUESTION_CANDIDATES)
    a_col = pick_col(df, ANSWER_CANDIDATES)

    missing = []
    if CAT_COL not in df.columns:
        missing.append(CAT_COL)
    if q_col is None:
        missing.append("question")
    if a_col is None:
        missing.append("answer")
    if missing:
        st.error("필수 컬럼이 없습니다: " + ", ".join(missing))
        st.stop()

    if brand_col is not None:
        df["_brand_label"] = df[brand_col].map(brand_ko)
    else:
        df["_brand_label"] = ""

    top1, top2 = st.columns([2.2, 3.8], gap="small")
    with top1:
        if brand_col is None:
            brand_choice = "전체"
            st.selectbox("브랜드", ["(brand 컬럼 없음)"], disabled=True)
        else:
            brands = sorted([x for x in df["_brand_label"].astype(str).unique().tolist() if x.strip() != ""])
            brand_choice = st.selectbox("브랜드", ["전체"] + brands, index=0)

    with top2:
        keyword = st.text_input("질문 검색", placeholder="질문 내용으로 검색")

    is_hyundai = str(brand_choice).strip() in ["현대", "hyundai", "HYUNDAI"]

    sig = (brand_choice, keyword.strip(), st.session_state.selected_cat)
    if st.session_state.get("filter_sig") != sig:
        st.session_state.filter_sig = sig
        st.session_state.page = 1

    view = df.copy()

    if brand_col is not None and brand_choice != "전체":
        view = view[view["_brand_label"].astype(str) == brand_choice]

    if keyword.strip():
        k = keyword.strip().lower()
        view = view[view[q_col].astype(str).str.lower().str.contains(k, na=False)]

    if brand_choice == "전체" and not keyword.strip():
        text = view[q_col].astype(str)
        boost = False
        for kw in FAQ_EV_KEYWORDS:
            boost = boost | text.str.contains(kw, case=False, na=False)
        view["_boost_ev"] = boost
        view = view.sort_values(["_boost_ev"], ascending=False, kind="mergesort")

    if is_hyundai:
        cats = sorted([x for x in view[CAT_COL].astype(str).unique().tolist() if x.strip() != ""])
        all_cats = ["전체"] + cats

        st.markdown('<div class="catgrid">', unsafe_allow_html=True)
        per_row = 6
        for idx in range(0, len(all_cats), per_row):
            row_cats = all_cats[idx : idx + per_row]
            cols = st.columns(len(row_cats), gap="small")
            for i, cat in enumerate(row_cats):
                active_cat = cat == st.session_state.selected_cat
                with cols[i]:
                    if st.button(cat, key=f"cat_{cat}", use_container_width=True, type="primary" if active_cat else "secondary"):
                        st.session_state.selected_cat = cat
                        st.session_state.page = 1
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.selected_cat != "전체":
            view = view[view[CAT_COL].astype(str) == st.session_state.selected_cat]
    else:
        st.session_state.selected_cat = "전체"

    total_rows = len(view)
    total_pages = max(1, math.ceil(total_rows / FAQ_PAGE_SIZE))
    st.session_state.page = max(1, min(st.session_state.page, total_pages))

    start_idx = (st.session_state.page - 1) * FAQ_PAGE_SIZE
    end_idx = start_idx + FAQ_PAGE_SIZE
    page_rows = view.iloc[start_idx:end_idx]

    st.caption(f"총 {total_rows}개 · {st.session_state.page}/{total_pages} 페이지")

    if page_rows.empty:
        st.info("조건에 맞는 질문이 없습니다.")
    else:
        for _, r in page_rows.iterrows():
            q = str(r[q_col]).strip()
            a = str(r[a_col]).strip()
            title = f"Q. {q}"
            with st.expander(title, expanded=False):
                st.write(a)

    render_pagination(total_pages, key_prefix="faqpg")


elif st.session_state.main_menu == "전기차 모델":
    st.title("전기차 모델")
    car_df = load_car_model()

    car_brand_col = pick_col(car_df, CAR_BRAND_CANDIDATES)
    car_name_col = pick_col(car_df, CAR_NAME_CANDIDATES)
    car_img_col = pick_col(car_df, CAR_IMG_CANDIDATES)
    car_price_col = pick_col(car_df, CAR_PRICE_CANDIDATES)

    miss = []
    if car_brand_col is None:
        miss.append("brand(브랜드)")
    if car_name_col is None:
        miss.append("car_name(모델명)")
    if car_img_col is None:
        miss.append("image_url(이미지 링크)")
    if miss:
        st.error("car_model에서 필요한 컬럼을 못 찾았어요: " + ", ".join(miss))
        st.stop()

    view = car_df.copy()
    if car_price_col is not None:
        view["_price_num"] = view[car_price_col].map(parse_price_to_num)
    else:
        view["_price_num"] = None

    brand_options = [
        ("전체", "전체"),
        ("현대", "hyundai"),
        ("기아", "kia"),
    ]

    f1, f2, f3 = st.columns([2.0, 2.0, 4.0], gap="small")
    with f1:
        label_list = [x[0] for x in brand_options]
        current_label = st.session_state.get("ev_brand_label", "전체")
        if current_label not in label_list:
            current_label = "전체"
        brand_label = st.selectbox("브랜드", label_list, index=label_list.index(current_label))
        st.session_state.ev_brand_label = brand_label
        brand_db = dict(brand_options)[brand_label]

    with f2:
        sort_opt = st.selectbox(
            "가격 정렬",
            ["가격 낮은순", "가격 높은순", "기본"],
            index=["가격 낮은순", "가격 높은순", "기본"].index(st.session_state.ev_sort_opt),
        )
        st.session_state.ev_sort_opt = sort_opt

    with f3:
        q = st.text_input("모델 검색", placeholder="모델명으로 검색")

    ev_sig = (brand_db, q.strip(), sort_opt)
    if st.session_state.get("ev_sig") != ev_sig:
        st.session_state.ev_sig = ev_sig
        st.session_state.page = 1

    if brand_db != "전체":
        view = view[view[car_brand_col].astype(str).str.strip().str.lower() == brand_db]

    if q.strip():
        k = q.strip().lower()
        view = view[view[car_name_col].astype(str).str.lower().str.contains(k, na=False)]

    if sort_opt == "가격 낮은순":
        view = view.sort_values("_price_num", ascending=True, na_position="last")
    elif sort_opt == "가격 높은순":
        view = view.sort_values("_price_num", ascending=False, na_position="last")

    total_rows = len(view)
    total_pages = max(1, math.ceil(total_rows / EV_PAGE_SIZE))
    st.session_state.page = max(1, min(st.session_state.page, total_pages))

    start_idx = (st.session_state.page - 1) * EV_PAGE_SIZE
    end_idx = start_idx + EV_PAGE_SIZE
    page_rows = view.iloc[start_idx:end_idx]

    st.caption(f"총 {total_rows}개 · {st.session_state.page}/{total_pages} 페이지")

    if page_rows.empty:
        st.info("조건에 맞는 모델이 없습니다.")
    else:
        cols_per_row = 3
        rows = [page_rows.iloc[i : i + cols_per_row] for i in range(0, len(page_rows), cols_per_row)]
        for r in rows:
            cols = st.columns(cols_per_row, gap="small")
            for i in range(cols_per_row):
                if i >= len(r):
                    cols[i].empty()
                    continue
                row = r.iloc[i]
                img = str(row[car_img_col]).strip()
                name = str(row[car_name_col]).strip()
                br_label = brand_ko(row[car_brand_col])
                price = ""
                if car_price_col is not None:
                    price = str(row[car_price_col]).strip()
                with cols[i]:
                    st.markdown('<div class="carcard">', unsafe_allow_html=True)
                    if img:
                        st.markdown(f'<div class="carimgbox"><img src="{img}" alt="car"/></div>', unsafe_allow_html=True)
                    else:
                        st.markdown(
                            '<div class="carimgbox" style="color:rgba(0,0,0,0.45); font-weight:800;">이미지 없음</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown(f'<div class="carname"><span class="evbolt">⚡</span>{name}</div>', unsafe_allow_html=True)
                    if price:
                        st.markdown(f'<div class="carprice">{price}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="carbrand">{br_label}</div>', unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    if total_pages > 1:
        render_pagination(total_pages, key_prefix="evpg")