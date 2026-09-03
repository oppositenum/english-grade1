const CACHE = "kouyu-v6";
const PREFIX = "kouyu-v";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-180.png"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const isPage = url.pathname.endsWith("/") || url.pathname.endsWith("/index.html");
  if (isPage) {
    // 页面：先走网络拿最新版，断网时用缓存
    e.respondWith(
      fetch(e.request).then(r => {
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return r;
      }).catch(() => caches.match(e.request))
    );
  } else {
    // 音频等静态资源：本地缓存优先，零延迟
    e.respondWith(
      caches.match(e.request, { ignoreSearch: true }).then(hit => hit ||
        fetch(e.request).then(r => {
          const copy = r.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
          return r;
        })
      )
    );
  }
});
