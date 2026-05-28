"""
학생건강검사 원시자료 → health_stats.json 전처리 스크립트
사용법: python preprocess_health.py
출력: 학생건강자료/health_stats.json
"""

import pandas as pd
import numpy as np
import json
import os

DATA_DIR = "학생건강자료"
OUT_FILE = os.path.join(DATA_DIR, "health_stats.json")

# ── 파일 목록 ──────────────────────────────────────────────
FILES = [
    {"year": 2025, "path": os.path.join(DATA_DIR, "2025년 학생건강검사 원시자료.csv"),  "fmt": "csv"},
    {"year": 2024, "path": os.path.join(DATA_DIR, "2024년 학생건강검사 원시자료.csv"),  "fmt": "csv"},
    {"year": 2023, "path": os.path.join(DATA_DIR, "2023 학생건강검사 데이터 공개자료.xlsx"), "fmt": "xlsx"},
]

COLS_NEEDED = [
    "학교급", "학년", "성별", "키", "몸무게", "체질량지수",
    "수축기혈압", "이완기혈압",
    "아침식사", "라면", "음료수", "패스트푸드", "육류",
    "우유유제품", "과일", "채소김치제외",
    "주3회이상운동", "하루30분이상운동", "하루수면량",
]

# ── 코드 → 라벨 ───────────────────────────────────────────
# 식품빈도: 1=먹지않음 2=1-2번/주 3=3-5번/주 4=매일
FOOD_FREQ = {1: "먹지않음", 2: "1-2회/주", 3: "3-5회/주", 4: "매일"}
# 아침식사: 1=거의먹음 2=대체로먹음 3=대체로안먹음 4=거의안먹음
BREAKFAST = {1: "거의먹음", 2: "대체로먹음", 3: "대체로안먹음", 4: "거의안먹음"}
# 운동(초): 1=예 2=아니오  /  운동(중고): 1=거의안함 2=1-2일 3=3-4일 4=5일이상
EXERCISE_ELEM   = {1: "예", 2: "아니오"}
EXERCISE_MID    = {1: "거의안함", 2: "1-2일", 3: "3-4일", 4: "5일이상"}
# 수면: 1=6h이내 2=6-7h 3=7-8h 4=8h이상
SLEEP = {1: "6시간이내", 2: "6-7시간", 3: "7-8시간", 4: "8시간이상"}


def _pct(series, vals):
    """vals에 해당하는 값의 비율(%) 반환"""
    total = series.notna().sum()
    if total == 0:
        return 0.0
    return round(series.isin(vals).sum() / total * 100, 1)


def _dist(series, code_map):
    """코드별 분포 % 반환 (dict)"""
    total = series.notna().sum()
    if total == 0:
        return {}
    return {label: round((series == code).sum() / total * 100, 1)
            for code, label in code_map.items()}


def _mean_std(series):
    s = pd.to_numeric(series, errors='coerce').dropna()
    if len(s) == 0:
        return None, None
    return round(float(s.mean()), 2), round(float(s.std()), 2)


def _percentiles(series):
    s = pd.to_numeric(series, errors='coerce').dropna()
    if len(s) < 10:
        return {}
    pcts = [5, 10, 25, 50, 75, 85, 90, 95]
    return {str(p): round(float(np.percentile(s, p)), 1) for p in pcts}


def load_df(file_info):
    path = file_info["path"]
    if not os.path.exists(path):
        print(f"  ⚠ 파일 없음: {path}")
        return None
    print(f"  로딩: {os.path.basename(path)}")
    if file_info["fmt"] == "csv":
        df = pd.read_csv(path, encoding='cp949', sep='\t', low_memory=False)
    else:
        df = pd.read_excel(path)
    # 필요한 컬럼만
    cols = [c for c in COLS_NEEDED if c in df.columns]
    df = df[cols].copy()
    df["학년도"] = file_info["year"]
    return df


def aggregate(df_all):
    result = {}

    for school_type in ["초", "중", "고"]:
        result[school_type] = {}
        sub = df_all[df_all["학교급"] == school_type]

        # 학년 범위
        grades = sorted(sub["학년"].dropna().unique().tolist())

        for grade in grades:
            grade = int(grade)
            result[school_type][str(grade)] = {}
            g = sub[sub["학년"] == grade]

            for gender in ["남", "여"]:
                gg = g[g["성별"] == gender]
                n = len(gg)
                if n < 10:
                    continue

                stat = {"n": int(n)}

                # ── 신체계측 ──
                h_mean, h_std = _mean_std(gg["키"])
                w_mean, w_std = _mean_std(gg["몸무게"])
                stat["키"] = {"평균": h_mean, "표준편차": h_std,
                              "백분위": _percentiles(gg["키"])}
                stat["몸무게"] = {"평균": w_mean, "표준편차": w_std,
                                  "백분위": _percentiles(gg["몸무게"])}

                # BMI 직접 계산 (키cm → m)
                h_s = pd.to_numeric(gg["키"], errors='coerce')
                w_s = pd.to_numeric(gg["몸무게"], errors='coerce')
                bmi_s = w_s / ((h_s / 100) ** 2)
                b_mean, b_std = round(float(bmi_s.dropna().mean()), 2), round(float(bmi_s.dropna().std()), 2)
                stat["BMI"] = {"평균": b_mean, "표준편차": b_std,
                               "백분위": _percentiles(bmi_s)}

                # 체질량지수 카테고리 분포
                if "체질량지수" in gg.columns:
                    bmi_cat = gg["체질량지수"].value_counts(normalize=True).mul(100).round(1).to_dict()
                    stat["체질량지수_분포"] = bmi_cat
                    stat["비만율"] = round(bmi_cat.get("비만", 0), 1)
                    stat["과체중이상율"] = round(bmi_cat.get("비만", 0) + bmi_cat.get("과체중", 0), 1)

                # ── 혈압 ──
                if "수축기혈압" in gg.columns:
                    sbp_m, _ = _mean_std(gg["수축기혈압"])
                    dbp_m, _ = _mean_std(gg["이완기혈압"])
                    stat["수축기혈압_평균"] = sbp_m
                    stat["이완기혈압_평균"] = dbp_m

                # ── 아침식사 ──
                if "아침식사" in gg.columns:
                    stat["아침식사_분포"] = _dist(gg["아침식사"], BREAKFAST)
                    stat["아침식사_섭취율"] = _pct(gg["아침식사"], [1, 2])

                # ── 식품 빈도 ──
                for col in ["라면", "음료수", "패스트푸드", "육류", "우유유제품", "과일", "채소김치제외"]:
                    if col in gg.columns:
                        stat[f"{col}_분포"] = _dist(gg[col], FOOD_FREQ)
                        # '자주 먹음' = 3-5번 + 매일
                        stat[f"{col}_자주섭취율"] = _pct(gg[col], [3, 4])

                # ── 운동 ──
                if school_type == "초" and "주3회이상운동" in gg.columns:
                    stat["운동_분포"] = _dist(gg["주3회이상운동"], EXERCISE_ELEM)
                    stat["운동_실천율"] = _pct(gg["주3회이상운동"], [1])
                elif "하루30분이상운동" in gg.columns:
                    stat["운동_분포"] = _dist(gg["하루30분이상운동"], EXERCISE_MID)
                    stat["운동_실천율"] = _pct(gg["하루30분이상운동"], [3, 4])

                # ── 수면 ──
                if "하루수면량" in gg.columns:
                    stat["수면_분포"] = _dist(gg["하루수면량"], SLEEP)
                    stat["수면_충분율"] = _pct(gg["하루수면량"], [3, 4])  # 7시간 이상

                result[school_type][str(grade)][gender] = stat

    return result


def main():
    print("=== 학생건강검사 원시자료 전처리 시작 ===")
    dfs = []
    for fi in FILES:
        df = load_df(fi)
        if df is not None:
            dfs.append(df)
            cnt = len(df)
            print(f"    -> {cnt:,}건 로딩")

    if not dfs:
        print("[오류] 로딩된 파일이 없습니다.")
        return

    df_all = pd.concat(dfs, ignore_index=True)
    print(f"\n전체 {len(df_all):,}건 (3년 합산)")

    print("\n집계 중...")
    stats = aggregate(df_all)

    # 메타 정보 추가
    output = {
        "meta": {
            "source": "학생건강검사 표본조사 (교육부/한국교육환경보호원)",
            "years": [fi["year"] for fi in FILES if os.path.exists(fi["path"])],
            "total_records": int(len(df_all)),
            "updated": "2025",
        },
        "stats": stats,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n[완료] 저장: {OUT_FILE}")
    print(f"   파일 크기: {os.path.getsize(OUT_FILE) / 1024:.1f} KB")

    # 간단 확인
    print("\n=== 집계 결과 샘플 (초5 남) ===")
    s = stats.get("초", {}).get("5", {}).get("남", {})
    if s:
        print(f"  n={s['n']}, 키 평균={s[chr(53076)]['평균']}cm")
        print(f"  BMI 평균={s['BMI']['평균']}, 비만율={s.get('비만율','-')}%")


if __name__ == "__main__":
    main()
