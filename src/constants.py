regions = [
    "전국","서울","부산","대구","인천","광주","대전","울산","세종","경기","강원","충북","충남","전북","전남","경북","경남","제주",
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
    "서울": "서울특별시","부산": "부산광역시","대구": "대구광역시","인천": "인천광역시","광주": "광주광역시",
    "대전": "대전광역시","울산": "울산광역시","세종": "세종특별자치시","경기": "경기도","강원": "강원도",
    "충북": "충청북도","충남": "충청남도","전북": "전라북도","전남": "전라남도","경북": "경상북도",
    "경남": "경상남도","제주": "제주특별자치도",
}

SIDO_FULL_EN = {
    "서울": "Seoul","부산": "Busan","대구": "Daegu","인천": "Incheon","광주": "Gwangju",
    "대전": "Daejeon","울산": "Ulsan","세종": "Sejong","경기": "Gyeonggi","강원": "Gangwon",
    "충북": "North Chungcheong","충남": "South Chungcheong","전북": "North Jeolla","전남": "South Jeolla",
    "경북": "North Gyeongsang","경남": "South Gyeongsang","제주": "Jeju",
}

ZCODE_TO_SHORT = {
    "11": "서울","26": "부산","27": "대구","28": "인천","29": "광주","30": "대전",
    "31": "울산","36": "세종","41": "경기","42": "강원","43": "충북","44": "충남",
    "45": "전북","46": "전남","47": "경북","48": "경남","50": "제주",
}