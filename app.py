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
tab1, tab2, tab3, tab4 = st.tabs(["📅 오늘의 급식", "📋 주간 급식", "📊 월별 칼로리 분석", "🥗 맞춤 식단"])

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
    # ── AI 분석 함수 ─────────────────────────────────────────
    def _call_groq(api_key: str, prompt: str, max_tokens: int = 1024) -> str:
        import requests, urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile",
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": max_tokens},
            verify=False, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def _analyze_meal_with_ai(menu: str, school_type: str, api_key: str) -> dict:
        prompt = f"""오늘 {school_type} 점심 급식 메뉴입니다:
{menu}

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

    # ── 주간 급식 요약 분석 함수 ──────────────────────────────
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

    # ── 식품의약품안전처 영양성분 DB 조회 ──────────────────────────
    def _fetch_nutrition_curl(food_name: str) -> dict:
        """식약처 통합식품영양성분 DB API 조회
        - requests(verify=False) 우선 시도 → Streamlit Cloud 등 일반 환경
        - 실패 시 curl subprocess 폴백 → 학교 SSL 프록시 환경
        """
        import subprocess, json as _json, urllib.parse, re as _re2
        # ① 식품명 정리: *, 숫자, 괄호 등 알레르기 마커 완전 제거
        clean = _re2.sub(r"\(.*?\)", "", food_name)   # (1.2.5) 형태 제거
        clean = _re2.sub(r"[\*\[\]\d\.\s]+$", "", clean).strip()  # 뒤쪽 * 및 숫자 제거
        clean = _re2.sub(r"^\s*[\*\d]+\s*", "", clean).strip()   # 앞쪽 * 및 숫자 제거
        if len(clean) < 2:
            return {}

        NUTRI_API_KEY = (
            "ca41a09537bd54e63daaa0dbbc32539394e7c0244d1aff5afb879d09240edeb8"
        )

        def _do_query(name: str) -> dict:
            encoded = urllib.parse.quote(name)
            url = (
                "https://api.data.go.kr/openapi/tn_pubr_public_nutri_food_info_api"
                f"?serviceKey={NUTRI_API_KEY}&pageNo=1&numOfRows=3&type=json&foodNm={encoded}"
            )
            # 방법 1: requests verify=False (Streamlit Cloud / 일반 환경)
            try:
                import requests as _req, urllib3 as _u3
                _u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)
                r = _req.get(url, verify=False, timeout=8)
                data = r.json()
                items = data.get("response", {}).get("body", {}).get("items", [])
                if isinstance(items, list) and items:
                    return items[0]
            except Exception:
                pass
            # 방법 2: curl subprocess (학교 네트워크 SSL 프록시 환경)
            try:
                result = subprocess.run(
                    ["curl", "-k", "-s", "--max-time", "8", url],
                    capture_output=True, text=True, timeout=12,
                )
                data = _json.loads(result.stdout)
                items = data.get("response", {}).get("body", {}).get("items", [])
                if isinstance(items, list) and items:
                    return items[0]
            except Exception:
                pass
            return {}

        # 전체 이름으로 먼저 시도
        res = _do_query(clean)
        if res:
            return res
        # 긴 복합어(6자 초과)는 앞 절반으로 재시도 (예: 망고블루베리요거트샐러드 → 망고블루베리)
        if len(clean) > 6:
            res = _do_query(clean[: len(clean) // 2 + 1])
            if res:
                return res
        return {}

    # ── UI ───────────────────────────────────────────────────
    st.markdown(
        f"<div style='background:{clr};border-radius:12px;padding:16px 20px;"
        f"margin-bottom:16px;'>"
        f"<h2 style='color:white;margin:0;text-align:center;'>🥗 맞춤 식단 추천</h2></div>",
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
                _nutri = {}
                prog = st.progress(0, text="식약처 영양성분 DB 조회 중...")
                for _i, _item in enumerate(_menu_items[:8]):
                    prog.progress((_i + 1) / min(len(_menu_items), 8),
                                  text=f"조회 중: {_item}")
                    _info = _fetch_nutrition_curl(_item)
                    if _info:
                        _nutri[_item] = _info
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
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            run_analysis = st.button(
                "🤖 AI 보완 식단 분석", type="primary",
                use_container_width=True, key="t4_run",
                disabled=not lunch_menu,
            )
        with col_btn2:
            run_weekly = st.button(
                "📋 주간 리포트 생성", use_container_width=True, key="t4_weekly",
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

        # ── 주간 리포트 ───────────────────────────────────────
        if run_weekly:
            with st.spinner("📋 이번 주 급식 분석 중..."):
                w_data, w_err = fetch_week_meals(
                    st.session_state.week_monday,
                    school["office"],
                    school["code"],
                )
                if w_err:
                    st.error(f"주간 데이터 오류: {w_err}")
                elif not any(v.get("menu") for v in w_data.values()):
                    st.info("이번 주 급식 데이터가 없습니다.")
                else:
                    report_text = _weekly_report_with_ai(
                        w_data, school.get("type", "초등학교"), final_api_key
                    )
                    st.session_state["t4_weekly_report"] = report_text

        if "t4_weekly_report" in st.session_state:
            st.markdown("---")
            monday_label = st.session_state.week_monday.strftime("%m월 %d일")
            friday_label = (st.session_state.week_monday + timedelta(days=4)).strftime("%m월 %d일")
            st.markdown(
                f"<div class='meal-card' style='border-left:4px solid {clr};'>"
                f"<div class='meal-title' style='color:{clr};'>"
                f"📅 주간 리포트 ({monday_label} ~ {friday_label})</div>"
                f"<div style='font-size:15px;line-height:1.8;color:#333;white-space:pre-line;'>"
                f"{st.session_state['t4_weekly_report']}</div></div>",
                unsafe_allow_html=True,
            )
