# 小红书图片笔记流水线（XHS Image-Note Pipeline）

把一张「真实爆款封面」的**空间与光影**复刻成 9 张成图，并自动回填进 Excel 模板 —— 供 AI Agent（Hermes Agent）驱动，也可脱离 Agent 当纯脚本用。

> 核心思路：**封面只借空间，人物与服装靠自己的参考图锁死。**
> `参考封面 → 反推环境提示词 → 首图 → 【动作提示词库】抽条生成 9 组 → 内嵌回 Excel → 出文案`

## 它能做什么

| 阶段 | 产出 |
|---|---|
| 0 抓封面 | 从 #ootdinspo / #howto穿搭 拉真实笔记封面，按 5 条合格 + 5 条红线筛选，3:4 裁切 |
| 1 反推 | 看图写出**只含环境与拍摄**的英文提示词（人脸/服装一律剥离） |
| 2 出图 | 首图（环境+人脸+上身+平铺 多图参考）→ 9 组动作变体（配额自动校验） |
| 3 文案 + 回填 | 标题/正文/话题，连同成图**内嵌**进 xlsx 单元格（保住 WPS DISPIMG 参考图） |

## 5 分钟跑起来

```bash
git clone <this-repo> && cd xhs-image-note-pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) 体检：提示词 / 知识库 / 【动作提示词库】是否齐
python3 skill/scripts/pipeline_loader.py --check

# 2) 装配一行的提示词包（会打印配额自查结果）
python3 skill/scripts/pipeline_loader.py --row 2 --item "示例单品" --groups 9 \
    --env "outdoor overcast street corner, brick wall, olive-yellow glass doors" \
    --garment-lock "深灰短大衣 + 直筒牛仔 + 黑短靴" \
    --space "墙面,玻璃门,路缘" \
    --out /tmp/pkg.json --emit-groups /tmp/groups.md

# 3) 先干跑校对提示词（不花钱），再去掉 --dry 真出图
python3 skill/scripts/run_image_note.py --pkg /tmp/pkg.json --row 2 \
    --outdir ./out/row2 --cover cover.jpg --face face.png --up1 up1.jpg --up2 up2.jpg --flat flat.jpg --dry
```

出图需要一个兼容 OpenAI 格式的生图接口。把 key 放进 `.env`：

```bash
cp .env.example .env    # 填 IMAGE_API_KEY / IMAGE_BASE_URL
```

模型从 `.env` 的 `IMAGE_MODEL` 读（`.env.example` 示例填 `gpt-image-2-vip`，不填则用 `gpt-image-1`）。
`nano-banana*` 族走比例+尺寸档（`--model nano-banana-pro --size 2K`），`gpt-image-*` 族直接给像素（`--aspect 864x1152`）。
执行器默认用本仓库自带的 `skill/scripts/image_api.py`；要换成你自己的，给环境变量 `IMAGE_API_SCRIPT`。

## 目录

```
skill/
├── SKILL.md                 给 Agent 用的技能说明（Hermes / Claude Code 均可读）
├── prompts/                 ✏️ 提示词配方（改这里＝改行为，脚本实时读取、不缓存）
│   ├── 00-README.md             怎么改 · 占位符表 · 文件↔阶段对应
│   ├── 01-cover-filter.md       封面合格标准与红线
│   ├── 02-reverse-reasoning.md  反推 6 段式（场景/光影/镜头/色调/关键词/搭配）+ 必须剥离清单
│   ├── 03-locks.md              五块锁（人脸/服装/比例/质感/禁止）+ 首图机位
│   ├── 04-nine-groups.md        9 组输出格式 + 配额矩阵
│   ├── 05-copywriting.md        文案规格 + 知识库取料顺序
│   └── 06-space-profiles.md     空间画像（按空间批量推荐动作时读它）
├── scripts/
│   ├── pipeline_loader.py       🧩 装配器：提示词 + 知识库 + 【动作提示词库】 → 提示词包（内置配额闸门/空间适配）
│   ├── run_image_note.py        🚀 运行器：串行 / 可续跑 / 重试；**脚本内零提示词正文**
│   ├── fill_action_prompts.py   ✍️ 动作提示词三段式（机位·远近·动作）生成 / 校验
│   ├── qc_contact_sheet.py      🔍 出图后把「首图＋9 组」拼成大图，交视觉模型逐张核对
│   └── image_api.py             生图接口封装（兼容 OpenAI 格式）
└── references/
    ├── 01-reverse-prompt-spec.md              反推规格（含动作写法与抽组顺序）
    ├── 02-xhs-cover-sourcing.md               封面抓取纪律（含下载被拒的解法）
    ├── 03-action-library.md                   🎬 【动作提示词库】：11 族 133 条（+27 条真实爆款反推）/ 三段式动作提示词 / 六槽位值域 / 抽组配比
    ├── 04-locks-and-groups.md                 锁块与分布矩阵速查
    ├── 05-pipeline-orchestration.md           流水线总纲（阶段 0–3 · 命令序列 · 闸门 · 29 条已知坑）
    ├── 06-action-sampling-and-space-fit.md    动作抽条两坑（逐行重复 / 空间不符）
    └── 07-garment-source-and-prop-discipline.md 服装依据＝平铺图（上身图仅参考）+ 道具纪律
knowledge_base/              你自己的品牌素材（模板已给，填了才叫「有品牌」）
examples/template-schema.md  Excel 模板列位说明（自己建一张空表即可）
docs/architecture.md         四阶段表 + 两道自动闸门（概要）
```

## 数据流

```
prompts/*.md ─┐
knowledge_base/ ─┼→ pipeline_loader.py → 提示词包 pkg.json ─┐
references/03-action-library.md ─┘                          │
                                                            ▼
                              run_image_note.py → 首图 + 9 组图
                                                            │
                       降噪 → 内嵌回 xlsx（保住 DISPIMG）→ 交付闸门
```

## 已知坑（省你几天）

1. **内嵌图的显示尺寸**：行高解析若用 `[^>]*ht="` 会被 `customHeight="1"` 劫持 → 图缩成 15×20px（肉眼看不见但文件一切正常）。必须 `\sht="`。
2. **先改行高再算图尺寸**：图会永远按旧行高缩放。
3. **一次调用写全部浮图**：新增 + 模板里已有的一起写，否则旧浮图变死链。
4. **生图需串行**：多数模型并发直接报错；脚本已串行 + 退避重试。
5. **参考图先缩到长边 ≤1024**：否则请求体过大，返回误导性的鉴权错误。
6. **抓封面**：浏览走代理、**下载必须去代理**；连续下载被拒时每条间隔 12s、退避 25s。
7. **长文本单元格要 wrapText**：否则 `\n` 不换行。

## 关于「上游内部件」

本仓库只公开**方法层**。文档里偶尔提到的下列名字属于**上游技能库的内部件，未随本仓库一起公开**，
按名字在这里解释一下，免得你去找：

| 文中出现 | 是什么 |
|---|---|
| 《约束与排障》 | 出图约束库：9 张同街区机位表、尺寸/耗时/换模型纪律、回填写入规范 |
| 《xlsx 内嵌坑位》 | `customHeight` 劫持行高等 xlsx 手术踩坑记录 |
| 《封面下载运维》 | 平台链接形态变化、代理按域名分流、节流与续跑 |
| `xlsx_surgery.py` / `assemble_image_note.py` / `verify_image_note_xlsx.py` | **保住 DISPIMG 的 xlsx 手术与交付闸门**（本仓库只含生成侧脚本） |
| `check_action_distribution.py` | 动作组配额闸门 |
| `qc_face_match.py` | 人脸一致性核验（要解析 xlsx 里 `cellimages.xml` / DISPIMG 内部结构，属私有的回填层；方法说明见 `skill/references/05-pipeline-orchestration.md` 第 29 条） |
| `templates/batch_row_driver.py` | 行级批量驱动起步件（多行续跑 / 定向返工用；本仓库未带 `templates/` 目录） |

回填层（xlsx 手术与交付闸门）属上游内部件，**本仓库有意只公开生成侧**：方法论可学、生成侧可跑；
要把这套流程用到自己的表上，按上面的坑位说明自行实现即可。

## 合规与边界

- 只用**真实笔记封面**做空间参考，不搬运他人成图；人物与服装一律用**你自己有权使用的**参考图
- 生成前自查：不得出现他人品牌 Logo / 酒杯香烟等违禁道具 / 乱码文字
- 生图模型与平台的服务条款、以及当地广告法（绝对化用语等），部署方自行把关

## 怎么分发

| 方式 | 命令 | 说明 |
|---|---|---|
| **官方技能注册表** | `hermes skills publish ./skill` | 发布后别人 `hermes skills search` 就能搜到并安装 |
| **GitHub 仓库（推荐）** | push 到 GitHub 后：`hermes skills tap add <user>/<repo>` | 也可直接 `hermes skills install https://raw.githubusercontent.com/<user>/<repo>/main/skill/SKILL.md` |
| 纯脚本用法 | 无需 Agent：`python3 skill/scripts/pipeline_loader.py …` 即可 | 装配器与运行器不依赖任何框架 |

## License

代码 MIT；`skill/prompts`、`skill/references` 文档 CC BY 4.0。
