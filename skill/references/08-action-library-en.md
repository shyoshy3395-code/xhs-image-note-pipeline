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
| D02 | Close-up of cuff and wrist | Close-up of the cuff and wrist junction, fabric folds reading naturally |
| D03 | Close-up of neckline and collar | Close-up of the neckline, collar and collarbone line, the placket sitting straight |
| D04 | Close-up of the waistline seam | Close-up of the waistline seam and where the hem starts, the hem closed with no slit |
| D05 | Close-up of shoes and ground contact | Close-up of the shoes meeting the ground, heel height matching the hero shot |
| D06 | Close-up of bag strap on the shoulder | Close-up of the bag strap resting on the shoulder, only a corner of the bag in frame |
| D07 | Close-up of hand-to-prop contact | Close-up of the fingers gripping a cup or bag handle at the contact point |
| D08 | Close-up of fabric in raking light | Close-up of the fabric texture in raking side light, weave clear with no clumped noise |
| H02 | Switching the bag to the other hand | Moving the bag from one hand to the other while standing |
| H03 | Fingertips touching an earring | Fingertips lightly touching an earring, head tilted a little |
| H14 | Straightening a necklace pendant | Straightening the pendant of a necklace with two fingers |
| C03 | Bending down to pick something up | Bending forward to pick an object off the ground, one hand already extended |
| P14 | Turning away with a shoulder bag | Turning away with a shoulder bag swinging slightly at the side |
| P04 | Looking at a watch | Glancing down at a watch on the wrist |
| H17 | Fingertips pressing the end of a tie | Fingertips pressing the lower end of a tie, head slightly down |
| G07 | Eyes closed, feeling the air | Eyes gently closed as if feeling a light breeze, expression relaxed |
| T05 | Sitting at a windowsill, facing out | Sitting at a windowsill facing outward, one hand resting on the ledge |
| G01 | Looking up at the sky | Chin lifted, looking up at the sky, shoulders relaxed |
| E01 | Empty room with light on the wall | An empty moment: light falling on the wall, no person in frame |
| H09 | Pulling the front of a jacket straight | Both hands pulling the front panels outward and releasing, the fabric settling back |
| C02 | Crouching to greet a small animal | Crouching low with one hand extended toward a small animal at foot level, weight settled back |
| C05 | Kneeling to look through a bag | Kneeling on one knee, head down looking through the items in a bag on the ground |
| E02 | Ground shadow composition | Framed around the shadow and light pattern on the ground, the figure only partly in frame from the waist down |
| E03 | Reflection in shop glass | Shot through the reflection in a shop window, the figure's faint reflection layered over the interior |
| E04 | Depth down a street corner | The figure standing at the far end of a street corner, a corridor-like receding composition |
| G02 | Calm direct look at the camera | Looking straight into the camera, calm expression, lips lightly closed, no forced expression |
| G09 | The moment of laughing out loud | Just burst out laughing, eyes curving, shoulders moving slightly |
| H06 | Bringing hair over one shoulder | Head down bringing the ends of the hair from behind over one shoulder |
| H11 | Pulling up a zip | One hand pulling a zip upward, the other steadying the hem |
| M04 | The instant a foot leaves the ground | Mid-moment as the foot leaves the ground and the weight shifts |
| M05 | Hand halfway raised | The hand caught halfway up, the movement not yet finished |
| M07 | Walking briskly with slight motion blur | Walking quickly so the figure's edges carry slight motion blur while the surroundings stay still |
| P01 | Both hands around a takeaway cup | Both hands holding a takeaway cup, gaze off-camera |
| P02 | Cup held close to the chest | One hand holding a cup with the elbow tucked in against the chest |
| P06 | Taking a photo of the street | One hand raising a phone toward the street, the screen away from the camera, body leaning slightly forward |
| P07 | On a call, head turned | Phone at the ear on a call, head turned slightly, the other arm hanging naturally |
| P10 | Pushing a door open | One hand pushing a glass door open, the body mid-step over the threshold |
| P13 | Taking off sunglasses | One hand caught mid-motion taking sunglasses off the face |
| S05 | Leaning on a railing, looking out | Elbow resting on a railing, body in profile, looking into the distance |
| S06 | Leaning on a pillar, legs crossed | Standing with the back against a pillar, legs crossed naturally, hands clasped in front |
| S07 | Arms folded, in profile | Arms folded naturally, body in profile looking off-camera, shoulders relaxed and not hunched |
| S08 | Both hands in pockets, chin tucked | Both hands in pockets, chin tucked slightly, steady gaze |
| S12 | Leaning toward a shop window | Leaning slightly toward the glass to look inside, weight forward, feet not moving |
| S14 | Smoothing the front placket | Head down smoothing the front placket with the fingertips pinching the fabric |
| S15 | One hand at a hat brim | One hand lifting lightly to a hat brim, head slightly down |
| S16 | Hand raised against the light | Palm held loosely in front of the forehead, eyes narrowed looking into the distance |
| T01 | Sitting on a step, hands on knees | Sitting on a step with both hands on the knees, upper body leaning slightly forward |
| T02 | Sitting side-on on a bench | Sitting on a bench turned side-on toward something off-camera, one leg drawn up in front |
| T07 | Cross-legged, adjusting footwear | Sitting cross-legged on the ground, head down adjusting the opening of a shoe |
| W01 | Walking straight toward the camera | Walking naturally straight toward the camera, weight forward, arms swinging, gaze passing over the lens into the distance |
| W02 | The pause after a step | Just planted the front foot with the back foot about to follow, the body still carrying a slight forward lean |
| W04 | Two steps then turning back | Two steps in, turning back to change direction, the body twisting while the feet keep moving |
| W06 | Over-the-shoulder tracking | Camera behind and slightly to the right of the subject, shoulder line and street depth visible, the back of the head and right shoulder in frame |
| W07 | Stepping up onto a step | One foot stepping up onto a step with the other behind, arms hanging naturally |
| W08 | Stepping down, watching the ground | Mid-step down, head down watching the feet, one hand slightly raised for balance |
| W10 | Crossing the road, mid-way | Walking in the middle of a zebra crossing, the figure small in frame with the environment dominating |
| W11 | Waiting at a traffic light | Standing at the edge of a junction waiting for the light, feet apart, gaze toward the traffic ahead |
| W12 | Walking briskly with a bag | Carrying a bag in one hand, slightly longer stride, a hint of hurry |

## X 族 · 真实爆款反推动作（2026-09-21 补齐）

| 编号 | English name | English action description |
|---|---|---|
| X03 | Side-seated on a bench, arm on table holding a cup | Seated sideways on a bench with legs crossed, right arm resting on a table holding a cup, other hand in pocket, looking off-frame |
| X05 | Seated leaning back, reaching out holding a cup | Seated leaning back with legs crossed and extended, one arm reaching out holding a cup, head lowered |
| X07 | Feet crossed standing, phone raised | Standing with feet crossed, one hand raising a phone and the other carrying a bag, gaze not visible |
| X08 | Seated on a step, chin rested on hand holding a cup | Seated sideways on a step with legs crossed, chin propped on one hand, the other holding a cup, looking off-frame |
| X09 | Seated on a chair, leaning forward head propped | Seated on a chair with knees together, leaning forward and to the left, one hand propping the head, the other arm resting on the knee |
| X10 | Striding forward with a bag swinging back | Right leg striding forward, left leg pushing off, a bag in the left hand swinging back |
| X11 | Seated on a step, knee raised, both hands on a bag | Seated sideways on a step with one knee raised, both hands resting on a bag |
| X12 | Seated on a step, elbow propped, hand on waist | Seated on a step with one knee propping an elbow, the other hand on the waist, ankles crossed |
| X14 | Seated on a stool, legs crossed, leaning forward with a phone | Seated on a stool with legs crossed, leaning forward, one hand on the knee holding a phone and the other holding a bag |
| X16 | Phone selfie with hand in pocket, feet together | Taking a selfie with one hand raising a phone, the other in pocket, feet together, gaze not visible |
| X17 | Knees drawn to the side, hand on knee, leaning back | Knees drawn to one side, one hand resting on the knee, upper body leaning back, head lowered |
| X18 | Holding a cup out with crossed feet | One arm holding a cup out to the side, feet crossed, head lowered |
| X19 | Reclining on a sofa, knees up, head propped, cup in hand | Reclining with knees raised, one hand propping the back of the head and the other holding a cup, looking at the camera |
| X20 | Both hands on the waist, feet crossed, leaning | Both hands resting on the waist, legs crossed, leaning against a surface, looking off-frame |
| X21 | Seated at an angle, arm on the armrest, object raised | Seated at an angle on a chair, left arm on the armrest, right hand raising a small object, ankles crossed, chin lifted |
| X22 | Mid-step pause, weight on the back leg | Pausing mid-step, front leg extended with weight settled on the back leg, glancing sideways at the camera |
| X24 | Seated on a chair, weight leaning, propping the chair with a bag | Weight shifted to the left propping the chair, a bag in hand, both legs extended to the right and crossed, looking at the camera |
| X25 | Seated on a step, cup raised, hand on waist | Seated on a step, left hand raising a cup and right hand on the waist, looking at the camera |
| X26 | Seated on a surface, both hands around a cup, one knee up | Seated with weight on the hips, legs crossed and one knee raised, both hands around a cup, looking off-frame |
| X27 | Feet offset, carrying a bag, head lowered | Feet offset with weight on the right leg, left arm bent at the elbow carrying a bag, head lowered |
| X28 | Standing with both hands propped back on a low wall | Standing with the torso facing the camera and leaning slightly back, both hands propped on the edge of a low wall behind, ankles lightly crossed |
| X29 | Stepping forward on the street | Mid-step on the street with the upper body tilted slightly to one side, one leg bearing weight, head tilted toward the shoulder, gaze at the camera |
| X30 | One arm raised with the hand on top of the head | Standing with one arm raised and bent so the hand rests on top of the head, the other arm hanging with an object, feet slightly offset, gaze at the camera |
| X31 | Seated low with knees drawn up, one hand reaching down | Seated at ground level leaning forward, one knee drawn toward the chest and the other leg folded underneath, one hand reaching down near the ankle |
| X32 | Seated on a step with forearms crossed on the knees | Seated on the edge of a step with legs together and the lower legs on the step below, forearms crossed on the knees, head turned to one side |
| X33 | Standing with one hand behind the back | Standing with the torso angled to one side, one forearm resting in front of the waist and the other hand tucked behind the hip, legs close together |
| X34 | Seated by the window with one hand resting on a cup | Seated on a bench by the window with legs apart and knees bent outward, one forearm on the table edge with the hand on a cup, the other hand on a bag |
| X35 | Seated sideways on a ledge with a hand propping the cheek | Seated sideways on the edge of a basin counter, hips and lower back against the rim, one elbow on the thigh with the hand propping the cheek, the other hand holding a phone |
| X36 | Seated on a step holding a drink, one knee bent outward | Seated on a step with weight on one supporting leg and the other knee bent outward, forearms crossed in front of the waist, one hand holding a drink |