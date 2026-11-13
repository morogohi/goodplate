"""API 없이 수집 로직을 검증하는 모의 테스트: python collector/test_collect.py"""
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import collect  # noqa: E402

today = datetime.now(collect.KST)
d = lambda n: (today - timedelta(days=n)).strftime("%Y%m%d")


def fake_get(url, **kw):
    p = kw.get("params", {})
    if "keyword.json" in url:   # 착한가격업소 주소 검색
        return {"documents": [{"id": "9", "x": "126.9840", "y": "37.5705", "category_name": "음식점 > 한식 > 백반",
                               "place_url": "http://place.map.kakao.com/9", "road_address_name": "서울 종로구 인사동길 9"}]}
    if "kakao" in url:
        if p["page"] > 1:
            return {"documents": [], "meta": {"is_end": True}}
        return {"meta": {"is_end": True}, "documents": [
            {"id": "1", "place_name": "테스트국밥 종로점", "category_name": "음식점 > 한식 > 국밥",
             "road_address_name": "서울 종로구 어딘가 1", "x": "126.9910", "y": "37.5716", "place_url": "http://place.map.kakao.com/1"},
            {"id": "2", "place_name": "조용한식당", "category_name": "음식점 > 한식", "x": "126.9912", "y": "37.5718"},
        ]}
    if "naver" in url:
        if "테스트국밥" in p["query"]:
            return {"items": [
                {"title": "<b>테스트국밥</b> 가성비 해장 최고", "description": "친절하고 양 많음", "link": "https://blog/1", "postdate": d(1)},
                {"title": "테스트국밥 협찬 후기", "description": "소정의 원고료", "link": "https://blog/2", "postdate": d(3)},
                {"title": "테스트국밥 옛날 글", "description": "", "link": "https://blog/3", "postdate": d(90)},
                {"title": "다른 가게 이야기", "description": "", "link": "https://blog/4", "postdate": d(1)},
            ]}
        return {"items": []}
    if "googleapis" in url:
        return {"items": [{"id": {"videoId": "abc"}, "snippet": {
            "title": "종로 해장 투어 테스트국밥", "description": "", "publishedAt": today.strftime("%Y-%m-%dT00:00:00Z")}}]}
    raise AssertionError(url)


def run():
    collect.get = fake_get
    collect.time.sleep = lambda s: None
    real_csv = collect.load_csv
    collect.load_csv = lambda n: ([{"업소명": "테스트국밥", "주소": "서울 종로구 어딘가 1", "메뉴1": "순대국밥", "가격1": "8,000원"},
                                   {"업소명": "착한백반집", "주소": "서울 종로구 인사동길 9", "메뉴1": "백반", "가격1": "7000"}]
                                  if n == "goodprice.csv" else [])
    tmp = Path(tempfile.mkdtemp())
    collect.DATA = tmp
    collect.GEOCACHE = tmp / "geocache.json"
    os.environ.update(KAKAO_REST_KEY="x", NAVER_CLIENT_ID="x", NAVER_CLIENT_SECRET="x", YOUTUBE_API_KEY="x")
    collect.main()
    idx = json.loads((tmp / "index.json").read_text(encoding="utf-8"))
    assert len(idx["regions"]) == 17 and idx["courses"], "전국 17개 시도 + 코스"
    assert idx["regions"]["seoul"]["count"] == 2
    j = json.loads((tmp / "r" / "seoul.json").read_text(encoding="utf-8"))
    st = {s["name"]: s for s in j["stores"]}
    s = st["테스트국밥 종로점"]
    assert "조용한식당" not in st, "언급 없는 일반 가게는 제외"
    assert s["src"] == {"yt": 1, "blog": 2, "insta": 0}, s["src"]       # 90일 전 글·다른 가게 글 제외
    assert any(m["sponsored"] for m in s["mentions"]), "협찬 표기 감지"
    assert s["last"] == 0 and s["emoji"] == "🍲"
    assert {"가성비", "해장", "친절", "양 많음"} <= set(s["kw"]), s["kw"]
    assert s["good"] == "price" and s["menu"] == "순대국밥" and s["price"] == 8000, (s.get("menu"), s.get("price"))
    g = st["착한백반집"]   # 카카오 반경에 없던 착한가격업소 → 주소 검색으로 추가, 언급 없어도 유지
    assert g["good"] == "price" and g["price"] == 7000 and g["emoji"] == "🍚"
    assert json.loads((tmp / "geocache.json").read_text(encoding="utf-8")), "좌표 캐시 저장"
    # 네이버 키 없는 모드: 언급 없는 일반 가게도 지역 상위 순위면 남는다
    os.environ.pop("NAVER_CLIENT_ID"); os.environ.pop("NAVER_CLIENT_SECRET")
    collect.main()
    j2 = json.loads((tmp / "r" / "seoul.json").read_text(encoding="utf-8"))
    st2 = {s["name"]: s for s in j2["stores"]}
    assert "조용한식당" in st2 and st2["조용한식당"]["src"] == {"yt": 0, "blog": 0, "insta": 0}, "네이버 없을 때 카카오 상위 가게 유지"
    assert st2["테스트국밥 종로점"]["src"]["yt"] == 1 and "rank" not in st2["조용한식당"], "유튜브 유지·내부 순위 필드 제거"
    collect.load_csv = real_csv
    print("ALL PASS", s["src"], s["kw"], s["price"], g["name"])


if __name__ == "__main__":
    run()
