#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【动作提示词库】· 英文三列生成器（动作名 EN / 片段 EN / 三段式 EN）

为什么要有它：Y–AG 单元格是**全英文**输出（见 `prompts/04-nine-groups.md`），
但库里 135 条的「动作名 / 提示词片段 / 动作提示词」三列原本只有中文。
本工具从 `action-en-map（本仓库未收录）`（英文映射表）取英文名与英文描述，
与库里的「建议机位 / 建议景别」拼成英文三段式，回写为三个新列。

来源优先级（不重造轮子）：
  ① `action-en-map（本仓库未收录）` 的 English name / English description —— 已有 135 条，直接复用
  ② 机位 / 远近的英文从 `pipeline_loader.py` 的 EN_CAM / EN_SHOT 词典读（改词典即改口径）

用法：
  python3 scripts/fill_action_prompts_en.py --dry      # 只打印差异
  python3 scripts/fill_action_prompts_en.py --write    # 回写（只补空格）
  python3 scripts/fill_action_prompts_en.py --check    # 交叉校验：库 vs 英文映射表 是否一致

⚠️ 与 `fill_action_prompts.py`（中文列）的分工：那个管第 8 列「动作提示词（机位·远近·动作）」，
   本工具管第 9–11 列英文（`Action name (EN)` / `Clip (EN)` / `Action prompt (EN)`），互不覆盖。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB_CANDIDATES = ("references/10-action-library.md", "references/03-action-library.md")
EN_CANDIDATES = ("action-en-map（本仓库未收录）", "references/08-action-library-en.md")

COL_NAME_EN = "Action name (EN)"
COL_FRAG_EN = "Clip (EN)"
COL_PROMPT_EN = "Action prompt (EN) (camera · framing · action)"

ALL_FAMS = list("WSCTHPGMDEX")
LEAD_SHOT_RE = re.compile(r"^(全身|七分|半身|局部特写|全景空镜带人)(景)?[，,、;；\s]*")


def _find(cands):
    for c in cands:
        p = os.path.join(SKILL, c)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(f"找不到文件：{cands}")


def load_en_map() -> dict:
    """从英文映射表读 {编号: (English name, English description)}。"""
    p = _find(EN_CANDIDATES)
    out = {}
    for line in open(p, encoding="utf-8"):
        m = re.match(r"^\|\s*([WSCTHPGMDEX]\d{1,3})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def load_en_dicts() -> tuple[dict, dict]:
    """从 loader 取机位/远近的英文词典（改词典即改口径）。"""
    sys.path.insert(0, os.path.join(SKILL, "scripts"))
    import pipeline_loader as pl
    cam = {}
    for cn, en in getattr(pl, "EN_CAM", {}).items():
        cam[cn] = en
    shot = {}
    for cn, en in getattr(pl, "EN_SHOT", {}).items():
        shot[cn] = en
    return cam, shot


def parse_rows(lines: list[str]):
    fam, cols, out = "", None, []
    for i, line in enumerate(lines):
        m = re.match(r"^###\s+([WSCTHPGMDEX])\s+·\s+(.+)", line)
        if m:
            fam, cols = m.group(1), None
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if any("编号" in c for c in cells) and any("动作名" in c for c in cells):
            cols = list(cells)
            continue
        if cols is None or not cells or not re.match(r"^[WSCTHPGMDEX]\d{1,3}$", cells[0]):
            continue
        # 只认真条目行（含提示词片段），不碰 X 族来源表行（来源表行只有 6–8 列且无「正在…」片段）
        if len(cells) < len(cols):
            continue
        out.append((fam, i, list(cols), cells))
    return out


def idx(cols, key, fallback=None):
    for i, c in enumerate(cols):
        if key in c:
            return i
    if fallback is not None:
        return fallback
    raise KeyError(key)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true", help="只交叉校验，不改文件")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    lib = _find(LIB_CANDIDATES)
    en_map = load_en_map()
    cam_d, shot_d = load_en_dicts()
    lines = open(lib, encoding="utf-8").read().splitlines()
    rows = parse_rows(lines)

    print(f"库：{lib}\n英文映射表：{len(en_map)} 条\n条目 {len(rows)} 条\n")

    if a.check:
        miss_cn, miss_en, cn_left = [], [], []
        for fam, i, cols, cells in rows:
            no = cells[0]
            if no not in en_map:
                miss_cn.append(no)
            if idx(cols, "Action name (EN)", -1) >= 0 and not cells[idx(cols, COL_NAME_EN)].strip():
                miss_en.append(no)
            # 英文三段式里不得残留中文 —— 通常是 loader 的 EN_CAM / EN_SHOT 词典缺了某个取值
            # （2026-09-21 踩过：`全景空镜带人` 未收录 → W10/E01–E04 五条英文段里冒出中文）
            if re.search(r"[\u4e00-\u9fff]", cells[-1]):
                cn_left.append(f"{no}:{cells[-1][:60]}")
        print(f"英文映射表缺：{miss_cn or '无 ✅'}")
        print(f"库内英文列缺：{miss_en or '无 ✅'}")
        print(f"英文段残留中文：{cn_left or '无 ✅'}")
        return 0 if not (miss_cn or miss_en or cn_left) else 1

    written = skipped = 0
    heads_done = 0
    for fam, i, cols, cells in rows:
        no = cells[0]
        if no not in en_map:
            print(f"  ⚠️ {no} 英文映射表未收录，跳过")
            continue
        en_name, en_desc = en_map[no]
        cam_cn = cells[idx(cols, "建议机位")]
        shot_cn = cells[idx(cols, "建议景别")]
        cam_base = re.sub(r"[（(].*", "", cam_cn).strip()
        h = cam_cn
        height = "eye level" if "平视" in h or not any(k in h for k in ("俯拍", "仰拍", "跟拍", "过肩")) else ""
        if "俯拍" in h:
            height = "high angle"
        elif "仰拍" in h:
            height = "low angle"
        elif "跟拍" in h:
            height = "tracking"
        elif "过肩" in h:
            height = "over the shoulder"
        en_cam = cam_d.get(cam_base, cam_base)
        en_shot = shot_d.get(shot_cn, shot_cn)
        action = LEAD_SHOT_RE.sub("", en_desc).strip()
        # ⚠️ 段间分隔必须用**全角 ｜**：半角 | 会被 Markdown 当列边界，把一行拆成三列（2026-09-21 踩过）
        prompt_en = f"Camera: {en_cam} · {height} ｜ Framing: {en_shot} ｜ Action: {action}"

        vals = {COL_NAME_EN: en_name, COL_FRAG_EN: en_desc, COL_PROMPT_EN: prompt_en}
        for col, val in vals.items():
            if col in cols:
                ci = cols.index(col)
                if ci < len(cells) and cells[ci].strip() and not a.force:
                    skipped += 1
                    continue
                while len(cells) <= ci:
                    cells.append("")
                cells[ci] = val
            else:
                cells.append(val)
        lines[i] = "| " + " | ".join(cells) + " |"
        written += 1
        if a.dry:
            print(f"{no:>4} | {en_name}\n       {prompt_en}")

    # 表头补三列（条目表：含「编号+动作名+提示词片段」；X 来源表不含动作名，自动排除）
    for i, l in enumerate(lines):
        if not l.strip().startswith("|"):
            continue
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if not (any("编号" in c for c in cells) and any("动作名" in c for c in cells)
                and any("提示词片段" in c for c in cells)):
            continue
        new = cells + [c for c in (COL_NAME_EN, COL_FRAG_EN, COL_PROMPT_EN) if c not in cells]
        if len(new) != len(cells):
            lines[i] = "| " + " | ".join(new) + " |"
            sep = lines[i + 1]
            if set(sep.strip()) <= set("|-: "):
                lines[i + 1] = "|" + "---|" * len(new)
            heads_done += 1

    print(f"\n条目补列 {written} · 已有内容跳过 {skipped} · 表头补列 {heads_done}")
    if a.dry:
        print("（--dry：未写文件；确认后加 --write）")
        return 0
    with open(lib, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"✅ 已回写 {lib}")
    return 0


if __name__ == "__main__":
    sys.exit(main())