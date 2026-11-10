"""data/ 의 샘플(또는 최신) 데이터를 index.html 의 내장 대체 데이터로 넣는다."""
import json
from pathlib import Path
root = Path(__file__).resolve().parent.parent
idx = json.loads((root / "data/index.json").read_text(encoding="utf-8"))
r = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (root / "data/r").glob("*.json")}
blob = json.dumps({"index": idx, "r": r}, ensure_ascii=False, separators=(",", ":"))
h = (root / "app.html").read_text(encoding="utf-8")
a = h.index("const SAMPLE=") + len("const SAMPLE=")
b = h.index(";\nconst BG=")
(root / "app.html").write_text(h[:a] + blob + h[b:], encoding="utf-8")
print(f"embedded {len(blob)//1024}KB")
