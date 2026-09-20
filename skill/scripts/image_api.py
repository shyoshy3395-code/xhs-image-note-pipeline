#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通用生图客户端（OpenAI 兼容 /v1/images 接口）

只做一件事：把 prompt（+ 可选参考图）交给一个兼容接口，存下结果并返回路径。
任何提供 OpenAI 兼容 images 接口的服务都能用（自建 / 各家云 / 开源网关）。

鉴权与地址全部来自环境变量（见 .env.example）：
    IMAGE_API_KEY   必填
    IMAGE_BASE_URL  默认 https://api.openai.com/v1
    IMAGE_MODEL     默认 gpt-image-1

用法（脚本内）：
    from image_api import generate
    generate("prompt...", ["ref1.jpg"], model="gpt-image-1", size="1024x1536", out_path="x.png")
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request


def _env(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    if v:
        return v
    # 退化：读同目录/上层的 .env
    for cand in (".env", os.path.join(os.path.dirname(__file__), "..", "..", ".env")):
        if os.path.exists(cand):
            for line in open(cand, encoding="utf-8", errors="ignore"):
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


def _post(url: str, payload: dict, key: str, timeout: int) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def generate(prompt: str, refs: list[str] | None = None, model: str | None = None,
             size: str = "1024x1536", out_path: str = "out.png",
             timeout: int = 400, tries: int = 3) -> str | None:
    """生成一张图并落盘。refs 非空时优先走 edits（多图参考），否则走 generations。

    返回落盘路径；失败返回 None（并把最后一次错误打到 stderr）。
    """
    key = _env("IMAGE_API_KEY")
    base = _env("IMAGE_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = model or _env("IMAGE_MODEL", "gpt-image-1")
    if not key:
        raise RuntimeError("缺少 IMAGE_API_KEY —— 请参考 .env.example 配置")

    payload: dict = {"model": model, "prompt": prompt, "size": size, "n": 1}
    if refs:
        payload["reference_images"] = [  # 多数网关用这个字段名；不支持时退化为纯文生图
            "data:image/jpeg;base64," + base64.b64encode(open(r, "rb").read()).decode() for r in refs
        ]
    endpoint = "/images/edits" if refs else "/images/generations"

    last = ""
    for k in range(tries):
        try:
            data = _post(base + endpoint, payload, key, timeout)
            item = (data.get("data") or [{}])[0]
            b64 = item.get("b64_json")
            if not b64:                              # 有的服务返回 URL
                url = item.get("url")
                if not url:
                    raise RuntimeError(f"响应无图像字段：{str(data)[:200]}")
                with urllib.request.urlopen(url, timeout=timeout) as r:
                    b64 = base64.b64encode(r.read()).decode()
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, "wb") as fh:
                fh.write(base64.b64decode(b64))
            return out_path
        except Exception as e:                        # noqa: BLE001 — 网络/网关错误统一重试
            last = f"{type(e).__name__}: {e}"
            if k < tries - 1:
                time.sleep(5 * (k + 1))
    print(f"[image_api] 生成失败：{last}", flush=True)
    return None


SIZE_PRESETS = {"1K": "1024x1536", "2K": "2048x3072", "4K": "3584x5376"}


def resolve_size(size: str | None, aspect: str | None) -> str:
    """把「精确像素 / 尺寸档 / 比例」归一成接口要的像素 WxH。

    · 调用方直接给精确像素（如 `--aspect 864x1152`）→ 原样用
    · 给尺寸档（`--size 2K`）→ 查 SIZE_PRESETS
    · 只给比例（`--aspect 3:4`）→ 按 1024 宽换算
    · 认不出的档位 → **原样透传**（有的网关自己认 "2K"，不替你猜）
    """
    for v in (aspect, size):
        if v and "x" in v.lower():
            return v
    if size and size.upper() in SIZE_PRESETS:
        return SIZE_PRESETS[size.upper()]
    if aspect and ":" in aspect:
        w, h = (int(x) for x in aspect.split(":")[:2])
        return f"1024x{round(1024 * h / w)}"
    return size or "1024x1536"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="生图执行器（可单独测连通性，也被 run_image_note.py 按同一套参数调用）")
    ap.add_argument("--prompt", default="a calm street corner, film photograph")
    ap.add_argument("--out", default="/tmp/image_api_test.png")
    ap.add_argument("--size", default="1024x1536", help="尺寸档（1K/2K/4K）或精确像素 WxH")
    ap.add_argument("--aspect", default=None, help="比例（3:4）或精确像素 WxH；与 --size 二者给一个即可")
    ap.add_argument("--model", default=None, help="覆盖 .env 里的 IMAGE_MODEL")
    ap.add_argument("--image", action="append", default=[], help="参考图路径，可重复（给即走 images/edits）")
    ap.add_argument("--timeout", type=int, default=400)
    a = ap.parse_args()
    px = resolve_size(a.size, a.aspect)
    p = generate(a.prompt, a.image or None, a.model, px, a.out, timeout=a.timeout)
    print(("✅ 成功:" if p else "❌ 失败:"), p or "", os.path.getsize(p) if p else "")
    raise SystemExit(0 if p else 1)
