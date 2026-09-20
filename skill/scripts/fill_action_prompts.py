#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【动作提示词库】· 动作提示词列回写工具（机位 / 远近 / 人体动作 三段式）

用途：给 `references/10-action-library.md` 的**全部 11 族**（W S C T H P G M D E X）
     逐条生成一列「动作提示词」，只描述三件事：
       ① 拍摄角度机位  ② 拍摄远近（景别）  ③ 人体动作
     不描述人物外貌，也不描述主体服装（原因：人脸/服装由锁块与参考图负责，写进来只会互殴）。

用法：
  python3 scripts/fill_action_prompts.py --dry           # 只打印，不写文件（默认）
  python3 scripts/fill_action_prompts.py --write         # 回写（只填空白格；已有内容不动）
  python3 scripts/fill_action_prompts.py --write --force # 覆盖已填格（重算，慎用）
  python3 scripts/fill_action_prompts.py --scan          # 只扫禁用词（外貌/服装）

设计约束（重要）：
- 新列加在**表尾**（基础族在「风险」之后；X 族在「来源」之后）。原因：`pipeline_loader.py --append`
  按 7 段写入，若把新列插在中间，`--append` 写的新行会把「风险」挤进新列 → 静默错位。
- `pipeline_loader.load_actions()` 是**按表头名**取列的，加列不影响它解析/计数。
- X 族片段自带前导景别（「全身，正在…」）与本列「远近」重复 → 生成时**剥掉前导景别词**。

禁用项（`--scan` 会拦，回写前必须 0 命中）：
  外貌类：五官/妆容/肤/发色/发型/身材/年龄/气质…
  服装类：面料/材质/颜色/印花/图案/版型/廓形/剪裁/款式/品牌/logo/尺码…
允许项：身体部位（手·指尖·肘·肩·腰·膝·脚·下颌）、视线、以及**作接触点的服装部位名**
  （口袋·袖口·衣襟·下摆·纽扣·拉链·帽檐·裤脚·鞋带）——它们定义动作，不是"描述服装"。
"""
from __future__ import annotations

import argparse
import os
import re
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 动作提示词库：兼容本库命名与对外版命名（`10-` / `03-`），与 pipeline_loader 一致
LIB_CANDIDATES = ("references/10-action-library.md", "references/03-action-library.md",
                  "references/action-library.md", "action-library.md")


def lib_path() -> str:
    env = os.environ.get("NOTE_ACTION_LIB")
    if env and os.path.exists(env):
        return env
    for c in LIB_CANDIDATES:
        p = os.path.join(SKILL, c)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("找不到【动作提示词库】。候选：" + "、".join(LIB_CANDIDATES))

# 全部 11 族（W S C T H P G M D E X）；X 族为真实爆款反推族，列结构多「归入族/来源」两列
ALL_FAMS = list("WSCTHPGMDEX")

NEW_COL = "动作提示词（机位·远近·动作）"

# X 族片段自带前导景别（「全身，正在…」/「七分景，正在…」）→ 剥掉，避免与「远近」段重复
LEAD_SHOT_RE = re.compile(r"^(全身|七分|半身|局部特写|全景空镜带人)(景)?[，,、;；\s]*")

# 视角 → 机位·高度（高度：平视 / 俯拍 / 仰拍 / 跟拍 / 过肩）
CAM_BASE = {"正面": "正面", "3-4侧": "3-4侧", "全侧": "全侧", "背面": "背面"}
HEIGHT_HINT = [("俯拍", "俯拍"), ("仰拍", "仰拍"), ("跟拍", "跟拍"), ("过肩", "过肩")]

# 外貌 / 服装 禁用词
BAN = [
    "五官", "妆容", "肤色", "皮肤", "肤质", "发色", "发型", "长发", "短发", "卷发", "刘海",
    "身材", "年龄", "气质", "颜值", "高挑", "纤细", "漂亮", "帅气", "好看", "脸型",
    "面料", "材质", "颜色", "配色", "印花", "图案", "版型", "廓形", "剪裁", "款式", "品牌",
    "logo", "尺码", "垂坠", "挺括", "厚薄", "肌理",
]

# 逐条人工定稿（把片段里"描述服装/外貌"的写法换成"只写动作与接触点"）
OVERRIDES: dict[str, str] = {
    "W03": "迈步中段，前腿承重、后脚跟刚离地，双臂自然摆动，下摆与裤脚被带出轻微动态",
    "W05": "背对镜头沿街向前走，越走越远，背影在画面里占幅约 1/3",
    "W06": "相机在人物右后方过肩，画面可见肩线与前方街区纵深，后脑与右肩入画",
    "S02": "一只手自然插进口袋，另一手垂落",
    "S07": "双手自然抱臂，侧身看向画外，肩背放松不耸肩",
    "S14": "低头用手捋顺前襟，指尖轻捏衣襟边缘",
    "S09": "一只手自然贴在后腰侧、肘部微曲，不做叉腰手势",
    "G06": "微微仰头看树叶与天光，下巴与颈部自然舒展，肩部放松",
    "S15": "一只手轻抬扶住帽檐，头微低",
    "C07": "弯腰把裤脚拉平，指尖捏住脚踝处的边缘",
    "D01": "手部与腕部的静态局部特写，画面只有手腕、手指与腕上配饰",
    "D02": "手腕与袖口交界处的静态局部特写，画面只有手腕、袖口与腕上配饰",
    "D03": "颈侧到锁骨一线的静态局部特写，画面只有颈部、锁骨与颈上配饰",
    "D04": "腰部横向分割线的静态局部特写，画面只有腰线与两侧轮廓",
    "D05": "鞋面与地面接触处的静态局部特写，画面只有脚部与地面",
    "D06": "肩部到斜挎带走势的静态局部特写，画面只有肩线与带子走向",
    "D07": "手与所持物件接触点的静态局部特写，画面只有手指、物件与接触处",
    "D08": "身体侧面受光面的静态局部特写，画面只有受光面与光线过渡，不含面部",
}


def read(p: str) -> str:
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def parse_rows(lines: list[str]):
    """产出 (族字母, 行号, cols, cells)；只认含「动作名」+「提示词片段」的条目表。"""
    fam, cols, out = "", None, []
    for i, line in enumerate(lines):
        m = re.match(r"^###\s+([WSCTHPGMDEX])\s+·\s+(.+)", line)
        if m:
            fam, cols = m.group(1), None
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if any("编号" in c for c in cells):
            cols = list(cells) if (any("动作名" in c for c in cells)
                                   and any("提示词片段" in c for c in cells)) else None
            continue
        if cols is None or not cells or not re.match(r"^[WSCTHPGMDEX]\d{1,3}$", cells[0]):
            continue
        out.append((fam, i, list(cols), cells))
    return out


def cam_str(raw: str) -> str:
    base = re.sub(r"[（(].*", "", raw).strip()
    height = "平视"
    for key, val in HEIGHT_HINT:
        if key in raw:
            height = val
            break
    return f"{CAM_BASE.get(base, base)}·{height}"


def compose(frag: str, cam: str, shot: str, no: str) -> str:
    act = OVERRIDES.get(no, frag).strip().rstrip("。")
    act = LEAD_SHOT_RE.sub("", act).strip()          # 剥掉片段自带的前导景别（X 族常见）
    return f"机位：{cam} ｜ 远近：{shot} ｜ 动作：{act}"


def scan(text: str) -> list[str]:
    return [w for w in BAN if w in text]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="只打印（默认行为）")
    ap.add_argument("--write", action="store_true", help="回写文件")
    ap.add_argument("--force", action="store_true", help="覆盖已填格（重算）")
    ap.add_argument("--scan", action="store_true", help="只扫禁用词")
    a = ap.parse_args()

    lib = lib_path()
    lines = read(lib).splitlines()
    rows = parse_rows(lines)
    base = [(f, i, c, cl) for (f, i, c, cl) in rows if f in ALL_FAMS]
    print(f"库：{lib}")
    print(f"条目 {len(base)} 条（族：{'/'.join(ALL_FAMS)}）· 表尾新列「{NEW_COL}」\n")

    if a.scan:
        # 闸门只看**成稿**（覆盖稿生效后的值）；原片段命中但已被覆盖稿改写 → 仅提示，不算失败。
        fail, noted = 0, 0
        for fam, i, cols, cells in base:
            no = cells[0]
            fx = cols.index(next(x for x in cols if "提示词片段" in x))
            cx = cols.index(next(x for x in cols if "建议机位" in x))
            sx = cols.index(next(x for x in cols if "建议景别" in x))
            val = compose(cells[fx], cam_str(cells[cx]), cells[sx], no)
            hits = scan(val)
            if hits:
                fail += 1
                print(f"  ⛔ {no} 成稿命中 {hits}\n      {val}")
                continue
            raw = scan(cells[fx])
            if raw:
                noted += 1
                print(f"  ℹ️  {no} 原片段含 {raw} → 已由覆盖稿改写（成稿干净）")
        print(f"\n禁用词扫描：{'✅ 0 命中（成稿）' if not fail else f'❌ {fail} 条成稿命中'}"
              f"｜原片段待改写提示 {noted} 条")
        return 0 if not fail else 1

    written, skipped, missing_col, banned = 0, 0, [], []
    for fam, i, cols, cells in base:
        no = cells[0]
        fx = cols.index(next(x for x in cols if "提示词片段" in x))
        cx = cols.index(next(x for x in cols if "建议机位" in x))
        sx = cols.index(next(x for x in cols if "建议景别" in x))
        val = compose(cells[fx], cam_str(cells[cx]), cells[sx], no)
        hits = scan(val)
        if hits:
            banned.append((no, hits))
        if NEW_COL not in cols:
            missing_col.append(i)
            cells = cells + [val]
        elif not a.force and cells[cols.index(NEW_COL)].strip():
            skipped += 1
            continue
        else:
            cells[cols.index(NEW_COL)] = val
        lines[i] = "| " + " | ".join(cells) + " |"
        written += 1
        if a.dry:
            print(f"{no:>4} {cells[1][:8]:<9} {val}")

    # 表头补新列（加在表尾）；条目表＝含「编号+动作名+提示词片段」的表（来源表不含动作名）
    heads = [i for i, l in enumerate(lines)
             if l.strip().startswith("|") and "编号" in l and "动作名" in l
             and "提示词片段" in l]
    added_heads = 0
    for i in heads:
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if NEW_COL in cells:
            continue
        new_cells = cells + [NEW_COL]
        lines[i] = "| " + " | ".join(new_cells) + " |"
        sep = lines[i + 1]
        if set(sep.strip()) <= set("|-: "):
            lines[i + 1] = "|" + "---|" * len(new_cells)
        added_heads += 1

    print(f"\n条目需补列 {len(missing_col)} · 已处理 {written} · 已有内容跳过 {skipped}"
          f" · 表头补列 {added_heads}")
    if banned:
        print("⛔ 生成值命中禁用词（未写入）：")
        for no, hits in banned:
            print(f"   {no}: {hits}")
        return 1
    if a.dry:
        print("\n（--dry：未写文件；确认后加 --write）")
        return 0
    with open(lib, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n✅ 已回写 {lib}")
    return 0


if __name__ == "__main__":
    sys.exit(main())