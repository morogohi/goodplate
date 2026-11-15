// 착한맛자랑 서비스워커 — 화면(HTML)·데이터·설정은 네트워크 우선(오프라인이면 캐시), 라이브러리·아이콘은 캐시 우선
const V = 'goodplate-v5';
const SHELL = ['./', 'index.html', 'app.html', 'og.png', 'vendor/leaflet/leaflet.js', 'vendor/leaflet/leaflet.css', 'manifest.webmanifest', 'js/auth-config.js', 'icon.svg', 'icon-192.png', 'data/index.json'];
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (e.request.mode === 'navigate' || u.pathname.endsWith('.html') || u.pathname.endsWith('/') || u.pathname.includes('/data/') || u.pathname.endsWith('/auth-config.js') || u.pathname.endsWith('/sw.js')) {  // 설정·데이터는 최신 우선
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(V).then(x => x.put(e.request, c)); return r; })
      .catch(() => caches.match(e.request, { ignoreSearch: true })));
  } else {
    e.respondWith(caches.match(e.request).then(m => m || fetch(e.request)));
  }
});
