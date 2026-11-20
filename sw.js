// 헤아림 앱 설치용 서비스 워커: 화면 파일은 늘 새로 받고, 인터넷이 끊겼을 때만 저장해 둔 것을 씀
// 설문·답(파이어베이스)은 건드리지 않음
const CACHE = 'hearim-v2';
const SHELL = ['./', 'index.html', 'qrcode.js', 'icon.svg', 'icon-192.png', 'manifest.webmanifest', 'demo.js'];
self.addEventListener('install', function(e){ e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(SHELL); }).catch(function(){})); self.skipWaiting(); });
self.addEventListener('activate', function(e){ e.waitUntil(caches.keys().then(function(ks){ return Promise.all(ks.filter(function(k){ return k !== CACHE; }).map(function(k){ return caches.delete(k); })); }).then(function(){ return self.clients.claim(); })); });
self.addEventListener('fetch', function(e){
  const req = e.request; if (req.method !== 'GET') return;
  const url = new URL(req.url); if (url.origin !== self.location.origin) return;
  e.respondWith(fetch(req).then(function(res){
    if (res && res.ok && url.pathname.indexOf('/promo/') < 0) { const cp = res.clone(); caches.open(CACHE).then(function(c){ c.put(req, cp); }); }
    return res;
  }).catch(function(){ return caches.match(req, { ignoreSearch: true }).then(function(r){ return r || caches.match('index.html'); }); }));
});
