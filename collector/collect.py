#!/usr/bin/env python3
"""착한맛자랑 — 전국 맛집 일일 수집기

매일 1회 실행해 data/index.json(지역·코스)과 data/r/<시도>.json(가게)을 갱신한다.
지역은 collector/regions.json, 여행코스는 collector/courses.json 에서 관리한다.
  1) 카카오 로컬 API   : 종로 세부지역 반경 안 음식점 목록(이름·좌표·카카오맵 링크)
  2) 네이버 블로그 API : 가게별 최근 블로그 언급(제목·링크·날짜만 저장)
  3) YouTube Data API  : 지역 키워드로 최근 영상 검색 → 제목/설명에 가게명이 있으면 언급으로 연결
  4) 착한가격업소 CSV  : collector/goodprice.csv 와 이름·주소로 대조해 배지 부여
  5) 인스타그램        : 자동 수집하지 않음. collector/insta_links.csv 에 사람이 넣은 링크만 반영

환경변수: KAKAO_REST_KEY, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, YOUTUBE_API_KEY
키가 없는 출처는 건너뛴다. 원문(사진·본문·영상)은 저장하지 않는다.
"""
from __future__ import annotations

import csv
import html
import json
import math
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HERE = Path(__file__).resolve().parent

REGIONS = json.loads((Path(__file__).resolve().parent / "regions.json").read_text(encoding="utf-8"))
COURSES = json.loads((Path(__file__).resolve().parent / "courses.json").read_text(encoding="utf-8"))
# 세부지역 평탄화: {area_key: {..., "sido": "seoul"}}
AREAS = {ak: {**a, "sido": sk} for sk, r in REGIONS.items() for ak, a in r["areas"].items()}
RADIUS_M = 700          # 세부지역별 수집 반경
KAKAO_PAGES = 3         # 페이지당 15곳 → 지역당 최대 45곳
BLOG_DAYS = 30          # 이 기간 안의 블로그 글만 언급으로 인정
YT_DAYS = 14
SPONSORED = re.compile(r"협찬|제공받아|원고료|소정의|체험단|광고")
# 블로그 본문에서 뽑는 키워드 — 웹앱이 목적(데이트·친목·회식·부모님·혼밥·아이와) 분류에 사용
KEYWORDS = ["가성비", "양 많음", "친절", "혼밥", "웨이팅", "노포", "데이트", "분위기", "해장",
            "점심", "집밥", "깔끔", "줄서는", "현지인", "주차", "단체", "포장", "맵",
            "회식", "모임", "룸", "부모님", "효도", "아이", "키즈", "기념일", "조용", "술"]
EMOJI = [("국밥", "🍲"), ("해장", "🍲"), ("찌개", "🥘"), ("만두", "🥟"), ("삼계", "🍲"), ("버거", "🍔"), ("도시락", "🍱"), ("칼국수", "🍜"), ("국수", "🍜"), ("냉면", "🍜"), ("면", "🍜"), ("초밥", "🍣"),
         ("일식", "🍱"), ("돈까스", "🍱"), ("중식", "🥟"), ("분식", "🍙"), ("떡볶이", "🌶️"), ("치킨", "🍗"),
         ("피자", "🍕"), ("양식", "🍝"), ("햄버거", "🍔"), ("카페", "☕"), ("베이커리", "🥐"), ("디저트", "🍰"),
         ("고기", "🥩"), ("한식", "🍚"), ("술집", "🍶"), ("아시아", "🍲")]

S = requests.Session()
S.headers["User-Agent"] = "goodplate-collector/1.0"


# ---------------------------------------------------------------- 공통
def dist_m(a_lat, a_lng, b_lat, b_lng):
    r, t = 6371000, math.pi / 180
    dla, dlo = (b_lat - a_lat) * t, (b_lng - a_lng) * t
    h = math.sin(dla / 2) ** 2 + math.cos(a_lat * t) * math.cos(b_lat * t) * math.sin(dlo / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def clean(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def norm(s: str) -> str:
    s = re.sub(r"\(.*?\)|본점|종로점|광화문점|\s|[^0-9A-Za-z가-힣]", "", s or "")
    return s.lower()


def get(url, **kw):
    for i in range(3):
        r = S.get(url, timeout=15, **kw)
        if r.status_code == 429:
            time.sleep(2 * (i + 1))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()


def emoji_for(cat: str) -> str:
    for k, e in EMOJI:
        if k in cat:
            return e
    return "🍽️"


# ---------------------------------------------------------------- 1. 카카오 로컬
def kakao_stores(key):
    stores, ranks = {}, {}
    for ak, a in AREAS.items():
      for code, pages in (("FD6", KAKAO_PAGES), ("CE7", 1)):   # 음식점 · 카페(코스의 '쉼' 슬롯용)
        for page in range(1, pages + 1):
            j = get("https://dapi.kakao.com/v2/local/search/category.json",
                    headers={"Authorization": f"KakaoAK {key}"},
                    params={"category_group_code": code, "x": a["lng"], "y": a["lat"],
                            "radius": RADIUS_M, "page": page, "sort": "accuracy"})
            for d in j.get("documents", []):
                sid = "k" + d["id"]
                if sid in stores:
                    continue
                cat = d.get("category_name", "").split(">")
                stores[sid] = {
                    "id": sid, "area": ak, "name": d["place_name"],
                    "cat": cat[-1].strip() if cat else "음식점",
                    "cat_full": d.get("category_name", ""),
                    "addr": d.get("road_address_name") or d.get("address_name", ""),
                    "lat": float(d["y"]), "lng": float(d["x"]),
                    "place_url": d.get("place_url"),
                    "_code": code,
                    "rank": ranks.setdefault((ak, code), [0])[0],  # 지역·분류별 카카오 정확도순 순위 (0부터)
                }
                ranks[(ak, code)][0] += 1
            if j.get("meta", {}).get("is_end"):
                break
    return stores


# ---------------------------------------------------------------- 2. 네이버 블로그
def naver_blog(store, cid, secret, now):
    area = AREAS[store["area"]]["name"].split()[-1].split("·")[0]
    j = get("https://openapi.naver.com/v1/search/blog.json",
            headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": secret},
            params={"query": f"\"{store['name']}\" {area}", "display": 20, "sort": "date"})
    out, texts = [], []
    key = norm(store["name"])
    for it in j.get("items", []):
        title, desc = clean(it.get("title")), clean(it.get("description"))
        if key and key not in norm(title + desc):
            continue
        try:
            d = datetime.strptime(it.get("postdate", ""), "%Y%m%d").replace(tzinfo=KST)
        except ValueError:
            continue
        if (now - d).days > BLOG_DAYS:
            continue
        sponsored = bool(SPONSORED.search(title + desc))
        out.append({"src": "blog", "title": title[:80], "url": it.get("link"),
                    "date": d.date().isoformat(), "sponsored": sponsored})
        texts.append(title + " " + desc)
    return out, texts


# ---------------------------------------------------------------- 3. 유튜브
def youtube_mentions(stores, key, now):
    after = (now - timedelta(days=YT_DAYS)).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    by_key = {norm(s["name"]): s["id"] for s in stores.values() if len(norm(s["name"])) >= 3}
    hits: dict[str, list] = {}
    for a in AREAS.values():
        for q in a["q"]:          # 검색 1회 = 100 units, 하루 무료 10,000 units
            j = get("https://www.googleapis.com/youtube/v3/search",
                    params={"key": key, "part": "snippet", "q": q, "type": "video",
                            "maxResults": 50, "order": "date", "publishedAfter": after,
                            "regionCode": "KR", "relevanceLanguage": "ko"})
            for it in j.get("items", []):
                sn = it["snippet"]
                text = norm(sn.get("title", "") + sn.get("description", ""))
                vid = it["id"]["videoId"]
                for k, sid in by_key.items():
                    if k in text and not any(m["url"].endswith(vid) for m in hits.get(sid, [])):
                        hits.setdefault(sid, []).append({
                            "src": "yt", "title": clean(sn["title"])[:80],
                            "url": f"https://www.youtube.com/watch?v={vid}",
                            "date": sn["publishedAt"][:10], "sponsored": False})
    return hits


# ---------------------------------------------------------------- 4·5. 로컬 CSV
def load_csv(name):
    p = HERE / name
    if not p.exists():
        return []
    with p.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


MENU_COLS = ("대표메뉴", "메뉴", "메뉴1", "품목", "품목1")
PRICE_COLS = ("가격", "가격1", "대표가격", "판매가격")
GEOCACHE = HERE / "geocache.json"


def fetch_goodprice():
    """GOODPRICE_CSV_URL 이 있으면 착한가격업소 목록을 내려받아 goodprice.csv 로 저장 (UTF-8·CP949 모두 처리)"""
    url = os.getenv("GOODPRICE_CSV_URL")
    if not url:
        return
    try:
        r = S.get(url, timeout=60)
        r.raise_for_status()
        raw = r.content
        for enc in ("utf-8-sig", "cp949"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            print("[goodprice] 인코딩을 알 수 없어 건너뜀")
            return
        if "업소명" not in text.splitlines()[0] and "상호" not in text.splitlines()[0]:
            print("[goodprice] 첫 줄에 업소명/상호 열이 없어 건너뜀 — CSV 파일 주소인지 확인하세요")
            return
        (HERE / "goodprice.csv").write_text(text, encoding="utf-8")
        print(f"[goodprice] {len(text.splitlines()) - 1}행 내려받음")
    except requests.RequestException as e:
        print("[goodprice] 내려받기 실패, 기존 파일 사용:", e)


def good_rows(rows):
    """착한가격업소 CSV 행을 표준 형태로. 컬럼명이 조금 달라도 읽는다.
    필수: 업소명 · 선택: 주소, 대표메뉴/메뉴1/품목, 가격/가격1"""
    out = []
    for r in rows:
        name = (r.get("업소명") or r.get("상호") or "").strip()
        if not name:
            continue
        menu = next((r[c].strip() for c in MENU_COLS if r.get(c)), None)
        price = next((r[c] for c in PRICE_COLS if r.get(c)), None)
        price = int(re.sub(r"[^0-9]", "", price)) if price and re.sub(r"[^0-9]", "", price) else None
        out.append({"name": name, "addr": (r.get("주소") or r.get("소재지") or "").strip(), "menu": menu, "price": price})
    return out


def addr_ok(a, b):
    """두 주소가 같은 시군구·도로명을 공유하면 True (한쪽이 비어 있으면 True)"""
    if not a or not b:
        return True
    ta, tb = set(a.split()[:4]), set(b.split()[:4])
    return len(ta & tb) >= 2


def match_good(store, goods, sharing):
    k = norm(store["name"])
    for g in goods:
        if norm(g["name"]) == k and addr_ok(g["addr"], store.get("addr", "")):
            if g["menu"] and not store.get("menu"):
                store["menu"] = g["menu"]
            if g["price"] and not store.get("price"):
                store["price"] = g["price"]
            g["_matched"] = True
            return "price"
    for row in sharing:     # 컬럼: 업소명 (선한영향력가게 등 협약 목록)
        if norm(row.get("업소명", "")) == k:
            return "share"
    return None


def add_unmatched_goods(stores, goods, key):
    """카카오 반경 수집에 안 잡힌 착한가격업소를 주소로 찾아 서비스 지역(3km 안)이면 추가.
    좌표는 geocache.json 에 저장해 다음 날 다시 호출하지 않는다."""
    cache = json.loads(GEOCACHE.read_text(encoding="utf-8")) if GEOCACHE.exists() else {}
    added = 0
    for g in goods:
        if g.get("_matched"):
            continue
        ck = f"{g['name']}|{g['addr']}"
        if ck not in cache:
            q = f"{g['name']} {' '.join(g['addr'].split()[:2])}".strip()
            try:
                j = get("https://dapi.kakao.com/v2/local/search/keyword.json",
                        headers={"Authorization": f"KakaoAK {key}"}, params={"query": q, "size": 1})
                d = (j.get("documents") or [None])[0]
            except requests.HTTPError:
                d = None
            cache[ck] = d and {"id": d["id"], "x": d["x"], "y": d["y"], "cat": d.get("category_name", ""),
                               "url": d.get("place_url"), "addr": d.get("road_address_name") or d.get("address_name", "")}
        d = cache[ck]
        if not d:
            continue
        lat, lng = float(d["y"]), float(d["x"])
        ak, dm = min(((k, dist_m(a["lat"], a["lng"], lat, lng)) for k, a in AREAS.items()), key=lambda t: t[1])
        sid = "k" + d["id"]
        if dm > 3000 or sid in stores:
            continue
        cat = d["cat"].split(">")
        stores[sid] = {"id": sid, "area": ak, "name": g["name"], "cat": cat[-1].strip() if cat else "음식점",
                       "cat_full": d["cat"], "addr": d["addr"] or g["addr"], "lat": lat, "lng": lng,
                       "place_url": d["url"], "menu": g["menu"], "price": g["price"], "_good": "price"}
        added += 1
    GEOCACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return added


# ---------------------------------------------------------------- 실행
def main():
    now = datetime.now(KST)
    kakao = os.getenv("KAKAO_REST_KEY")
    nid, nsec = os.getenv("NAVER_CLIENT_ID"), os.getenv("NAVER_CLIENT_SECRET")
    yt = os.getenv("YOUTUBE_API_KEY")
    if not kakao:
        # 키를 아직 등록하지 않았으면 실패 대신 건너뛴다 (샘플 데이터 유지, 매일 실패 알림 방지)
        print("KAKAO_REST_KEY 가 없어 수집을 건너뜁니다. 저장소 Settings → Secrets 에 등록하세요.")
        sys.exit(0)

    only = [s for s in os.getenv("SIDO", "").split(",") if s]   # 예: SIDO=seoul,busan (비우면 전국)
    if only:
        for k in [k for k, a in AREAS.items() if a["sido"] not in only]:
            AREAS.pop(k)
    prev = {}
    for f in (DATA / "r").glob("*.json"):
        try:
            old = json.loads(f.read_text(encoding="utf-8"))
            if not old.get("sample"):
                prev.update({s["id"]: s for s in old.get("stores", [])})
        except Exception:
            pass

    stores = kakao_stores(kakao)
    print(f"[kakao] {len(stores)}곳")
    fetch_goodprice()
    good, share = good_rows(load_csv("goodprice.csv")), load_csv("sharing.csv")
    for s in stores.values():
        s["good"] = match_good(s, good, share)
    print(f"[goodprice] 추가 {add_unmatched_goods(stores, good, kakao)}곳")
    insta = load_csv("insta_links.csv")   # 컬럼: 업소명, url, date(YYYY-MM-DD)

    yt_hits = youtube_mentions(stores, yt, now) if yt else {}
    print(f"[youtube] {sum(map(len, yt_hits.values()))}건")

    blog_n = 0
    for s in stores.values():
        mentions, texts = [], []
        if nid and nsec:
            try:
                m, t = naver_blog(s, nid, nsec, now)
                mentions += m
                texts += t
                blog_n += len(m)
            except requests.HTTPError as e:
                print("[naver] skip", s["name"], e)
            time.sleep(0.12)
        mentions += yt_hits.get(s["id"], [])
        for row in insta:
            if norm(row.get("업소명", "")) == norm(s["name"]) and row.get("url"):
                mentions.append({"src": "insta", "title": "인스타그램 게시물 (사용자 공유)",
                                 "url": row["url"], "date": row.get("date") or now.date().isoformat(),
                                 "sponsored": False})
        mentions.sort(key=lambda m: m["date"], reverse=True)
        cnt = {k: sum(1 for m in mentions if m["src"] == k) for k in ("yt", "blog", "insta")}
        joined = " ".join(texts)
        s.update({
            "emoji": emoji_for(s["cat_full"]),
            "good": s.pop("_good", None) or s.get("good"),
            "src": cnt,
            "mentions": mentions[:8],
            "kw": [k for k in KEYWORDS if k in joined][:8],
            "last": (now.date() - datetime.fromisoformat(mentions[0]["date"]).date()).days if mentions else None,
            "first_seen": prev.get(s["id"], {}).get("first_seen", now.date().isoformat()),
        })
        s.pop("cat_full", None)
    print(f"[naver] {blog_n}건" if nid and nsec else "[naver] 키 없음 — 블로그 언급 없이 지역별 카카오 상위 가게를 함께 싣습니다")

    # 언급이 하나도 없는 일반 가게는 빼고, 착한가게는 언급이 없어도 남긴다
    keep = select_stores(stores.values(), naver=bool(nid and nsec))
    write_outputs(keep, now)


def _count(sk):
    try:
        return len(json.loads((DATA / "r" / f"{sk}.json").read_text(encoding="utf-8"))["stores"])
    except Exception:
        return 0


KEEP_PER_AREA = 15   # 블로그 수집이 없을 때 지역·분류(음식점/카페)마다 남길 카카오 상위 가게 수


def select_stores(stores, naver):
    """남길 가게 고르기.
    - 언급(유튜브·블로그·인스타)이 있거나 착한가게면 항상 남긴다.
    - 네이버 블로그 수집이 없으면 언급이 드물어 목록이 비므로, 지역별 카카오 상위 가게도 남긴다."""
    stores = list(stores)
    keep = {s["id"]: s for s in stores if s["mentions"] or s["good"]}
    if not naver:
        for s in stores:
            if s.get("rank", 99) < KEEP_PER_AREA:
                keep.setdefault(s["id"], s)
    out = list(keep.values())
    for s in out:
        s.pop("rank", None)
        s.pop("_code", None)
    return out


def write_outputs(keep, now, sample=False):
    (DATA / "r").mkdir(parents=True, exist_ok=True)
    stamp = now.isoformat(timespec="minutes")
    counts, goods = {}, {}
    for sk in {AREAS[s["area"]]["sido"] for s in keep} | {a["sido"] for a in AREAS.values()}:
        rows = [s for s in keep if AREAS[s["area"]]["sido"] == sk]
        counts[sk] = len(rows)
        goods[sk] = sum(1 for s in rows if s.get("good"))
        (DATA / "r" / f"{sk}.json").write_text(json.dumps(
            {"sample": sample, "sido": sk, "generated_at": stamp, "stores": rows},
            ensure_ascii=False, indent=1), encoding="utf-8")
    index = {
        "sample": sample, "generated_at": stamp,
        "regions": {sk: {"name": r["name"], "count": counts[sk] if sk in counts else _count(sk), "good": goods.get(sk, 0),
                         "areas": {ak: {"name": a["name"], "lat": a["lat"], "lng": a["lng"]}
                                   for ak, a in r["areas"].items()}}
                    for sk, r in REGIONS.items()},
        "courses": COURSES,
    }
    (DATA / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[done] {len(keep)}곳 · {len(counts)}개 시도 → {DATA}")


if __name__ == "__main__":
    main()
