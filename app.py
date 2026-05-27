"""
급식알리미 - Streamlit 웹 버전
meal.py의 급식 조회/칼로리 분석 기능을 웹에서 제공합니다.
"""
import sys, types, re, calendar
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
tab1, tab2, tab3 = st.tabs(["📅 오늘의 급식", "📋 주간 급식", "📊 월별 칼로리 분석"])

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
