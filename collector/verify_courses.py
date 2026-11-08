#!/usr/bin/env python3
"""여행코스 관광지 좌표 검증 — 카카오 로컬 키워드 검색으로 실제 위치와 비교한다.

  python collector/verify_courses.py          # 보고서만 (collector/course_check.md)
  python collector/verify_courses.py --fix    # 오차가 큰 좌표를 courses.json 에 반영

환경변수: KAKAO_REST_KEY
식사 슬롯(meal)은 '그 근처'라는 뜻이라 검증하지 않는다.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import collect  # noqa: E402

HERE = Path(__file__).resolve().parent
TOL_M = 250        # 이 거리 이상 차이 나면 '확인 필요'
FIX_MAX_M = 3000   # 이보다 멀면 동명이인 장소일 수 있어 자동 수정하지 않음


def lookup(name, sido_name, key):
    j = collect.get("https://dapi.kakao.com/v2/local/search/keyword.json",
                    headers={"Authorization": f"KakaoAK {key}"},
                    params={"query": f"{sido_name} {name.split('·')[0].strip()}", "size": 3})
    docs = j.get("documents", [])
    # 관광명소(AT4)·문화시설(CT1)을 우선
    docs.sort(key=lambda d: d.get("category_group_code") not in ("AT4", "CT1"))
    return docs[0] if docs else None


def main(fix=False):
    key = os.getenv("KAKAO_REST_KEY") or sys.exit("KAKAO_REST_KEY 가 필요합니다.")
    path = HERE / "courses.json"
    courses = json.loads(path.read_text(encoding="utf-8"))
    rows, changed = [], 0
    for c in courses:
        sido = collect.REGIONS[c["sido"]]["name"]
        for s in c["stops"]:
            if s["t"] != "spot":
                continue
            d = lookup(s["name"], sido, key)
            if not d:
                rows.append((c["id"], s["name"], "검색 결과 없음", "", "확인 필요"))
                continue
            lat, lng = float(d["y"]), float(d["x"])
            gap = collect.dist_m(s["lat"], s["lng"], lat, lng)
            state = "OK" if gap < TOL_M else ("수정" if fix and gap < FIX_MAX_M else "확인 필요")
            if state == "수정":
                s["lat"], s["lng"] = round(lat, 6), round(lng, 6)
                changed += 1
            rows.append((c["id"], s["name"], d["place_name"], f"{gap:,.0f}m", state))
    md = ["| 코스 | 관광지 | 카카오 검색 결과 | 오차 | 상태 |", "| --- | --- | --- | --- | --- |"]
    md += [f"| {' | '.join(r)} |" for r in rows]
    (HERE / "course_check.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if fix and changed:
        path.write_text(json.dumps(courses, ensure_ascii=False, indent=1), encoding="utf-8")
    bad = sum(r[4] == "확인 필요" for r in rows)
    print(f"관광지 {len(rows)}곳 · 수정 {changed} · 확인 필요 {bad} → collector/course_check.md")
    return rows


if __name__ == "__main__":
    main(fix="--fix" in sys.argv)
