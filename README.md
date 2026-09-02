# english-grade1

广州小学一年级英语口语跟读网页（PWA）。点击卡片朗读单词/句子，孩子跟读。

- 纯静态站点：`index.html` + `audio/`（预生成 mp3）+ PWA 文件，上传即用
- 四套音色：Fish Audio Sarah（默认）/ Edge TTS Ava / Jenny / Ana，另有本机语音兜底
- PWA 离线：首次访问后整站缓存到本机，添加到主屏幕后断网可用、点击零延迟

## 重新生成音频（内容有改动时）

```bash
python3 -m venv .venv && .venv/bin/pip install edge-tts aiohttp pillow
.venv/bin/python gen_audio.py                 # Edge TTS 三套音色（免费）
FISH_API_KEY=你的key .venv/bin/python gen_fish.py   # Fish Audio Sarah（免费模型 s2.1-pro-free）
.venv/bin/python gen_sw.py                    # 重新生成 Service Worker 缓存清单
```

Fish Audio 的 API Key 只通过环境变量传入，不要写进任何文件。
