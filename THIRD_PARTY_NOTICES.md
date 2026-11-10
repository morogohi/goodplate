# 제3자 구성요소·데이터 고지 (Third-Party Notices)

착한맛자랑이 쓰는 제3자 구성요소와 외부 데이터입니다. 각 항목은 표기된 조건을 따르며, [LICENSE](LICENSE)·[COPYRIGHT.md](COPYRIGHT.md)의 제한은 여기에 적용되지 않습니다.

## 외부 데이터

| 데이터 | 위치·용도 | 조건 | 비고 |
|---|---|---|---|
| 카카오 로컬 API (가게 목록·좌표·장소 링크) | `collector/collect.py` → `data/` | Kakao Developers 운영정책·이용약관 | 가게 이름·주소 등 사실 정보 |
| 네이버 검색 API (블로그 언급) | `collector/collect.py` → `data/` | NAVER Developers 이용약관 | 제목·출처·날짜·링크만 저장, 원문은 링크로 연결 |
| YouTube Data API (영상 언급) | `collector/collect.py` → `data/` | YouTube API Services 약관 | 제목·채널·링크만 저장, 영상은 링크로 연결 |
| 착한가격업소 목록 (행정안전부) | `collector/goodprice.csv` (저장소에는 머리글만 있음) | 원 제공처 이용조건 | 아래 '확인 필요' 참고 |
| 나눔가게(선한영향력가게 등) 협약 목록 | `collector/sharing.csv` (저장소에는 머리글만 있음) | 원 제공처 이용조건 | 아래 '확인 필요' 참고 |
| 인스타그램 게시물 링크 | `collector/insta_links.csv` (사람이 직접 넣은 링크만) | 각 게시자의 권리 | 자동 수집하지 않음, 링크만 표시 |

## 소프트웨어·글꼴

| 구성요소 | 용도 | 라이선스 | 출처 |
|---|---|---|---|
| Noto Sans KR, Noto Serif KR | 글꼴 (Google Fonts에서 불러옴) | SIL Open Font License 1.1 | https://fonts.google.com |
| Capacitor (@capacitor/core·android·ios·filesystem·geolocation·share·splash-screen·status-bar) | iOS·Android 앱 | MIT | https://capacitorjs.com |
| @capacitor/cli, @capacitor/assets | 앱 빌드 도구 (개발 의존성) | MIT | npm |
| `android/`, `ios/` 기본 프로젝트 파일 | Capacitor가 생성한 네이티브 템플릿 | Capacitor 라이선스(MIT) | Capacitor CLI |
| Python 수집기 의존성 | `collector/requirements.txt` | 각 패키지 라이선스 | PyPI |

## 확인 필요

- 착한가격업소 목록을 받은 경로(공공데이터포털 파일, 지자체 게시 목록 등)와 공공누리 유형 등 이용조건이 저장소에 기록되어 있지 않습니다. 실제 파일을 넣을 때 출처와 조건을 이 표에 적어 주세요.
- 나눔가게 협약 목록의 원 제공처와 이용조건이 기록되어 있지 않습니다.
- 카카오·네이버·YouTube 응답을 가공해 공개 저장소(`data/`)에 계속 게시하는 방식이 각 API 약관의 저장·재배포 조항에 맞는지 최신 약관으로 확인이 필요합니다.
