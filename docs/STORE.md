# 앱스토어·플레이스토어 출시 가이드

웹(GitHub Pages)과 같은 코드(`app.html`)를 Capacitor로 감싸 iOS·Android 앱으로 냅니다. 빌드와 업로드는 Codemagic(`codemagic.yaml`)이 맡습니다. `v1.0.0` 처럼 `v` 로 시작하는 태그를 push 하면 두 스토어용 빌드가 함께 돌아갑니다.

| 항목 | 값 |
| --- | --- |
| 앱 이름 | 착한맛자랑 |
| 번들 ID / 패키지명 | `io.github.morogohi.goodplate` |
| 카테고리 | iOS: 음식 및 음료 (보조: 여행) · Android: 음식 및 음료 |
| 가격 | 무료, 인앱 결제·광고 없음 |
| 지원 기기 | iPhone (iPad 제외), Android 휴대폰 |
| 개인정보처리방침 URL | https://morogohi.github.io/goodplate/privacy.html |
| 지원 URL | https://morogohi.github.io/goodplate/support.html |
| 마케팅 URL | https://morogohi.github.io/goodplate/ |

## 1. 사전 준비 (한 번만)

### Google Play
1. Play Console 에서 앱 만들기 → 패키지명 `io.github.morogohi.goodplate`
2. 업로드 키스토어 생성 후 Codemagic → Team settings → Code signing identities → Android keystores 에 `goodplate_upload_key` 이름으로 등록
   `keytool -genkey -v -keystore goodplate.jks -alias goodplate -keyalg RSA -keysize 2048 -validity 10000`
3. Google Cloud 서비스 계정 JSON 을 만들어 Play Console → 사용자 및 권한에 추가 → Codemagic 환경 변수 그룹 `google_play` 에 `GCLOUD_SERVICE_ACCOUNT_CREDENTIALS` 로 등록
4. 첫 업로드는 Play Console 에 AAB 를 직접 한 번 올려야 API 업로드가 열립니다 (Codemagic 아티팩트의 `.aab` 다운로드 → 내부 테스트 트랙에 수동 업로드)

### App Store
1. Apple Developer 에서 App ID `io.github.morogohi.goodplate` 등록
2. App Store Connect 에서 새 앱 생성 → 생성된 **Apple ID(숫자)** 를 `codemagic.yaml` 의 `APP_STORE_APPLE_ID` 에 넣기
3. App Store Connect API 키(App Manager 권한) 발급 → Codemagic → Team integrations → App Store Connect 에 `goodplate_asc` 이름으로 등록
4. Codemagic 이 서명 인증서·프로비저닝 프로필을 자동으로 만들고 가져옵니다 (`ios_signing`)

## 2. 출시
```bash
git tag v1.0.0 && git push origin v1.0.0
```
- Android → Play Console **내부 테스트** 트랙에 초안으로 올라갑니다. 검토 후 프로덕션으로 승격하세요.
- iOS → **TestFlight** 에 올라갑니다. App Store Connect 에서 심사 제출하세요.

## 3. 스토어 등록 문구

**부제 (iOS, 30자)**: 착한가게·맛집·여행코스를 내 위치에서
**간단한 설명 (Android, 80자)**: 전국 착한가격업소·맛집과 여행코스를 내 위치에서 찾는 무료 공익 서비스

**설명**
```
착한 한 끼로 떠나는 우리 동네 여행, 착한맛자랑

가격을 지키는 착한가게와 동네 사람들이 아끼는 맛집을 내 위치에서 바로 찾아보세요. 관광지 사이 식사 시간에는 근처 착한가게를 골라 여행코스로 이어 드려요.

■ 누구랑, 얼마로, 뭐 먹을지
데이트·친목·회식·부모님·혼밥·아이와 6가지 목적, 1인 예산, 11가지 취향으로 지금 나에게 맞는 가게만 추려 보여 줍니다.

■ 착한 여행코스
경복궁·북촌, 부산 원도심, 전주 한옥마을, 경주, 여수 밤바다, 제주 원도심 등 전국 12개 코스. 식사 시간마다 900m 안 착한가게를 우선 추천하고 다른 가게로 바꿀 수 있어요.

■ 매일 새로 고침
매일 새벽 유튜브·블로그·지도의 새 언급을 모아 NEW로 알려 드려요. 원문은 복사하지 않고 링크로 연결해 만든 분께 조회수가 돌아갑니다. 협찬 글은 따로 표시해요.

■ 사진 한 장으로 응원
다녀온 착한가게를 좋아하는 이유와 함께 공유 카드로 만들어 인스타그램·카카오톡에 나눠 보세요. 사장님은 비용 없이 알려집니다.

■ 착하게 운영해요
· 손님도 가게도 무료, 광고로 순위를 바꾸지 않아요
· 별점 대신 "왜 좋은지"를 보여 줘요
· 회원가입 없음. 위치·리스트·사진은 휴대폰에만 저장되고 서버로 보내지 않아요

착한가격업소는 지자체가 가격·위생·친절을 확인해 지정한 가게입니다. 가게 정보는 자동 수집되어 실제와 다를 수 있으니 방문 전 확인해 주세요.
```
**키워드 (iOS, 100자)**: 착한가게,착한가격업소,맛집,가성비,여행코스,동네맛집,혼밥,부모님,데이트,회식,국밥,나눔가게,지역여행

## 4. 심사 설문 답변
- **개인정보 (App Privacy / 데이터 보안)**: 수집하는 데이터 없음. 위치는 기기 안에서만 처리하고 전송하지 않음 → Apple "Data Not Collected", Google "데이터 수집 없음 · 공유 없음"
- **연령 등급**: 전체 이용가 (폭력·도박·성인 콘텐츠 없음, 사용자 생성 콘텐츠는 기기 안 공유 카드만)
- **암호화**: 표준 HTTPS 만 사용 → `ITSAppUsesNonExemptEncryption = NO` (Info.plist 반영됨)
- **광고**: 없음
- **로그인**: 없음 (심사용 계정 불필요)
- **심사 메모 예시 (Apple 4.2 최소 기능 대비)**: "앱은 기기 위치 기반 가게 검색, 목적·예산·취향 필터, 여행코스 일정과 식사 추천, 기기 내 리스트 저장, 네이티브 공유 시트로 이미지 공유를 제공합니다. 데이터는 매일 갱신되며 오프라인에서도 마지막 데이터로 동작합니다."

## 5. 그래픽 자료 (`store/`)
| 파일 | 용도 | 크기 |
| --- | --- | --- |
| `store/screenshots/ios/*.png` | App Store 6.7" iPhone 스크린샷 5장 | 1290×2796 |
| `store/screenshots/android/*.png` | Google Play 휴대폰 스크린샷 5장 | 1080×1920 |
| `store/feature-graphic.png` | Google Play 그래픽 이미지 | 1024×500 |
| `assets/icon-only.png` | 앱 아이콘 원본 (iOS 1024) | 1024×1024 |

아이콘·스플래시를 바꾸면 `assets/` 의 원본을 고치고 `npm run assets` → `npx cap sync` 하세요.

## 6. 로컬 개발
```bash
npm ci
npm run sync          # app.html → www/ → android/ios 반영
npm run android       # Android Studio 열기
npm run ios           # Xcode 열기 (macOS)
```
