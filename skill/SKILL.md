---
name: xhs-image-note-pipeline
description: 小红书图片笔记流水线 —— 从真实爆款封面反推环境提示词，生成首图与 9 组动作变体，回填 Excel 模板并产出标题/正文/话题。提示词全部外置在 prompts/ 可编辑，运行时读取自带知识库与动作提示词库。
license: MIT
---

# 小红书图片笔记流水线

> 一张「真实爆款封面」的空间与光影 → 你自己的模特与服装 → 9 张成图 → 回填 Excel。
> **本技能的命令与文件结构见 `README.md`；提示词正文在 `prompts/`，改它不用碰代码。**

## 用法（Agent 流程）

1. **阶段 0**：读 `prompts/01-cover-filter.md` + `references/02-xhs-cover-sourcing.md`，抓封面并按标准筛选 → 3:4 内嵌到参考图列
2. **阶段 1**：看封面图，按 `prompts/02-reverse-reasoning.md` 写**只含环境与拍摄**的英文提示词 → 反推列
3. **阶段 2**：`python3 skill/scripts/pipeline_loader.py …` 装配提示词包（自动从动作库抽条 + 配额自查）→ `python3 skill/scripts/run_image_note.py …` 出首图与各组
4. **阶段 3**：读 `prompts/05-copywriting.md` + `knowledge_base/` 写标题/正文/话题 → 内嵌回 xlsx → 过交付闸门

## 关键纪律

- 锁块（人脸/服装/比例/质感/禁止）**逐字复用**，改了就可能在交互动作里丢配饰
- 9 组配额：机位 正面≥2·3-4侧≥2·全侧≥1·背面≥1；景别 全身≥4·七分≥2·半身≥2·特写≥1；看镜头 ≤2
- **每句文案必须能在图里找到依据**（写体感不写卖点断言）；9 图同空间就别靠「换场景」凑丰富度

## 改提示词

改 `skill/prompts/*.md` → 立即生效（脚本每次运行实时读取）。改完 `pipeline_loader.py --check` 自检。
