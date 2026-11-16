/* 지도 설정 — 카카오맵 JavaScript 키 (카카오 디벨로퍼스 → 내 애플리케이션 → 앱 키 → JavaScript 키)
 * JavaScript 키는 웹페이지에 공개되는 용도라 여기에 넣어도 됩니다. 대신 카카오 콘솔의
 * [플랫폼 → Web 사이트 도메인]에 등록된 주소에서만 지도가 열립니다:
 *   https://morogohi.github.io   (웹)
 *   https://localhost             (안드로이드 앱)
 *   http://localhost:8765         (로컬 테스트, 선택)
 * REST API 키·Admin 키는 절대 넣지 마세요. 비어 있거나 지도를 못 불러오면 기본 지도(OpenStreetMap)로 자동 대체됩니다. */
window.MAP_CONFIG = {
  kakaoJsKey: '',
};
