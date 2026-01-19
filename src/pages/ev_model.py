# src/pages/ev_model.py
import math
import streamlit as st

from ..db import load_car_model
from ..config import EV_PAGE_SIZE
from ..constants import (
    CAR_BRAND_CANDIDATES,
    CAR_NAME_CANDIDATES,
    CAR_IMG_CANDIDATES,
    CAR_PRICE_CANDIDATES,
)
from ..utils import pick_col, brand_ko, parse_price_to_num
from ..ui import render_pagination


def render():
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
        return

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
            price = str(row[car_price_col]).strip() if car_price_col is not None else ""

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
