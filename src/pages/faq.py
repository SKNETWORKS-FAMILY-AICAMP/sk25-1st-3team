# src/pages/faq.py
import math
import streamlit as st

from ..db import load_faq
from ..config import FAQ_PAGE_SIZE
from ..constants import (
    CAT_COL,
    BRAND_COL_CANDIDATES,
    QUESTION_CANDIDATES,
    ANSWER_CANDIDATES,
    FAQ_EV_KEYWORDS,
)
from ..utils import pick_col, brand_ko
from ..ui import render_pagination


def render():
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

    # 필터 시그니처가 바뀌면 page 초기화
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

    # 전체 + 키워드 미입력 시: EV 관련 질문 우선 노출
    if brand_choice == "전체" and not keyword.strip():
        text = view[q_col].astype(str)
        boost = False
        for kw in FAQ_EV_KEYWORDS:
            boost = boost | text.str.contains(kw, case=False, na=False)
        view["_boost_ev"] = boost
        view = view.sort_values(["_boost_ev"], ascending=False, kind="mergesort")

    # 현대일 때만 카테고리 버튼
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
                    if st.button(
                        cat,
                        key=f"cat_{cat}",
                        use_container_width=True,
                        type="primary" if active_cat else "secondary",
                    ):
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
            with st.expander(f"Q. {q}", expanded=False):
                st.write(a)

    render_pagination(total_pages, key_prefix="faqpg")