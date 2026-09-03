"""扫描站点文件生成 sw.js（Service Worker），把整站预缓存到手机本地。
音频有增删或 index.html 更新后重新运行一次，并把 VERSION 自动+1。"""
import re
from pathlib import Path

ROOT = Path(__file__).parent

def main():
    # 安装时只预缓存核心文件；全部音频由页面前台逐个拉取、经 SW 落盘
    # （iOS 会掐掉耗时过长的 SW 安装，一次性 addAll 几百个文件必然翻车）
    assets = ["./", "./index.html", "./manifest.json", "./icon-180.png"]

    version = 1
    sw = ROOT / "sw.js"
    if sw.exists():
        m = re.search(r'kouyu-v(\d+)', sw.read_text())
        if m:
            version = int(m.group(1)) + 1

    asset_lines = ",\n  ".join(f'"{a}"' for a in assets)
    sw.write_text(f'''const CACHE = "kouyu-v{version}";
const PREFIX = "kouyu-v";
const ASSETS = [
  {asset_lines}
];

self.addEventListener("install", e => {{
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
}});

self.addEventListener("activate", e => {{
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
}});

self.addEventListener("fetch", e => {{
  if (e.request.method !== "GET") return;
  const url = new URL(e.request.url);
  const isPage = url.pathname.endsWith("/") || url.pathname.endsWith("/index.html");
  if (isPage) {{
    // 页面：先走网络拿最新版，断网时用缓存
    e.respondWith(
      fetch(e.request).then(r => {{
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return r;
      }}).catch(() => caches.match(e.request))
    );
  }} else {{
    // 音频等静态资源：本地缓存优先，零延迟
    e.respondWith(
      caches.match(e.request, {{ ignoreSearch: true }}).then(hit => hit ||
        fetch(e.request).then(r => {{
          const copy = r.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
          return r;
        }})
      )
    );
  }}
}});
''', encoding="utf-8")
    print(f"sw.js: kouyu-v{version}, {len(assets)} 个文件")

if __name__ == "__main__":
    main()
