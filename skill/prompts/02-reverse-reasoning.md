# 阶段 1 · P 列反推（只反推【环境与拍摄】＋【Accessories】）

识别 Q 列参考图，在 P 列输出**全英文**提示词（2026-09-20 起：标签与正文**必须全英文**）。

## 🚫 必须剥离（一律不描述）

- **人物本身**：脸、发型、身材、姿态、表情、肤色
- 若图中有人物姿态：只保留「人物在画面中的位置、朝向、景别占幅、动作」四个中性信息
- **主体服装的款式/颜色/材质**（服装一律以 T/V 平铺图为准，见 `references/07-garment-source-and-prop-discipline.md`）

## ✅ 固定 6 段输出（英文标签，逐字沿用）

```text
[Scene]
[Lighting]
[Camera & Composition]
[Color & Texture]
[Reusable Keywords]
[Accessories]
```

1. **[Scene]**：真实可见的空间、建筑、门窗、道路、家具、植物及道具，并注明**画面位置**（左/中/右、上/下）。**严禁虚构画面中不存在的物体、建筑或 Logo**。
2. **[Lighting]**：光源类型、方向、软硬、色温、明暗比与投影，**以参考图为准**（不套用未出现的斜阳/戏剧光）。
3. **[Camera & Composition]**：手机快照感、等效焦段（24/28/35mm）、机位高度、景别、主体位置、留白比例与自然裁切。
4. **[Color & Texture]**：主辅色、饱和度、对比度、真实手机摄影质感。**必须原样包含下面这句**：

   ```text
   Keep both the subject and background clear and naturally detailed. No background blur, no shallow depth of field, no bokeh, and no portrait-mode blur. Preserve realistic spatial depth without exaggeration.
   ```

   ⚠️ 2026-09-20 规格变更：**不再要求「背景轻微低锐化/自然虚化」**。人物与背景必须同等清晰，保留真实空间层次。
5. **[Reusable Keywords]**：8–12 个可直接拼进生图提示词的英文关键词（**不得出现其他品牌名与真人姓名**）。
6. **[Accessories]**：**只描述参考图中可见**的鞋子、首饰、包袋等穿戴项（品类 + 颜色 + 材质 + 位置/戴法），**不推测不可见细节**。
   ⚠️ 上衣与下装的款式/颜色/材质仍以 T/V 平铺图为准；本段只补「平铺图看不到的穿戴项」。若 T/V 已含腰带等配件，在此复述一遍以强化锁定。

## 输出纪律

- **标签与正文全英文**（P 列不得出现中文），一列一段，六段齐全
- 不写人物外貌；服装主体以 T/V 为准
- 图片比例固定 3:4