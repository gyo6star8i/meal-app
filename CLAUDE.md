# 급식알리미 앱 - Claude Code 작업 컨텍스트

> 맥북에서 이어서 작업할 때 이 파일을 먼저 읽어주세요.
> 마지막 작업일: 2026-05-28 / 데스크탑 → 맥북 이전

---

## 프로젝트 개요

**앱 이름**: (경북)신동초등학교 급식알리미  
**목적**: AI 활용 대회 출품작 — 학교 급식 정보 + AI 맞춤 식단 분석 + 전국 건강 기준 비교  
**스택**: Python + Streamlit (웹앱), Groq AI (LLM), NEIS API (급식 데이터)  
**라이브 URL**: https://meal-app-rxcc7ptln9uw3qxpmypsb8.streamlit.app/  
**GitHub**: https://github.com/gyo6star8i/meal-app.git (branch: main)

---

## 파일 구조

```
급식앱/
├── app.py                  # 메인 앱 (2000줄) ← 모든 작업의 핵심
├── preprocess_health.py    # 학생건강검사 원시자료 → health_stats.json 변환 (1회 실행용)
├── requirements.txt        # streamlit, pandas, requests, openpyxl, numpy
├── setup_mac.sh            # 맥북 자동 설치 스크립트 (brew, python, venv, API키 설정)
├── .streamlit/
│   └── secrets.toml        # GROQ_API_KEY="gsk_..." (gitignore, 직접 생성 필요)
└── 학생건강자료/
    └── health_stats.json   # 전처리된 통계 (86KB, git 포함 ✅, 서버 탑재 완료)
```

> 원시 CSV/xlsx 파일들은 .gitignore 처리됨 (대용량, 맥북에는 없어도 됨)

---

## 탭 구조 (현재 5개)

| 탭 | 이름 | 핵심 기능 |
|----|------|----------|
| Tab 1 | 📅 오늘의 급식 | NEIS 급식 조회, 학교알리미 학교 정보 |
| Tab 2 | 📋 주간 급식 | 주간 급식 + AI 리포트 + 요일별 장보기 + 가족 공유 |
| Tab 3 | 📊 칼로리 분석 | 월별/주별 칼로리 추이 차트 |
| Tab 4 | 🥗 개인 맞춤 식단 분석 | AI 영양 분석 + 저녁/간식 추천 + 장보기 목록 |
| Tab 5 | 🏥 건강 기준 비교 | 학생건강검사 전국 통계 vs 내 신체 비교 ← 최근 추가 |

---

## API 키 목록

```toml
# .streamlit/secrets.toml
GROQ_API_KEY = "gsk_..."   # Groq LLM (무료, https://console.groq.com)
```

코드 내 하드코딩된 키들:
```python
NEIS_API_KEY    = "9bffa2116eb747c18a082f5e52617d37"          # NEIS 급식
NUTRI_API_KEY   = "ca41a09537bd54e63daaa0dbbc32539394e7c0244d1aff5afb879d09240edeb8"  # 식약처 영양성분DB
SCHOOL_INFO_KEY = "d15d9706ca1747bb946e0365191f7140"          # 학교알리미 OpenAPI
```

---

## app.py 주요 함수 위치

### 모듈 레벨 함수 (탭 정의 이전)

| 줄 | 함수 | 설명 |
|----|------|------|
| L255 | `_clean_school_name(name)` | 학교명에서 (경북) 등 접두어 제거 |
| L264 | `_get_sgg_candidates(school_name, sido)` | 시군구 코드 후보 반환 (3단계 조회) |
| L282 | `_get_city_from_neis(school_code, office)` | NEIS 주소API로 시군구명 추출 |
| L308 | `_fetch_schoolinfo_meal(...)` | 학교알리미 급식 조회 (3단계 폴백) |
| L830 | `_call_groq(api_key, prompt, max_tokens)` | Groq API 호출 공통 함수 |
| L845 | `_weekly_report_with_ai(week_meals, ...)` | 주간 급식 AI 리포트 생성 |
| L865 | `_analyze_meal_with_ai(menu, school_type, api_key, health_context="")` | 오늘 급식 AI 분석 + 저녁/간식 추천 |
| L901 | `_weekly_shopping_with_ai(week_meals, ...)` | 주간 장보기 목록 AI 생성 |
| L942 | `_get_groq_key()` | secrets 또는 session_state에서 키 반환 |
| L954 | `_load_health_stats()` | health_stats.json 로드 (캐시) |

### 탭 위치

| 줄 | 구분 |
|----|------|
| L534 | 탭 5개 정의 |
| L539 | `with tab1:` |
| L970 | `with tab2:` |
| L1187 | `with tab3:` |
| L1394 | `with tab4:` (내부에 `_fetch_nutrition_curl` 정의 L1396) |
| L1857 | `with tab5:` |

---

## 주요 기술 이슈 & 해결책 (과거 버그 기록)

### 1. 학교알리미 시군구 없는 학교 조회 실패
- **원인**: `(경북)신동초등학교` 처럼 시군구명이 없는 경우
- **해결**: 3단계 조회: ① 키워드 매칭 → ② NEIS 주소API로 도시 추출 → ③ 전체 시도 스캔

### 2. pandas 2.x DataFrame TypeError
- **원인**: `pd.DataFrame(dict).T` — 문자열/숫자 혼합 타입
- **해결**: `pd.DataFrame([{"연도": yr, "값": int(v)}])` 리스트-of-딕트 방식

### 3. Streamlit HTML이 코드블록으로 렌더링
- **원인**: f-string 내 4칸 이상 들여쓰기
- **해결**: 한 줄 f-string 연결로 변환

### 4. Tab4 캐시 날짜 변경 시 미갱신
- **원인**: session_state 키가 고정값
- **해결**: `f"t4_nutri_{날짜}_{학교코드}"` 핑거프린트 키 사용

### 5. Tab2 주간이 Tab1 날짜와 미동기
- **해결**: `t2_last_cur_date` 트래커 — cur_date 변경 시에만 week_monday 재계산

---

## 데이터 연동 현황

| 데이터 | 방식 | 상태 |
|--------|------|------|
| NEIS 급식 API | REST API | ✅ |
| 식약처 영양성분 DB | REST API | ✅ |
| 학교알리미 OpenAPI | REST API (apiType=34) | ✅ |
| Groq AI (llama-3.3-70b) | REST API | ✅ |
| 학생건강검사 표본통계 | JSON 번들 (269,013명, 2023-2025) | ✅ |
| **PAPS 체력평가 통계** | **미정 (파일 기반 예정)** | ❌ 남은 작업 |

---

## 남은 작업: PAPS 체력평가 통계 연동

### 목표
PAPS(학생 건강체력평가) 데이터를 연동해 Tab 5 또는 신규 탭에서:
- 학년/성별별 체력 등급 기준 표시
- 내 체력 지표 전국 비교

### 데이터 출처 후보
- **교육부 데이터포털** (data.go.kr): `PAPS` 검색
- **schoolhealth.kr**: 학생건강검사 원시자료와 같은 사이트에 PAPS 데이터 있을 가능성
- API 없음 → 건강검사와 동일하게 파일 다운로드 후 `preprocess_health.py` 방식으로 처리

### 연동 방식 (권장)
1. PAPS 원시자료 CSV 다운로드
2. `preprocess_paps.py` 작성 → `paps_stats.json` 생성
3. Tab 5에 PAPS 섹션 추가 or Tab 6 신설
4. `paps_stats.json` git commit → Streamlit Cloud 자동 배포

---

## 로컬 실행 방법

```bash
# 맥북 최초 설정 (클론 후 1회)
git clone https://github.com/gyo6star8i/meal-app.git
cd meal-app
bash setup_mac.sh   # Homebrew, Python, venv, API키 자동 설정

# 이후 실행
source venv/bin/activate
streamlit run app.py
# → http://localhost:8501
```

### secrets.toml 수동 생성 (setup_mac.sh 건너뛴 경우)
```bash
mkdir -p .streamlit
echo 'GROQ_API_KEY = "gsk_여기에키입력"' > .streamlit/secrets.toml
```

---

## 건강검사 통계 재처리 방법 (새 데이터 나올 때)

```bash
# 새 CSV를 학생건강자료/ 에 넣고
python preprocess_health.py
# → 학생건강자료/health_stats.json 갱신됨
git add 학생건강자료/health_stats.json
git commit -m "update: 건강검사 통계 갱신 (20XX년)"
git push
```

---

## Streamlit Cloud 배포 설정

- **Repository**: gyo6star8i/meal-app
- **Branch**: main
- **Main file**: app.py
- **Secrets**: GROQ_API_KEY (Streamlit Cloud 대시보드에서 설정)
- push 하면 자동 재배포 (1~2분 소요)
