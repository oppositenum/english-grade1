"""用 Fish Audio 免费接口 (s2.1-pro-free) 生成一套 mp3 到 audio/fish/。
API Key 从环境变量 FISH_API_KEY 读取；代理走 https_proxy 环境变量。
slug 规则与 index.html / gen_audio.py 一致。"""
import asyncio
import os
import sys
from pathlib import Path

import aiohttp

from gen_audio import ROOT, extract_texts, slug

API = "https://api.fish.audio/v1/tts"
VOICE_ID = "933563129e564b19a115bedd57b7406a"  # Sarah
KEY = os.environ["FISH_API_KEY"]
PROXY = os.environ.get("https_proxy")
OUT = ROOT / "audio" / "fish"


async def gen_one(session: aiohttp.ClientSession, sem: asyncio.Semaphore, text: str):
    path = OUT / f"{slug(text)}.mp3"
    if path.exists() and path.stat().st_size > 0:
        return
    async with sem:
        for attempt in range(4):
            try:
                async with session.post(
                    API,
                    json={"text": text, "reference_id": VOICE_ID, "format": "mp3"},
                    headers={"Authorization": f"Bearer {KEY}", "model": "s2.1-pro-free"},
                    proxy=PROXY,
                    timeout=aiohttp.ClientTimeout(total=90),
                ) as r:
                    if r.status == 200:
                        data = await r.read()
                        if len(data) > 1000:
                            path.write_bytes(data)
                            print(f"  ok  {path.name}")
                            return
                    elif r.status == 429:
                        await asyncio.sleep(5 * (attempt + 1))
                        continue
                    else:
                        print(f"  HTTP {r.status} {text!r}: {(await r.text())[:120]}", file=sys.stderr)
            except Exception as e:
                print(f"  retry {text!r}: {e}", file=sys.stderr)
            await asyncio.sleep(2 + attempt)
        print(f"  FAIL {text!r}", file=sys.stderr)


async def main():
    texts = extract_texts()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"{len(texts)} 条 → audio/fish/ (Sarah)")
    sem = asyncio.Semaphore(2)
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*(gen_one(session, sem, t) for t in texts))
    n = len(list(OUT.glob("*.mp3")))
    print(f"audio/fish: {n}/{len(texts)}")


if __name__ == "__main__":
    asyncio.run(main())
