// 착한맛자랑 서비스워커 — 화면은 캐시 우선, 데이터(data/)는 네트워크 우선(실패 시 캐시)
const V = 'goodplate-v3';
const SHELL = ['./', 'index.html', 'app.html', 'og.png', 'manifest.webmanifest', 'icon.svg', 'icon-192.png', 'data/index.json'];
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return;
  if (u.pathname.includes('/data/')) {
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(V).then(x => x.put(e.request, c)); return r; })
      .catch(() => caches.match(e.request)));
  } else {
    e.respondWith(caches.match(e.request).then(m => m || fetch(e.request)));
  }
});
