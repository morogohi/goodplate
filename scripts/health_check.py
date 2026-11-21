"""운영 점검 — 데이터가 최신인지, 갑자기 줄지 않았는지, 사이트에 반영됐는지 확인
문제가 있으면 내용을 출력하고 종료 코드 1 (워크플로가 GitHub 이슈로 알림)
  python scripts/health_check.py [--live https://morogohi.github.io/goodplate/]"""
import json, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_AGE_H = 30          # 매일 04:00 수집 → 30시간 넘게 갱신이 없으면 이상
MIN_RATIO = 0.7         # 최근 7일 최대치의 70% 아래로 떨어지면 이상


def check(live=None):
    probs, notes = [], []
    idx = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    gen = datetime.fromisoformat(idx["generated_at"].replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - gen).total_seconds() / 3600
    notes.append(f"마지막 수집 {gen:%Y-%m-%d %H:%M} UTC ({age:.0f}시간 전)")
    if idx.get("sample"):
        probs.append("샘플 데이터가 게시돼 있음 (실데이터 수집 실패 가능)")
    if age > MAX_AGE_H:
        probs.append(f"데이터가 {age:.0f}시간 동안 갱신되지 않음 (기준 {MAX_AGE_H}시간)")
    hist_f = ROOT / "data/history.json"
    if hist_f.exists():
        hist = json.loads(hist_f.read_text(encoding="utf-8"))
        if hist:
            last, peak = hist[-1], max(h["stores"] for h in hist[-7:])
            notes.append(f"가게 {last['stores']:,}곳 · 착한가게 {last['good']:,}곳 (최근 7일 최대 {peak:,}곳)")
            if last["stores"] < peak * MIN_RATIO:
                probs.append(f"가게 수 급감: {peak:,} → {last['stores']:,}")
            gpeak = max(h["good"] for h in hist[-7:])
            if gpeak and last["good"] < gpeak * MIN_RATIO:
                probs.append(f"착한가게 수 급감: {gpeak:,} → {last['good']:,} (착한가격업소 목록 내려받기 실패 가능)")
    if live:
        try:
            with urllib.request.urlopen(live.rstrip("/") + "/data/index.json", timeout=20) as r:
                lgen = json.loads(r.read().decode("utf-8")).get("generated_at")
            if lgen != idx["generated_at"]:
                lage = (datetime.now(timezone.utc) - datetime.fromisoformat(lgen.replace("Z", "+00:00"))).total_seconds() / 3600
                (probs if lage > MAX_AGE_H else notes).append(f"사이트 반영 지연: 사이트 {lgen} / 저장소 {idx['generated_at']}")
        except Exception as e:  # noqa: BLE001
            probs.append(f"사이트 접속 실패: {e}")
    return probs, notes


if __name__ == "__main__":
    live = sys.argv[sys.argv.index("--live") + 1] if "--live" in sys.argv else None
    probs, notes = check(live)
    for n in notes:
        print("·", n)
    for p in probs:
        print("⚠", p)
    print("결과:", "이상 있음" if probs else "정상")
    sys.exit(1 if probs else 0)
