import re
import pandas as pd

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
    mapping = {
        "충청북": "충북",
        "충청남": "충남",
        "전라북": "전북",
        "전라남": "전남",
        "경상북": "경북",
        "경상남": "경남",
    }
    if first in mapping:
        return mapping[first]
    if first in {"강원", "경기"}:
        return first
    if first in {"서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "제주"}:
        return first
    return None
