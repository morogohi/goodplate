# 착한맛자랑 — 전국 착한 맛집 + 여행코스 (무료·공익 모바일 웹)

전국 17개 시도 25개 지역의 맛집 언급을 매일 새벽 4시에 자동으로 모읍니다. 실제 관광지로 짠 여행코스 12개의 식사 시간에는 근처 착한가게를 자동으로 추천합니다.

```
index.html                     모바일 웹앱 (단일 파일 · data/ 를 읽고, 없으면 내장 샘플 사용)
data/index.json                시도·지역·여행코스 목록
data/r/<시도>.json             시도별 가게·언급 데이터 (지금은 가상 샘플, "sample": true)
collector/regions.json         수집 지역 (시도 → 세부지역 좌표·검색어) ← 지역 추가는 여기서
collector/courses.json         여행코스 (관광지 좌표·체류시간·식사 슬롯) ← 코스 추가는 여기서
collector/collect.py           일일 수집기 (카카오 로컬·네이버 블로그·YouTube)
collector/test_collect.py      API 없이 돌리는 모의 테스트
collector/make_sample.py       가상 샘플 생성
collector/embed_sample.py      data/ 를 index.html 내장 대체 데이터로 넣기
collector/goodprice.csv        착한가격업소 목록 (업소명,주소) — 행안부 누리집·공공데이터에서 내려받아 채움
collector/sharing.csv          나눔가게 목록 (업소명)
collector/insta_links.csv      사람이 확인한 인스타 링크 (업소명,url,date) — 인스타는 자동 수집 안 함
.github/workflows/collect.yml  매일 04:00 KST 실행 → data/ 커밋
```

## 화면
- **홈**: 지역 인사·검색, **누구랑 가세요?(데이트·친목·회식·부모님·혼밥·아이와)**, 예산·취향 맞춤 결과, 이 지역 여행코스, 주목받는 착한가게, 전국 코스
- **맞춤 찾기**: 목적 6종 · 1인 예산 4구간 · 취향 11종(한식·국밥·탕·면·고기·해산물·중식·일식·양식·분식·카페·디저트·매운맛). 분류는 업종·메뉴·가격과 블로그 키워드(분위기·단체·친절·혼밥 등)로 웹앱이 자동 판정 (`classify()`), 지도·홈·코스 식사 추천에 공통 적용
- **지도**: 반경 500m/1km/3km, 착한가게만, 가까운순·화제순·최신 언급
- **여행코스**: 코스 상세(예상 소요·이동거리, 경로도, 단계별 타임라인), 식사 슬롯마다 근처 착한가게 자동 추천과 ↻ 교체, 코스 저장·공유 카드
- **내 리스트**: 가보고 싶어요 / 다녀왔어요 / 단골 / 저장한 코스, 가게별 메모
- **뽐내기**: 사진과 좋아하는 이유(별점 없음)로 인스타·카톡 공유 카드 만들기

## 1. API 키 (모두 무료)
| 키 | 발급처 | 용도 |
| --- | --- | --- |
| `KAKAO_REST_KEY` | developers.kakao.com → 내 애플리케이션 → REST API 키 | 가게 목록·좌표 (필수) |
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | developers.naver.com → 검색 API | 블로그 언급 |
| `YOUTUBE_API_KEY` | console.cloud.google.com → YouTube Data API v3 | 영상 언급 |

전국 기준 하루 호출량(추정)은 다음과 같습니다. 발급할 때 최신 쿼터를 확인하세요.
- 카카오: 지역 25곳 × 3페이지
- 네이버: 가게 수만큼, 최대 약 1,100회
- YouTube: 검색 약 32회 × 100 units, 약 3,200 units

`SIDO=seoul,busan` 처럼 지정하면 일부 시도만 갱신합니다.

## 2. GitHub 배포
1. 이 폴더를 새 저장소(예: `morogohi/goodplate`)에 올립니다.
2. Settings → Secrets and variables → Actions 에 키 4개를 등록합니다.
3. Actions → `daily-collect` → Run workflow 로 첫 수집을 합니다.
4. Settings → Pages → `main` / root 를 켜면 `https://morogohi.github.io/goodplate/` 에서 서비스가 열립니다.

실데이터가 쌓이면 `python collector/embed_sample.py` 로 내장 대체 데이터도 갱신할 수 있습니다(선택).

## 3. 착한가격업소 목록·좌표 검증
- `collector/goodprice.csv` 는 `업소명` 필수, `주소`·`대표메뉴`(또는 `메뉴1`·`품목`)·`가격`(또는 `가격1`) 열을 읽습니다. 행안부 목록을 그대로 넣어도 됩니다.
- 이름이 같고 주소가 맞는 가게에는 배지·대표 메뉴·가격을 붙입니다. 이 가격으로 웹앱의 예산 필터가 작동합니다.
- 카카오 반경 수집에 안 잡힌 착한가격업소는 주소로 검색해 서비스 지역 3km 안이면 추가합니다. 좌표는 `collector/geocache.json` 에 캐시합니다.
- 여행코스 좌표 검증: Actions → `verify-courses` 실행. 결과는 `collector/course_check.md` 에 남습니다. `fix` 를 켜면 250m~3km 오차 좌표를 자동 수정하고, 3km 이상은 사람이 확인합니다.

## 4. 위치·설치
- **📍 내 위치**: GitHub Pages(https)에서 GPS 로 가장 가까운 서비스 지역을 찾습니다. 좌표는 기기 메모리에만 두고 저장·전송하지 않습니다. 20km 안에 서비스 지역이 없으면 가장 가까운 지역을 보여줍니다.
- **PWA**: `manifest.webmanifest`·`sw.js`. 홈 화면에 추가할 수 있고, 마지막으로 본 데이터는 오프라인에서도 보입니다.

## 5. 수집 원칙
- 원문 사진·본문·영상은 저장하지 않습니다. **제목·출처·날짜·링크만** 저장해 원문으로 보냅니다.
- 협찬·원고료·체험단 문구가 있는 블로그 글은 `sponsored` 로 표시합니다.
- 언급 없는 일반 가게는 빼고, 착한가게는 언급이 없어도 남깁니다.
- 손님 위치는 기기에서만 계산합니다.
- 여행코스 관광지 좌표는 근사값이므로, 운영 전에 한국관광공사 TourAPI 등으로 검증하세요.

## 로컬 실행
```bash
pip install -r collector/requirements.txt
python collector/test_collect.py
python -m http.server 8000      # http://localhost:8000
```
