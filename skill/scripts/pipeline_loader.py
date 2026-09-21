#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片笔记流水线 · 素材装配器（pipeline_loader）

作用：把「可编辑提示词 + {{品牌}} 知识库 + AI 动作提示词库」装配成一个「本行提示词包」。
      —— 提示词从 prompts/*.md 实时读取（改完立即生效，不缓存、不内联、不改代码）
      —— 素材从 knowledge_base 实时读取（外部定位/卖点/禁用词/渠道语气/参照成品）
      —— 动作从 references/ 下的动作库实时抽条（按配额，带编号；`10-` / `03-` 两种命名均兼容）

用法：
  python3 pipeline_loader.py --check                     # 体检：提示词文件/知识库/【动作提示词库】是否可读
  python3 pipeline_loader.py --list-families             # 看【动作提示词库】各族条目数
  python3 pipeline_loader.py --row 2 --item 暮海蓝牛仔裤 --groups 9 \
          --out /tmp/pkg_row2.json --emit-groups /tmp/groups_row2.md
  python3 pipeline_loader.py --render-locks --out /tmp/locks.txt
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HOME = os.path.expanduser("~")
SKILL = os.environ.get("NOTE_PIPELINE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPTS = os.path.join(SKILL, "prompts")
# 动作提示词库：兼容多种命名（本库 references/10-action-library.md；对外版 references/03-action-library.md）
ACTION_LIB_CANDIDATES = ("references/10-action-library.md", "references/03-action-library.md",
                         "references/action-library.md", "action-library.md")
KB = os.environ.get("NOTE_KB_DIR", os.path.join(SKILL, "..", "knowledge_base"))


def action_lib_path() -> str:
    """定位【动作提示词库】。可用 NOTE_ACTION_LIB 环境变量指定；否则按候选名依次找。"""
    env = os.environ.get("NOTE_ACTION_LIB")
    if env and os.path.exists(env):
        return env
    for c in ACTION_LIB_CANDIDATES:
        p = os.path.join(SKILL, c)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        "找不到【动作提示词库】。候选：" + "、".join(ACTION_LIB_CANDIDATES)
        + f"（根目录 {SKILL}）；可用 NOTE_ACTION_LIB=/abs/path 指定")

# 配额（9 组 / 8 组）——「机位, 景别, 视线」三元组，按此顺序占满槽位
# 注意：机位只认 正面/3-4侧/全侧/背面 四大类；「局部特写」是【景别】不是机位。
# 两组配额的分母不同（8 组版 3-4侧 要 ≥3），逐项核对：
#   9 组 → 机位 正面2 · 3-4侧2 · 全侧2 · 背面2  |  景别 全身4 · 七分2 · 半身2 · 特写1  |  看镜头 1
#   8 组 → 机位 正面2 · 3-4侧3 · 全侧2 · 背面1  |  景别 全身4 · 七分2 · 半身2          |  看镜头 1
QUOTA = {
    9: [("正面", "全身", "看镜头"), ("正面", "半身", "看向画外"), ("3-4侧", "全身", "看向画外"),
        ("3-4侧", "七分", "低头"), ("全侧", "全身", "看向画外"), ("全侧", "七分", "看向画外"),
        ("背面", "全身", "不可见"), ("背面", "半身", "低头"), ("正面", "局部特写", "不可见")],
    8: [("正面", "全身", "看镜头"), ("正面", "半身", "看向画外"), ("3-4侧", "全身", "看向画外"),
        ("3-4侧", "七分", "低头"), ("3-4侧", "半身", "看向画外"), ("全侧", "全身", "看向画外"),
        ("全侧", "七分", "看向画外"), ("背面", "全身", "不可见")],
    # 9r = 2026-09-18 客户放宽版；2026-09-20 调整：正面共 2 张 = 1 张全身 + 1 张七分
    #      （避免「首图 + 组1 + 组2」三张都是正面全身站姿）
    "9r": [("正面", "全身", "看镜头"), ("正面", "七分", "看向画外"), ("3-4侧", "七分", "看向画外"),
           ("3-4侧", "半身", "低头"), ("全侧", "全身", "看向画外"), ("全侧", "半身", "看向画外"),
           ("背面", "全身", "不可见"), ("背面", "七分", "低头"), ("正面", "局部特写", "不可见")],
}
QUOTA_FLOOR = {   # 闸门用：各维度下限（与 04-nine-groups.md 的配额表一致）
    9: {"机位": {"正面": 2, "3-4侧": 2, "全侧": 1, "背面": 1},
        "景别": {"全身": 4, "七分": 2, "半身": 2, "局部特写": 1}, "看镜头": 2},
    8: {"机位": {"正面": 2, "3-4侧": 3, "全侧": 2, "背面": 1},
        "景别": {"全身": 4, "七分": 2, "半身": 2}, "看镜头": 2},
    # 放宽版下限（客户 2026-09-18 口径；2026-09-20 起补「组合」下限）
    "9r": {"机位": {"正面": 2, "3-4侧": 1, "全侧": 1, "背面": 1},
           "景别": {"全身": 3, "七分": 2, "半身": 2, "局部特写": 1}, "看镜头": 2,
           # 组合口径：正面必须「1 张全身 + 1 张七分」，不许两张都是正面全身
           "组合": {"正面|全身": 1, "正面|七分": 1}},
}
CAM_ALIAS = {"正面": ("正面",), "3-4侧": ("3-4侧", "3-4侧(过肩)", "3-4侧(俯拍)", "3-4侧(仰拍)"),
             "全侧": ("全侧", "全侧(跟拍)"), "背面": ("背面", "背面(过肩)")}


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ── 1. 提示词层 ────────────────────────────────────────────────
def load_prompt(name: str) -> str:
    """按文件名（不带 .md）读提示词文件；缺失即报错，退化为空字符串会让出图静默跑偏。"""
    path = os.path.join(PROMPTS, f"{name}.md")
    if not os.path.exists(path):
        raise FileNotFoundError(f"提示词文件缺失：{path}")
    return read(path)


def prompts_all() -> dict[str, str]:
    return {n: load_prompt(n) for n in
            ("01-cover-filter", "02-reverse-reasoning", "03-locks", "04-nine-groups", "05-copywriting")}


def extract_fenced(text: str, idx: int = 0, lang: str | None = None) -> str:
    """取第 idx 个 ``` 代码块内容（提示词块体都写在代码块里）。"""
    blocks = re.findall(r"```(?:text)?\n(.*?)```", text, re.S)
    if not blocks:
        return ""
    return blocks[min(idx, len(blocks) - 1)].strip()


# ── 2. 知识库层 ────────────────────────────────────────────────
def kb_positioning() -> str:
    """对外口径（01-brand.md §1.1 🔒 块）。"""
    p = os.path.join(KB, "01-brand.md")
    if not os.path.exists(p):
        return ""
    t = read(p)
    m = re.search(r"🔒.*?(?=\n## )", t, re.S)
    return (m.group(0) if m else t[:1200]).strip()


def kb_banned() -> list[str]:
    """禁用词（03-compliance.md 表格首列）。"""
    p = os.path.join(KB, "03-compliance.md")
    if not os.path.exists(p):
        return []
    out = []
    for line in read(p).splitlines():
        m = re.match(r"\|\s*\*{0,2}([^|*]{2,24})\*{0,2}\s*\|", line)
        if m and not m.group(1).startswith("---") and "禁用" not in m.group(1):
            w = m.group(1).strip()
            if w and w not in ("词", "类别", "原词"):
                out.append(w)
    return out[:60]


def kb_product(item: str) -> dict:
    """按单品名从 02-product.md ③ 全表抽六字段；找不到则回退返回空。"""
    p = os.path.join(KB, "02-product.md")
    if not (item and os.path.exists(p)):
        return {}
    t = read(p)
    m = re.search(rf"\*\*[0-9A-C]+-\d+　{item}[^*]*\*\*[^\n]*\n(.*?)(?=\n\*\*|\n### |\Z)", t, re.S)
    if not m:
        return {}
    fields = {}
    for lab, key in [("核心卖点", "sell"), ("版型/廓形", "shape"), ("设计细节", "design"),
                     ("面料/工艺", "fabric"), ("穿着利益", "benefit"), ("风格/场景", "style")]:
        fm = re.search(rf"- {lab}：(.*)", m.group(1))
        if fm:
            fields[key] = fm.group(1).strip()
    return fields


def kb_channel_examples(n: int = 3) -> list[dict]:
    """从 02a 抽 n 件成品文案当风格参照。"""
    p = os.path.join(KB, "02a-单品渠道文案.md")
    if not os.path.exists(p):
        return []
    t = read(p)
    out = []
    for m in re.finditer(r"### (\d[ABC]-\d+)　([^\s　]+).*?\n\n(.*?)(?=\n### |\Z)", t, re.S):
        body = m.group(3)
        def g(lab):
            mm = re.search(rf"- \*\*{lab}\*\*：(.*)", body)
            return mm.group(1).strip() if mm else ""
        out.append({"id": m.group(1), "name": m.group(2), "tmall": g("天猫长文本"),
                    "social": g("社媒转发/图片文案"), "private": g("私域"), "campaign": g("活动机制")})
        if len(out) >= n:
            break
    return out


# ── 3. 动作提示词库 ────────────────────────────────────────────
def load_actions() -> list[dict]:
    """解析【动作提示词库】的条目表 → 结构化动作条目（含 env_need：该动作需要的环境物）。

    2026-09-17 修两处（都是「表结构一变就静默出错」）：
      ① 原来按**固定列序**取值（ID+7 格）→ 表里插入「归入族」列后 `risk` 取到了族名、
         禁用项过滤失效。改为**按表头文字定位列**。
      ② 来源表（每行也以 `| X09 |` 开头）被当成动作条目 → 条数虚高（18 算成 28）。
         改为：**只解析表头同时含「动作名」与「提示词片段」的表**。
    """
    lib = action_lib_path()          # ← 调用【动作提示词库】的唯一入口（NOTE_ACTION_LIB 可覆盖）
    if not os.path.exists(lib):
        raise FileNotFoundError(f"【动作提示词库】缺失：{lib}")
    rows, fam, cols = [], "", None
    for line in read(lib).splitlines():
        hm = re.match(r"^###\s+([WSCTHPGMDEX])\s+·\s+(.+)", line)
        if hm:
            fam, cols = f"{hm.group(1)} · {hm.group(2).strip()}", None
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if any("编号" in c for c in cells):          # 任意表头行
            if any("动作名" in c for c in cells) and any("提示词片段" in c for c in cells):
                cols = list(cells)                   # 条目表 → 记下列名顺序
            else:
                cols = None                          # 来源表等非条目表 → 关闭解析（防误吞）
            continue
        if cols is None or not cells or not re.match(r"^[WSCTHPGMDEX]\d{1,3}$", cells[0]):
            continue                                 # 非条目表 / 分隔行 → 跳过

        def g(key: str) -> str:
            for i, name in enumerate(cols):
                if key in name and i < len(cells):
                    return cells[i]
            return ""

        contact = g("接触")
        # env_need：空间适配用。必须同时认出「环境(台阶)」（半角）与「环境接触（坐椅）」（全角+带"接触"）
        # —— 2026-09-17 修：原正则只匹配 `环境\(`，X 族条目一律写成「环境接触（…）」→ 永远解析不到，
        #    `--space` 空间过滤对 X 族静默失效。
        em = re.search(r"环境(?:接触)?[（(]([^）)+]+)[）)]", contact)
        rows.append({"no": cells[0], "name": g("动作名"), "fragment": g("提示词片段"),
                     "camera": g("建议机位"), "shot": g("建议景别"), "contact": contact,
                     "risk": g("风险"), "family": fam,
                     "env_need": em.group(1).strip() if em else ""})
    return rows


def sample_actions(groups: int, items: list[dict], space: str = "", rotate: int = 0, extra_avoid: str = "") -> list[dict]:
    """按配额给槽位配动作：四轮放宽（机位+景别 → 仅景别 → 仅机位 → 任取），被禁用（❌）的跳过。

    - space 命中 prompts/06-space-profiles.md 的画像时：① 按「可用环境物」过滤需要不存在道具的动作；
      ② 按画像「避开」词过滤空间不符的动作（如室内空间避开「沿街 / 路口 / 车流 / 台阶」）——这是
      动作库片段里含街景词、却没有机器可读空间标签的补偿手段（2026-09-17 实测踩到：室内抽出「背向
      走远·沿街向前走」）。
    - rotate：把候选池循环位移 N 位，用于让不同行抽出**不同**的九组（否则同一 space 各行结果完全一致）。
    """
    props, prof = resolve_space(space)
    avoid = [x for x in prof.get("avoid", []) if x]
    # --avoid：按「当次造型」追加排除词（例：这套没有包/腕表 → --avoid 包,腕表,咖啡杯）
    avoid += [x.strip() for x in re.split(r"[,，/、]", extra_avoid) if x.strip()]

    def env_fit(a) -> bool:
        need = a.get("env_need") or ""
        if not (props and need):
            return True
        return any(need in p or p in need for p in props)

    avoid_fams = [x for x in prof.get("avoid_fams", []) if x]

    def is_excluded(a) -> bool:
        if avoid_fams and a["no"][:1] in avoid_fams:
            return True
        return bool(avoid) and any(x in (a["fragment"] + a["contact"] + a["name"]) for x in avoid)

    pool = [a for a in items if "❌" not in a["risk"]]
    good = [a for a in pool if not is_excluded(a)]
    rest = [a for a in pool if is_excluded(a)]
    good.sort(key=lambda a: 0 if env_fit(a) else 1)          # 空间可用的优先
    if rotate and good:                                       # 只在「空间适配」段内位移，避免把不符动作转上来
        k = rotate % len(good)
        good = good[k:] + good[:k]
    pool = good + rest                                        # 不符项排到最后：配额无解时仍可兜底，不会抽不满
    used, out = set(), []
    for i, (cam, shot, gaze) in enumerate(QUOTA[groups], 1):
        def cam_ok(a):
            return any(a["camera"].startswith(c) for c in CAM_ALIAS.get(cam, (cam,)))

        def shot_ok(a, want):
            return want and want in (a["shot"] or "")

        pick = None
        for a in pool:                                        # ① 机位+景别
            if a["no"] not in used and cam_ok(a) and shot_ok(a, shot):
                pick = a; break
        if pick is None:                                      # ② 只对景别（稀缺档优先）
            for a in pool:
                if a["no"] not in used and shot_ok(a, shot):
                    pick = a; break
        if pick is None:                                      # ③ 只对机位
            for a in pool:
                if a["no"] not in used and cam_ok(a):
                    pick = a; break
        if pick is None:                                      # ④ 任取
            for a in pool:
                if a["no"] not in used:
                    pick = a; break
        if pick is None:
            break
        used.add(pick["no"])
        out.append({**pick, "slot": i, "quota_camera": cam, "quota_shot": shot or pick["shot"], "gaze": gaze})
    return out


def check_quota(actions: list[dict], groups: int) -> list[str]:
    """按 QUOTA_FLOOR 自查，返回违规描述列表（空＝达标）。"""
    floor = QUOTA_FLOOR[groups]
    bad = []
    cams, shots = {}, {}
    for a in actions:
        cams[a["quota_camera"]] = cams.get(a["quota_camera"], 0) + 1
        s = a["quota_shot"] or a["shot"]
        key = "局部特写" if "特写" in s else ("全身" if "全身" in s else ("七分" if "七分" in s else ("半身" if "半身" in s else s)))
        shots[key] = shots.get(key, 0) + 1
    for k, need in floor["机位"].items():
        if cams.get(k, 0) < need:
            bad.append(f"机位 {k} 需 ≥{need}，实际 {cams.get(k, 0)}")
    for k, need in floor["景别"].items():
        if shots.get(k, 0) < need:
            bad.append(f"景别 {k} 需 ≥{need}，实际 {shots.get(k, 0)}")
    # 组合下限（如「正面|全身≥1 且 正面|七分≥1」——防止两张正面都是全身站姿）
    if floor.get("组合"):
        pair = {}
        for a in actions:
            s = a["quota_shot"] or a["shot"]
            key = "局部特写" if "特写" in s else ("全身" if "全身" in s else ("七分" if "七分" in s else ("半身" if "半身" in s else s)))
            pair[f"{a['quota_camera']}|{key}"] = pair.get(f"{a['quota_camera']}|{key}", 0) + 1
        for k, need in floor["组合"].items():
            if pair.get(k, 0) < need:
                bad.append(f"组合 {k} 需 ≥{need}，实际 {pair.get(k, 0)}")
    looks = sum(1 for a in actions if "看镜头" in a["gaze"])
    if looks > floor["看镜头"]:
        bad.append(f"看镜头 需 ≤{floor['看镜头']}，实际 {looks}")
    if len({a["no"] for a in actions}) != len(actions):
        bad.append("存在重复动作条目")
    return bad


LIGHT_CYCLE = ["受光面偏正", "侧光加强", "轮廓光", "进入遮挡阴影", "侧逆光勾边"]


def render_group_lines(actions: list[dict]) -> str:
    """把抽到的动作渲染成「组N｜机位｜景别｜动作｜视线｜接触｜光影」九行骨架（供人改/供出图）。"""
    lines = []
    for a in actions:
        light = LIGHT_CYCLE[(a["slot"] - 1) % len(LIGHT_CYCLE)]
        shot = a["quota_shot"] or a["shot"]
        lines.append(f"【组{a['slot']}】{a['quota_camera']}｜{shot}｜{a['no']} {a['name']}"
                     f"（{a['fragment']}）｜{a['gaze']}｜{a['contact']}接触｜{light}")
    return "\n".join(lines)


EN_CAM = {"正面": "Front view", "正面(俯拍)": "Front view (slightly high angle)",
          "3-4侧": "Three-quarter view", "3-4侧(跟拍)": "Three-quarter view (tracking)",
          "全侧": "Full side profile", "全侧(跟拍)": "Full side profile (tracking)",
          "背面": "Back view"}
EN_SHOT = {"全身": "full body", "七分": "three-quarter length", "半身": "half body",
           "局部特写": "close-up detail", "局部": "close-up detail"}
EN_GAZE = {"看镜头": "Looking at the camera", "看向画外": "Looking off-camera", "低头": "Looking down",
           "不可见": "Not visible", "侧目看镜头": "Glancing at the camera", "仰头": "Looking up"}
EN_CONTACT = {"无": "No physical contact", "自身": "Self-contact", "环境": "Contact with the environment",
              "道具": "Contact with the prop", "环境(墙)": "Contact with the wall"}

# 接触对象关键词 → 英文（用于把「自身接触（双手在身后相握）」这类中文括注翻成纯英文）
CONTACT_KEYS = [
    (("双手", "手指", "手部", "手腕", "手臂", "手肘", "指尖", "手"), "hands"),
    (("鞋", "靴", "脚", "裤脚"), "footwear"),
    (("包", "袋"), "bag"),
    (("帽",), "hat"),
    (("唇", "脸", "下颌", "发"), "hand to face or hair"),
    (("椅面", "凳", "坐", "长椅", "台阶", "沙发", "座"), "seat"),
    (("墙",), "wall"),
    (("扶手", "栏杆"), "handrail"),
    (("杯", "碟"), "cup"),
    (("手机", "屏幕"), "phone"),
    (("镜",), "mirror"),
    (("门", "把手"), "door"),
    (("桌", "台面", "吧台"), "table"),
    (("货架", "架"), "shelf"),
]

EN_MAP_FILE = os.path.join(SKILL, "references", "action-en-map（本仓库未收录）")


def load_action_en_map() -> dict:
    """读 action-en-map（本仓库未收录）：| 编号 | English name | English action description |"""
    if not os.path.exists(EN_MAP_FILE):
        return {}
    out = {}
    for line in open(EN_MAP_FILE, encoding="utf-8"):
        m = re.match(r"^\|\s*([A-Z]\d{2})\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", line)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def _en_action(a: dict) -> tuple[str, str, bool]:
    """返回 (英文动作名, 英文动作描述, 是否命中映射表)。未命中则回落中文。"""
    m = load_action_en_map()
    if a.get("no") in m:
        name, frag = m[a["no"]]
        return name, frag, True
    return a.get("name", ""), a.get("fragment", ""), False


def _en_cam(v: str) -> str:
    return EN_CAM.get(v, v)


def _en_shot(v: str) -> str:
    return EN_SHOT.get(v, v)


def _en_gaze(v: str) -> str:
    return EN_GAZE.get(v, v)


def _en_contact(v: str) -> str:
    """把动作库的中文接触描述翻成纯英文（去掉所有中文括注）。"""
    raw = (v or "无").strip()
    if raw in ("", "无", "无接触"):
        return "No physical contact"
    if "自身" in raw and "环境" in raw:
        base = "Self-contact and contact with the environment"
    elif "自身" in raw:
        base = "Self-contact"
    elif "环境" in raw:
        base = "Contact with the environment"
    elif "道具" in raw:
        base = "Contact with the prop"
    else:
        base = EN_CONTACT.get(raw, "Contact with the environment")
    for keys, en in CONTACT_KEYS:
        if any(k in raw for k in keys):
            return f"{base} ({en})"
    return base


EN_CONSTRAINT = ("Same person, facial features, hairstyle, body proportions, outfit and accessories as the reference. "
                 "Keep the same setting, object placement, color palette and lighting. Natural anatomy, realistic scale "
                 "and physical contact. Candid smartphone photography, subject in sharp focus, background clear and "
                 "naturally detailed. No background blur, no shallow depth of field, no bokeh, no portrait-mode blur. "
                 "Preserve realistic spatial depth without exaggeration.")


def render_set_block(pkg: dict, slot: int) -> str:
    """Y–AG 单元格内容：纯英文 [Set N] 六槽块（2026-09-20 规格）。"""
    a = pkg["actions"][slot - 1]
    cam = _en_cam(a.get("quota_camera") or a.get("camera", ""))
    shot = _en_shot(a.get("quota_shot") or a.get("shot", ""))
    name, frag, hit = _en_action(a)
    gaze, contact = _en_gaze(a.get("gaze", "")), _en_contact(a.get("contact", ""))
    env = " ".join(pkg.get("env", "").split())
    full = (f"In the same setting as the reference image: {env} "
            f"Camera position: {cam}. Framing: {shot}. Action: {frag} "
            f"Gaze: {gaze.lower()}. Physical contact: {contact.lower()}. {EN_CONSTRAINT}")
    return (f"[Set {slot}]\n"
            f"Camera Position: {cam}\n"
            f"Framing: {shot}\n"
            f"Action: {a.get('no', '')} {name}"
            + ("" if hit else "（⚠️ 未收录英文映射，请在 action-en-map（本仓库未收录） 补）") + "\n"
            f"Gaze: {gaze}\n"
            f"Physical Contact: {contact}\n"
            f"Full Image Prompt: {full}")


def render_prompt(pkg: dict, slot: int) -> str:
    """Y–AG 单元格内容（英文 Set 块）。生成用提示词请用 render_prompt_for_gen()。"""
    return render_set_block(pkg, slot)


def render_prompt_for_gen(pkg: dict, slot: int) -> str:
    """实际送模型的提示词 = 中文锁块（人脸/服装/解剖/禁虚化） + 英文环境 + 英文动作槽位。"""
    a = pkg["actions"][slot - 1]
    locks = pkg["prompts"]["locks_body"].replace("{{服装锁词}}", pkg.get("garment_lock", ""))
    head = (f"[Set {a['slot']}]\nCamera Position: {_en_cam(a.get('quota_camera') or a.get('camera',''))}\n"
            f"Framing: {_en_shot(a.get('quota_shot') or a.get('shot',''))}\n"
            f"Action: {a.get('no','')} {_en_action(a)[0]} — {_en_action(a)[1]}\n"
            f"Gaze: {_en_gaze(a.get('gaze',''))}\nPhysical Contact: {_en_contact(a.get('contact',''))}\n"
            "在同一空间内，仅改变机位、景别、人物动作、视线与接触关系；空间结构、家具、门窗、地面、"
            "陈设道具位置、色调、服装与配饰全部不变。\n")
    return f"{head}{pkg.get('env','')}\n{locks}\n{EN_CONSTRAINT}"


# ── 4. CLI ─────────────────────────────────────────────────────
def cmd_check() -> int:
    ok = True
    print("── 提示词层（prompts/）──")
    for n in ("00-README", "01-cover-filter", "02-reverse-reasoning", "03-locks", "04-nine-groups", "05-copywriting"):
        p = os.path.join(PROMPTS, f"{n}.md")
        e = os.path.exists(p)
        ok &= e
        print(f"  {'✓' if e else '✗'} {n}.md  {os.path.getsize(p) if e else 0} 字节")
    print("── 知识库（knowledge_base）──")
    for f, label in [("01-brand.md", "对外口径"), ("02-product.md", "产品卖点 99 件"),
                     ("03-compliance.md", "禁用词"), ("05-channel.md", "渠道语气"),
                     ("02a-单品渠道文案.md", "参照成品")]:
        p = os.path.join(KB, f)
        e = os.path.exists(p)
        print(f"  {'✓' if e else '✗'} {f}  {os.path.getsize(p)//1024 if e else 0} KB  ({label})")
    print("── 动作提示词库 ──")
    acts = load_actions()
    fams = {}
    for a in acts:
        fams.setdefault(a["family"], 0)
        fams[a["family"]] += 1
    print(f"  ✓ 解析到 {len(acts)} 条 · {len(fams)} 族")
    for k, v in fams.items():
        print(f"     {v:>3}  {k[:56]}")
    print(f"\n结论：{'全部可读 ✅' if ok and acts else '有缺失 ❌'}")
    return 0 if (ok and acts) else 1


def cmd_lib() -> int:
    """列出【动作提示词库】全貌：族 / 条目数 / 可配组数（技能调用动作库的第一入口）。"""
    acts = load_actions()
    print(f"【动作提示词库】{action_lib_path()}")
    print(f"共 {len(acts)} 条 · {len({a['family'] for a in acts})} 族\n")
    fams = {}
    for a in acts:
        fams.setdefault(a["family"], []).append(a)
    for f, items in fams.items():
        cams = {}
        shots = {}
        for a in items:
            cams[a["camera"]] = cams.get(a["camera"], 0) + 1
            shots[a["shot"]] = shots.get(a["shot"], 0) + 1
        print(f"  {f}")
        print(f"     条目 {len(items)} · 机位 {dict(cams)}")
        print(f"     景别 {dict(shots)}")
    print("\n用法：--find 关键词 / --family D / --sample 9 --space 墙面,玻璃门 / --append '编号|动作名|片段|机位|景别|接触|风险' --family D")
    return 0


def cmd_find(kw: str) -> int:
    """在动作库中检索（编号 / 动作名 / 提示词片段）。"""
    hits = [a for a in load_actions()
            if kw.lower() in (a["no"] + a["name"] + a["fragment"] + a["contact"] + a["family"]).lower()]
    print(f"检索「{kw}」→ {len(hits)} 条")
    for a in hits:
        print(f"  {a['no']:>4} {a['name']} ｜{a['camera']}｜{a['shot']}｜{a['contact']}｜{a['risk']}")
        print(f"       {a['fragment']}")
    return 0 if hits else 1


def cmd_family(letter: str) -> int:
    """列出某族全部条目（如 D / S / H / X）。"""
    letter = letter.strip().upper()
    items = [a for a in load_actions() if a["no"].startswith(letter)]
    if not items:
        print(f"没有 {letter} 族条目"); return 1
    print(f"{items[0]['family']} — {len(items)} 条")
    for a in items:
        print(f"| {a['no']} | {a['name']} | {a['fragment']} | {a['camera']} | {a['shot']} | {a['contact']} | {a['risk']} |")
    return 0


def cmd_sample(n: int, space: str, groups: int = 9) -> int:
    """只抽条（不出图）：按配额从动作库抽 n 条并输出骨架，供人工替换/校对。"""
    acts = sample_actions(groups, load_actions(), space)
    acts = acts[:n]
    bad = check_quota(acts, groups) if n == groups else []
    print(render_group_lines(acts))
    print(f"\n（抽条 {len(acts)} 条｜空间适配 --space={space or '未指定'}｜"
          f"配额{'✅ 通过' if not bad else '⚠️ ' + '；'.join(bad)}）")
    return 0


# ── 3b. 空间画像 + 值域校验（都从可编辑文件里读，代码不写死规则）────────────────
SPACE_PROFILE_FILE = os.path.join(PROMPTS, "06-space-profiles.md")


def load_space_profiles() -> dict:
    """解析 prompts/06-space-profiles.md → {空间名: {props, weights, avoid}}。"""
    if not os.path.exists(SPACE_PROFILE_FILE):
        return {}
    profs, cur = {}, None
    for line in read(SPACE_PROFILE_FILE).splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1).strip()
            profs[cur] = {"props": [], "weights": {}, "avoid": [], "avoid_fams": []}
            continue
        if cur is None or not line.strip().startswith("-"):
            continue
        key, _, val = line.strip().lstrip("-").strip().partition("：")
        if "环境物" in key or "可用" in key:
            profs[cur]["props"] = [s.strip() for s in re.split(r"[,，/、]", val) if s.strip()]
        elif "族" in key:
            for tok in re.split(r"[,，/、\s]+", val):
                fm = re.match(r"([WSCTHPGMDEX])[=:×*]?(\d+)?$", tok.strip())
                if fm:
                    profs[cur]["weights"][fm.group(1)] = int(fm.group(2) or 2)
        elif "避开族" in key:
            profs[cur]["avoid_fams"] = [s.strip().upper() for s in re.split(r"[,，/、\s]", val) if s.strip()]
        elif "避开" in key or "禁用" in key:
            profs[cur]["avoid"] = [s.strip() for s in re.split(r"[,，/、]", val) if s.strip()]
    return profs


def resolve_space(space: str) -> tuple[list[str], dict]:
    """把 --space 解析成（可用环境物清单, 空间画像）。命中画像就用画像，否则按逗号当环境物清单。"""
    profs = load_space_profiles()
    key = next((k for k in profs if space and (space in k or any(s and s in space for s in k.split("/")))), None)
    if key:
        return profs[key]["props"], profs[key]
    return [s.strip() for s in re.split(r"[,，/、]", space) if s.strip()], {}


def load_domains() -> dict:
    """从动作库 §二 六槽位值域表解析合法值域（库本身是唯一事实源，改库即改校验）。

    坑：库里多张表都有「机位 / 景别」行（§二 值域表、§4.1 配额表…）。必须**只在值域章节内解析**，
    否则配额表的「全身≥4 · 七分≥2」会被当成合法值域 → 合法条目被误拒（2026-09-17 实测踩到）。
    """
    dom: dict[str, list[str]] = {}
    try:
        text = read(action_lib_path())
    except FileNotFoundError:
        return dom
    in_section = False
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            in_section = bool(re.search(r"值域", line))
            continue
        if not in_section or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        key = re.sub(r"\*", "", cells[0]).strip()
        if key not in ("机位", "景别", "视线", "接触关系") or key in dom:
            continue
        vals = []
        cell = re.sub(r"<br\s*/?>.*$", "", cells[1], flags=re.S)   # 丢掉 <br> 之后的变体清单
        cell = re.sub(r"（[^）]*）|\([^)]*\)", "", cell)            # 丢掉括号说明（里头也有加粗的说明词）
        vals = [v.strip() for v in re.findall(r"\*\*([^*]+)\*\*", cell)]
        if not vals:
            vals = [v.strip() for v in re.split(r"[/|]", cell) if v.strip()]
        # 过滤：只剔除配额类（带 ≥/≤）与超长说明；**保留含数字的值**（如 3-4侧）
        clean = [re.sub(r"（.*", "", v).strip() for v in vals if v.strip()]
        clean = [v for v in clean if v and "≥" not in v and "≤" not in v and len(v) <= 8]
        if clean:
            dom[key] = clean
    return dom


def validate_spec(no: str, name: str, frag: str, camera: str, shot: str,
                  contact: str, risk: str, family: str) -> list[str]:
    """入库校验：编号/机位/景别/接触/风险值域 + 片段与动作名长度。返回错误列表（空＝通过）。"""
    errs, dom = [], load_domains()
    if not re.match(rf"^{family}\d{{1,3}}$", no):
        errs.append(f"编号 {no} 与族 {family} 不匹配（应形如 {family}07）")
    cam = re.sub(r"[（(].*", "", camera).strip()      # 变体可能写在半角或全角括号里，两种都要剥
    if dom.get("机位") and cam not in dom["机位"] and "空镜" not in cam:
        errs.append(f"机位「{camera}」不在值域 {dom['机位']}（变体请写进括号，如 正面(仰拍)）")
    if dom.get("景别") and not any(v in shot for v in dom["景别"]):
        errs.append(f"景别「{shot}」不在值域 {dom['景别']}")
    if dom.get("接触关系") and contact and not any(v.replace("接触", "") in contact for v in dom["接触关系"]):
        errs.append(f"接触「{contact}」不在值域 {dom['接触关系']}（环境/道具类请写成 环境(台阶)）")
    if not re.match(r"^[✅⚠️❌]", risk):
        errs.append(f"风险「{risk}」须以 ✅ / ⚠️ / ❌ 开头（可跟说明）")
    n = len(re.sub(r"\s", "", frag))
    if not 8 <= n <= 140:
        errs.append(f"提示词片段 {n} 字，须在 8–140 字之间（太短没信息、太长会稀释锁块）")
    if not 2 <= len(name) <= 14:
        errs.append(f"动作名 {len(name)} 字，须在 2–14 字之间")
    return errs


def rank_by_space(space: str, top: int = 20) -> tuple[list[tuple], list[str], dict]:
    """按空间批量推荐：可用环境物过滤 + 族权重排序 + 风险加权。返回 (排序结果, 环境物, 画像)。"""
    props, prof = resolve_space(space)
    weights, avoid = prof.get("weights", {}), prof.get("avoid", [])
    rows = []
    for a in load_actions():
        if "❌" in a["risk"]:
            continue
        need = a.get("env_need") or ""
        if need and props and not any(need in p or p in need for p in props):
            continue                                    # 需要空间里没有的物件 → 不推荐
        if avoid and any(x and x in (a["fragment"] + a["contact"]) for x in avoid):
            continue
        w = int(weights.get(a["no"][0], 1))
        score = 2 * w + (1 if a["risk"].startswith("✅") else 0) - (2 if "⚠️⚠️" in a["risk"] else 0)
        rows.append((score, w, a))
    rows.sort(key=lambda t: (-t[0], t[2]["no"]))
    return rows[:top], props, prof


def cmd_space(space: str, top: int, groups: int, emit: str = "") -> int:
    """按空间批量推荐动作（--space 咖啡馆 --top 20）。"""
    rows, props, prof = rank_by_space(space, top)
    tag = "空间画像命中" if prof else "按环境物清单（无画像）"
    print(f"空间「{space}」 → {tag}｜可用环境物：{'、'.join(props) or '未指定'}")
    if prof:
        print(f"族权重：{prof.get('weights')}｜避开：{prof.get('avoid') or '—'}")
    print(f"\n推荐 {len(rows)} 条：\n")
    print("| 序 | 编号 | 动作名 | 机位 | 景别 | 接触 | 风险 |")
    print("|---|---|---|---|---|---|---|")
    for i, (score, w, a) in enumerate(rows, 1):
        print(f"| {i} | {a['no']} | {a['name']} | {a['camera']} | {a['shot']} | {a['contact']} | {a['risk']} |")
    if emit:
        with open(emit, "w", encoding="utf-8") as fh:
            fh.write(f"# 空间「{space}」动作推荐 top{top}（{tag}）\n\n")
            fh.write("| 序 | 编号 | 动作名 | 提示词片段 | 机位 | 景别 | 接触 | 风险 |\n|---|---|---|---|---|---|---|---|\n")
            for i, (score, w, a) in enumerate(rows, 1):
                fh.write(f"| {i} | {a['no']} | {a['name']} | {a['fragment']} | {a['camera']} | {a['shot']} | {a['contact']} | {a['risk']} |\n")
        print(f"\n  ✓ 已导出 → {emit}")
    return 0 if rows else 1


def cmd_append(family: str, spec: str, force: bool = False) -> int:
    """把实测新动作**写回动作库**（库是活的）；入库前过「值域 / 长度」校验，防脏数据。"""
    fam = family.strip().upper()
    parts = [p.strip() for p in spec.strip().strip("|").split("|")]
    if len(parts) < 5:
        print("格式：'编号|动作名|提示词片段|机位|景别|接触|风险'（至少 5 段）"); return 2
    parts += [""] * (7 - len(parts))
    no, name, frag, camera, shot, contact, risk = parts[:7]
    errs = validate_spec(no, name, frag, camera, shot, contact, risk, fam)
    if errs:
        print("⛔ 入库校验未通过（未写入）：")
        for e in errs:
            print("   ✗", e)
        if not force:
            print("\n改好再提交；确要强行写入可加 --force（不建议——脏数据会污染闸门与动作分布统计）")
            return 2
        print("\n⚠️ --force：忽略以上问题继续写入")
    lib = action_lib_path()
    lines = read(lib).splitlines()
    if any(l.strip().startswith(f"| {no} ") for l in lines):
        print(f"{no} 已存在，未写入（要改就直接改库文件）"); return 1
    # 定位该族的条目表，插到最后一行之后
    head = next((i for i, l in enumerate(lines) if re.match(rf"^###\s+{fam}\s+·", l)), None)
    if head is None:
        print(f"库里没有 {fam} 族"); return 1
    last = None
    for i in range(head + 1, len(lines)):
        if lines[i].startswith("### ") or (lines[i].startswith("## ") and i > head + 1):
            break
        if re.match(rf"^\|\s*{fam}\d{{1,3}}\s*\|", lines[i]):
            last = i
    if last is None:
        print(f"{fam} 族下没找到条目表"); return 1
    lines.insert(last + 1, "| " + " | ".join(parts) + " |")
    # 族标题里的（N）计数要 +1（注意：计数可能在行中间，后面还跟着说明文字）
    m = re.match(rf"^(###\s+{fam}\s+·\s+[^（]*)（(\d+)）(.*)$", lines[head])
    if m:
        lines[head] = f"{m.group(1)}（{int(m.group(2)) + 1}）{m.group(3)}"
    open(lib, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"✅ 已写入 {action_lib_path()} → {no}（族内计数已 +1；记得跑 sync/push）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="图片笔记流水线素材装配器")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list-families", action="store_true")
    ap.add_argument("--row", type=int)
    ap.add_argument("--item", default="", help="知识库里的单品名（用于拉卖点锁词）")
    ap.add_argument("--groups", type=int, default=9, choices=[8, 9])
    ap.add_argument("--env", default="", help="阶段1 反推得到的环境描述（P 列内容）")
    ap.add_argument("--garment-lock", default="", help="服装锁词（不填则用知识库/AI 生成）")
    ap.add_argument("--space", default="", help="本空间可用环境物（逗号分隔，如 墙面,玻璃门,路缘），用于动作空间适配")
    ap.add_argument("--out", help="输出提示词包 JSON")
    ap.add_argument("--emit-groups", help="输出九组骨架 MD（可读可改）")
    ap.add_argument("--render-locks", action="store_true")
    # ── 【动作提示词库】独立调用入口（本项目的一等公民能力）──
    ap.add_argument("--lib", action="store_true", help="列出动作库全貌（族/条目数/机位景别分布）")
    ap.add_argument("--find", default="", help="在动作库检索条目（编号/动作名/提示词片段/族）")
    ap.add_argument("--family", default="", help="列出某族全部条目（如 D / S / H / X）")
    ap.add_argument("--sample", type=int, default=0, help="只从动作库抽 N 条（配 --space），不出图")
    ap.add_argument("--append", default="", help="向动作库回写新条目：'编号|动作名|片段|机位|景别|接触|风险'（配 --family）")
    ap.add_argument("--top", type=int, default=0, help="按空间批量推荐 N 条（配 --space，如 --space 咖啡馆 --top 20）")
    ap.add_argument("--emit-space", default="", help="把空间推荐结果导出为 MD")
    ap.add_argument("--force", action="store_true", help="--append 时跳过入库校验（不建议）")
    ap.add_argument("--avoid", default="", help="按当次造型追加排除词（逗号分隔，如 包,腕表,咖啡杯）")
    ap.add_argument("--quota", choices=["std", "relaxed"], default="std",
                    help="配额口径：std=严格版（正面2/3-4侧2/全侧≥1/背面≥1 景别全身4/七分2/半身2/特写1）；relaxed=放宽版（3-4侧≥1/七分≥1/半身≥1，客户 2026-09-18 口径）")
    a = ap.parse_args()

    if a.check:
        return cmd_check()
    if a.list_families:
        # 修 2026-09-17：原来是 `for k, v in sorted({x["family"] ...})` —— 集合元素是字符串，
        # 二元组解包必然 ValueError（族名超 2 字符）。改为按族计数输出。
        from collections import Counter
        counts = Counter(x["family"] for x in load_actions())
        total = sum(counts.values())
        for fam, n in sorted(counts.items()):
            print(f"  {n:>4}  {fam}")
        print(f"  ──── 共 {len(counts)} 族 / {total} 条")
        return 0
    # ── 【动作提示词库】独立调用入口 ──
    if a.lib:
        return cmd_lib()
    if a.find:
        return cmd_find(a.find)
    if a.family and not a.append:
        return cmd_family(a.family)
    if a.sample:
        return cmd_sample(a.sample, a.space, a.groups)
    if a.top:
        return cmd_space(a.space, a.top, a.groups, a.emit_space)
    if a.append:
        return cmd_append(a.family, a.append, a.force)

    P = prompts_all()
    locks_md = P["03-locks"]
    pkg = {
        "row": a.row, "item": a.item, "groups": a.groups,
        "prompts": {"locks_file": "prompts/03-locks.md",
                    "locks_body": extract_fenced(locks_md, 0),
                    "hero_position": extract_fenced(locks_md, 1),
                    "ref_rule": extract_fenced(locks_md, 2),
                    "reverse_spec": P["02-reverse-reasoning"],
                    "groups_spec": P["04-nine-groups"],
                    "copy_spec": P["05-copywriting"],
                    "cover_filter": P["01-cover-filter"]},
        "env": a.env, "garment_lock": a.garment_lock or "{{服装锁词·待填}}", "space": a.space,
        "kb": {"positioning": kb_positioning()[:800], "product": kb_product(a.item),
               "banned": kb_banned(), "refs": kb_channel_examples(2)},
        "facts": {"aspect": "3:4", "size_1k": "864x1152", "model": "gpt-image-2-vip", "need_serial": True},
    }
    # 按行号自动位移候选池 → 不同行抽出不同九组；--quota relaxed 切到放宽版配额表
    _qkey = a.groups if a.quota == "std" else (f"{a.groups}r" if f"{a.groups}r" in QUOTA else a.groups)
    pkg["quota_profile"] = _qkey
    pkg["actions"] = sample_actions(_qkey, load_actions(), a.space, rotate=(a.row or 0) * 11,
                                     extra_avoid=a.avoid)
    pkg["quota_violations"] = check_quota(pkg["actions"], _qkey)
    pkg["groups_skeleton"] = render_group_lines(pkg["actions"])
    if pkg["quota_violations"]:
        print("  ⚠️ 配额未达标（请在 prompts/04-nine-groups.md 放宽或手工补）："
              + "；".join(pkg["quota_violations"]), file=sys.stderr)
    else:
        print("  ✅ 配额自查通过（机位/景别/看镜头/无重复）")

    if a.render_locks:
        print(pkg["prompts"]["locks_body"].replace("{{服装锁词}}", pkg["garment_lock"]))
    if a.emit_groups:
        with open(a.emit_groups, "w", encoding="utf-8") as fh:
            fh.write(f"# 行{a.row} · {a.item} · {a.groups} 组骨架（改六槽位即可）\n\n```\n{pkg['groups_skeleton']}\n```\n")
        print(f"  ✓ 九组骨架 → {a.emit_groups}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(pkg, fh, ensure_ascii=False, indent=1)
        print(f"  ✓ 提示词包 → {a.out}（{os.path.getsize(a.out)//1024} KB）")
    if not (a.render_locks or a.emit_groups or a.out):
        print(f"行{a.row} · {a.item} · {a.groups} 组")
        print(pkg["groups_skeleton"])
    return 0


if __name__ == "__main__":
    sys.exit(main())