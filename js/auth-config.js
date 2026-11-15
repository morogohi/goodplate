/* 로그인 서버(Supabase) 설정 — docs/LOGIN.md 순서대로 프로젝트를 만든 뒤 두 값을 채우세요.
 * Project URL 과 anon(publishable) key 는 공개용이라 이 파일에 넣어도 됩니다 (데이터는 행 단위 보안 규칙으로 보호).
 * service_role 키 · 카카오/구글 Client Secret 은 절대 여기에 넣지 마세요 (Supabase 대시보드에만 입력).
 * 비어 있으면 로그인 버튼은 '준비 중'으로 보이고, 나머지 기능은 그대로 동작합니다. */
window.AUTH_CONFIG = {
  supabaseUrl: '',
  supabaseAnonKey: '',
  providers: ['kakao', 'google'],
};
