"""从 index.html 提取所有英文条目，用 edge-tts 生成两套 mp3（Jenny 女声 / Ana 童声）。
文件名 slug 规则必须与 index.html 里的 JS slug() 一致。"""
import asyncio
import re
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).parent
VOICES = {
    "jenny": "en-US-JennyNeural",
    "ana": "en-US-AnaNeural",
    "ava": "en-US-AvaMultilingualNeural",
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def extract_texts() -> list[str]:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    texts = re.findall(r'en:\s*"([^"]+)"', html)
    seen, out = set(), []
    for t in texts:
        s = slug(t)
        if s not in seen:
            seen.add(s)
            out.append(t)
    return out


async def gen_one(sem: asyncio.Semaphore, voice: str, text: str, path: Path):
    if path.exists() and path.stat().st_size > 0:
        return
    async with sem:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, voice, rate="-5%").save(str(path))
                print(f"  ok  {path.relative_to(ROOT)}")
                return
            except Exception as e:
                if attempt == 2:
                    print(f"  FAIL {path.relative_to(ROOT)}: {e}", file=sys.stderr)
                else:
                    await asyncio.sleep(1 + attempt)


async def main():
    texts = extract_texts()
    print(f"{len(texts)} 条文本 × {len(VOICES)} 个音色")
    sem = asyncio.Semaphore(6)
    tasks = []
    for name, voice in VOICES.items():
        d = ROOT / "audio" / name
        d.mkdir(parents=True, exist_ok=True)
        for t in texts:
            tasks.append(gen_one(sem, voice, t, d / f"{slug(t)}.mp3"))
    await asyncio.gather(*tasks)
    for name in VOICES:
        n = len(list((ROOT / "audio" / name).glob("*.mp3")))
        print(f"audio/{name}: {n}/{len(texts)}")


if __name__ == "__main__":
    asyncio.run(main())
