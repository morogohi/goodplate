# 제보 처리 방법 — 이용자 제보를 데이터에 반영하기

이용자가 앱에서 **정보가 달라요 · 수정 요청** 또는 **가게 제보하기**를 누르면 아래 두 곳 중 하나로 들어와요.

| 로그인 서버(Supabase) | 들어오는 곳 |
|---|---|
| 설정 전 | 메일 — support.um09@gmail.com (제목 `[착한맛자랑] …`, 본문에 가게 ID) |
| 설정 후 | Supabase → Table Editor → `reports` (익명, `status = new`) |

## 처리 순서 (가게 1곳에 3분)

1. **확인**: 가게 화면의 카카오맵 링크·전화·최근 리뷰로 사실인지 확인해요. 확인이 안 되면 `rejected`.
2. **고치기**: 저장소의 `collector/overrides.json` 에 한 줄 추가 (GitHub 웹에서 연필 아이콘으로 바로 편집 가능).
3. **반영**: 다음 날 새벽 4시 자동 수집 때 적용돼요. 바로 반영하려면 Actions → daily-collect → Run workflow.
4. **마무리**: Supabase `reports` 의 `status` 를 `done` 으로 바꿔요. 메일 제보는 답장으로 "반영했어요"를 알려 주세요.

수정 파일은 매일 수집 결과에 **다시 적용**되므로, 카카오 정보가 그대로여도 고친 내용이 사라지지 않아요. 고친 가게에는 앱에서 "운영자 확인" 표시가 붙어요.

## overrides.json 작성법

```json
{
  "hide": [
    {"id": "k14951761", "why": "폐업 확인 2026-11-21"},
    {"name": "○○헬스", "area": "jongno-jonggak", "why": "음식점 아님"}
  ],
  "fix": {
    "k1234567": {"price": 9000, "menu": "김치찌개", "date": "2026-11-21", "why": "가격 인상 제보"},
    "k7654321": {"good": null, "why": "착한가격업소 지정 해제"},
    "k1111111": {"lat": 37.5712, "lng": 126.9841, "why": "위치 수정"}
  },
  "add": [
    {"id": "m-0001", "name": "종로 착한분식", "area": "jongno-jonggak", "lat": 37.5701, "lng": 126.9832,
     "cat": "분식", "emoji": "🍜", "menu": "칼국수", "price": 7000, "good": "price",
     "addr": "서울 종로구 …", "date": "2026-11-21", "why": "이용자 제보 + 지자체 목록 확인"}
  ]
}
```

- **가게 ID**: 앱 가게 화면 → 공유 링크 끝(`#store-seoul-k1234567`)이나 제보 메일 본문의 `가게 ID`.
- **hide**: `id` 로 숨기거나, 같은 지역(`area`)의 같은 이름으로 숨겨요.
- **fix**: 바꿀 수 있는 항목은 `name, menu, price, pp(1인 가격), good(price/share/null), lat, lng, addr, cat, emoji, place_url`. `null` 은 그 항목을 지워요.
- **add**: `id`(직접 추가는 `m-` 로 시작), `name`, `area`, `lat`, `lng` 는 꼭 넣어요. `area` 는 `collector/regions.json` 의 세부 지역 키.
- `why`·`date` 는 기록용이에요 (`date` 는 "운영자 확인" 날짜로 표시).

## 자주 오는 제보와 처리

| 제보 | 처리 |
|---|---|
| 가격·메뉴가 달라요 | `fix` 에 `price`·`menu` |
| 문을 닫았어요 | 카카오맵에서 폐업 확인 → `hide` |
| 위치가 달라요 | 카카오맵 좌표 확인 → `fix` 에 `lat`·`lng` |
| 착한가게 표시가 틀려요 | 지자체 착한가격업소 목록 확인 → `fix` 에 `good` |
| 가게 제보 | 착한가격업소 목록에 있으면 다음 수집에서 자동 포함될 수 있음, 없으면 `add` |

같은 유형이 자주 오면(예: 특정 업종이 계속 섞임) 수집 규칙(`collector/collect.py`)을 고치는 편이 나아요.
