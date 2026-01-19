import streamlit as st

def init_session_state():
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
                set_page(1, total_pages); st.rerun()
        i += 1
        with row[i]:
            if st.button("‹", key=f"{key_prefix}_prev", use_container_width=True, disabled=(cur == 1), type="secondary"):
                set_page(cur - 1, total_pages); st.rerun()
        i += 1
        for p in pages:
            with row[i]:
                if st.button(str(p), key=f"{key_prefix}_{p}", use_container_width=True, type="primary" if p == cur else "secondary"):
                    set_page(p, total_pages); st.rerun()
            i += 1
        with row[i]:
            if st.button("›", key=f"{key_prefix}_next", use_container_width=True, disabled=(cur == total_pages), type="secondary"):
                set_page(cur + 1, total_pages); st.rerun()
        i += 1
        with row[i]:
            if st.button("≫", key=f"{key_prefix}_last", use_container_width=True, disabled=(cur == total_pages), type="secondary"):
                set_page(total_pages, total_pages); st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
