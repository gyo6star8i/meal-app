"""
급식알리미 - Streamlit 웹 버전
meal.py의 급식 조회/칼로리 분석 기능을 웹에서 제공합니다.
"""
import sys, types, re, calendar, json
from datetime import datetime, timedelta

# ──────────────────────────────────────────────────────────
# tkinter 목업 (서버 환경에서 meal.py 임포트를 위해 필요)
# ──────────────────────────────────────────────────────────
def _setup_tkinter_mock():
    class _W:
        def __init__(self, *a, **k): pass
        def __getattr__(self, n): return _W()
        def __call__(self, *a, **k): return _W()
        def winfo_children(self): return []
        def winfo_width(self): return 0
        def winfo_height(self): return 0

    class _SV:
        def __init__(self, *a, **k): self._v = ""
        def set(self, v): self._v = v
        def get(self): return self._v

    tk = types.ModuleType("tkinter")
    for n in ["Tk", "Frame", "Label", "Button", "Canvas", "Toplevel",
              "Scrollbar", "Listbox", "Entry", "Text", "LabelFrame"]:
        setattr(tk, n, _W)

    tk.StringVar = _SV
    tk.IntVar = _SV
    tk.BooleanVar = _SV

    for n in ["END", "VERTICAL", "HORIZONTAL", "N", "S", "E", "W",
              "NW", "NE", "SW", "SE", "LEFT", "RIGHT", "TOP", "BOTTOM",
              "CENTER", "BOTH", "X", "Y", "WORD", "NORMAL", "DISABLED",
              "ACTIVE", "FLAT", "GROOVE", "RAISED", "RIDGE", "SUNKEN"]:
        setattr(tk, n, n.lower())

    ttk = types.ModuleType("tkinter.ttk")
    for n in ["Separator", "Scrollbar", "Combobox", "Treeview",
              "Frame", "Label", "Button", "Entry"]:
        setattr(ttk, n, _W)
    tk.ttk = ttk

    mb = types.ModuleType("tkinter.messagebox")
    mb.showinfo = mb.showerror = mb.showwarning = mb.askyesno = lambda *a, **k: None
    tk.messagebox = mb

    sys.modules["tkinter"] = tk
    sys.modules["tkinter.ttk"] = ttk
    sys.modules["tkinter.messagebox"] = mb


_setup_tkinter_mock()

# ──────────────────────────────────────────────────────────
# meal.py에서 필요한 부분만 임포트
# ──────────────────────────────────────────────────────────
import streamlit as st

try:
    from meal import (
        SCHOOL_LIST,
        SCHOOL_BY_OFFICE_TYPE,
        OFFICE_INFO,
        DEFAULT_SCHOOL,
        fetch_meal,
        fetch_week_meals,
        _fetch_all_pages,
        _analyze,
        RECOMMENDED_LUNCH_KCAL,
        RECOMMENDED_DAILY_KCAL,
        KCAL_MARGIN,
        API_KEY,
        MEAL_NAMES,
    )
except Exception as e:
    st.error(f"meal.py 로드 실패: {e}")
    st.stop()

# ──────────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────────
SCHOOL_TYPES = ["유치원", "초등학교", "중학교", "고등학교", "특수학교", "기관"]

TYPE_COLORS = {
    "유치원":   "#F48FB1",
    "초등학교": "#66BB6A",
    "중학교":   "#42A5F5",
    "고등학교": "#AB47BC",
    "특수학교": "#78909C",
    "기관":     "#FF8A65",
}

WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]

# ──────────────────────────────────────────────────────────
# 유틸 함수
# ──────────────────────────────────────────────────────────
def date_label(d: datetime) -> str:
    wd = WEEKDAY_KR[d.weekday()]
    return d.strftime(f"%Y년 %m월 %d일 ({wd})")


def _kcal_value(kcal_str: str) -> float:
    try:
        return float(re.search(r"[\d.]+", kcal_str).group())
    except Exception:
        return 0.0


def _judge(val: float, rec: int) -> tuple:
    """(status, icon, color) 반환"""
    lo, hi = rec * (1 - KCAL_MARGIN), rec * (1 + KCAL_MARGIN)
    if val < lo:
        return "에너지 부족", "🔵", "#2196F3"
    elif val > hi:
        return "에너지 과다", "🔴", "#E53935"
    else:
        return "에너지 적절", "🟢", "#43A047"


def school_color(school: dict) -> str:
    return TYPE_COLORS.get(school.get("type", "초등학교"), "#66BB6A")


# ──────────────────────────────────────────────────────────
# 학교알리미 급식 실시 현황 API 연동
# ──────────────────────────────────────────────────────────
_SCHOOLINFO_KEY = "d15d9706ca1747bb946e0365191f7140"

# NEIS 교육청코드 → 학교알리미 시도코드 매핑
_NEIS_TO_SIDO = {
    "B10": "11", "C10": "26", "D10": "27", "E10": "28",
    "F10": "29", "G10": "30", "H10": "31", "I10": "36",
    "J10": "41", "K10": "51", "M10": "43", "N10": "44",
    "P10": "52", "Q10": "46", "R10": "47", "S10": "48",
    "T10": "50",
}

# 학교급 코드 매핑 (학교알리미 기준)
_SCHOOL_TYPE_TO_KND = {
    "초등학교": "02", "중학교": "03", "고등학교": "04", "특수학교": "05",
}

# 학교명 키워드 → 시군구 코드 후보 (sido별)
_SGG_MAP = {
    "11": {  # 서울
        "강남": ["11680"], "강동": ["11740"], "강북": ["11305"], "강서": ["11500"],
        "관악": ["11620"], "광진": ["11215"], "구로": ["11530"], "금천": ["11545"],
        "노원": ["11350"], "도봉": ["11320"], "동대문": ["11230"], "동작": ["11590"],
        "마포": ["11440"], "서대문": ["11410"], "서초": ["11650"], "성동": ["11200"],
        "성북": ["11290"], "송파": ["11710"], "양천": ["11470"], "영등포": ["11560"],
        "용산": ["11170"], "은평": ["11380"], "종로": ["11110"], "중구": ["11140"],
        "중랑": ["11260"],
    },
    "26": {  # 부산
        "강서": ["26440"], "금정": ["26410"], "기장": ["26710"], "남구": ["26290"],
        "동구": ["26170"], "동래": ["26260"], "북구": ["26320"], "사상": ["26530"],
        "사하": ["26380"], "서구": ["26140"], "수영": ["26500"], "연제": ["26470"],
        "영도": ["26200"], "중구": ["26110"], "해운대": ["26350"],
    },
    "27": {  # 대구
        "달성": ["27710"], "달서": ["27290"], "남구": ["27200"], "동구": ["27140"],
        "북구": ["27230"], "서구": ["27170"], "수성": ["27260"], "중구": ["27110"],
    },
    "28": {  # 인천
        "강화": ["28710"], "계양": ["28245"], "남동": ["28200"], "미추홀": ["28177"],
        "부평": ["28237"], "서구": ["28260"], "연수": ["28185"], "옹진": ["28720"],
        "중구": ["28110"],
    },
    "29": {  # 광주
        "광산": ["29200"], "남구": ["29155"], "동구": ["29110"], "북구": ["29170"],
        "서구": ["29140"],
    },
    "30": {  # 대전
        "대덕": ["30230"], "동구": ["30110"], "서구": ["30170"], "유성": ["30200"],
        "중구": ["30140"],
    },
    "31": {  # 울산
        "남구": ["31140"], "동구": ["31170"], "북구": ["31200"], "울주": ["31710"],
        "중구": ["31110"],
    },
    "36": {"세종": ["36110"]},  # 세종
    "41": {  # 경기
        "가평": ["41820"], "고양": ["41281", "41285", "41287"],
        "과천": ["41290"], "광명": ["41210"], "광주": ["41610"],
        "구리": ["41310"], "군포": ["41410"], "김포": ["41570"],
        "남양주": ["41360"], "동두천": ["41250"],
        "부천": ["41192", "41194", "41196"],
        "성남": ["41131", "41133", "41135"],
        "수원": ["41111", "41113", "41115", "41117"],
        "시흥": ["41390"], "안산": ["41271", "41273"],
        "안성": ["41550"], "안양": ["41171", "41173"],
        "양주": ["41630"], "양평": ["41830"], "여주": ["41670"],
        "연천": ["41800"], "오산": ["41370"],
        "용인": ["41461", "41463", "41465"],
        "의왕": ["41430"], "의정부": ["41150"], "이천": ["41500"],
        "파주": ["41480"], "평택": ["41220"], "포천": ["41650"],
        "하남": ["41450"], "화성": ["41591", "41593", "41595", "41597"],
    },
    "43": {  # 충북
        "괴산": ["43760"], "단양": ["43800"], "보은": ["43720"], "영동": ["43740"],
        "옥천": ["43730"], "음성": ["43770"], "제천": ["43150"], "증평": ["43745"],
        "진천": ["43750"], "청주": ["43111", "43112", "43113", "43114"], "충주": ["43130"],
    },
    "44": {  # 충남
        "계룡": ["44250"], "공주": ["44150"], "금산": ["44710"], "논산": ["44230"],
        "당진": ["44270"], "보령": ["44180"], "부여": ["44760"], "서산": ["44210"],
        "서천": ["44770"], "아산": ["44200"], "예산": ["44810"], "청양": ["44790"],
        "천안": ["44130", "44131"], "태안": ["44825"], "홍성": ["44800"],
    },
    "46": {  # 전남
        "강진": ["46810"], "고흥": ["46770"], "곡성": ["46720"], "광양": ["46230"],
        "구례": ["46730"], "나주": ["46170"], "담양": ["46710"], "목포": ["46110"],
        "무안": ["46840"], "보성": ["46780"], "순천": ["46150"], "신안": ["46920"],
        "여수": ["46130"], "영광": ["46870"], "영암": ["46830"], "완도": ["46900"],
        "장성": ["46880"], "장흥": ["46800"], "진도": ["46910"], "함평": ["46860"],
        "해남": ["46820"], "화순": ["46790"],
    },
    "47": {  # 경북
        "경산": ["47290"], "경주": ["47130"], "고령": ["47830"], "구미": ["47190"],
        "군위": ["47720"], "김천": ["47150"], "문경": ["47280"], "봉화": ["47920"],
        "상주": ["47250"], "성주": ["47840"], "안동": ["47170"], "영덕": ["47770"],
        "영양": ["47760"], "영주": ["47210"], "영천": ["47230"], "예천": ["47900"],
        "울릉": ["47940"], "울진": ["47930"], "의성": ["47730"], "청도": ["47820"],
        "청송": ["47750"], "칠곡": ["47850"], "포항": ["47110", "47111"],
    },
    "48": {  # 경남
        "거제": ["48310"], "거창": ["48880"], "고성": ["48820"], "김해": ["48250"],
        "남해": ["48840"], "밀양": ["48270"], "산청": ["48860"], "사천": ["48240"],
        "양산": ["48330"], "의령": ["48720"], "진주": ["48170"], "창녕": ["48740"],
        "창원": ["48120", "48121", "48123", "48125", "48127"],
        "통영": ["48220"], "하동": ["48850"], "함안": ["48730"],
        "함양": ["48870"], "합천": ["48890"],
    },
    "50": {"서귀포": ["50130"], "제주": ["50110"]},  # 제주
    "51": {  # 강원
        "강릉": ["51150"], "고성": ["51820"], "동해": ["51170"], "삼척": ["51230"],
        "속초": ["51210"], "양구": ["51800"], "양양": ["51830"], "영월": ["51750"],
        "원주": ["51130"], "인제": ["51810"], "정선": ["51770"], "철원": ["51780"],
        "춘천": ["51110"], "태백": ["51190"], "평창": ["51760"],
        "홍천": ["51720"], "화천": ["51790"], "횡성": ["51730"],
    },
    "52": {  # 전북
        "고창": ["52790"], "군산": ["52130"], "김제": ["52210"], "남원": ["52190"],
        "무주": ["52730"], "부안": ["52800"], "순창": ["52770"], "완주": ["52710"],
        "익산": ["52140"], "임실": ["52750"], "장수": ["52740"],
        "전주": ["52110", "52111"], "정읍": ["52180"], "진안": ["52720"],
    },
}


def _clean_school_name(name: str) -> str:
    """괄호 접두사·학교급 접미사 제거 후 정규화"""
    import re as _re
    name = _re.sub(r"^\([^)]+\)\s*", "", name)   # (경북), (경기) 등 괄호 접두사 제거
    for suffix in ["초등학교", "중학교", "고등학교", "특수학교", "유치원"]:
        name = name.replace(suffix, "")
    return name.strip()


def _get_sgg_candidates(school_name: str, sido: str) -> list:
    """학교명 키워드로 시군구코드 후보 추출 (긴 키워드 우선).
    매칭 없으면 해당 sido의 전체 sgg 코드 목록을 반환(fallback).
    """
    sgg_map = _SGG_MAP.get(sido, {})
    clean = _clean_school_name(school_name)
    for kw, codes in sorted(sgg_map.items(), key=lambda x: -len(x[0])):
        if kw in clean:
            return codes
    # fallback: 시/군/구 이름이 학교명에 없으면 시도 내 전체 sgg 순회
    all_codes: list = []
    for codes in sgg_map.values():
        for c in codes:
            if c not in all_codes:
                all_codes.append(c)
    return all_codes


def _get_city_from_neis(school_code: str, office: str) -> str:
    """NEIS schoolInfo API로 학교 주소를 가져와 시/군/구 이름 추출"""
    import requests as _req, urllib3 as _u3
    _u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)
    try:
        url = (
            f"https://open.neis.go.kr/hub/schoolInfo"
            f"?KEY={API_KEY}&Type=json&pIndex=1&pSize=1"
            f"&ATPT_OFCDC_SC_CODE={office}&SD_SCHUL_CODE={school_code}"
        )
        r = _req.get(url, verify=False, timeout=8)
        info = r.json()
        rows = (info.get("schoolInfo", [{}])[1] or {}).get("row", [])
        if rows:
            addr = rows[0].get("ORG_RDNMA", "") or rows[0].get("ORG_TELNO", "")
            # 주소 예: "경상북도 상주시 ..." → 첫 두 단어 중 시/군/구 추출
            parts = addr.split()
            for part in parts[1:3]:
                city = part.replace("시", "").replace("군", "").replace("구", "")
                if len(city) >= 2:
                    return city
    except Exception:
        pass
    return ""


def _fetch_schoolinfo_meal(school_name: str, office: str,
                            school_type: str, pban_yr: int,
                            school_code: str = "") -> dict | None:
    """학교알리미 급식 실시 현황 API 조회 (apiType=34)"""
    import requests as _req, urllib3 as _u3
    _u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)

    sido = _NEIS_TO_SIDO.get(office, "")
    knd  = _SCHOOL_TYPE_TO_KND.get(school_type, "02")
    if not sido:
        return None

    # 1단계: 학교명 키워드 매칭
    sgg_list = _get_sgg_candidates(school_name, sido)

    # 2단계: 키워드 매칭 실패 시 NEIS 주소 API로 도시명 보완
    if not sgg_list and school_code:
        city_kw = _get_city_from_neis(school_code, office)
        if city_kw:
            sgg_map = _SGG_MAP.get(sido, {})
            for kw, codes in sorted(sgg_map.items(), key=lambda x: -len(x[0])):
                if kw in city_kw or city_kw in kw:
                    sgg_list = codes
                    break

    # 3단계: 그래도 없으면 시도 내 전체 sgg 순회 (fallback)
    if not sgg_list:
        sgg_map = _SGG_MAP.get(sido, {})
        seen: list = []
        for codes in sgg_map.values():
            for c in codes:
                if c not in seen:
                    seen.append(c)
        sgg_list = seen

    if not sgg_list:
        return None

    # 비교용 정제된 학교명
    clean_target = _clean_school_name(school_name)

    for sgg in sgg_list:
        url = (
            "https://www.schoolinfo.go.kr/openApi.do"
            f"?apiKey={_SCHOOLINFO_KEY}&Type=json&pbanYr={pban_yr}"
            f"&schulKndCode={knd}&apiType=34&sidoCode={sido}&sggCode={sgg}"
        )
        try:
            r = _req.get(url, verify=False, timeout=10)
            data = r.json()
            if data.get("resultCode") == "success":
                for item in data.get("list", []):
                    nm = item.get("SCHUL_NM", "")
                    clean_nm = _clean_school_name(nm)
                    if (clean_nm == clean_target
                            or school_name in nm
                            or nm in school_name
                            or clean_target in clean_nm):
                        return item
        except Exception:
            continue
    return None


# ──────────────────────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="급식알리미",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    .meal-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .meal-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
    }
    .meal-menu {
        font-size: 15px;
        line-height: 1.9;
        color: #2C3A2E;
        white-space: pre-line;
    }
    .kcal-badge {
        display: inline-block;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 13px;
        font-weight: bold;
        margin-top: 8px;
    }
    .status-box {
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        margin: 8px 0;
    }
    .week-day-header {
        text-align: center;
        border-radius: 8px;
        padding: 5px;
        font-weight: bold;
        font-size: 14px;
    }
    .week-meal-text {
        font-size: 13px;
        line-height: 1.7;
        white-space: pre-line;
        margin-top: 6px;
    }
    .no-meal {
        color: #BBBBBB;
        font-size: 13px;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────
# 세션 상태 초기화
# ──────────────────────────────────────────────────────────
_today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

if "school" not in st.session_state:
    st.session_state.school = DEFAULT_SCHOOL.copy()
if "cur_date" not in st.session_state:
    st.session_state.cur_date = _today
if "week_monday" not in st.session_state:
    st.session_state.week_monday = _today - timedelta(days=_today.weekday())

# ──────────────────────────────────────────────────────────
# 사이드바 — 학교 선택
# ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏫 학교 설정")

    # 교육청 목록
    office_names = ["전체"] + [v["name"] for v in OFFICE_INFO.values()]
    office_by_name = {"전체": "전체", **{v["name"]: k for k, v in OFFICE_INFO.items()}}

    sel_office_name = st.selectbox("교육청", office_names)
    sel_office = office_by_name[sel_office_name]

    # 학교급
    sel_type = st.selectbox(
        "학교급",
        SCHOOL_TYPES,
        index=SCHOOL_TYPES.index(st.session_state.school.get("type", "초등학교")),
    )

    # 후보 학교 목록
    if sel_office == "전체":
        candidates = [s for s in SCHOOL_LIST if s.get("type") == sel_type]
    else:
        candidates = SCHOOL_BY_OFFICE_TYPE.get((sel_office, sel_type), [])

    # 이름 검색
    query = st.text_input("학교명 검색", placeholder="학교 이름을 입력하세요...")

    if query.strip():
        filtered = [s for s in candidates if query.strip() in s["name"]]
    else:
        filtered = candidates[:300]

    if filtered:
        school_options = [s["name"] for s in filtered]
        cur_name = st.session_state.school.get("name", "")
        default_i = school_options.index(cur_name) if cur_name in school_options else 0

        sel_name = st.selectbox("학교 선택", school_options, index=default_i)
        sel_school_obj = next(s for s in filtered if s["name"] == sel_name)

        st.caption(f"검색 결과: {len(filtered)}개" + (" (최대 300개 표시)" if len(candidates) > 300 and not query.strip() else ""))

        if st.button("✅ 이 학교로 보기", use_container_width=True, type="primary"):
            st.session_state.school = sel_school_obj.copy()
            st.rerun()
    else:
        st.info("검색 결과가 없습니다.")

    st.divider()

    sc = st.session_state.school
    color = school_color(sc)
    st.markdown(
        f"<div style='background:{color}22;border-left:3px solid {color};"
        f"border-radius:6px;padding:8px 12px;'>"
        f"<b style='color:{color};'>현재 학교</b><br>{sc['name']}</div>",
        unsafe_allow_html=True,
    )
    st.caption("NEIS 학교급식 공개 API 제공")

# ──────────────────────────────────────────────────────────
# 메인 영역
# ──────────────────────────────────────────────────────────
school = st.session_state.school
clr = school_color(school)

# 헤더
st.markdown(
    f"<h1 style='color:{clr};margin-bottom:0;'>🍱 {school['name']} 급식알리미</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='color:#888;margin-top:4px;'>"
    f"BY LEE YANG-HO · NEIS 급식 공개 API</p>",
    unsafe_allow_html=True,
)

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📅 오늘의 급식", "📋 주간 급식", "📊 월별 칼로리 분석", "🥗 오늘의 급식 및 맞춤 식단 추천"])

# ══════════════════════════════════════════════════════════
# TAB 1: 오늘의 급식
# ══════════════════════════════════════════════════════════
with tab1:
    # 날짜 내비게이션
    c1, c2, c3, c4, c5 = st.columns([1.2, 1, 3, 1, 1.2])
    with c1:
        if st.button("◀ 어제", use_container_width=True, key="t1_prev"):
            st.session_state.cur_date -= timedelta(days=1)
            st.rerun()
    with c2:
        if st.button("오늘", use_container_width=True, key="t1_today"):
            st.session_state.cur_date = _today
            st.rerun()
    with c3:
        st.markdown(
            f"<h3 style='text-align:center;color:{clr};margin:0;line-height:2.2;'>"
            f"{date_label(st.session_state.cur_date)}</h3>",
            unsafe_allow_html=True,
        )
    with c4:
        pass
    with c5:
        if st.button("내일 ▶", use_container_width=True, key="t1_next"):
            st.session_state.cur_date += timedelta(days=1)
            st.rerun()

    # 날짜 직접 선택
    picked = st.date_input(
        "날짜 선택",
        value=st.session_state.cur_date.date(),
        label_visibility="collapsed",
        key="t1_datepick",
    )
    picked_dt = datetime.combine(picked, datetime.min.time())
    if picked_dt != st.session_state.cur_date:
        st.session_state.cur_date = picked_dt
        st.rerun()

    st.markdown("---")

    # 급식 조회
    with st.spinner(f"⏳ {school['name']} 급식 불러오는 중..."):
        meal_data, meal_err = fetch_meal(
            st.session_state.cur_date,
            school["office"],
            school["code"],
        )

    if meal_err:
        st.error(f"❌ 오류 발생\n\n{meal_err}")

    elif not meal_data:
        st.markdown(
            f"<div class='meal-card' style='background:#F5F5F5;'>"
            f"<div class='meal-title' style='color:#9E9E9E;'>🚫 급식 없는 날</div>"
            f"<div class='meal-menu' style='color:#AAAAAA;'>"
            f"{date_label(st.session_state.cur_date)}은<br>"
            f"급식을 운영하지 않는 날입니다.<br><br>"
            f"주말 · 방학 · 재량휴업일일 수 있어요!</div></div>",
            unsafe_allow_html=True,
        )

    else:
        # ── 점심 (메인) ──
        lunch = meal_data.get(2)
        if lunch:
            kcal_val = _kcal_value(lunch.get("kcal", ""))
            rec = RECOMMENDED_LUNCH_KCAL.get(school.get("type", "초등학교"), 650)
            status, s_icon, s_color = _judge(kcal_val, rec) if kcal_val > 0 else ("", "", clr)
            kcal_clean = re.sub(r'\(해당.*?\)', '', lunch.get("kcal", "")).strip()

            col_menu, col_info = st.columns([3, 2])

            with col_menu:
                st.markdown(
                    f"<div class='meal-card' style='border-left:5px solid {clr};'>"
                    f"<div class='meal-title' style='color:{clr};'>🍚 점심 급식</div>"
                    f"<div class='meal-menu'>{lunch['menu']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                if lunch.get("orplc"):
                    with st.expander("🌿 원산지 정보"):
                        orplc = lunch["orplc"].replace("<br/>", "\n").replace("/", "\n").strip()
                        st.text(orplc)

            with col_info:
                if kcal_val > 0:
                    st.metric("🔥 열량", kcal_clean)
                    st.markdown(
                        f"<div class='status-box' style='background:{s_color}22;border:2px solid {s_color};'>"
                        f"<span style='color:{s_color};'>{s_icon} {status}</span></div>",
                        unsafe_allow_html=True,
                    )
                    ratio = kcal_val / rec * 100
                    st.progress(min(ratio / 150, 1.0))
                    st.caption(f"권장 {rec} kcal 대비 {ratio:.0f}%")

                # 밥풀이 캐릭터 자리
                if kcal_val > 0:
                    if status == "에너지 적절":
                        face = "😊"
                        msg = "냠냠~ 딱 좋아요!"
                    elif status == "에너지 부족":
                        face = "😢"
                        msg = "조금 부족해요..."
                    else:
                        face = "😅"
                        msg = "오늘은 좀 많네요!"
                    st.markdown(
                        f"<div style='text-align:center;margin-top:16px;'>"
                        f"<div style='font-size:60px;'>{face}</div>"
                        f"<div style='background:#FFFDE7;border:1px solid #FFD54F;"
                        f"border-radius:20px;padding:6px 12px;display:inline-block;"
                        f"font-size:14px;font-weight:bold;color:{s_color};margin-top:8px;'>"
                        f"{msg}</div></div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.info(f"🚫 {date_label(st.session_state.cur_date)}에 점심 급식 정보가 없습니다.")

        # ── 아침 / 저녁 (있는 경우) ──
        extra = [(mc, meal_data[mc]) for mc in [1, 3] if mc in meal_data]
        if extra:
            st.markdown("---")
            st.markdown("#### 🍽️ 아침 / 저녁 급식")
            cols = st.columns(len(extra))
            MEAL_ICONS = {1: "☀️", 2: "🍚", 3: "🌙"}
            MEAL_BG    = {1: "#FFF8F0", 2: "#F0F7EE", 3: "#F0F0FF"}
            MEAL_CLR   = {1: "#FF8C00", 2: clr, 3: "#5C6BC0"}

            for idx, (mc, md) in enumerate(extra):
                with cols[idx]:
                    name = MEAL_NAMES.get(mc, "급식")
                    icon = MEAL_ICONS[mc]
                    bg   = MEAL_BG[mc]
                    mc_color = MEAL_CLR[mc]
                    kcal_e = re.sub(r'\(해당.*?\)', '', md.get("kcal", "")).strip()
                    st.markdown(
                        f"<div class='meal-card' style='background:{bg};"
                        f"border-left:4px solid {mc_color};'>"
                        f"<div class='meal-title' style='color:{mc_color};'>{icon} {name} 급식</div>"
                        f"<div class='meal-menu'>{md['menu']}</div>"
                        f"{'<div style=\"color:#888;font-size:13px;margin-top:6px;\">🔥 열량: ' + kcal_e + '</div>' if kcal_e else ''}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        # ── 학교알리미 급식 운영 현황 ────────────────────────────────
        st.markdown("---")
        with st.expander("🏫 학교알리미 급식 운영 현황 (연도별)", expanded=False):
            st.caption("출처: 학교알리미 공개 OpenAPI (schoolinfo.go.kr) · 보건/복지 > 급식 실시 현황")

            _si_yr_options = [2025, 2024, 2023]
            _si_col_yr, _si_col_btn = st.columns([2, 1])
            with _si_col_yr:
                _si_sel_yr = st.selectbox(
                    "공시 연도",
                    _si_yr_options,
                    index=0,
                    key="t1_si_year",
                    label_visibility="collapsed",
                )
            with _si_col_btn:
                _si_fetch_btn = st.button(
                    "📡 조회", key="t1_si_fetch", use_container_width=True
                )

            if _si_fetch_btn:
                with st.spinner(f"학교알리미 조회 중… ({school['name']})"):
                    _si_data = _fetch_schoolinfo_meal(
                        school["name"], school["office"],
                        school.get("type", "초등학교"), _si_sel_yr,
                        school_code=school.get("code", ""),
                    )
                if _si_data:
                    st.session_state["t1_si_data"] = _si_data
                    st.session_state["t1_si_yr"] = _si_sel_yr
                    st.session_state.pop("t1_si_not_found", None)
                else:
                    st.session_state["t1_si_not_found"] = True

            if st.session_state.get("t1_si_not_found"):
                st.warning(
                    f"⚠️ '{school['name']}' 급식 운영 현황을 학교알리미에서 찾지 못했습니다.\n\n"
                    "지원되는 학교: 시/군/구 이름이 포함된 학교명 (예: 광명북초, 강남중학교)"
                )

            if "t1_si_data" in st.session_state:
                _d = st.session_state["t1_si_data"]
                _yr = st.session_state.get("t1_si_yr", 2025)

                # 운영방식 배지 색상
                _oper = _d.get("OPER_MET_CODE", "")
                _oper_color = "#2196F3" if _oper == "직영" else "#FF9800"

                st.markdown(
                    f"<div style='background:#F8F9FA;border-radius:12px;"
                    f"padding:14px 18px;border-left:4px solid {clr};margin:8px 0;'>"
                    f"<b style='color:{clr};font-size:16px;'>"
                    f"📋 {_yr}년도 급식 운영 현황</b>"
                    f"<span style='margin-left:10px;background:{_oper_color}22;"
                    f"color:{_oper_color};border:1px solid {_oper_color}55;"
                    f"border-radius:20px;padding:2px 10px;font-size:13px;font-weight:bold;'>"
                    f"🏷️ {_oper}</span></div>",
                    unsafe_allow_html=True,
                )

                # 핵심 지표 4개
                _si_c1, _si_c2, _si_c3, _si_c4 = st.columns(4)
                _ks_rate = _d.get("KS_RATE", 0)
                _mlsv = _d.get("MLSV_STDNT_FGR", 0)
                _tot  = _d.get("HAKSAENGSU_TOT", 0)
                _ntr  = _d.get("NTRST_FGR", 0)
                _cook = _d.get("COOK_FGR", 0)
                _cooas = _d.get("COOAS_FGR", 0)

                with _si_c1:
                    st.metric("🍽️ 급식률", f"{_ks_rate}%")
                with _si_c2:
                    st.metric("👨‍🎓 급식 학생", f"{_mlsv}명")
                with _si_c3:
                    st.metric("👩‍🍳 영양사", f"{_ntr}명")
                with _si_c4:
                    st.metric("🧑‍🍳 조리인력",
                              f"{_cook + _cooas}명",
                              help=f"조리사 {_cook}명 + 조리보조원 {_cooas}명")

                # 급식률 프로그레스 바
                if _ks_rate:
                    _rate_val = min(float(_ks_rate) / 100, 1.0)
                    st.progress(_rate_val, text=f"급식률 {_ks_rate}% (전체 학생 {_tot}명 중 {_mlsv}명 급식)")

                # 급식 유형 표시 (COL_1=조식, COL_4=중식, COL_5=석식, COL_6=간식)
                _meal_types = []
                if _d.get("COL_1") == "○": _meal_types.append("☀️ 조식")
                if _d.get("COL_4") == "○": _meal_types.append("🍚 중식")
                if _d.get("COL_5") == "○": _meal_types.append("🌙 석식")
                if _d.get("COL_6") == "○": _meal_types.append("🍎 간식")
                if _meal_types:
                    st.caption("급식 유형: " + "  |  ".join(_meal_types))

                # 연도별 트렌드 조회 버튼
                if st.button("📈 3년 트렌드 보기", key="t1_si_trend"):
                    with st.spinner("3년 데이터 수집 중..."):
                        import pandas as _pd
                        _trend = {}
                        for _ty in [2023, 2024, 2025]:
                            _td = _fetch_schoolinfo_meal(
                                school["name"], school["office"],
                                school.get("type", "초등학교"), _ty,
                                school_code=school.get("code", ""),
                            )
                            if _td:
                                try:
                                    _trend[str(_ty)] = {
                                        "급식학생수": int(_td.get("MLSV_STDNT_FGR") or 0),
                                        "전체학생수": int(_td.get("HAKSAENGSU_TOT") or 0),
                                        "급식률(%)":  float(_td.get("KS_RATE") or 0),
                                    }
                                except (TypeError, ValueError):
                                    pass
                    if _trend:
                        st.session_state["t1_si_trend"] = _trend

                if "t1_si_trend" in st.session_state:
                    _tr = st.session_state["t1_si_trend"]
                    import pandas as _pd2
                    try:
                        # 안전한 DataFrame 생성 (None/빈값 처리 포함)
                        _rows = [
                            {
                                "연도": str(_yr),
                                "급식학생수": int(_v.get("급식학생수") or 0),
                                "전체학생수": int(_v.get("전체학생수") or 0),
                                "급식률(%)":  float(_v.get("급식률(%)") or 0),
                            }
                            for _yr, _v in sorted(_tr.items())
                        ]
                        _df_trend = _pd2.DataFrame(_rows).set_index("연도")
                        st.markdown("##### 📊 연도별 급식 현황 변화")
                        st.bar_chart(_df_trend[["급식학생수", "전체학생수"]])
                        st.dataframe(
                            _df_trend.style.format({"급식률(%)": "{:.1f}%"}),
                            use_container_width=True,
                        )
                    except Exception as _e:
                        st.warning(f"트렌드 차트 생성 실패: {_e}")

# ──────────────────────────────────────────────────────────
# Groq AI 유틸 (Tab2 자동 리포트 · Tab4 AI 분석 공용)
# ──────────────────────────────────────────────────────────
def _call_groq(api_key: str, prompt: str, max_tokens: int = 1024) -> str:
    import requests as _rq, urllib3 as _u3
    _u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)
    resp = _rq.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": max_tokens},
        verify=False, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _weekly_report_with_ai(week_meals: dict, school_type: str, api_key: str) -> str:
    meals_text = "\n".join(
        f"{ymd[4:6]}월 {ymd[6:8]}일: {v.get('menu','급식없음')}"
        for ymd, v in sorted(week_meals.items()) if v.get("menu")
    )
    if not meals_text:
        return "이번 주 급식 데이터가 없습니다."

    prompt = f"""이번 주 {school_type} 급식 메뉴입니다:
{meals_text}

이번 주 급식의 영양 균형을 평가하고, 학부모에게 전달하는 간결한 주간 리포트를 3~4문장으로 작성해주세요.
부족한 영양소와 가정에서 보완할 수 있는 방법을 포함해주세요."""

    try:
        return _call_groq(api_key, prompt, max_tokens=512)
    except Exception as e:
        return f"오류: {e}"


def _get_groq_key() -> str:
    """Streamlit secrets 또는 session_state 에서 Groq API 키 반환"""
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return st.session_state.get("t4_api_key_input", "")


# ══════════════════════════════════════════════════════════
# TAB 2: 주간 급식
# ══════════════════════════════════════════════════════════
with tab2:
    monday = st.session_state.week_monday
    friday = monday + timedelta(days=4)

    w1, w2, w3 = st.columns([1.2, 4, 1.2])
    with w1:
        if st.button("◀ 이전 주", use_container_width=True, key="w_prev"):
            st.session_state.week_monday -= timedelta(weeks=1)
            st.rerun()
    with w2:
        st.markdown(
            f"<h3 style='text-align:center;color:{clr};margin:0;line-height:2.2;'>"
            f"📋 {monday.strftime('%Y년 %m월 %d일')} ~ {friday.strftime('%m월 %d일')}</h3>",
            unsafe_allow_html=True,
        )
    with w3:
        if st.button("다음 주 ▶", use_container_width=True, key="w_next"):
            st.session_state.week_monday += timedelta(weeks=1)
            st.rerun()

    if st.button("이번 주로", key="w_today"):
        st.session_state.week_monday = _today - timedelta(days=_today.weekday())
        st.rerun()

    st.markdown("---")

    with st.spinner("주간 급식 불러오는 중..."):
        week_data, week_err = fetch_week_meals(
            st.session_state.week_monday,
            school["office"],
            school["code"],
        )

    if week_err:
        st.error(f"오류: {week_err}")
    else:
        days_kr = ["월요일", "화요일", "수요일", "목요일", "금요일"]
        cols = st.columns(5)
        today_date = _today.date()

        for i, col in enumerate(cols):
            d = monday + timedelta(days=i)
            ymd = d.strftime("%Y%m%d")
            day_meal = week_data.get(ymd, {})
            is_today = (d.date() == today_date)

            with col:
                header_bg = clr if is_today else "#EEEEEE"
                header_fg = "white" if is_today else "#555555"
                st.markdown(
                    f"<div class='week-day-header' style='background:{header_bg};color:{header_fg};'>"
                    f"{days_kr[i]}<br><span style='font-size:12px;font-weight:normal;'>"
                    f"{d.month}/{d.day}</span></div>",
                    unsafe_allow_html=True,
                )

                if day_meal and day_meal.get("menu"):
                    kcal_str = day_meal.get("kcal", "")
                    kcal_val = _kcal_value(kcal_str)
                    rec = RECOMMENDED_LUNCH_KCAL.get(school.get("type", "초등학교"), 650)
                    kcal_clean = re.sub(r'\(해당.*?\)', '', kcal_str).strip()

                    if kcal_val > 0:
                        status, s_icon, s_color = _judge(kcal_val, rec)
                        kcal_html = (
                            f"<div style='font-size:12px;color:#888;margin-top:4px;'>"
                            f"🔥 {kcal_clean}</div>"
                            f"<div style='color:{s_color};font-weight:bold;font-size:12px;'>"
                            f"{s_icon} {status}</div>"
                        )
                    else:
                        kcal_html = ""

                    st.markdown(
                        f"<div class='week-meal-text'>{day_meal['menu']}</div>"
                        f"{kcal_html}",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<div class='no-meal'>급식 없음</div>",
                        unsafe_allow_html=True,
                    )

        # ── 주간 AI 리포트 (자동 생성) ────────────────────────
        _groq_key = _get_groq_key()
        _report_cache_key = f"t2_report_{monday.strftime('%Y%m%d')}"

        if _groq_key and not week_err:
            _has_meals = any(v.get("menu") for v in week_data.values())
            if _has_meals and _report_cache_key not in st.session_state:
                with st.spinner("📋 AI 주간 리포트 생성 중..."):
                    _rpt = _weekly_report_with_ai(
                        week_data, school.get("type", "초등학교"), _groq_key
                    )
                    st.session_state[_report_cache_key] = _rpt

            if _report_cache_key in st.session_state:
                st.markdown("---")
                _mon_lbl = monday.strftime("%m월 %d일")
                _fri_lbl = (monday + timedelta(days=4)).strftime("%m월 %d일")
                st.markdown(
                    f"<div class='meal-card' style='border-left:4px solid {clr};'>"
                    f"<div class='meal-title' style='color:{clr};'>"
                    f"📋 AI 주간 급식 리포트 ({_mon_lbl} ~ {_fri_lbl})</div>"
                    f"<div style='font-size:15px;line-height:1.8;color:#333;"
                    f"white-space:pre-line;'>"
                    f"{st.session_state[_report_cache_key]}</div>"
                    f"<div style='margin-top:8px;font-size:12px;color:#aaa;'>"
                    f"🤖 Groq AI (llama-3.3-70b) 분석 · 참고용 정보입니다</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

# ══════════════════════════════════════════════════════════
# TAB 3: 월별 칼로리 분석
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📊 월별 칼로리 분석")
    st.caption("해당 월의 전체 급식 칼로리를 분석하고 권장 칼로리와 비교합니다.")

    col_y, col_m = st.columns(2)
    with col_y:
        sel_year = st.selectbox(
            "연도",
            list(range(_today.year - 2, _today.year + 1)),
            index=2,
            key="m_year",
        )
    with col_m:
        sel_month = st.selectbox(
            "월",
            list(range(1, 13)),
            index=_today.month - 1,
            key="m_month",
        )

    if st.button("📊 분석 시작", type="primary", key="m_analyze"):
        from_ymd = f"{sel_year}{sel_month:02d}01"
        last_day = calendar.monthrange(sel_year, sel_month)[1]
        to_ymd   = f"{sel_year}{sel_month:02d}{last_day:02d}"

        with st.spinner(
            f"⏳ {sel_year}년 {sel_month}월 데이터 불러오는 중...\n"
            f"(API 키 없는 경우 날짜별 개별 조회로 시간이 걸릴 수 있습니다)"
        ):
            month_data, month_err = _fetch_all_pages(
                from_ymd, to_ymd,
                school["office"],
                school["code"],
            )

        if month_err:
            st.error(f"오류: {month_err}")
        elif not month_data:
            st.info("해당 월의 급식 데이터가 없습니다.")
        else:
            stype = school.get("type", "초등학교")
            meal_days, avg, status, is_full = _analyze(month_data, stype)

            rec = (
                RECOMMENDED_DAILY_KCAL.get(stype, 2300)
                if is_full
                else RECOMMENDED_LUNCH_KCAL.get(stype, 650)
            )

            STATUS_COLOR = {
                "에너지 적절": "#43A047",
                "에너지 부족": "#2196F3",
                "에너지 과다": "#E53935",
                "데이터 없음": "#888888",
            }
            STATUS_ICON = {
                "에너지 적절": "🟢",
                "에너지 부족": "🔵",
                "에너지 과다": "🔴",
                "데이터 없음": "⚪",
            }
            s_color = STATUS_COLOR.get(status, "#888")
            s_icon  = STATUS_ICON.get(status, "⚪")

            st.markdown("---")
            st.markdown(f"#### {sel_year}년 {sel_month}월 분석 결과")

            # 요약 지표
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("📅 급식일수", f"{meal_days}일")
            with m2:
                st.metric("🔥 평균 칼로리", f"{avg:.0f} kcal")
            with m3:
                st.metric("🎯 권장 칼로리", f"{rec} kcal")

            # 종합 판정
            st.markdown(
                f"<div class='status-box' style='background:{s_color}15;"
                f"border:2px solid {s_color};font-size:22px;'>"
                f"{s_icon} {status}<br>"
                f"<span style='font-size:14px;font-weight:normal;color:#555;'>"
                f"{'하루 전체' if is_full else '점심'} 기준 · 권장 {rec} kcal</span></div>",
                unsafe_allow_html=True,
            )

            if avg > 0 and rec > 0:
                ratio = avg / rec * 100
                st.progress(min(ratio / 150, 1.0))
                st.caption(f"권장량 대비 {ratio:.1f}%")

            # 일별 칼로리 차트
            import pandas as pd

            chart_rows = []
            for ymd in sorted(month_data.keys()):
                meals = month_data[ymd]
                if not meals:
                    continue
                day = int(ymd[6:8])
                if is_full:
                    v = sum(meals.values())
                else:
                    v = meals.get(2, 0)
                    if v == 0:
                        v = next(iter(meals.values()), 0)
                if v > 0:
                    chart_rows.append({"날짜": f"{day}일", "칼로리": v, "권장량": rec})

            if chart_rows:
                df = pd.DataFrame(chart_rows).set_index("날짜")
                st.markdown("##### 일별 칼로리")
                st.line_chart(df)
            else:
                st.info("차트를 그릴 데이터가 없습니다.")

    else:
        st.info("위에서 연도와 월을 선택한 뒤 '분석 시작' 버튼을 클릭하세요.")

# ══════════════════════════════════════════════════════════
# TAB 4: 맞춤 식단 추천
# ══════════════════════════════════════════════════════════
with tab4:
    # ── 식품의약품안전처 영양성분 DB 조회 ──────────────────────────
    def _fetch_nutrition_curl(food_name: str) -> dict:
        """식약처 통합식품영양성분 DB API 조회
        - requests(verify=False) 우선 → Streamlit Cloud 등 일반 환경
        - 실패 시 curl subprocess 폴백 → 학교 SSL 프록시 환경
        - 복합어 처리: 앞 수식어 2·4글자 제거 후 재검색 (근대된장국→된장국, 춘천닭갈비→닭갈비)
        """
        import subprocess, json as _json, urllib.parse, re as _re2
        # ① 식품명 정리: *, 숫자, 괄호 등 알레르기 마커 완전 제거
        clean = _re2.sub(r"\(.*?\)", "", food_name)
        clean = _re2.sub(r"[\*\[\]\d\.\s]+$", "", clean).strip()
        clean = _re2.sub(r"^\s*[\*\d]+\s*", "", clean).strip()
        if len(clean) < 2:
            return {}

        NUTRI_API_KEY = (
            "ca41a09537bd54e63daaa0dbbc32539394e7c0244d1aff5afb879d09240edeb8"
        )

        def _extract_items(data: dict) -> list:
            """한국 공공 OpenAPI 응답 형식 통합 파싱
            - 형식A: {"response":{"body":{"items":[{...},{...}]}}}
            - 형식B: {"response":{"body":{"items":{"item":[{...}]}}}}
            - 형식C: {"response":{"body":{"items":{"item":{...}}}}}  ← 단일 결과
            """
            body = (data.get("response") or {}).get("body") or {}
            raw = body.get("items")
            if not raw:
                return []
            if isinstance(raw, list):          # 형식A
                return raw
            if isinstance(raw, dict):
                inner = raw.get("item")
                if isinstance(inner, list):    # 형식B
                    return inner
                if isinstance(inner, dict):    # 형식C (단일 결과)
                    return [inner]
            return []

        def _do_query(name: str) -> dict:
            if len(name) < 2:
                return {}
            encoded = urllib.parse.quote(name)
            url = (
                "https://api.data.go.kr/openapi/tn_pubr_public_nutri_food_info_api"
                f"?serviceKey={NUTRI_API_KEY}&pageNo=1&numOfRows=5&type=json&foodNm={encoded}"
            )
            # 방법 1: requests verify=False (Streamlit Cloud / 일반 환경)
            try:
                import requests as _req, urllib3 as _u3
                _u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)
                r = _req.get(url, verify=False, timeout=8)
                items = _extract_items(r.json())
                if items:
                    return items[0]
            except Exception:
                pass
            # 방법 2: curl subprocess (학교 네트워크 SSL 프록시 환경)
            try:
                result = subprocess.run(
                    ["curl", "-k", "-s", "--max-time", "8", url],
                    capture_output=True, text=True, timeout=12,
                )
                items = _extract_items(_json.loads(result.stdout))
                if items:
                    return items[0]
            except Exception:
                pass
            return {}

        # ② 동의어/유사어 매핑 (API에 없는 음식을 가장 유사한 DB 항목으로 매핑)
        # 실험으로 확인한 API 수록 식품 기준 매핑표
        SYNONYM_MAP = {
            # 국/탕 류: 된장국→된장찌개, 국 접미사→찌개
            "된장국": "된장찌개", "근대된장국": "된장찌개", "아욱된장국": "된장찌개",
            "미역국": "미역국", "김치국": "김치찌개", "갈비탕": "갈비탕",
            # 닭 류
            "닭갈비": "닭볶음탕", "춘천닭갈비": "닭볶음탕", "닭볶음": "닭볶음탕",
            "찜닭": "닭볶음탕",
            # 튀김 류 (야채튀김→오징어튀김으로 열량 비슷)
            "야채튀김": "오징어튀김", "혼합튀김": "오징어튀김",
            "두부튀김": "두부조림",
            # 찜 류
            "고추찜": "고추장볶음", "애기고추찜": "고추장볶음",
            "계란찜": "달걀찜", "달걀찜": "달걀찜",
            # 우유·유제품
            "우유": "우유",           # 아래 hardcoded fallback 사용
            "저지방우유": "우유",
            "흰우유": "우유",
            # 요거트·샐러드
            "요거트": "요거트",       # hardcoded fallback
            "샐러드": "과일샐러드",
            "망고블루베리요거트샐러드": "과일샐러드",
            "블루베리요거트샐러드": "과일샐러드",
            # 기타
            "제육볶음": "제육볶음", "떡볶이": "떡볶이",
            "시금치나물": "시금치나물", "콩나물무침": "콩나물",
        }

        # 자주 등장하는 접미사 변환 (DB 수록 형태로)
        SUFFIX_MAP = [
            ("찌개",  "찌개"),   # 접미사가 이미 맞으면 그냥 유지
            ("볶음",  "볶음"),
            ("국",    "찌개"),   # 된장국→된장찌개
            ("찜",    "볶음"),   # 고추찜→고추볶음
            ("구이",  "구이"),
            ("조림",  "조림"),
            ("나물",  "나물"),
            ("튀김",  "오징어튀김"),  # 특정 튀김 없으면 오징어튀김
            ("갈비",  "갈비탕"),
            ("닭",    "닭볶음탕"),
        ]

        # ③ 하드코딩 폴백 (API에 없는 필수 식품 기본 영양값)
        HARDCODED = {
            "우유": {"foodNm": "우유(표준)", "enerc": "63", "prot": "3.29",
                     "fatce": "3.27", "chocdf": "4.78", "fibtg": "", "ca": "113",
                     "nat": "42", "vitc": "0"},
            "요거트": {"foodNm": "플레인요거트(표준)", "enerc": "61", "prot": "3.47",
                      "fatce": "3.25", "chocdf": "4.66", "fibtg": "", "ca": "121",
                      "nat": "46", "vitc": "0"},
        }

        # ④ 후보 목록 구성
        candidates = []

        # 동의어 매핑 우선 적용
        if clean in SYNONYM_MAP:
            syn = SYNONYM_MAP[clean]
            if syn in HARDCODED:
                return HARDCODED[syn]
            candidates.append(syn)

        # 전체 이름
        candidates.append(clean)

        # 앞 수식어 제거 (2글자씩)
        for skip in (2, 4):
            if len(clean) > skip + 2:
                trimmed = clean[skip:]
                candidates.append(trimmed)
                # 잘라낸 후에도 동의어 적용
                if trimmed in SYNONYM_MAP:
                    syn = SYNONYM_MAP[trimmed]
                    if syn in HARDCODED:
                        return HARDCODED[syn]
                    candidates.append(syn)

        # 접미사 기반 변환
        for suffix, replacement in SUFFIX_MAP:
            if clean.endswith(suffix) and clean != suffix:
                base = clean[: -len(suffix)]
                if base:
                    new_name = base + replacement
                    candidates.append(new_name)
                    # 기본 유사 음식도 후보에 추가
                    candidates.append(replacement)

        # 뒤 3·2글자 (최후 수단)
        if len(clean) > 3:
            candidates.append(clean[-3:])
        if len(clean) > 2:
            candidates.append(clean[-2:])

        # 중복 제거 (순서 유지)
        seen = set()
        unique = []
        for c in candidates:
            if c not in seen and len(c) >= 2:
                seen.add(c)
                unique.append(c)

        for candidate in unique:
            # 하드코딩 폴백 확인
            if candidate in HARDCODED:
                return HARDCODED[candidate]
            res = _do_query(candidate)
            if res:
                return res
        return {}

    # ── UI ───────────────────────────────────────────────────
    st.markdown(
        f"<div style='background:{clr};border-radius:12px;padding:16px 20px;"
        f"margin-bottom:16px;'>"
        f"<p style='color:white;margin:0;text-align:center;font-size:24px;"
        f"font-weight:700;'>🥗 오늘의 급식 및 맞춤 식단 추천</p></div>",
        unsafe_allow_html=True,
    )

    # Streamlit secrets 우선 사용 (없으면 직접 입력한 키 사용)
    try:
        _secret_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        _secret_key = ""
    final_api_key = _secret_key or st.session_state.get("t4_api_key", "")

    # secrets에 키가 없을 때만 입력창 표시
    if not _secret_key:
        with st.expander("🔑 Groq AI API 키 설정", expanded="t4_api_key" not in st.session_state):
            api_key_input = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_...",
                help="https://console.groq.com 에서 무료 발급",
                key="t4_api_key_input",
            )
            if api_key_input:
                st.session_state["t4_api_key"] = api_key_input
                final_api_key = api_key_input
                st.success("API 키가 설정되었습니다.")

    if not final_api_key:
        st.info("위에서 Groq API 키를 입력하면 맞춤 식단 분석이 시작됩니다.")
        st.markdown(
            "[🔗 무료 API 키 발급 받기](https://console.groq.com) · 하루 14,400회 무료"
        )
    else:
        # 오늘 점심 급식 조회
        with st.spinner("오늘 급식 불러오는 중..."):
            t4_data, t4_err = fetch_meal(
                st.session_state.cur_date,
                school["office"],
                school["code"],
            )

        lunch_menu = t4_data.get(2, {}).get("menu", "") if t4_data else ""
        lunch_kcal = t4_data.get(2, {}).get("kcal", "") if t4_data else ""

        # 오늘 점심 카드
        st.markdown("#### 📌 오늘 점심 급식")
        if lunch_menu:
            kcal_clean = re.sub(r'\(해당.*?\)', '', lunch_kcal).strip()
            st.markdown(
                f"<div class='meal-card' style='border-left:4px solid {clr};'>"
                f"<div class='meal-menu'>{lunch_menu}</div>"
                f"{'<div style=\"color:#888;font-size:13px;margin-top:6px;\">🔥 ' + kcal_clean + '</div>' if kcal_clean else ''}"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.info("오늘 급식 데이터가 없습니다. 날짜를 확인해주세요.")

        # ── 식약처 영양성분 DB 조회 버튼 ──────────────────────────
        if lunch_menu:
            # HTML 태그 제거 후 메뉴 아이템 파싱
            _clean = re.sub(r"<[^>]+>", "\n", lunch_menu)
            _raw_items = [x.strip() for x in _clean.replace(",", "\n").split("\n") if x.strip()]
            def _clean_food(s):
                s = re.sub(r"\(.*?\)", "", s)          # (1.2.5) 알레르기 코드 제거
                s = re.sub(r"[\*\[\]\d\.\s]+$", "", s) # 뒤쪽 * 및 숫자 제거
                s = re.sub(r"^\s*[\*\d]+\s*", "", s)   # 앞쪽 * 및 숫자 제거
                return s.strip()
            _menu_items = [
                _clean_food(x)
                for x in _raw_items
                if len(_clean_food(x)) >= 2
            ]

            if st.button("🔬 영양성분 DB 조회", key="t4_nutri_btn", use_container_width=True,
                         help="식품의약품안전처 통합식품영양성분 DB에서 각 메뉴의 영양소를 조회합니다"):
                import time as _time
                _nutri = {}
                _total = min(len(_menu_items), 9)
                prog = st.progress(0, text="식약처 영양성분 DB 조회 중...")
                for _i, _item in enumerate(_menu_items[:9]):
                    prog.progress((_i + 1) / _total, text=f"조회 중: {_item}")
                    _info = _fetch_nutrition_curl(_item)
                    if _info:
                        _nutri[_item] = _info
                    _time.sleep(0.25)   # 레이트 리밋 방지
                prog.empty()
                st.session_state["t4_nutri"] = _nutri
                if not _nutri:
                    st.session_state["t4_nutri_empty"] = True

        if st.session_state.get("t4_nutri_empty"):
            st.warning("영양성분 DB에서 오늘 메뉴 항목을 찾지 못했습니다. (식품명 불일치 또는 네트워크 오류)")
            st.session_state.pop("t4_nutri_empty", None)

        if "t4_nutri" in st.session_state and st.session_state["t4_nutri"]:
            _nutri_data = st.session_state["t4_nutri"]
            with st.expander(
                f"🔬 식약처 영양성분 DB 분석 — {len(_nutri_data)}개 메뉴 조회됨",
                expanded=True,
            ):
                st.caption(
                    "📊 출처: 식품의약품안전처 통합식품영양성분 DB (data.go.kr) · "
                    "1인 1회 제공량 기준"
                )
                for _food, _info in _nutri_data.items():
                    _kcal  = _info.get("enerc", "")
                    _prot  = _info.get("prot", "")
                    _fat   = _info.get("fatce", "")
                    _carb  = _info.get("chocdf", "")
                    _fiber = _info.get("fibtg", "")
                    _ca    = _info.get("ca", "")
                    _na    = _info.get("nat", "")
                    _vitc  = _info.get("vitc", "")
                    _db_nm = _info.get("foodNm", _food)

                    st.markdown(
                        f"<div style='background:#F8F9FA;border-radius:10px;"
                        f"padding:10px 14px;margin:6px 0;border-left:3px solid #4CAF50;'>"
                        f"<b style='font-size:15px;'>🍽️ {_food}</b>"
                        f"<span style='color:#888;font-size:12px;margin-left:8px;'>DB명: {_db_nm}</span>"
                        f"<div style='display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;'>",
                        unsafe_allow_html=True,
                    )
                    _badges = [
                        ("🔥", "열량",   _kcal,  "kcal", "#FF5722"),
                        ("💪", "단백질", _prot,  "g",    "#2196F3"),
                        ("🌾", "탄수화물",_carb, "g",    "#FF9800"),
                        ("🫙", "지방",   _fat,   "g",    "#9C27B0"),
                        ("🌿", "식이섬유",_fiber,"g",    "#4CAF50"),
                        ("🦴", "칼슘",   _ca,    "mg",   "#00BCD4"),
                        ("🧂", "나트륨", _na,    "mg",   "#607D8B"),
                        ("🍋", "비타민C",_vitc, "mg",   "#FFEB3B"),
                    ]
                    _badge_html = ""
                    for _icon, _label, _val, _unit, _color in _badges:
                        if _val:
                            _badge_html += (
                                f"<span style='background:{_color}18;color:{_color};"
                                f"border:1px solid {_color}44;border-radius:20px;"
                                f"padding:3px 9px;font-size:12px;white-space:nowrap;'>"
                                f"{_icon} {_label} <b>{_val}{_unit}</b></span>"
                            )
                    st.markdown(_badge_html + "</div></div>", unsafe_allow_html=True)

                # 합산 칼로리
                _total_kcal = 0.0
                for _info in _nutri_data.values():
                    try:
                        _total_kcal += float(_info.get("enerc", 0) or 0)
                    except (ValueError, TypeError):
                        pass
                if _total_kcal > 0:
                    st.markdown(
                        f"<div style='text-align:right;font-size:13px;color:#555;"
                        f"margin-top:4px;'>🔥 조회된 메뉴 합산 열량: "
                        f"<b>{_total_kcal:.0f} kcal</b></div>",
                        unsafe_allow_html=True,
                    )

        st.markdown("---")

        # AI 분석 버튼
        run_analysis = st.button(
            "🤖 AI 보완 식단 분석", type="primary",
            use_container_width=True, key="t4_run",
            disabled=not lunch_menu,
        )

        # ── AI 보완 식단 분석 결과 ────────────────────────────
        if run_analysis and lunch_menu:
            with st.spinner("🤖 Claude AI가 급식을 분석하는 중..."):
                result = _analyze_meal_with_ai(
                    lunch_menu, school.get("type", "초등학교"), final_api_key
                )
            st.session_state["t4_result"] = result

        if "t4_result" in st.session_state:
            result = st.session_state["t4_result"]

            if "error" in result:
                st.error(f"분석 오류: {result['error']}")
            else:
                # 영양 분석 요약
                st.markdown(
                    f"<div class='meal-card' style='background:#F0F7EE;"
                    f"border-left:4px solid {clr};'>"
                    f"<div class='meal-title' style='color:{clr};'>🤖 AI 보완 식단</div>"
                    f"<div style='color:#444;margin:4px 0;'>{result.get('nutrition_summary','')}</div>"
                    f"<div style='margin-top:8px;'>"
                    + "".join(
                        f"<span style='background:{clr}22;color:{clr};border-radius:12px;"
                        f"padding:3px 10px;font-size:13px;margin:2px;display:inline-block;'>"
                        f"⚠️ {n} 부족</span>"
                        for n in result.get("missing_nutrients", [])
                    )
                    + "</div></div>",
                    unsafe_allow_html=True,
                )

                col_d, col_s = st.columns(2)

                # 저녁 추천
                dinner = result.get("dinner", {})
                with col_d:
                    st.markdown(
                        f"<div class='meal-card' style='border-left:4px solid #5C6BC0;'>"
                        f"<div class='meal-title' style='color:#5C6BC0;'>🌙 저녁 추천</div>"
                        f"<div style='font-size:16px;font-weight:bold;margin:6px 0;'>"
                        f"{dinner.get('menu','')}</div>"
                        f"<div style='color:#888;font-size:13px;'>{dinner.get('reason','')}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # 간식 추천
                snack = result.get("snack", {})
                with col_s:
                    st.markdown(
                        f"<div class='meal-card' style='border-left:4px solid #FF8C00;'>"
                        f"<div class='meal-title' style='color:#FF8C00;'>🍎 간식 추천</div>"
                        f"<div style='font-size:16px;font-weight:bold;margin:6px 0;'>"
                        f"{snack.get('menu','')}</div>"
                        f"<div style='color:#888;font-size:13px;'>{snack.get('reason','')}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # 장보기 목록
                shopping = result.get("shopping_list", [])
                st.markdown(
                    f"<div class='meal-card'>"
                    f"<div class='meal-title'>🛒 장보기 목록 ({len(shopping)}개 항목)</div>"
                    + "".join(
                        f"<div style='padding:6px 0;border-bottom:1px solid #F0F0F0;"
                        f"font-size:15px;'>✅ {item}</div>"
                        for item in shopping
                    )
                    + "</div>",
                    unsafe_allow_html=True,
                )

                # 가족에게 공유
                share_text = f"""📋 [{date_label(st.session_state.cur_date)}] {school['name']} 급식 분석

🍚 오늘 점심:
{lunch_menu}
{('🔥 ' + re.sub(r'\\(해당.*?\\)', '', lunch_kcal).strip()) if lunch_kcal else ''}

🤖 AI 분석: {result.get('nutrition_summary','')}
⚠️ 보완 필요: {', '.join(result.get('missing_nutrients', []))}

🌙 저녁 추천: {dinner.get('menu','')}
🍎 간식 추천: {snack.get('menu','')}

🛒 장보기: {', '.join(shopping)}

💡 {result.get('weekly_tip','')}"""

                with st.expander("📤 가족에게 공유", expanded=False):
                    st.text_area(
                        "아래 내용을 복사해서 공유하세요",
                        value=share_text,
                        height=250,
                        key="t4_share",
                    )
                    st.caption("📋 위 텍스트를 선택 → 복사 후 카카오톡/문자로 전송하세요")

                # 조언
                tip = result.get("weekly_tip", "")
                if tip:
                    st.markdown(
                        f"<div style='background:#FFFDE7;border:1px solid #FFD54F;"
                        f"border-radius:10px;padding:12px 16px;margin-top:8px;"
                        f"font-size:14px;color:#555;'>"
                        f"💡 <b>오늘의 영양 조언</b><br>{tip}</div>",
                        unsafe_allow_html=True,
                    )

