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
    f"BY LEE YANG-HO & HEE-MYEONG · NEIS 급식 공개 API</p>",
    unsafe_allow_html=True,
)

# 탭 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📅 오늘의 급식", "📋 주간 급식", "📊 칼로리 분석", "🥗 개인 맞춤 식단 분석", "🏥 건강 기준 비교", "💪 PAPS 체력분석"])

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
                    kcal_e_html = f'<div style="color:#888;font-size:13px;margin-top:6px;">🔥 열량: {kcal_e}</div>' if kcal_e else ''
                    st.markdown(
                        f"<div class='meal-card' style='background:{bg};"
                        f"border-left:4px solid {mc_color};'>"
                        f"<div class='meal-title' style='color:{mc_color};'>{icon} {name} 급식</div>"
                        f"<div class='meal-menu'>{md['menu']}</div>"
                        f"{kcal_e_html}"
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


def _analyze_meal_with_ai(menu: str, school_type: str, api_key: str, health_context: str = "") -> dict:
    """오늘 급식 메뉴 AI 영양 분석 및 저녁/간식 추천"""
    _ctx = (
        f"\n\n[학생 건강 정보 - 학생건강검사 전국 표본통계 기반]\n{health_context.strip()}"
        if health_context.strip() else ""
    )
    prompt = f"""오늘 {school_type} 점심 급식 메뉴입니다:
{menu}{_ctx}

위 급식의 영양 구성을 분석하고, 아래 JSON 형식으로만 응답해주세요 (다른 텍스트 없이):
{{
  "nutrition_summary": "이 급식의 영양 구성 한 줄 요약",
  "missing_nutrients": ["부족한 영양소1", "부족한 영양소2", "부족한 영양소3"],
  "dinner": {{
    "menu": "저녁 추천 메뉴 (예: 현미밥 + 닭가슴살 구이)",
    "reason": "추천 이유 한 문장"
  }},
  "snack": {{
    "menu": "간식 추천 (예: 방울토마토)",
    "reason": "추천 이유 한 문장"
  }},
  "shopping_list": ["재료1", "재료2", "재료3", "재료4", "재료5"],
  "weekly_tip": "이번 주 영양 균형을 위한 한 줄 조언"
}}"""

    try:
        raw = _call_groq(api_key, prompt, max_tokens=1024)
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except Exception as e:
        return {"error": str(e)}


def _weekly_shopping_with_ai(week_meals: dict, school_type: str, api_key: str) -> dict:
    """주간 급식을 분석해 요일별 장보기 목록 반환.
    반환 형태: {"월": [{"item": "연어", "reason": "오메가-3 보충"}, ...], "화": [...], ...}
    """
    meals_text = "\n".join(
        f"{['월','화','수','목','금'][i]}요일({ymd[4:6]}/{ymd[6:8]}): {v.get('menu','급식없음')}"
        for i, (ymd, v) in enumerate(sorted(week_meals.items())[:5])
        if v.get("menu")
    )
    if not meals_text:
        return {}

    days = [d for ymd, v in sorted(week_meals.items())[:5]
            for d in [['월','화','수','목','금'][sorted(week_meals.keys()).index(ymd)]]
            if v.get("menu")]

    prompt = f"""이번 주 {school_type} 급식 메뉴입니다:
{meals_text}

각 요일별로 학교 급식에서 부족할 수 있는 영양소를 가정에서 보충할 수 있는 장보기 재료를 추천해주세요.
아래 JSON 형식으로만 응답해주세요 (설명 없이 JSON만):
{{
  "월": [{{"item": "재료명", "reason": "간단한 이유(10자 이내)", "emoji": "이모지"}}],
  "화": [{{"item": "재료명", "reason": "간단한 이유(10자 이내)", "emoji": "이모지"}}],
  "수": [{{"item": "재료명", "reason": "간단한 이유(10자 이내)", "emoji": "이모지"}}],
  "목": [{{"item": "재료명", "reason": "간단한 이유(10자 이내)", "emoji": "이모지"}}],
  "금": [{{"item": "재료명", "reason": "간단한 이유(10자 이내)", "emoji": "이모지"}}]
}}
급식 없는 날은 빈 배열로 두세요. 각 요일마다 3~4가지 재료를 추천해주세요."""

    try:
        raw = _call_groq(api_key, prompt, max_tokens=1024)
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except Exception:
        return {}


def _get_groq_key() -> str:
    """Streamlit secrets 또는 session_state 에서 Groq API 키 반환"""
    try:
        key = st.secrets.get("GROQ_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return st.session_state.get("t4_api_key_input", "")


@st.cache_data
def _load_health_stats() -> dict:
    """학생건강검사 전처리 통계 로드 (health_stats.json)"""
    import os as _os, json as _json
    path = "학생건강자료/health_stats.json"
    if not _os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as _f:
            return _json.load(_f)
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════
# TAB 2: 주간 급식
# ══════════════════════════════════════════════════════════
with tab2:
    # cur_date가 변경됐을 때만 해당 주간으로 동기화
    # (Tab2 내 이전/다음 주 버튼으로 이동 중에는 덮어쓰지 않음)
    _cur = st.session_state.cur_date
    if st.session_state.get("t2_last_cur_date") != _cur:
        st.session_state.week_monday = _cur - timedelta(days=_cur.weekday())
        st.session_state["t2_last_cur_date"] = _cur

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

                # ── 주간 장보기 목록 ─────────────────────────────
                _shop_cache_key = f"t2_shop_{monday.strftime('%Y%m%d')}"
                if _shop_cache_key not in st.session_state:
                    with st.spinner("🛒 주간 장보기 목록 생성 중..."):
                        _shop_data = _weekly_shopping_with_ai(
                            week_data, school.get("type", "초등학교"), _groq_key
                        )
                        st.session_state[_shop_cache_key] = _shop_data

                _shop = st.session_state.get(_shop_cache_key, {})
                if _shop:
                    st.markdown("---")
                    st.markdown(
                        f"<div style='font-size:18px;font-weight:bold;color:{clr};"
                        f"margin-bottom:12px;'>🛒 주간 장보기 목록</div>"
                        f"<div style='font-size:13px;color:#888;margin-bottom:14px;'>"
                        f"이번 주 급식의 부족 영양소를 보완하는 가정 장보기 추천 · "
                        f"요일별로 나눠 몰아서 장보세요</div>",
                        unsafe_allow_html=True,
                    )

                    _days_order = ["월", "화", "수", "목", "금"]
                    _day_cols = st.columns(5)
                    for _ci, _day in enumerate(_days_order):
                        _items = _shop.get(_day, [])
                        _d_date = monday + timedelta(days=_ci)
                        with _day_cols[_ci]:
                            st.markdown(
                                f"<div style='background:{clr}18;border-radius:10px;"
                                f"padding:10px 8px;min-height:160px;'>"
                                f"<div style='font-weight:bold;font-size:15px;"
                                f"color:{clr};text-align:center;margin-bottom:6px;'>"
                                f"{_day}요일<br>"
                                f"<span style='font-size:11px;font-weight:normal;"
                                f"color:#888;'>{_d_date.month}/{_d_date.day}</span></div>"
                                + (
                                    "".join(
                                        f"<div style='font-size:13px;padding:4px 2px;"
                                        f"border-bottom:1px solid {clr}22;'>"
                                        f"{it.get('emoji','🛒')} <b>{it.get('item','')}</b>"
                                        f"<div style='font-size:11px;color:#777;"
                                        f"margin-left:18px;'>{it.get('reason','')}</div>"
                                        f"</div>"
                                        for it in _items
                                    ) if _items else
                                    f"<div style='font-size:12px;color:#bbb;"
                                    f"text-align:center;margin-top:20px;'>급식 없음</div>"
                                )
                                + "</div>",
                                unsafe_allow_html=True,
                            )

                    st.caption("🤖 Groq AI 추천 · 참고용 정보입니다")

                    # ── 가족에게 공유 (장보기 위주) ──────────────
                    _days_kr_full = ["월요일","화요일","수요일","목요일","금요일"]
                    _share_lines = [
                        f"🛒 [{_mon_lbl} ~ {_fri_lbl}] {school['name']} 주간 장보기 목록",
                        "",
                        "📅 이번 주 급식 메뉴",
                    ]
                    for _si in range(5):
                        _sd = monday + timedelta(days=_si)
                        _symd = _sd.strftime("%Y%m%d")
                        _smeal = week_data.get(_symd, {})
                        _smenu = _smeal.get("menu", "급식없음") if _smeal else "급식없음"
                        _smenu_clean = re.sub(r"<[^>]+>", " ", _smenu).strip()
                        _share_lines.append(
                            f"  {_days_kr_full[_si]}({_sd.month}/{_sd.day}): {_smenu_clean}"
                        )
                    _share_lines += ["", "🛒 요일별 장보기 추천"]
                    for _si, _day in enumerate(["월","화","수","목","금"]):
                        _items_s = _shop.get(_day, [])
                        if not _items_s:
                            continue
                        _sd = monday + timedelta(days=_si)
                        _share_lines.append(f"\n📌 {_day}요일 ({_sd.month}/{_sd.day})")
                        for _it in _items_s:
                            _share_lines.append(
                                f"  • {_it.get('item','')} — {_it.get('reason','')}"
                            )
                    _share_lines += ["", "🤖 Groq AI 추천 · 참고용 정보입니다"]
                    _share_text = "\n".join(_share_lines)

                    with st.expander("📤 가족에게 공유", expanded=False):
                        st.text_area(
                            "아래 내용을 복사해서 공유하세요",
                            value=_share_text,
                            height=300,
                            key=f"t2_shop_share_{monday.strftime('%Y%m%d')}",
                        )
                        st.caption("📋 위 텍스트를 선택 → 복사 후 카카오톡/문자로 전송하세요")

# ══════════════════════════════════════════════════════════
# TAB 3: 월별 칼로리 분석
# ══════════════════════════════════════════════════════════
with tab3:
    import pandas as pd

    # 공통 상수
    _STATUS_COLOR = {"에너지 적절": "#43A047", "에너지 부족": "#2196F3",
                     "에너지 과다": "#E53935", "데이터 없음": "#888888"}
    _STATUS_ICON  = {"에너지 적절": "🟢", "에너지 부족": "🔵",
                     "에너지 과다": "🔴", "데이터 없음": "⚪"}

    st.markdown("### 📊 칼로리 분석")

    # ── 분석 모드 전환 ────────────────────────────────────────
    _mode = st.radio(
        "분석 단위", ["📅 월별 분석", "📋 주별 분석"],
        horizontal=True, key="t3_mode", label_visibility="collapsed",
    )

    st.markdown("---")

    # ════════════════════════════════════════════════════════
    # 월별 분석
    # ════════════════════════════════════════════════════════
    if _mode == "📅 월별 분석":
        st.caption("해당 월의 전체 급식 칼로리를 분석하고 권장 칼로리와 비교합니다.")

        col_y, col_m = st.columns(2)
        with col_y:
            sel_year = st.selectbox(
                "연도", list(range(_today.year - 2, _today.year + 1)),
                index=2, key="m_year",
            )
        with col_m:
            sel_month = st.selectbox(
                "월", list(range(1, 13)),
                index=_today.month - 1, key="m_month",
            )

        if st.button("📊 분석 시작", type="primary", key="m_analyze"):
            from_ymd = f"{sel_year}{sel_month:02d}01"
            last_day = calendar.monthrange(sel_year, sel_month)[1]
            to_ymd   = f"{sel_year}{sel_month:02d}{last_day:02d}"

            with st.spinner(f"⏳ {sel_year}년 {sel_month}월 데이터 불러오는 중..."):
                month_data, month_err = _fetch_all_pages(
                    from_ymd, to_ymd, school["office"], school["code"],
                )

            if month_err:
                st.error(f"오류: {month_err}")
            elif not month_data:
                st.info("해당 월의 급식 데이터가 없습니다.")
            else:
                stype = school.get("type", "초등학교")
                meal_days, avg, status, is_full = _analyze(month_data, stype)
                rec = (RECOMMENDED_DAILY_KCAL.get(stype, 2300) if is_full
                       else RECOMMENDED_LUNCH_KCAL.get(stype, 650))
                s_color = _STATUS_COLOR.get(status, "#888")
                s_icon  = _STATUS_ICON.get(status, "⚪")

                st.markdown(f"#### {sel_year}년 {sel_month}월 분석 결과")
                m1, m2, m3 = st.columns(3)
                with m1: st.metric("📅 급식일수", f"{meal_days}일")
                with m2: st.metric("🔥 평균 칼로리", f"{avg:.0f} kcal")
                with m3: st.metric("🎯 권장 칼로리", f"{rec} kcal")

                st.markdown(
                    f"<div class='status-box' style='background:{s_color}15;"
                    f"border:2px solid {s_color};font-size:22px;'>"
                    f"{s_icon} {status}<br>"
                    f"<span style='font-size:14px;font-weight:normal;color:#555;'>"
                    f"{'하루 전체' if is_full else '점심'} 기준 · 권장 {rec} kcal"
                    f"</span></div>",
                    unsafe_allow_html=True,
                )
                if avg > 0 and rec > 0:
                    st.progress(min(avg / rec / 1.5, 1.0))
                    st.caption(f"권장량 대비 {avg/rec*100:.1f}%")

                chart_rows = []
                for ymd in sorted(month_data.keys()):
                    meals = month_data[ymd]
                    if not meals:
                        continue
                    day = int(ymd[6:8])
                    v = sum(meals.values()) if is_full else (
                        meals.get(2, 0) or next(iter(meals.values()), 0))
                    if v > 0:
                        chart_rows.append({"날짜": f"{day}일", "칼로리": v, "권장량": rec})

                if chart_rows:
                    df_m = pd.DataFrame(chart_rows).set_index("날짜")
                    st.markdown("##### 📈 일별 칼로리")
                    st.line_chart(df_m)
        else:
            st.info("위에서 연도와 월을 선택한 뒤 '분석 시작' 버튼을 클릭하세요.")

    # ════════════════════════════════════════════════════════
    # 주별 분석
    # ════════════════════════════════════════════════════════
    else:
        st.caption("해당 주의 요일별 급식 칼로리를 분석하고 권장 칼로리와 비교합니다.")

        # 주 선택 (Tab2와 같은 session_state 공유)
        _w_mon = st.session_state.week_monday
        _w_fri = _w_mon + timedelta(days=4)

        wa1, wa2, wa3 = st.columns([1.2, 4, 1.2])
        with wa1:
            if st.button("◀ 이전 주", key="t3_wprev", use_container_width=True):
                st.session_state.week_monday -= timedelta(weeks=1)
                st.rerun()
        with wa2:
            st.markdown(
                f"<h4 style='text-align:center;color:{clr};margin:4px 0;'>"
                f"{_w_mon.strftime('%Y년 %m월 %d일')} ~ {_w_fri.strftime('%m월 %d일')}</h4>",
                unsafe_allow_html=True,
            )
        with wa3:
            if st.button("다음 주 ▶", key="t3_wnext", use_container_width=True):
                st.session_state.week_monday += timedelta(weeks=1)
                st.rerun()

        if st.button("이번 주로", key="t3_wtoday"):
            st.session_state.week_monday = _today - timedelta(days=_today.weekday())
            st.rerun()

        with st.spinner("주간 급식 데이터 불러오는 중..."):
            _wk_data, _wk_err = fetch_week_meals(
                st.session_state.week_monday, school["office"], school["code"],
            )

        if _wk_err:
            st.error(f"오류: {_wk_err}")
        else:
            stype = school.get("type", "초등학교")
            rec_w = RECOMMENDED_LUNCH_KCAL.get(stype, 650)
            days_kr = ["월", "화", "수", "목", "금"]
            _rows_w = []
            _day_results = []

            for i in range(5):
                d = st.session_state.week_monday + timedelta(days=i)
                ymd = d.strftime("%Y%m%d")
                meal = _wk_data.get(ymd, {})
                kcal_raw = meal.get("kcal", "") if meal else ""
                kcal_v   = _kcal_value(kcal_raw)
                _rows_w.append({"요일": f"{days_kr[i]}({d.month}/{d.day})",
                                 "칼로리": kcal_v, "권장량": rec_w})
                if kcal_v > 0:
                    st_label, st_icon, st_col = _judge(kcal_v, rec_w)
                    _day_results.append((days_kr[i], kcal_v, st_label, st_icon, st_col))

            # 요약 지표
            valid_kcals = [r["칼로리"] for r in _rows_w if r["칼로리"] > 0]
            if valid_kcals:
                _avg_w = sum(valid_kcals) / len(valid_kcals)
                _max_w = max(valid_kcals)
                _min_w = min(valid_kcals)

                st.markdown("---")
                wc1, wc2, wc3, wc4 = st.columns(4)
                with wc1: st.metric("📅 급식일수", f"{len(valid_kcals)}일")
                with wc2: st.metric("🔥 주간 평균", f"{_avg_w:.0f} kcal")
                with wc3: st.metric("⬆️ 최고", f"{_max_w:.0f} kcal")
                with wc4: st.metric("⬇️ 최저", f"{_min_w:.0f} kcal")

                # 종합 판정
                _ov_st, _ov_ic, _ov_col = _judge(_avg_w, rec_w)
                st.markdown(
                    f"<div class='status-box' style='background:{_ov_col}15;"
                    f"border:2px solid {_ov_col};font-size:20px;'>"
                    f"{_ov_ic} 주간 평균 {_ov_st}<br>"
                    f"<span style='font-size:13px;font-weight:normal;color:#555;'>"
                    f"점심 기준 · 권장 {rec_w} kcal</span></div>",
                    unsafe_allow_html=True,
                )
                st.progress(min(_avg_w / rec_w / 1.5, 1.0))
                st.caption(f"권장량 대비 {_avg_w/rec_w*100:.1f}%")

                # 요일별 막대 차트
                st.markdown("##### 📊 요일별 칼로리")
                df_w = pd.DataFrame(_rows_w).set_index("요일")
                st.bar_chart(df_w)

                # 요일별 상세 카드
                st.markdown("##### 📋 요일별 상세")
                _dcols = st.columns(len(_day_results))
                for idx, (day_name, kcal, lbl, icon, col) in enumerate(_day_results):
                    with _dcols[idx]:
                        st.markdown(
                            f"<div style='text-align:center;padding:10px 6px;"
                            f"border-radius:10px;background:{col}15;"
                            f"border:1.5px solid {col};'>"
                            f"<div style='font-weight:bold;font-size:15px;'>{day_name}요일</div>"
                            f"<div style='font-size:18px;font-weight:bold;color:{col};margin:4px 0;'>"
                            f"{kcal:.0f}</div>"
                            f"<div style='font-size:11px;color:#666;'>kcal</div>"
                            f"<div style='font-size:13px;font-weight:bold;color:{col};'>"
                            f"{icon} {lbl}</div></div>",
                            unsafe_allow_html=True,
                        )
            else:
                st.info("해당 주에 칼로리 데이터가 없습니다.")

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

        # ── 캐시 키: 날짜 + 학교코드 기반 ────────────────────
        _t4_fp = f"{st.session_state.cur_date.strftime('%Y%m%d')}_{school['code']}"
        _t4_nutri_key  = f"t4_nutri_{_t4_fp}"
        _t4_result_key = f"t4_result_{_t4_fp}"

        # 오늘 점심 카드
        st.markdown("#### 📌 오늘 점심 급식")
        if lunch_menu:
            kcal_clean = re.sub(r'\(해당.*?\)', '', lunch_kcal).strip()
            kcal_clean_html = f'<div style="color:#888;font-size:13px;margin-top:6px;">🔥 {kcal_clean}</div>' if kcal_clean else ''
            st.markdown(
                f"<div class='meal-card' style='border-left:4px solid {clr};'>"
                f"<div class='meal-menu'>{lunch_menu}</div>"
                f"{kcal_clean_html}"
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
                st.session_state[_t4_nutri_key] = _nutri
                if not _nutri:
                    st.session_state["t4_nutri_empty"] = True

        if st.session_state.get("t4_nutri_empty"):
            st.warning("영양성분 DB에서 오늘 메뉴 항목을 찾지 못했습니다. (식품명 불일치 또는 네트워크 오류)")
            st.session_state.pop("t4_nutri_empty", None)

        if st.session_state.get(_t4_nutri_key):
            _nutri_data = st.session_state[_t4_nutri_key]
            with st.expander(
                f"🔬 식약처 영양성분 DB 분석 — {len(_nutri_data)}개 메뉴 조회됨",
                expanded=True,
            ):
                st.caption(
                    "📊 출처: 식품의약품안전처 통합식품영양성분 DB (data.go.kr) · "
                    "1인 1회 제공량 기준"
                )
                def _nutri_card(food, info):
                    """영양성분 카드 HTML 생성"""
                    db_nm = info.get("foodNm", food)
                    badges = [
                        ("🔥", "열량",    info.get("enerc",""),  "kcal", "#FF5722"),
                        ("💪", "단백질",  info.get("prot",""),   "g",    "#2196F3"),
                        ("🌾", "탄수화물",info.get("chocdf",""), "g",    "#FF9800"),
                        ("🫙", "지방",    info.get("fatce",""),  "g",    "#9C27B0"),
                        ("🌿", "식이섬유",info.get("fibtg",""),  "g",    "#4CAF50"),
                        ("🦴", "칼슘",    info.get("ca",""),     "mg",   "#00BCD4"),
                        ("🧂", "나트륨",  info.get("nat",""),    "mg",   "#607D8B"),
                        ("🍋", "비타민C", info.get("vitc",""),   "mg",   "#FFEB3B"),
                    ]
                    badge_html = "".join(
                        f"<span style='background:{c}18;color:{c};border:1px solid {c}44;"
                        f"border-radius:20px;padding:2px 8px;font-size:11px;white-space:nowrap;'>"
                        f"{ic} {lb} <b>{v}{u}</b></span>"
                        for ic, lb, v, u, c in badges if v
                    )
                    return (
                        f"<div style='background:#F8F9FA;border-radius:10px;"
                        f"padding:10px 12px;margin:4px 0;border-left:3px solid #4CAF50;'>"
                        f"<b style='font-size:14px;'>🍽️ {food}</b>"
                        f"<span style='color:#aaa;font-size:11px;margin-left:6px;'>({db_nm})</span>"
                        f"<div style='display:flex;flex-wrap:wrap;gap:5px;margin-top:6px;'>"
                        f"{badge_html}</div></div>"
                    )

                # 2열 그리드로 표시
                _items_list = list(_nutri_data.items())
                for _row in range(0, len(_items_list), 2):
                    _gc1, _gc2 = st.columns(2)
                    with _gc1:
                        st.markdown(_nutri_card(*_items_list[_row]), unsafe_allow_html=True)
                    with _gc2:
                        if _row + 1 < len(_items_list):
                            st.markdown(_nutri_card(*_items_list[_row + 1]), unsafe_allow_html=True)

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
            with st.spinner("🤖 AI가 급식을 분석하는 중..."):
                result = _analyze_meal_with_ai(
                    lunch_menu, school.get("type", "초등학교"), final_api_key,
                    health_context=st.session_state.get("t4_health_ctx", ""),
                )
            st.session_state[_t4_result_key] = result

        if st.session_state.get(_t4_result_key):
            result = st.session_state[_t4_result_key]

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
                _kcal_line = ('🔥 ' + re.sub(r'\(해당.*?\)', '', lunch_kcal).strip()) if lunch_kcal else ''
                share_text = f"""📋 [{date_label(st.session_state.cur_date)}] {school['name']} 급식 분석

🍚 오늘 점심:
{lunch_menu}
{_kcal_line}

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

# ══════════════════════════════════════════════════════════
# Tab 5 – 건강 기준 비교
# ══════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### 🏥 전국 학생 건강 기준과 내 건강 비교")
    _hs_data = _load_health_stats()
    if not _hs_data:
        st.warning("health_stats.json 파일이 없습니다. preprocess_health.py 를 먼저 실행하세요.")
    else:
        st.caption("학생건강검사 표본통계 (교육부, 2023-2025 / 269,013명 기반)")

        # ── 프로필 입력 ──────────────────────────────────────
        st.markdown("##### 내 정보 입력")
        _hc1, _hc2, _hc3 = st.columns(3)
        with _hc1:
            _school_sel = st.selectbox("학교급", ["초", "중", "고"], key="hc_school")
        with _hc2:
            _grade_map_hc = {"초": ["1","2","3","4","5","6"], "중": ["1","2","3"], "고": ["1","2","3"]}
            _grade_sel = st.selectbox("학년", _grade_map_hc.get(_school_sel, ["1"]), key="hc_grade")
        with _hc3:
            _gender_sel = st.selectbox("성별", ["남", "여"], key="hc_gender")

        _hk1, _hk2 = st.columns(2)
        with _hk1:
            _my_h = st.number_input("내 키 (cm)", min_value=100.0, max_value=220.0, value=160.0, step=0.1, key="hc_h")
        with _hk2:
            _my_w = st.number_input("내 몸무게 (kg)", min_value=20.0, max_value=150.0, value=55.0, step=0.1, key="hc_w")

        _my_bmi = round(_my_w / ((_my_h / 100) ** 2), 1)

        # ── 전국 통계 조회 ────────────────────────────────────
        _ns = _hs_data.get("stats", {}).get(_school_sel, {}).get(_grade_sel, {}).get(_gender_sel, {})
        if not _ns:
            st.info("해당 그룹의 통계 데이터가 없습니다.")
        else:
            _nat_h       = _ns.get("키", {}).get("평균", 0)
            _nat_w       = _ns.get("몸무게", {}).get("평균", 0)
            _nat_bmi     = _ns.get("BMI", {}).get("평균", 0)
            _nat_bmi_pct = _ns.get("BMI", {}).get("백분위", {})
            _obesity     = _ns.get("비만율", 0)
            _overweight  = _ns.get("과체중이상율", 0)
            _breakfast_r = _ns.get("아침식사_섭취율", 0)
            _veg_r       = _ns.get("채소김치제외_자주섭취율", 0)
            _fruit_r     = _ns.get("과일_자주섭취율", 0)
            _exercise_r  = _ns.get("운동_실천율", 0)
            _sleep_r     = _ns.get("수면_충분율", 0)
            _ns_n        = _ns.get("n", 0)

            # BMI 등급 판정
            if _my_bmi < 18.5:
                _bmi_lbl, _bmi_clr = "저체중", "#5C6BC0"
            elif _my_bmi < 23:
                _bmi_lbl, _bmi_clr = "정상", "#43A047"
            elif _my_bmi < 25:
                _bmi_lbl, _bmi_clr = "과체중", "#FB8C00"
            else:
                _bmi_lbl, _bmi_clr = "비만", "#E53935"

            # BMI 백분위 계산
            _pct_vals = sorted([(int(k), float(v)) for k, v in _nat_bmi_pct.items()], key=lambda x: x[0])
            _bmi_rank_pct = 50
            for _pp, _pv in _pct_vals:
                if _my_bmi <= _pv:
                    _bmi_rank_pct = _pp
                    break
            else:
                _bmi_rank_pct = 99

            st.markdown("---")

            # ── 신체계측 비교 ──────────────────────────────────
            st.markdown("##### 신체계측 전국 비교")
            _m1, _m2, _m3 = st.columns(3)
            with _m1:
                st.metric("내 BMI", f"{_my_bmi}",
                          f"{_my_bmi - _nat_bmi:+.1f} (전국 평균 {_nat_bmi})")
            with _m2:
                st.metric("키 (전국 평균)", f"{_my_h:.1f} cm",
                          f"{_my_h - _nat_h:+.1f} cm")
            with _m3:
                st.metric("몸무게 (전국 평균)", f"{_my_w:.1f} kg",
                          f"{_my_w - _nat_w:+.1f} kg")

            # BMI 상태 배너
            st.markdown(
                f"<div style='background:#F8F9FA;border-radius:10px;padding:14px 18px;margin:10px 0;'>"
                f"<span style='font-size:16px;'>내 BMI 상태: "
                f"<b style='color:{_bmi_clr};'>{_bmi_lbl} (BMI {_my_bmi})</b>"
                f" &nbsp;·&nbsp; 전국 {_school_sel}{_grade_sel}학년 {_gender_sel} 하위 약 "
                f"<b>{_bmi_rank_pct}%ile</b></span><br>"
                f"<span style='font-size:13px;color:#666;'>전국 비만율 {_obesity}% "
                f"/ 과체중 이상 {_overweight}% &nbsp;(표본 {_ns_n:,}명)</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # ── 체질량지수 분포 ────────────────────────────────
            _bmi_dist = _ns.get("체질량지수_분포", {})
            if _bmi_dist:
                st.markdown("##### 전국 체질량지수 분포")
                _dc = st.columns(len(_bmi_dist))
                _cat_clr = {"저체중": "#5C6BC0", "정상": "#43A047", "과체중": "#FB8C00", "비만": "#E53935"}
                for _ci, (_cat, _pct_v) in enumerate(sorted(_bmi_dist.items(), key=lambda x: ["저체중","정상","과체중","비만"].index(x[0]) if x[0] in ["저체중","정상","과체중","비만"] else 9)):
                    with _dc[_ci]:
                        _cc = _cat_clr.get(_cat, "#888")
                        _is_mine = _cat == _bmi_lbl
                        _mine_html = '<div style="font-size:11px;color:#888;">← 내 위치</div>' if _is_mine else ''
                        st.markdown(
                            f"<div style='text-align:center;padding:10px 6px;border-radius:8px;"
                            f"background:{'#F0F7EE' if _is_mine else '#F8F9FA'};"
                            f"border:2px solid {_cc if _is_mine else '#eee'};'>"
                            f"<div style='font-size:13px;color:{_cc};font-weight:bold;'>{_cat}</div>"
                            f"<div style='font-size:22px;font-weight:bold;color:{_cc};'>{_pct_v}%</div>"
                            f"{_mine_html}"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

            st.markdown("---")

            # ── 식습관 · 생활습관 비교 ─────────────────────────
            st.markdown("##### 전국 같은 그룹 식습관 · 생활습관")
            _h1, _h2, _h3, _h4, _h5 = st.columns(5)
            with _h1:
                st.metric("아침식사 섭취율", f"{_breakfast_r}%")
            with _h2:
                st.metric("채소 자주섭취율", f"{_veg_r}%")
            with _h3:
                st.metric("과일 자주섭취율", f"{_fruit_r}%")
            with _h4:
                st.metric("운동 실천율", f"{_exercise_r}%")
            with _h5:
                st.metric("수면 충분율", f"{_sleep_r}%")

            # ── AI 식단 분석 연동 안내 ─────────────────────────
            st.markdown("---")
            # 건강 컨텍스트 session_state에 저장 (Tab4 AI 분석에서 활용)
            st.session_state["t4_health_ctx"] = (
                f"학생: {_school_sel}학교 {_grade_sel}학년 {_gender_sel} / "
                f"키 {_my_h}cm · 몸무게 {_my_w}kg · BMI {_my_bmi} ({_bmi_lbl})\n"
                f"전국 동일그룹 평균: 키 {_nat_h}cm · BMI {_nat_bmi} · 비만율 {_obesity}%\n"
                f"전국 식습관: 아침식사 {_breakfast_r}% / 채소자주섭취 {_veg_r}% / "
                f"과일자주섭취 {_fruit_r}% / 운동실천 {_exercise_r}%"
            )
            st.info(
                f"💡 이 건강 정보는 **개인 맞춤 식단 분석** 탭의 AI 분석에 자동으로 반영됩니다. "
                f"(현재 설정: {_school_sel}{_grade_sel}학년 {_gender_sel} / BMI {_my_bmi} {_bmi_lbl})"
            )


# ══════════════════════════════════════════════════════════
# TAB 6: PAPS 체력분석 (전국 평균 비교 + 급식 연계)
# ══════════════════════════════════════════════════════════

# ── 전국 학생 건강검사 통계 (한국교육개발원, 2019·2022·2023) ──
_NS = {
    "초": {
        "남": {
            "키":           {"2019": 145.3, "2022": 146.6, "2023": 150.5},
            "몸무게":        {"2019": 43.1,  "2022": 45.6,  "2023": 48.4},
            "제자리멀리뛰기": {"2019": 163.7, "2022": 151.6, "2023": 161.5},
            "윗몸말아올리기": {"2019": 71.7,  "2022": 61.1,  "2023": 67.8},
        },
        "여": {
            "키":           {"2019": 146.0, "2022": 146.9, "2023": 151.1},
            "몸무게":        {"2019": 40.8,  "2022": 42.2,  "2023": 45.3},
            "제자리멀리뛰기": {"2019": 144.5, "2022": 137.5, "2023": 144.4},
            "윗몸말아올리기": {"2019": 54.3,  "2022": 50.0,  "2023": 52.7},
        },
    },
    "중": {
        "남": {
            "키":           {"2019": 166.7, "2022": 166.3, "2023": 169.9},
            "몸무게":        {"2019": 61.0,  "2022": 62.5,  "2023": 65.4},
            "제자리멀리뛰기": {"2019": 200.2, "2022": 186.3, "2023": 197.6},
            "윗몸말아올리기": {"2019": 82.9,  "2022": 76.8,  "2023": 79.0},
        },
        "여": {
            "키":           {"2019": 159.1, "2022": 160.2, "2023": 160.4},
            "몸무게":        {"2019": 53.3,  "2022": 54.5,  "2023": 54.8},
            "제자리멀리뛰기": {"2019": 150.1, "2022": 147.5, "2023": 148.8},
            "윗몸말아올리기": {"2019": 44.7,  "2022": 45.4,  "2023": 43.4},
        },
    },
    "고": {
        "남": {
            "키":           {"2019": 173.4, "2022": 173.5, "2023": 174.3},
            "몸무게":        {"2019": 70.2,  "2022": 70.3,  "2023": 72.1},
            "제자리멀리뛰기": {"2019": 214.2, "2022": 208.1, "2023": 211.1},
            "윗몸말아올리기": {"2019": 69.3,  "2022": 66.6,  "2023": 64.0},
        },
        "여": {
            "키":           {"2019": 161.2, "2022": 161.4, "2023": 161.7},
            "몸무게":        {"2019": 57.5,  "2022": 57.6,  "2023": 58.1},
            "제자리멀리뛰기": {"2019": 151.2, "2022": 149.5, "2023": 149.3},
            "윗몸말아올리기": {"2019": 35.1,  "2022": 34.0,  "2023": 33.2},
        },
    },
}

with tab6:
    st.markdown("#### 💪 PAPS 체력 · 전국 평균 비교 및 급식 연계 분석")
    st.caption("출처: 한국교육개발원 교육통계연보 · 11세(초)·14세(중)·17세(고) 기준")

    # ── 기본 정보 ──────────────────────────────────────────
    st.markdown("##### 기본 정보")
    _n1, _n2 = st.columns(2)
    with _n1:
        _ns_school = st.selectbox("학교급", ["초", "중", "고"], key="ns_school",
                                  help="초=11세, 중=14세, 고=17세 기준 통계")
    with _n2:
        _ns_gender = st.selectbox("성별", ["남", "여"], key="ns_gender")

    st.markdown("---")

    # ── 신체 측정값 입력 ───────────────────────────────────
    st.markdown("##### 📏 신체 측정값 입력")
    _ns_ref = _NS[_ns_school][_ns_gender]
    _nat_h  = _ns_ref["키"]["2023"]
    _nat_w  = _ns_ref["몸무게"]["2023"]
    _nat_j  = _ns_ref["제자리멀리뛰기"]["2023"]
    _nat_su = _ns_ref["윗몸말아올리기"]["2023"]

    _mi1, _mi2, _mi3, _mi4 = st.columns(4)
    with _mi1:
        _my_h6 = st.number_input(
            f"키 (cm)\n전국평균 {_nat_h}",
            min_value=100.0, max_value=220.0,
            value=float(st.session_state.get("hc_h", _nat_h)),
            step=0.1, key="ns_h",
        )
    with _mi2:
        _my_w6 = st.number_input(
            f"몸무게 (kg)\n전국평균 {_nat_w}",
            min_value=20.0, max_value=150.0,
            value=float(st.session_state.get("hc_w", _nat_w)),
            step=0.1, key="ns_w",
        )
    with _mi3:
        _my_j = st.number_input(
            f"제자리멀리뛰기 (cm)\n전국평균 {_nat_j}",
            min_value=50.0, max_value=350.0,
            value=float(_nat_j), step=1.0, key="ns_jump",
        )
    with _mi4:
        _my_su = st.number_input(
            f"윗몸말아올리기 (회/분)\n전국평균 {_nat_su}",
            min_value=0.0, max_value=150.0,
            value=float(_nat_su), step=1.0, key="ns_situp",
        )

    _my_bmi6 = round(_my_w6 / ((_my_h6 / 100) ** 2), 1)
    _nat_bmi6 = round(_nat_w / ((_nat_h / 100) ** 2), 1)

    st.markdown("---")

    # ── ③ BMI + 체력 통합 비교 ────────────────────────────
    st.markdown("##### 📊 전국 평균 통합 비교 (2023년 기준)")

    def _cmp_card(label, icon, my_val, nat_val, unit, higher_is_better=True):
        diff = my_val - nat_val
        pct  = (my_val / nat_val * 100) if nat_val else 0
        if higher_is_better:
            good = diff >= 0
        else:
            good = diff <= 0   # BMI: 낮을수록 좋음은 아니지만 여기선 ±표시만
        bar_color  = "#43A047" if good else "#EF5350"
        diff_label = f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}"
        bar_val = min(pct / 150, 1.0)
        return (
            f"<div style='text-align:center;padding:14px 8px;border-radius:12px;"
            f"background:{bar_color}12;border:2px solid {bar_color};'>"
            f"<div style='font-size:22px;'>{icon}</div>"
            f"<div style='font-size:12px;color:#555;font-weight:bold;'>{label}</div>"
            f"<div style='font-size:26px;font-weight:bold;color:{bar_color};'>"
            f"{my_val:.1f}<span style='font-size:13px;'>{unit}</span></div>"
            f"<div style='font-size:12px;color:#888;'>전국 {nat_val}{unit}</div>"
            f"<div style='font-size:13px;font-weight:bold;color:{bar_color};'>"
            f"{'▲' if diff>=0 else '▼'} {diff_label}{unit}</div>"
            f"</div>"
        ), good

    _c1, _c2, _c3, _c4 = st.columns(4)
    _metrics = [
        (_c1, "BMI",           "⚖️",  _my_bmi6,  _nat_bmi6, "",    False),
        (_c2, "키",             "📏",  _my_h6,    _nat_h,    "cm",  True),
        (_c3, "제자리멀리뛰기",  "🦘",  _my_j,     _nat_j,    "cm",  True),
        (_c4, "윗몸말아올리기",  "💪",  _my_su,    _nat_su,   "회",  True),
    ]
    _deficit_areas = []
    for col, label, icon, mv, nv, unit, hib in _metrics:
        html, good = _cmp_card(label, icon, mv, nv, unit, hib)
        col.markdown(html, unsafe_allow_html=True)
        if not good and label not in ("BMI", "키"):
            _deficit_areas.append(label)

    # BMI 상태
    if _my_bmi6 < 18.5:
        _bmi6_lbl, _bmi6_clr = "저체중", "#5C6BC0"
    elif _my_bmi6 < 23:
        _bmi6_lbl, _bmi6_clr = "정상", "#43A047"
    elif _my_bmi6 < 25:
        _bmi6_lbl, _bmi6_clr = "과체중", "#FB8C00"
    else:
        _bmi6_lbl, _bmi6_clr = "비만", "#E53935"

    st.markdown(
        f"<div style='background:#F8F9FA;border-radius:10px;padding:10px 16px;"
        f"margin-top:8px;font-size:14px;'>"
        f"📋 <b>종합:</b> BMI {_my_bmi6} "
        f"<b style='color:{_bmi6_clr};'>({_bmi6_lbl})</b> · "
        f"전국평균 BMI {_nat_bmi6} · "
        f"{'✅ 체력 측정 2항목 모두 전국 평균 이상' if not _deficit_areas else '⚠️ 전국 평균 미달 항목: ' + ', '.join(_deficit_areas)}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── 연도별 트렌드 ─────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 📈 전국 평균 연도별 트렌드 (2019→2022→2023)")
    import pandas as _pd6
    _years = ["2019", "2022", "2023"]
    _trend_j  = [_ns_ref["제자리멀리뛰기"][y] for y in _years]
    _trend_su = [_ns_ref["윗몸말아올리기"][y] for y in _years]
    _ta, _tb = st.columns(2)
    with _ta:
        st.caption("🦘 제자리멀리뛰기 (cm)")
        _df_j = _pd6.DataFrame({"전국평균": _trend_j, "내 기록": [_my_j]*3}, index=_years)
        st.line_chart(_df_j)
    with _tb:
        st.caption("💪 윗몸말아올리기 (회/분)")
        _df_su = _pd6.DataFrame({"전국평균": _trend_su, "내 기록": [_my_su]*3}, index=_years)
        st.line_chart(_df_su)

    st.markdown("---")

    # ── ④ 급식 연계 분석 ─────────────────────────────────
    st.markdown("##### 🍽️ 오늘 급식 × 체력 수준 연계 분석")

    _DEFICIT_NUTRITION = {
        "제자리멀리뛰기": {
            "label": "순발력·근력",
            "icon": "🦘",
            "color": "#FB8C00",
            "nutrients": ["단백질", "칼슘", "비타민D", "탄수화물"],
            "foods": ["닭고기", "우유", "달걀", "현미밥"],
            "tip": "순발력은 근섬유 발달에 필요한 단백질과 에너지원인 탄수화물이 핵심입니다.",
        },
        "윗몸말아올리기": {
            "label": "근지구력",
            "icon": "💪",
            "color": "#1E88E5",
            "nutrients": ["단백질", "철분", "비타민B군", "마그네슘"],
            "foods": ["소고기", "시금치", "콩류", "견과류"],
            "tip": "근지구력 향상을 위해 근육 유지에 필요한 단백질과 피로 회복에 도움되는 철분이 중요합니다.",
        },
    }

    with st.spinner("급식 데이터 불러오는 중..."):
        _ns_meal, _ = fetch_meal(
            st.session_state.cur_date, school["office"], school["code"]
        )
    _ns_lunch = _ns_meal.get(2, {}).get("menu", "") if _ns_meal else ""
    _ns_kcal  = _ns_meal.get(2, {}).get("kcal", "")  if _ns_meal else ""

    if _ns_lunch:
        _kcal_disp = re.sub(r'\(해당.*?\)', '', _ns_kcal).strip()
        _kcal_html6 = f'<div style="color:#888;font-size:13px;margin-top:6px;">🔥 {_kcal_disp}</div>' if _kcal_disp else ''
        st.markdown(
            f"<div class='meal-card' style='border-left:4px solid {clr};'>"
            f"<div class='meal-title' style='color:{clr};'>🍚 오늘 점심</div>"
            f"<div class='meal-menu'>{_ns_lunch}</div>"
            f"{_kcal_html6}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("오늘 급식 데이터가 없습니다.")

    if _deficit_areas:
        st.markdown("##### 💊 전국 평균 미달 체력 보완 영양 계획")
        for area in _deficit_areas:
            info = _DEFICIT_NUTRITION.get(area, {})
            if not info:
                continue
            ac = info["color"]
            st.markdown(
                f"<div style='background:{ac}10;border-left:4px solid {ac};"
                f"border-radius:8px;padding:12px 16px;margin:8px 0;'>"
                f"<div style='font-weight:bold;color:{ac};font-size:15px;'>"
                f"{info['icon']} {area} ({info['label']}) — 전국 평균 대비 "
                f"{_ns_ref[area]['2023'] - (float(_my_j) if area=='제자리멀리뛰기' else float(_my_su)):.1f} 부족</div>"
                f"<div style='font-size:13px;color:#555;margin-top:5px;'>{info['tip']}</div>"
                f"<div style='margin-top:8px;'>"
                + "".join(
                    f"<span style='background:{ac}22;color:{ac};border:1px solid {ac}44;"
                    f"border-radius:12px;padding:2px 9px;font-size:12px;margin:2px;"
                    f"display:inline-block;'>🔹 {n}</span>"
                    for n in info["nutrients"]
                )
                + f"</div><div style='font-size:12px;color:#666;margin-top:6px;'>"
                f"🛒 보충 식품: <b>{', '.join(info['foods'])}</b></div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.success("✅ 두 체력 항목 모두 전국 평균 이상입니다! 현재 식단을 유지하세요.")

    # ── AI 통합 분석 ──────────────────────────────────────
    st.markdown("---")
    _ns_ai_key = _get_groq_key()

    if not _ns_ai_key:
        st.info("💡 AI 분석은 **개인 맞춤 식단 분석** 탭에서 Groq API 키를 입력하면 활성화됩니다.")
    elif not _ns_lunch:
        st.info("오늘 급식 데이터가 없어 AI 분석을 수행할 수 없습니다.")
    else:
        _ns_cache = (
            f"ns_ai_{st.session_state.cur_date.strftime('%Y%m%d')}"
            f"_{school['code']}_{_ns_school}_{_ns_gender}"
            f"_{int(_my_j)}_{int(_my_su)}"
        )
        if st.button("🤖 AI 체력 × 급식 통합 분석", type="primary",
                     use_container_width=True, key="ns_ai_btn"):
            _ns_prompt = f"""학생 건강 데이터:
- 학교급/성별: {_ns_school}학교 {_ns_gender}
- 키: {_my_h6}cm (전국평균 {_nat_h}cm, 차이 {_my_h6-_nat_h:+.1f})
- 몸무게: {_my_w6}kg (전국평균 {_nat_w}kg, 차이 {_my_w6-_nat_w:+.1f})
- BMI: {_my_bmi6} ({_bmi6_lbl}) / 전국평균 BMI {_nat_bmi6}
- 제자리멀리뛰기: {_my_j}cm (전국평균 {_nat_j}cm, 차이 {_my_j-_nat_j:+.1f})
- 윗몸말아올리기: {_my_su}회/분 (전국평균 {_nat_su}회/분, 차이 {_my_su-_nat_su:+.1f})
- 전국평균 미달 항목: {', '.join(_deficit_areas) if _deficit_areas else '없음 (모두 평균 이상)'}

오늘 점심 급식:
{_ns_lunch}

위 데이터를 분석하여 아래 JSON 형식으로만 응답하세요 (설명 없이 JSON만):
{{
  "overall_assessment": "학생의 체력 수준과 체형에 대한 종합 평가 (2문장)",
  "meal_fitness_score": "오늘 급식이 이 학생의 체력 향상에 기여하는 정도 (상/중/하)",
  "meal_feedback": "오늘 급식의 체력 관점 강점과 약점 (2문장)",
  "deficit_plans": [
    {{"item": "전국평균 미달 항목명", "nutrient_gap": "급식에서 부족한 영양소", "action": "저녁·간식 보완 방법"}}
  ],
  "exercise_plan": "이 학생에게 맞는 주 3회 운동 계획 (구체적 종목·시간 포함)",
  "weekly_diet_tip": "체력 향상을 위한 이번 주 식단 핵심 조언 (1~2문장)"
}}"""

            with st.spinner("🤖 체력 데이터와 급식을 종합 분석 중..."):
                try:
                    _raw = _call_groq(_ns_ai_key, _ns_prompt, max_tokens=1200)
                    if "```json" in _raw:
                        _raw = _raw.split("```json")[1].split("```")[0].strip()
                    elif "```" in _raw:
                        _raw = _raw.split("```")[1].split("```")[0].strip()
                    st.session_state[_ns_cache] = json.loads(_raw)
                except Exception as _e:
                    st.error(f"AI 분석 오류: {_e}")

        if st.session_state.get(_ns_cache):
            _nr = st.session_state[_ns_cache]

            # 종합 평가
            _score_color = {"상": "#43A047", "중": "#FB8C00", "하": "#EF5350"}.get(
                _nr.get("meal_fitness_score", "중"), "#888")
            st.markdown(
                f"<div style='background:#F8F9FA;border-radius:10px;padding:14px 18px;margin:8px 0;'>"
                f"<b style='font-size:15px;'>📋 종합 평가</b>"
                f"<span style='float:right;background:{_score_color}22;color:{_score_color};"
                f"border:1px solid {_score_color};border-radius:20px;padding:2px 12px;"
                f"font-size:13px;font-weight:bold;'>급식 기여도 {_nr.get('meal_fitness_score','')}</span>"
                f"<div style='margin-top:8px;font-size:14px;line-height:1.7;'>"
                f"{_nr.get('overall_assessment','')}</div></div>",
                unsafe_allow_html=True,
            )

            # 급식 피드백
            st.markdown(
                f"<div style='background:#E3F2FD;border-left:4px solid #1E88E5;"
                f"border-radius:8px;padding:12px 16px;margin:8px 0;'>"
                f"<b style='color:#1E88E5;'>🍽️ 오늘 급식 체력 피드백</b><br>"
                f"<span style='font-size:14px;'>{_nr.get('meal_feedback','')}</span></div>",
                unsafe_allow_html=True,
            )

            # 미달 항목 보완 계획
            _dp = _nr.get("deficit_plans", [])
            if _dp:
                st.markdown("##### 🔧 미달 항목 보완 계획")
                for item in _dp:
                    _ia = item.get("item", "")
                    _ic = _DEFICIT_NUTRITION.get(_ia, {}).get("color", "#888")
                    st.markdown(
                        f"<div style='background:{_ic}10;border:1px solid {_ic}44;"
                        f"border-radius:8px;padding:10px 14px;margin:6px 0;'>"
                        f"<b style='color:{_ic};'>{_ia}</b> — 부족 영양소: {item.get('nutrient_gap','')}<br>"
                        f"💡 보완 방법: <b>{item.get('action','')}</b></div>",
                        unsafe_allow_html=True,
                    )

            # 운동 계획 + 식단 조언
            _ra, _rb = st.columns(2)
            with _ra:
                st.markdown(
                    f"<div class='meal-card' style='border-left:4px solid #FB8C00;'>"
                    f"<div class='meal-title' style='color:#FB8C00;'>🏃 주 3회 운동 계획</div>"
                    f"<div style='font-size:14px;line-height:1.8;'>{_nr.get('exercise_plan','')}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with _rb:
                st.markdown(
                    f"<div class='meal-card' style='border-left:4px solid #43A047;'>"
                    f"<div class='meal-title' style='color:#43A047;'>🥗 이번 주 식단 핵심 조언</div>"
                    f"<div style='font-size:14px;line-height:1.8;'>{_nr.get('weekly_diet_tip','')}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.caption("🤖 Groq AI (llama-3.3-70b) · 한국교육개발원 통계 기반 · 참고용 정보입니다")
