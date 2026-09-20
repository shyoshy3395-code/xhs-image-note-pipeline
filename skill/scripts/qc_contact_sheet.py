#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐行质检拼图（图片笔记流水线固定环节 · 2026-09-19 固化）

为什么必须做：出图那一刻看不出「串款 / 少鞋 / 多披肩 / 空间漂移 / 人脸变形」，
必须把「首图 + 九组」拼成一张大图后**放大给视觉模型逐张核对**。
2026-09-19 实测：正是这一步逮到①行5 封面人物披灰斗篷 → 成图 6 张多出披肩
②行4 用了被弃用的带文字封面 ③行6 及膝长靴变成乐福鞋（【搭配】段被截断）。

用法：
    python3 qc_contact_sheet.py <工作目录> 2 3 4 5 6
    python3 qc_contact_sheet.py <工作目录> 2 --size 420 --out ~/Desktop/Hermes
产物：
    <out>/行N_质检.jpg   —— 5 列 × 2 行（左上＝首图，其余＝组1..9），每张上方标文件名

约定（与 run_image_note.py 落盘命名一致）：
    首图   X{N}_首图.*
    组图   行{N}_组{i}_{列}.*      同组多版时**「修正版」优先**
"""
import argparse
import glob
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("需要 Pillow：~/.hermes/python3 -m pip install pillow")

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


def load_font(size: int):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def pick(patterns, prefer_fixed=True):
    """同组多个产物时：含「修正版」优先，其次按修改时间取最新。"""
    hits = []
    for pat in patterns:
        hits.extend(glob.glob(pat))
    hits = sorted(set(hits))
    if not hits:
        return None
    if prefer_fixed:
        fixed = [h for h in hits if "修正版" in h or "修正" in h]
        if fixed:
            hits = fixed
    return max(hits, key=os.path.getmtime)


def build_one(work: str, row: int, out_dir: str, size: int, cols: int = 5) -> tuple:
    group_cols = "FGHIJKLMN"
    files, missing = [], []
    hero = pick([f"{work}/行{row}_gen/X{row}_首图.*", f"{work}/行{row}_gen/X{row}_*.jpg"])
    if hero:
        files.append(hero)
    else:
        missing.append(f"行{row} 首图")
    for i, col in enumerate(group_cols, start=1):
        f = pick([f"{work}/行{row}_gen/行{row}_组{i}_{col}*.jpg",
                  f"{work}/行{row}_gen/*组{i}*.jpg"])
        if f:
            files.append(f)
        else:
            missing.append(f"行{row} 组{i}({col})")
    if not files:
        return None, missing

    cw, ch = size, int(size * 4 / 3)          # 3:4
    rows = (len(files) + cols - 1) // cols
    label_h = 30
    sheet = Image.new("RGB", (cols * (cw + 8) + 8, rows * (ch + label_h + 8) + 8), "white")
    draw = ImageDraw.Draw(sheet)
    font = load_font(26)
    for idx, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        im.thumbnail((cw, ch))
        x = 8 + (idx % cols) * (cw + 8)
        y = 8 + (idx // cols) * (ch + label_h + 8)
        name = os.path.basename(f).replace(f"行{row}_", "").rsplit(".", 1)[0]
        draw.text((x, y), name, fill="black", font=font)
        sheet.paste(im, (x, y + label_h))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"行{row}_质检.jpg")
    sheet.save(path, quality=88)
    return path, missing


def main() -> int:
    ap = argparse.ArgumentParser(description="把 行N_gen/ 拼成逐行质检大图，供视觉模型逐张核对")
    ap.add_argument("work", help="批次工作目录（其下应有 行N_gen/）")
    ap.add_argument("rows", nargs="+", type=int, help="要质检的行号，如 2 3 4")
    ap.add_argument("--out", default=None, help="输出目录（默认 <工作目录>/质检）")
    ap.add_argument("--size", type=int, default=300, help="单张缩略宽度 px（默认 300；要看清文字/水印用 420+）")
    ap.add_argument("--cols", type=int, default=5, help="每行几张（默认 5）")
    a = ap.parse_args()

    work = os.path.expanduser(a.work)
    out_dir = os.path.expanduser(a.out) if a.out else os.path.join(work, "质检")
    rc = 0
    for row in a.rows:
        path, missing = build_one(work, row, out_dir, a.size, a.cols)
        if path:
            print(f"✓ 行{row} → {path}")
        else:
            print(f"✗ 行{row} 无产物（该行还没出图？）")
            rc = 1
        if missing:
            print(f"   ⚠️ 缺 {len(missing)} 项：{'、'.join(missing)}")
            rc = 1
    print("\n下一步（务必做）：把质检图交给视觉模型，逐张核对 6 项 ——")
    print("  ① 空间是否与封面一致（结构/陈设/光位/色温）")
    print("  ② 上装/下装是否与 T/V 平铺一致（款式/领型/腰头/颜色/材质）")
    print("  ③ 鞋与包是否与 P 列【搭配 STYLING】一致（少鞋 / 长靴变乐福鞋 = env 被截断）")
    print("  ④ 有无**封面人物串款**（披肩/斗篷/围巾/帽子/包/鞋 —— 见 references/11 §九 16）")
    print("  ⑤ 有无多余道具、文字/水印/Logo")
    print("  ⑥ 同一张脸 + 头身比自然 + 九张机位景别动作不重复")
    return rc


if __name__ == "__main__":
    sys.exit(main())