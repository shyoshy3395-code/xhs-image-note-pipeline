# 16 · 动作库英文映射表（Y–AG 英文输出的官方词典）

> 用途：`pipeline_loader.py` 渲染 `[Set N]` 英文块时，按 **动作编号** 查本表；未收录的条目会在单元格里打出
> `（⚠️ 未收录英文映射，请在 action-en-map（本仓库未收录） 补）` 提示。
> 格式（三列，管道符分隔，勿改列序）：`| 编号 | English action name | English action description |`
> 新增动作（`--append`）后，把英文名与英文描述追加到本表，即可让 Y–AG 自动输出英文。

| 编号 | English name | English action description |
|---|---|---|
| S01 | Standing with arms relaxed | Standing naturally, weight slightly to one side, arms hanging relaxed at the sides |
| S02 | One hand in pocket | One hand resting naturally in a pocket, the other arm hanging down |
| S03 | Weight-shift single-leg stance | Weight on the leg nearest the camera, the other knee soft, shoulders relaxed and level |
| S04 | Shoulder resting against the wall | Shoulders and upper back resting lightly against the wall, hands loosely together in front, feet shoulder-width apart |
| S09 | Palm resting on lower back | One hand resting naturally at the lower back, elbow slightly bent |
| S10 | Looking up, back to camera | Back to the camera, chin slightly raised as if looking up, both arms hanging naturally |
| S11 | Looking back off-camera | Body facing forward, head turned toward a point off-camera, shoulders not following the turn |
| S13 | Head tilted, listening | Head tilted slightly as if listening to someone off-camera, relaxed eyes |
| S17 | Standing still, back to camera | Standing with the back to the camera, arms hanging naturally, back relaxed, feet shoulder-width apart |
| C01 | Crouching to tie a shoelace | Crouching on one leg, head down, fingers pinching a shoelace |
| C04 | Leaning to look at a low shelf | Leaning slightly to look at items on a low shelf, arms hanging naturally |
| D01 | Close-up of hands and wrist details | Close-up detail of the hands and wrist accessories, five fingers on each hand with correct joint direction |
| G03 | Glancing at the camera | Head turned slightly off-frame, eyes sliding back to the camera |
| G05 | Looking down at the ground | Looking down at the ground underfoot, lashes lowered |
| G08 | Looking off-camera, pensive | Gaze resting on a point off-camera, expression open and unguarded |
| G10 | Holding back a smile | Lips pressed as if holding back a smile, gaze drifting to one side |
| H01 | Adjusting the bag strap | One hand pinching the bag strap to adjust its length, shoulder lifted slightly |
| H04 | Tucking hair behind the ear | Fingers guiding a strand of hair back behind the ear |
| H08 | Straightening the cuffs | Fingers pushing a cuff up slightly, revealing the wrist |
| H10 | Fastening a button | Head down fastening or unfastening one button at the front placket, fingertips at the button |
| H16 | Hand resting at the hip pocket | One hand resting naturally at the edge of a hip pocket, not inserted |
| M01 | Wind lifting the hem | A gust of wind lifting one corner of the hem while the person stays standing in place |
| M02 | Hair blown by the wind | A strand of hair blown across part of the face by the wind |
| M03 | Turning, skirt flaring | Mid-turn with the skirt flaring outward, feet not yet settled |
| M06 | Gesturing while talking | Gesturing briefly with one hand while talking to someone off-camera |
| M08 | Just stopped moving | Just come to a stop, the body still carrying a slight sway of momentum |
| P08 | Flipping through a book | Standing in the shop flipping through a picture book, fingers holding the page seam |
| P09 | Reading a menu or tag | Head down reading a small card in one hand, the other hand supporting it |
| P11 | Pulling the door handle, turning back | Hand on the door handle, body already turned, gaze coming back toward the camera |
| T03 | Seated, legs crossed, looking away | Legs crossed naturally, hands clasped on the lap, gaze toward something off-camera |
| T08 | Elbow on knee, chin propped | Elbow resting on the knee, palm loosely propping the chin, looking off-camera |
| W03 | Walking in profile, tracking shot | Mid-stride in profile, front leg bearing weight, rear heel just lifting, hem and trouser cuff carrying slight motion folds |
| W05 | Walking away, back to camera | Walking away from the camera along the street, growing smaller, the back view filling about one third of the frame |
| W09 | Moving along a handrail in profile | Moving forward in profile along a handrail, palm resting on the rail |
| X01 | Standing, hands clasped behind | Mid-moment of standing with hands clasped behind the back and feet together, weight centred facing forward |
| X02 | Seated side-on, hands in lap | Mid-moment of sitting side-on with hands layered in the lap, looking off-camera |
| X04 | Sitting back on a bench, looking back | Mid-moment of sitting back on a bench with both legs turned to one side, right hand on the seat, head turning to the camera |
| X06 | Carrying a bag, stepping down | Mid-moment of stepping down while carrying a bag, weight shifted forward |
| X13 | Back to the wall, hand in pocket | Mid-moment of standing back against the wall, left hand in a pocket, right hand carrying a bag |
| X15 | Single-leg weight, rear leg lifted | Mid-moment of balancing on one leg with the other knee bent and lifted, fingers touching the lips |
| X23 | Stepping sideways, bag in near hand | Three-quarter length, mid-moment of stepping sideways with front knee bent, bag in the near hand, glancing at the camera |
| C06 | Crouching to pet a small animal | Crouching low to meet a small animal at eye level, hands resting on the knees |
| C07 | Bending to straighten a trouser hem | Bending to smooth a trouser cuff, fingertips pinching the hem edge |
| G06 | Looking up at leaves and sky | Chin slightly raised looking up at leaves and daylight, neck line lengthened |
| H05 | Sweeping hair behind the ear | Palm sweeping one side of the hair behind the ear, revealing the ear and earrings |
| H07 | Checking a wristwatch | Head down checking the time on the wrist, the other hand steadying the band |
| H13 | Searching a pocket | One hand searching inside a pocket, the other steadying the pocket edge |
| H15 | Turning a ring | Thumb turning a ring on the other hand |
| P03 | Taking a sip | Head down taking a sip, cup rim at the lips, eyes looking elsewhere |
| P05 | Looking down at a phone | Head down looking at a phone in hand, thumb resting on the screen, shoulders relaxed |
| P12 | Scanning to pay | One hand raising a phone toward a counter to scan, gaze following the phone |
| T04 | Sitting on a low wall, one leg hanging | Sitting on a low wall, one leg hanging down, the other foot resting on the wall edge |
| T06 | Sitting by the window, hand on a cup | Sitting by the window, one hand resting lightly on a cup, gaze out of the window |

## 维护与排障（英文列交付前必读）

### 1. 覆盖度扫描（新批次开跑前做一次）

英文列一旦缺映射，单元格里会直接印出中文 + 「⚠️ 未收录英文映射」→ 闸门 `--check-en` 必报 FAIL。
**做法：把「所有空间画像 × 所有行」都跑一遍，取被抽中编号的**并集**，一次性补全**（只补当批用到的不够用，下一批换空间又缺）：

```bash
# 收集并集（把 8 个空间 × 各行的 pkg 抽出，取 actions[].no）
python3 scripts/pipeline_loader.py --row 2 --groups 9 --quota relaxed --space 街角 --env x --out /tmp/probe.json
# → 读 probe.json actions[].no，与 load_action_en_map() 求差集，差集逐条补英文
```

2026-09-20 实测：并集 **35 条** ＋ 常用安全动作 = **53 条**（本表现有数量）即可覆盖八空间全部抽条结果。

### 2. 接触字段的中文括注（最常漏的一处）

动作库的「接触」列写法很自由：`自身接触（双手在身后相握）`、`自身+鞋接触`、`道具(包)`、`自身＋环境接触（坐于椅面）`。
`pipeline_loader._en_contact()` 的规则：

- 先判**大前提**（自身 / 环境 / 道具 / 自身＋环境）→ 出 `Self-contact` / `Contact with the environment` / `Contact with the prop` 等纯英文基句；
- 再用 **`CONTACT_KEYS` 关键词表**把括注翻成英文对象（手→`hands`、鞋靴→`footwear`、包袋→`bag`、椅凳坐→`seat`、墙→`wall`、扶手→`handrail`、杯→`cup`、桌台→`table`、镜→`mirror`、门→`door`、货架→`shelf`、手机→`phone`…）；
- **兜底直接丢掉中文**，绝不残留。

⚠️ 新增动作若带了库里没有的环境物（例：`桌面`、`栏杆`、`纸袋`），要在 `CONTACT_KEYS` 里补关键词，
否则该格会回落成基句（不含中文，闸门不报错但语义变粗）。**改完立刻用闸门 `--check-en` 扫一遍**：

```bash
python3 scripts/verify_image_note_xlsx.py --src <模板> --out <交付> --rows 2 3 4 5 6 \
    --cols FGHIJKLMN --ref-col Q --check-en --no-blur
```

### 3. 单元格英文块 vs 生成用提示词（别搞混）

- `render_prompt(pkg, slot)` → **写 Y–AG 单元格**的英文 `[Set N]` 块；
- `render_prompt_for_gen(pkg, slot)` → **送模型**的提示词（中文锁块【人脸/服装/解剖/禁虚化】＋ 英文环境与动作槽位 ＋ `EN_CONSTRAINT`）。
- `run_image_note.py` 走后者。**改渲染器时两条链路一起改**，只改一条会出现「单元格好看但出图丢锁」。
| S18 | Front three-quarter, hand at the waist | One hand resting lightly at the waist, the other arm hanging naturally, steady weight, shoulders relaxed |
| G11 | Front three-quarter, chin lifted to the light | Chin lifted slightly as if looking at the light above the frame, neck line lengthened, gaze passing just over the camera |
| G04 | Looking past the camera into the distance | Gaze passing over the camera toward a distant point, as if watching people on the street |
| E05 | Framed by a doorway | Using a doorway or stair opening as a natural frame, the person standing inside that frame |
| H12 | Smoothing the hem | Both hands smoothing the hem downward |