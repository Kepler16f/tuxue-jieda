/* 图学基础教程习题解答 · 离线缓存 Service Worker
   策略：HTML/CSS/JS/数据 network-first（保证更新可下发），图片/视频 cache-first（省流量）。 */
const CORE = [
  './', './index.html', './style.css', './app.js',
  './data/index.js', './manifest.webmanifest'
];
const CACHE = 'tuxue-v16';

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isCode(url) {
  return /\.(html|css|js|webmanifest)$/.test(url.pathname) || url.pathname.endsWith('/');
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || !req.url.startsWith(self.location.origin)) return;
  if (req.headers.has('range')) return; // 视频拖动直连
  const url = new URL(req.url);

  if (isCode(url)) {
    e.respondWith(
      fetch(req).then((res) => {
        if (res && res.ok && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  e.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && res.ok && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      });
    })
  );
});
