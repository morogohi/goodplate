"""data/ 의 샘플(또는 최신) 데이터를 index.html 의 내장 대체 데이터로 넣는다."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent.parent
idx = json.loads((root / "data/index.json").read_text(encoding="utf-8"))
r = {}   # 가게 데이터는 data/r/*.json 에서 불러온다 (첫 화면을 가볍게: 지역·코스 목록만 내장)
blob = json.dumps({"index": idx, "r": r}, ensure_ascii=False, separators=(",", ":"))
h = (root / "app.html").read_text(encoding="utf-8")
a = h.index("const SAMPLE=") + len("const SAMPLE=")
b = h.index(";\nconst BG=")
(root / "app.html").write_text(h[:a] + blob + h[b:], encoding="utf-8")
print(f"embedded {len(blob)//1024}KB")
