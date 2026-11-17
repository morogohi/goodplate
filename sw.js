// 착한맛자랑 서비스워커 — 화면(HTML)·데이터·설정은 네트워크 우선(오프라인이면 캐시), 라이브러리·아이콘은 캐시 우선
const V = 'goodplate-v8';
const SHELL = ['./', 'index.html', 'app.html', 'og.png', 'vendor/leaflet/leaflet.js', 'vendor/leaflet/leaflet.css', 'manifest.webmanifest', 'js/auth-config.js', 'js/map-config.js', 'icon.svg', 'apple-touch-icon.png', 'icon-maskable-512.png', 'icon-192.png', 'data/index.json'];
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => c.addAll(SHELL.map(u => new Request(u, { cache: 'reload' })))).then(() => self.skipWaiting())));   // 설치 때도 HTTP 캐시를 건너뛰고 최신 파일로
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (e.request.mode === 'navigate' || u.pathname.endsWith('.html') || u.pathname.endsWith('/') || u.pathname.includes('/data/') || u.pathname.endsWith('-config.js') || u.pathname.endsWith('/sw.js')) {  // 설정·데이터는 최신 우선
    // 화면·데이터는 HTTP 캐시(최대 10분)도 거치지 않고 서버에 확인 → 배포 즉시 반영
    const req = e.request.mode === 'navigate' ? new Request(u.href, { cache: 'no-cache', credentials: 'same-origin' }) : new Request(e.request, { cache: 'no-cache' });
    e.respondWith(fetch(req).then(r => { const c = r.clone(); if (r.ok) caches.open(V).then(x => x.put(e.request, c)); return r; })
      .catch(() => caches.match(e.request, { ignoreSearch: true })));
  } else {
    e.respondWith(caches.match(e.request).then(m => m || fetch(e.request)));
  }
});
