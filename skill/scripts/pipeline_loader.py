#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""图片笔记流水线 · 素材装配器（pipeline_loader）

      —— 提示词从 prompts/*.md 实时读取（改完立即生效，不缓存、不内联、不改代码）
      —— 素材从 knowledge_base 实时读取（外部定位/卖点/禁用词/渠道语气/参照成品）
      —— 动作从 references/03-action-library.md 实时抽条（按配额，带编号）

用法：
  python3 pipeline_loader.py --check                     # 体检：提示词文件/知识库/动作库是否可读
  python3 pipeline_loader.py --list-families             # 看动作库各族条目数
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
ACTION_LIB = os.path.join(SKILL, "references/03-action-library.md")
KB = os.environ.get("NOTE_KB_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "knowledge_base"))

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
}
QUOTA_FLOOR = {   # 闸门用：各维度下限（与 04-nine-groups.md 的配额表一致）
    9: {"机位": {"正面": 2, "3-4侧": 2, "全侧": 1, "背面": 1},
        "景别": {"全身": 4, "七分": 2, "半身": 2, "局部特写": 1}, "看镜头": 2},
    8: {"机位": {"正面": 2, "3-4侧": 3, "全侧": 2, "背面": 1},
        "景别": {"全身": 4, "七分": 2, "半身": 2}, "看镜头": 2},
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
    """解析 10-action-library.md 的条目表 → 结构化动作条目（含 env_need：该动作需要的环境物）。"""
    if not os.path.exists(ACTION_LIB):
        raise FileNotFoundError(f"动作库缺失：{ACTION_LIB}")
    rows = []
    fam = ""
    for line in read(ACTION_LIB).splitlines():
        hm = re.match(r"^###\s+([WSCTHPGMDEX])\s+·\s+(.+)", line)
        if hm:
            fam = f"{hm.group(1)} · {hm.group(2).strip()}"
            continue
        m = re.match(r"^\|\s*([WSCTHPGMDEX]\d{1,3})\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", line)
        if not m:
            continue
        contact = m.group(6).strip()
        em = re.search(r"环境\(([^)]+)\)", contact)
        rows.append({"no": m.group(1), "name": m.group(2).strip(), "fragment": m.group(3).strip(),
                     "camera": m.group(4).strip(), "shot": m.group(5).strip(),
                     "contact": contact, "risk": m.group(7).strip(), "family": fam,
                     "env_need": em.group(1).strip() if em else ""})
    return rows


def sample_actions(groups: int, items: list[dict], space: str = "") -> list[dict]:
    """按配额给槽位配动作：四轮放宽（机位+景别 → 仅景别 → 仅机位 → 任取），被禁用（❌）的跳过。
    space（逗号分隔的本空间可用环境物，如 `墙面,玻璃门,路缘,长椅`）非空时，
    需要空间里不存在的道具的动作（如「台阶」）自动排到队尾 —— 避免机位配额达标却拍不出来的动作。"""
    def env_fit(a) -> bool:
        need = a.get("env_need") or ""
        if not (space and need):
            return True
        have = [s.strip() for s in re.split(r"[,，/、]", space) if s.strip()]
        return any(n in s or s in n for n in [need] for s in have)

    pool = [a for a in items if "❌" not in a["risk"]]
    pool.sort(key=lambda a: 0 if env_fit(a) else 1)          # 空间可用的优先，不淘汰（保配额）
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


def render_prompt(pkg: dict, slot: int) -> str:
    """组合第 slot 组的完整生图 prompt（锁块 + 环境 + 动作 + 卖点锁词）。"""
    a = pkg["actions"][slot - 1]
    locks = pkg["prompts"]["locks_body"]
    env = pkg.get("env", "")
    garant = pkg.get("garment_lock", "{{服装锁词}}")
    body = locks.replace("{{服装锁词}}", garant)
    head = (f"【组{a['slot']}】{a['quota_camera']}｜{a['quota_shot'] or a['shot']}｜"
            f"{a['no']} {a['name']}｜{a['gaze']}｜{a['contact']}接触\n"
            f"动作：{a['fragment']}\n"
            "在同一空间内，仅改变机位、景别、人物动作、视线与接触关系；空间结构、家具、门窗、地面、"
            "陈设道具位置、色调、服装与配饰全部不变。\n")
    return f"{head}{env}\n{body}"


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
    a = ap.parse_args()

    if a.check:
        return cmd_check()
    if a.list_families:
        for k, v in sorted({x["family"] for x in load_actions()}):
            print(" ", k)
        return 0

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
    pkg["actions"] = sample_actions(a.groups, load_actions(), a.space)
    pkg["quota_violations"] = check_quota(pkg["actions"], a.groups)
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