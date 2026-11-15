# 카카오·구글 로그인 켜기 (Supabase) — 약 30분

로그인은 **선택 기능**입니다. 설정 전에는 계정 버튼이 '준비 중'으로 보이고 나머지 기능은 그대로 동작합니다.
로그인하면 내 리스트(저장한 가게·코스·식당 선택·메모·뽐내기 기록)를 여러 기기에서 이어 봅니다. 위치·사진·맞춤 조건은 보내지 않습니다.

> 운명 연구소와 **별도의 Supabase 프로젝트**를 권장합니다 (카카오·구글 동의 화면에 서비스 이름이 '착한맛자랑'으로 나오도록, 데이터도 분리).
> 무료 플랜은 1주일 동안 접속이 없으면 일시 정지될 수 있습니다 → 대시보드에서 Restore.

## 1. Supabase 프로젝트
1. https://supabase.com → New project — 이름 `goodplate`, 지역 Northeast Asia (Seoul)
2. **SQL Editor** → `docs/supabase-login.sql` 전체 붙여 넣고 Run
3. **Authentication → URL Configuration**
   - Site URL: `https://morogohi.github.io/goodplate/app.html`
   - Redirect URLs: `https://morogohi.github.io/goodplate/app.html`, `io.github.morogohi.goodplate://auth`(앱), `http://localhost:8765/app.html`(로컬 테스트용)
4. **Project Settings → API**: `Project URL`, `anon public`(또는 publishable) 키를 복사 — **service_role 키는 절대 쓰지 않음**
5. **Authentication → Providers → Callback URL** 복사 (`https://<프로젝트>.supabase.co/auth/v1/callback`)

## 2. 카카오
1. https://developers.kakao.com → 내 애플리케이션 → 애플리케이션 추가 (앱 이름 `착한맛자랑`)
2. 앱 설정 → 플랫폼 → Web: `https://morogohi.github.io`
3. 카카오 로그인 → 활성화 ON, Redirect URI: 1-5의 Callback URL
4. 동의항목: 닉네임·프로필 사진 = 필수/선택 동의 (이메일은 요청하지 않음)
5. 보안 → Client Secret 생성 → 활성화
6. Supabase → Authentication → Providers → **Kakao**: Enabled, Client ID = **REST API 키**, Client Secret = 5번 값,
   **Allow users without an email** 켜기 → Save

## 3. 구글
1. https://console.cloud.google.com → 새 프로젝트 `goodplate`
2. OAuth 동의 화면: 외부, 앱 이름 `착한맛자랑`, 지원 이메일, 승인된 도메인 `supabase.co`, `github.io`
   개인정보처리방침 `https://morogohi.github.io/goodplate/privacy.html` → **앱 게시(프로덕션)**
3. 사용자 인증 정보 → OAuth 클라이언트 ID → 웹 애플리케이션
   - 승인된 JavaScript 원본: `https://morogohi.github.io`
   - 승인된 리디렉션 URI: 1-5의 Callback URL
4. Supabase → Providers → **Google**: Enabled, Client ID·Secret 입력 → Save

## 4. 사이트에 연결
`js/auth-config.js` 의 두 값만 채우고 push (또는 Project URL·anon 키를 Claude에게 알려 주면 넣어 드림):
```js
supabaseUrl: 'https://xxxx.supabase.co',
supabaseAnonKey: 'eyJ... 또는 sb_publishable_...',
```
배포 후 서비스 화면 오른쪽 위 👤 → 카카오/구글로 시작하기 → 저장한 가게가 다른 기기에서 보이면 완료.

## 보안 원칙
- 코드·채팅에 넣어도 되는 값: Project URL, anon/publishable 키 (공개용, 데이터는 행 단위 보안 규칙으로 보호)
- 절대 넣지 않는 값: service_role 키, 카카오·구글 Client Secret (Supabase 대시보드에만)
- 탈퇴는 앱 안 계정 화면에서 바로 (`delete_my_account` → 계정·리스트 함께 삭제)

## 5. 앱(iOS·Android) 로그인
앱은 시스템 브라우저(안드로이드 Custom Tabs, iOS Safari 창)로 로그인하고 `io.github.morogohi.goodplate://auth` 로 돌아옵니다 (구현 완료).
- **안드로이드**: 1-3의 Redirect URLs에 앱 주소만 있으면 바로 동작. 카카오 플랫폼에 Android 등록은 필요 없음(웹 로그인 방식).
- **iOS**: Apple 심사 지침 4.8 때문에 **Sign in with Apple을 켜야** 앱에 로그인 버튼이 보입니다 (안 켜면 '다음 업데이트' 안내만).
  1. Apple Developer → Identifiers → `io.github.morogohi.goodplate` → **Sign In with Apple** 체크
  2. Identifiers → **Services IDs** 추가 (예: `io.github.morogohi.goodplate.web`) → Sign In with Apple 설정: 도메인 `<프로젝트>.supabase.co`, Return URL = 1-5 Callback URL
  3. Keys → 새 키(Sign in with Apple) → .p8 내려받기 · Key ID · Team ID 확인
  4. Supabase → Providers → **Apple**: Client IDs = `io.github.morogohi.goodplate.web`, Secret Key는 Supabase 문서의 생성 도구로 .p8에서 만든 값 (**6개월마다 갱신 필요**)
  5. `js/auth-config.js` 의 providers 에 `'apple'` 추가
- 앱 새 버전(v 태그) 빌드 후 실제 기기에서 확인. 스토어 데이터 보안 설문도 바꿔야 함 (`docs/STORE.md` 4절).
