#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片笔记流水线 · 生成运行器（run_image_note）

设计原则：**本脚本不含任何提示词正文**。
- 提示词 → 由 pipeline_loader 从 `prompts/*.md` 实时装配（改提示词请改 prompts/，不要改这里）
- 素材 → 由 pipeline_loader 从 `knowledge_base` 实时拉取（定位/卖点/禁用词/参照成品）
- 动作 → 由 pipeline_loader 从 `references/` 下的【动作提示词库】实时抽条（按配额 + 空间适配；`10-` / `03-` 两种命名均兼容）

流程：首图 X（环境 + 人脸 + 上身 + 平铺 多图参考）→ 各组以首图为唯一参考走 edit 链路。
纪律：串行（vip 不支持并发）· 可续跑（已存在即跳过）· 失败重试 5 次退避 20s · 读产物一律 glob。

模型族自适应（2026-09-18）：
  · nano-banana 族 → `--aspect 3:4 --size 2K`（比例 + 尺寸档；实测 pro@2K = 1792×2400 / 61s）
  · gpt-image-* 族 → `--aspect <精确像素>`（实测 vip 全档曾整体 400 `generate failed`，用前先探活）

用法：
  python3 run_image_note.py --pkg /tmp/pkg.json --row 2 --outdir ./out \
      --cover 封面.jpg --face 人脸.png --up1 上身1.jpg --up2 上身2.jpg --flat 平铺.jpg \
      [--model nano-banana-pro] [--size 2K] [--dry]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pipeline_loader import render_prompt_for_gen, EN_CONSTRAINT  # noqa: E402

HOME = os.path.expanduser("~")

# 生图执行器解析顺序：环境变量 → **同目录 image_api.py**（对外版仓库自带）→ 本地 Hermes 技能库。
# 教训（2026-09-20）：原来硬编码本地技能库路径，导出后对外版用户的出图链路直接断（路径不存在 + 参数不兼容）。
NB = (os.environ.get("IMAGE_API_SCRIPT")
      or next((p for p in (os.path.join(HERE, "image_api.py"),
                           "",
                           "")
               if os.path.exists(p)), ""))
# 解释器解析顺序：环境变量 → 本地 Hermes venv → **当前解释器**（对外版用户走最后一支）
PY = (os.environ.get("IMAGE_PY")
      or next((p for p in ("",
                           "", sys.executable)
               if os.path.exists(p)), sys.executable))

# 三个"出图前就注定失败"的自检（省得跑一半才发现路径/参数不对）
if not NB:
    print("⚠️ 找不到生图执行器：请在 .env 或环境变量里给 IMAGE_API_SCRIPT，"
          "或把 image_api.py 放在本脚本同目录", file=sys.stderr)


def child_env() -> dict:
    """调用生图脚本时的环境：必须去掉代理（生图服务在境内），并带上 API key。"""
    env = {**os.environ}
    for v in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        env.pop(v, None)
    env["NO_PROXY"] = "localhost,127.0.0.1"
    # ① 通用名（对外版 .env.example 口径）：仓库根 / 当前目录的 .env
    for p in (os.path.join(HERE, "..", "..", ".env"), os.path.join(os.getcwd(), ".env")):
        if os.path.exists(p):
            for line in open(p, encoding="utf-8", errors="ignore"):
                line = line.strip()
                for k in ("IMAGE_API_KEY", "IMAGE_BASE_URL", "IMAGE_MODEL"):
                    if line.startswith(f"{k}=") and not env.get(k):
                        env[k] = line.split("=", 1)[1].strip().strip('"').strip("'")
    # ② 本地 Hermes 专用名（旧路径，保留兼容）
    for p in ("", ""):
        if os.path.exists(p):
            for line in open(p, errors="ignore"):
                if line.strip().startswith("生图接口_API_KEY="):
                    env["生图接口_API_KEY"] = line.split("=", 1)[1].strip()
                    env["生图接口_ENV_FILE"] = ""
                    return env
    return env


def shrink(path: str, cache: str, max_edge: int = 1024, quality: int = 88) -> str:
    """参考图缩到长边 ≤max_edge / JPEG q88 —— 不缩常因请求体过大返回误导性错误。"""
    from PIL import Image
    os.makedirs(cache, exist_ok=True)
    dst = os.path.join(cache, os.path.splitext(os.path.basename(path))[0] + f"_{max_edge}.jpg")
    if not os.path.exists(dst):
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((max_edge, max_edge))
            im.save(dst, "JPEG", quality=quality, optimize=True)
    return dst


def model_args(model: str, size_or_ratio: str) -> list[str]:
    """模型族自适应参数（见文件头说明）。"""
    if model.startswith("nano-banana"):
        return ["--aspect", "3:4", "--size", size_or_ratio]
    return ["--aspect", size_or_ratio]


def gen(prompt: str, base: str, refs: list[str], tag: str, env: dict, size: str, model: str,
        timeout: int = 400, tries: int = 5) -> dict:
    for k in range(tries):
        args = [PY, NB, "--model", model, *model_args(model, size), "--prompt", prompt,
                "--out", base + ".png", "--timeout", str(timeout)]
        for r in refs:
            args += ["--image", r]
        t0 = time.time()
        p = subprocess.run(args, capture_output=True, text=True, env=env)
        dt = time.time() - t0
        hit = glob.glob(base + ".*")                 # 扩展名可能被网关改写 → 一律 glob
        if hit:
            try:
                from PIL import Image
                with Image.open(hit[0]) as im:
                    dims = f"{im.size[0]}x{im.size[1]}"
            except Exception:                        # noqa: BLE001
                dims = "?"
            print(f"[{tag}] ✅ {dt:.0f}s {dims} {os.path.getsize(hit[0])//1024}KB", flush=True)
            return {"tag": tag, "file": hit[0], "ok": True, "sec": round(dt, 1), "dims": dims}
        err = next((l.strip() for l in (p.stdout + p.stderr).splitlines() if '"error"' in l or "error:" in l),
                   "超时/无输出")
        print(f"[{tag}] 第{k+1}/{tries}次失败 {dt:.0f}s {err[:110]}", flush=True)
        time.sleep(20)
    return {"tag": tag, "file": None, "ok": False, "sec": 0, "dims": None}


def main() -> int:
    ap = argparse.ArgumentParser(description="图片笔记生成运行器（提示词来自 prompts/）")
    ap.add_argument("--pkg", required=True, help="pipeline_loader 生成的提示词包 JSON")
    ap.add_argument("--row", type=int, required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--cover", required=True, help="参考图1：封面/环境（只借空间光影）")
    ap.add_argument("--face", required=True, help="参考图2：人脸图（锁人物）")
    ap.add_argument("--up1", help="参考图3：R 上身效果图（正面）——服装主源")
    ap.add_argument("--up2", help="参考图4：S 上身效果图（背面）——服装主源")
    ap.add_argument("--flat", help="参考图5：T 平铺图（上衣正面）——细节补充")
    ap.add_argument("--flat2", help="参考图6：U 平铺图（上衣反面）——细节补充")
    ap.add_argument("--flat3", help="参考图7：V 平铺图（下装正面）——细节补充")
    ap.add_argument("--flat4", help="参考图8：W 平铺图（下装反面）——细节补充")
    ap.add_argument("--model", default=None)
    ap.add_argument("--size", default=None, help="nano 族写档位（2K/4K）；gpt-image 族写精确像素")
    ap.add_argument("--dry", action="store_true", help="只打印 prompt，不调用模型")
    a = ap.parse_args()

    pkg = json.load(open(a.pkg, encoding="utf-8"))
    model = a.model or pkg["facts"]["model"]
    size = a.size or pkg["facts"].get("size_1k", "864x1152")
    groups = pkg["groups"]
    os.makedirs(a.outdir, exist_ok=True)
    cache = os.path.join(a.outdir, "_refs_cache")

    locks = pkg["prompts"]["locks_body"].replace("{{服装锁词}}", pkg["garment_lock"])
    hero_prompt = (f"3:4 竖构图真实生活随手拍首图。\n"
                   f"【空间与光影·照此重建】{pkg['env']}\n"
                   f"{pkg['prompts']['ref_rule']}\n{locks}\n{pkg['prompts']['hero_position']}\n{EN_CONSTRAINT}")
    group_prompts = [render_prompt_for_gen(pkg, i) for i in range(1, groups + 1)]

    if a.dry:
        print("═══ 首图 X prompt ═══\n" + hero_prompt[:1200])
        for i, gp in enumerate(group_prompts, 1):
            print(f"\n═══ 组{i} prompt ═══\n" + gp[:600])
        print(f"\n（dry-run：未调用模型 · 模型={model} 尺寸={size} · 提示词来自 {pkg['prompts']['locks_file']} 等 prompts/*.md）")
        return 0

    env = child_env()
    manifest = []
    refs = [shrink(a.cover, cache, 1024)]
    for f in (a.face, a.up1, a.up2):
        if f:
            refs.append(shrink(f, cache, 1024))
    for f in (a.flat, getattr(a, "flat2", None), getattr(a, "flat3", None), getattr(a, "flat4", None)):
        if f:
            refs.append(shrink(f, cache, 768))
    print(f"[行{a.row}] 模型={model} 尺寸={size} 参考图 {len(refs)} 张", flush=True)

    hero_base = os.path.join(a.outdir, f"X{a.row}_首图")
    if glob.glob(hero_base + ".*"):
        print("  首图已存在，跳过", flush=True)
    else:
        manifest.append(gen(hero_prompt, hero_base, refs, f"X{a.row}首图", env, size, model))
    hero_hits = glob.glob(hero_base + ".*")
    if not hero_hits:                      # 首图失败必须中止：组图以它为一致性锚点
        print("⛔ 首图未生成，已中止（脚本可续跑：修好后重跑，已完成的图会跳过）", file=sys.stderr)
        return 1
    hero_ref = shrink(sorted(hero_hits)[0], cache, 1024)

    cols = "FGHIJKLMN"
    for i, gp in enumerate(group_prompts, 1):
        col = cols[i - 1]
        base = os.path.join(a.outdir, f"行{a.row}_组{i}_{col}")
        if glob.glob(base + ".*"):
            print(f"[行{a.row}-组{i}({col})] 已存在，跳过", flush=True)
            continue
        manifest.append(gen(gp, base, [hero_ref], f"组{i}({col})", env, size, model))

    json.dump(manifest, open(os.path.join(a.outdir, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    have = len(glob.glob(os.path.join(a.outdir, f"行{a.row}_组*"))) + (1 if hero_hits else 0)
    print(f"\n=== 行{a.row} 完成：{have}/{groups + 1} ===")
    print("下一步：降噪 → 内嵌 xlsx → 交付闸门")
    return 0 if have == groups + 1 else 1


if __name__ == "__main__":
    sys.exit(main())