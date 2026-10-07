# R21 二层洗面与阁楼检修口 / 2階洗面・小屋裏点検口 / Upper-floor coordination

## 中文

二楼600×450 mm洗面台沿800 mm壁面居中，两端各留100 mm；世界坐标X2930–3380、Y4480–5080。洗面墙上增加独立命名壁灯，与室内灯光一键开关联动。

主卧D21和北卧室D23保留750 mm开口及推拉门参数；三维改为打开的壁挂门扇、上部轨道与拉手。开口保持净空，原房间面积不变。模型表达固定打开状态，不是已选产品或机械动画。

阁楼1200×650 mm检修口向西移535 mm，世界坐标X2355–3555、Y3505–4155；距阁楼储物板面西侧X2255留100 mm，饰框及护栏保持在板面内。储物阁楼西侧受斜屋顶限制，所以这里的“靠墙”是阁楼储物板面西侧墙边，不是整栋房屋西外墙。最高净高1350 mm及展开梯东侧入口保持。

基层板、饰面板及天花开口、边框候选梁、梯子、盖板、铰链和护栏共同移位。二楼走廊吊灯向西移500 mm至X1690、Y3800，避开检修梯和600 mm底端站位。新增壁灯后共16盏室内灯。

所有尺寸、空隙及照明为演示假设。展开梯仍占用走廊，实际安全使用、支承与接合、承重、照度、电气及法规未设计。STEP/GLB和DXF/PDF同步；承重准备报告绑定新的R21源数据重新生成。

## 日本語

2階の600×450 mm手洗いを800 mm壁面の中央に配置し、両端100 mmを確保。壁灯を追加し、室内灯スイッチと連動します。主寝室D21・北寝室D23の開口750 mmを保持し、3Dでは開いた壁付け引き戸・上部レール・引き手を表示。間取り面積は変わりません。

小屋裏点検口1200×650 mmを西へ535 mm移動。世界座標X2355–3555、Y3505–4155、収納床西端X2255から100 mm離します。西外壁直上は勾配屋根のため、収納床の西側壁際へ配置する意味です。床・天井開口、補強梁候補、はしご・蓋・ヒンジ・手すりを一括移動。2階ホール吊灯も西へ500 mm、X1690/Y3800に移し、はしごと下部立ち位置を避けます。室内灯は計16灯です。

全寸法・照明・空隙は仮定です。展開はしごはホールを占有し、安全操作・接合・構造耐力・電気・法規は未検証。STEP/GLB・DXF/PDFとR21分析の参照データを整合します。

## English

Centre the 600×450 mm F2 basin on its 800 mm niche wall, leaving 100 mm at each end. Add a named wall luminaire controlled by Indoor lights. Retain the 750 mm D21/D23 bedroom openings and sliding-door parameters; 3D now shows retracted face-mounted leaves, overhead tracks and pulls. Room areas are unchanged.

Shift the 1200×650 mm attic hatch 535 mm west to world X2355–3555/Y3505–4155, leaving 100 mm to the storage deck's west edge at X2255. The west exterior wall is below the low roof slope: this placement is beside the attic storage wall. Deck, ceiling openings, candidate trimmers, ladder, lid, hinges and guardrails move together. Move the F2 hall pendant 500 mm west to X1690/Y3800, clear of the ladder and its 600 mm lower standing zone. There are now 16 indoor fixtures.

All dimensions, clearances and lighting remain illustrative. The deployed ladder occupies the hall; safe operation, connections, capacity, electrical/photometric design and statutory compliance remain unresolved. STEP/GLB, DXF/PDF and the source-bound R21 review are coordinated.

## Validation / 検証 / 验证

2026-10-07: source-bound CAD release R21 (68 sources / 64 artifacts); 4028 saved 3D checks, 1128 structural geometry checks and 3951 W/S/RC geometry checks passed. CAD unit tests: 23 passed. Read-only engineering/area tool: 15 passed. The full web run passed 156/160 initially; four stale-position/naming/localization failures were corrected, then all 24 affected tests passed. Rust/WASM/TypeScript section parity passed without changes to the section algorithm.

Browser inspection at 1440×1000 and 390×844: second-floor/attic views, Chinese/Japanese/English switching, 7 visible F2 lights (including the vanity wall light), 2 attic lights, power off/on, vector plan and horizontal overflow checks passed; no browser warning/error messages were captured. Six updated house PDF pages were rendered and visually reviewed.

These checks establish artifact consistency and viewer behavior only. Structural capacity, safe ladder operation, chosen products, electrical design and statutory approval remain pending.
