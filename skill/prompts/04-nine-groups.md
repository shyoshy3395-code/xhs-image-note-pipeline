# 阶段 3 · Y–AG 九组动作提示词（配额 + 格式）

## 输出格式（每格一组，**全英文**，2026-09-20 起）

```text
[Set N]
Camera Position: ...
Framing: ...
Action: ...
Gaze: ...
Physical Contact: ...
Full Image Prompt: ...
```

- `Action` 必须取自【动作提示词库】（`references/03-action-library.md`，11 族 135 条），带编号（如 `S08`），英文用 `action-en-map（本仓库未收录）` 的映射表；**不要自由发挥**
- `Full Image Prompt` 简洁直述：具体环境 + 相机位置 + 景别 + 自然动作 + 视线 + 接触关系，并**逐字附带**统一约束句：
  `Same person, facial features, hairstyle, body proportions, outfit and accessories as the reference. Keep the same setting, object placement, color palette and lighting. Natural anatomy, realistic scale and physical contact. Candid smartphone photography, subject in sharp focus, background clear and naturally detailed. No background blur, no shallow depth of field, no bokeh, no portrait-mode blur. Preserve realistic spatial depth without exaggeration.`
- 同一空间内**只改机位/景别/动作/视线/接触关系**；空间结构、家具、门窗、地面、陈设、色调、服装配饰全部不变
- 只使用首图已有道具，**不凭空添加手机、咖啡杯或其他物件**

## 两套配额口径（用 `--quota std|relaxed` 选）

| 维度 | **std**（默认，严格版） | **relaxed / 9r**（客户口径，2026-09-20 调整） |
|---|---|---|
| 机位·正面 | ≥2 | **≥2（= 1 张全身 + 1 张七分）** |
| 机位·3-4侧 | ≥2 | ≥1 |
| 机位·全侧 | ≥1 | ≥1 |
| 机位·背面 | ≥1 | **背面全身 ≥1** |
| 景别·全身 | ≥4 | ≥3 |
| 景别·七分 | ≥2 | ≥2 |
| 景别·半身 | ≥2 | ≥2 |
| 景别·特写 | ≥1 | ≥1 |
| 看镜头 | ≤2 | ≤2 |
| **组合（新）** | — | **`正面｜全身 ≥1` 且 `正面｜七分 ≥1`** —— 正面两张不许都是全身站姿（首图＝正面全身，故第 2 张正面必须七分） |
| 其他 | 机位/景别/动作各 ≥3 种不同值；不允许两组以上完全同款；留 1 组给局部特写（配饰/面料验收镜头） | 同左 |


## 9s 口径（2026-09-21 客户新规格 · 用于 O 列参考图批次）

| 维度 | 要求 |
|---|---|
| 正面 | **正面全身 ≥1**（不再要求 2 组） |
| 3-4侧 | ≥1 |
| 全侧 | ≥1 |
| 七分 | ≥1 |
| 半身 | ≥1 |
| **局部/服装特写** | ≥1（优先库内 `D03 领口与颈部线条` / `D08 面料斜射光` / `D02 袖口与手腕`，**不要**选成腕表/戒指等配饰特写） |
| 第9组 | 自由补充，与前 8 组不重复 |
| 看镜头 | ≤2 |
| 其他 | 动作不重复；机位×景别组合有变化 |

用法：`pipeline_loader.py --quota 9s`

## 自查

```bash
python3 scripts/pipeline_loader.py --row 2 --item "<知识库单品名>" --groups 9 \
    --quota relaxed --space "<空间画像名>" --avoid "<当次不存在的道具>" \
    --env "<P列英文>" --garment-lock "<服装锁词>" --out /tmp/pkg.json --emit-groups /tmp/groups.md
# → 打印「✅ 配额自查通过」或列出未达标项
python3 scripts/check_action_distribution.py --file <提示词文件> --groups 9 --cols Y Z AA AB AC AD AE AF AG
```

## 完成检查（交付前）

- Y–AG 全英文；`Camera Position / Framing / Action / Gaze / Physical Contact / Full Image Prompt` 六槽齐全
- 九组与 F–N 九张图一一对应（Y→F、Z→G、AA→H、AB→I、AC→J、AD→K、AE→L、AF→M、AG→N）
- 每组 Full Image Prompt 含统一约束句与 no-blur 句