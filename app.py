import streamlit as st

try:
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

from src.pages.ev_register import render as render_ev_register
from src.pages.ev_map import render as render_ev_map
from src.pages.faq import render as render_faq
from src.pages.ev_model import render as render_ev_model


st.set_page_config(page_title="EV Dashboard", layout="wide")


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


def _set_menu(menu_name: str):
    """메뉴 변경 시 공통 초기화 규칙"""
    st.session_state.main_menu = menu_name
    st.session_state.page = 1
    st.rerun()


with st.sidebar:
    st.header("메뉴")
    st.markdown('<div class="navbtn">', unsafe_allow_html=True)

    active = st.session_state.main_menu

    if st.button(
        "전국 전기차 등록 현황",
        key="nav_ev_reg",
        use_container_width=True,
        type="primary" if active == "전국 전기차 등록 현황" else "secondary",
    ):
        _set_menu("전국 전기차 등록 현황")

    if st.button(
        "전국 전기차 충전소 지도",
        key="nav_ev_map",
        use_container_width=True,
        type="primary" if active == "전국 전기차 충전소 지도" else "secondary",
    ):
        _set_menu("전국 전기차 충전소 지도")

    if st.button(
        "기업 FAQ",
        key="nav_faq",
        use_container_width=True,
        type="primary" if active == "기업 FAQ" else "secondary",
    ):
        _set_menu("기업 FAQ")

    if st.button(
        "전기차 모델",
        key="nav_ev_model",
        use_container_width=True,
        type="primary" if active == "전기차 모델" else "secondary",
    ):
        _set_menu("전기차 모델")

    st.markdown("</div>", unsafe_allow_html=True)


menu = st.session_state.main_menu

if menu == "전국 전기차 등록 현황":
    render_ev_register()

elif menu == "전국 전기차 충전소 지도":
    render_ev_map()

elif menu == "기업 FAQ":
    render_faq()

elif menu == "전기차 모델":
    render_ev_model()

else:
    st.error("알 수 없는 메뉴입니다. 사이드바에서 메뉴를 다시 선택해주세요.")
