# R09 已确认户型 / 承認済み間取り / Approved layout

2026-10-07。当前状态：**平面已确认，三维与结构展示文件已更新**。以下草案章节保留设计与确认过程；当前实施状态见最后一节。历史 R02 图纸保留，公寓户型未改变。

用户允许调整主体尺寸，保留三卧室，二层阳台以晾衣为主。草案选择 **8190 × 7280 mm** 外轮廓（原为 7280 × 7280，向东增加 910），层高仍为 **2800 mm**。所有尺寸、南向、入口、阳台位置和材料厚度均为演示假设。

## 调整逻辑

- 一层厕所从东侧玄关中段移到东北侧、楼梯旁；二层在相同位置。厕所净边界仍为 **900 × 1700 mm / 1.53㎡**，不通过进一步压缩厕位来节省面积。
- 原厕所周围的长隔墙和一层走廊取消，玄关通过一道门直接进入开放 LDK。厕所保留独立短前厅和向前厅打开的门，厕门不直接面对玄关门。楼梯采用客厅楼梯，需确认用户对空调分区和声音传播的偏好。
- 浴室预留改为 1820 × 1820 mm，系统浴室实际型号、内法及安装尺寸未选定；洗面脱衣兼洗衣空间为 2910 × 1820 mm，包含洗面、洗衣机和布草柜，图示留有活动空间。
- 二层为三间卧室、主卧前开式衣柜、每间房的柜体、厕所和公共通道。主卧净房间 9.61㎡，另有 2.79㎡收纳；另两间卧室为 11.25 / 13.14㎡，均含图示柜体占地。不把 900 mm 深衣柜称作步入式 WIC。
- 南侧阳台外形 **3640 × 1500 mm / 5.46㎡**，扣除三侧 100 mm 栏杆占位后净几何面积 **4.816㎡**。从 900 mm 宽公共通道和 800 mm 门洞进入，不需要经过卧室。晾衣杆位于门扇展开区域之外。
- 楼梯上下层预留一致：900 mm 双跑、中间 100 mm 占位、900 mm 平台、16 个踢面 × 175 mm、踏面 260 mm。踏步、平台、楼板开口和门厅关系已做平面检查；梁下净高、扶手及楼梯构造未设计。

## 几何对比

| 项目 | 旧方案 | R09 草案 |
|---|---:|---:|
| 单层外轮廓矩形面积 | 52.9984㎡ | 59.6232㎡ |
| 一层 LDK（含家具） | 20.172㎡ | 33.05㎡ |
| 一层独立走廊/厕所前厅（不含玄关、楼梯） | 3.61㎡ | 0.828㎡ |
| 每层厕所 | 1.53㎡ | 1.53㎡ |
| 二层阳台外形 | 无 | 5.46㎡ |

主体面积增加，且新版 LDK 包含开放通行区域，因此走廊减少不能被解读为在同面积下全部转化为可用房间。二层公共通道含晾衣通道 7.047㎡，另有 0.828㎡厕所前厅；独立阳台通道以公共可达性换取一部分室内面积。外轮廓两层合计 119.2464㎡仅是矩形面积比较，二层有楼梯开口，不能视为法定延床面积。

## 原始参考与使用边界

1. [ヤマト住建 加古川店参考プラン PDF](https://www.yamatojk.co.jp/wordpress/wp-content/uploads/2023/01/kakogawa-1116.pdf)，第 2 页多种 27-35 坪户型：参考紧凑湿区、楼梯/厅、三卧室和南侧阳台的组织。草案没有复制任何整套户型。
2. [一条工務店 HUGme S34-4045-0002](https://www.ichijo.co.jp/lineup/hugme/madori/plandetail/?id=S34-4045-0002&type=2f)：公开南向两层 3LDK、客厅楼梯和收纳布局，主体尺寸示例 7280 × 8190 mm。本草案采用不同房间几何，主体长宽方向也不同。
3. [ミサワホーム九州 SMART STYLE Roomie](https://kyushu.misawa.co.jp/smart_style_roomie/)：参考家务动线、湿区和就近收纳的设计思路，不继承厂商节能、耐震或产品性能结论。

参考访问日期 2026-10-07。下载的参考 PDF 仅保留在忽略的临时目录；不随项目再发布厂商图片或图纸。

## 文件与复现

- `src/lib/house_redesign_plan.py`：参数、房间、门窗、家具占位、墙体及假设。
- `src/generate_redesign_plans.py`：原生可编辑 TEXT/DIMENSION，ACI7 高对比图层，A3 1:50 图纸。
- `DXF/house_redesign_R09_1f.dxf`、`DXF/house_redesign_R09_2f.dxf`。
- `output/pdf/house_floor_plans_R09_JP.pdf`：两页 A3；可在 PDF 查看器放大。
- `output/review/house_redesign_R09.json`、`validation_redesign_R09.json`：来源、假设、几何、检查结果和输出文件哈希。

```bash
.venv/bin/python src/generate_redesign_plans.py
.venv/bin/python checks/validate_redesign_plans.py
```

147 项几何/文件检查已通过：房间和家具边界、不重叠、门洞全宽连接、门扇与家具、滑门内墙收纳预留、所有空间可达、不穿卧室到达阳台、600 mm 宽示意通行带、上下层楼梯和厕所对齐、DXF 审计/单位/可编辑标注、图纸版本及比例。600 mm 仅为本次示意路径碰撞检测宽度，不是无障碍或法规合规结论。移门门袋、门框及折门实际五金尚未选型。检查保留了这些物理深化边界。

制图沿用项目已有的东京土木 CAD 共通项目准用方式，未宣称满足完整住宅施工图规范或 SXF 电子交付要求。

## 确认后需要完成的三维与工程工作

新版不能直接套用现有柱 C34、梁、候选承重墙、基础或十二套城市/结构叠加层。平面确认后重建具名墙、楼板、门窗、楼梯、家具、阳台、阁楼/屋顶及外构，并重新协调 W/S/RC 的荷载路径和地基。阳台承载、支持方式、栏杆高度/锚固、防水、坡度、排水、门槛、与下层开口关系须专项设计；地块退界、建蔽/容积、斜线、防火、采光通风等仍需真实场地和当地审查。现阶段不输出新版 STEP/GLB，以遵守先确认平面的流程。

## 日本語

R09は未承認の平面見直し案です。外形8190 × 7280 mm、階高2800 mmはデモ仮定。1階の長い廊下をLDKへ組み込み、900 × 1700 mmのトイレを階段横で上下階一致としました。2階は3個室・収納・共用物干し通路・南バルコニー（外形3640 × 1500 mm）。個室を通らず物干しができます。147項目の平面幾何・保存図面チェックは通過しましたが、構造・法規・敷地・製品納まりは未検証です。承認後に3Dと構造配置を更新し、現行公開モデルにはまだ反映しません。

## English

R09 is an unapproved layout review draft. The 8190 × 7280 mm outline, 2800 mm storey heights and south-facing 3640 × 1500 mm drying balcony are demonstration assumptions. The 900 × 1700 mm toilets move beside the stairs and align vertically. The first-floor long corridor becomes open LDK circulation. Three upstairs bedrooms remain, with a public balcony passage that bypasses bedrooms. All 147 geometry/artifact checks passed; engineering, code, site conditions and product installation remain unverified. Update named 3D parts and structural layouts only after plan approval; published assets remain the approved layout.

## R09 确认与三维更新（2026-10-07）

用户已确认。以上“待确认”和“确认后”章节保留草案阶段记录，以本节为当前状态：新版墙、楼板、门窗、楼梯、家具、晾衣阳台、阁楼、切妻屋顶、基础、院子和围栏已重建。阁楼检修口向西协调到X=4100，梯底与上端站位保持在公共走廊及板面内。电视柜向南微调100 mm以避开厨房操作带。阳台具名层包括楼板、饰面、透空栏杆、晾衣架、排水口及未计算的支柱/基础。W/S/RC文件和十二套城市条件记录以R09为建筑基础，所有承载结果及许可结论为空；RC外伸120 mm的结构边界仍需外立面/场地协调。

日本語：R09承認済み。具名3D・編集可能図面・小屋裏・外構・3構造表示を更新。検修口X=4100、テレビ台を南へ100 mm調整。寸法は仮定で、構造計算と法規確認は未実施です。

English: R09 is approved. Named 3D, editable drawings, attic, site and three structural overlays are updated. The hatch is coordinated at X=4100; the TV console moves south by100 mm to clear the kitchen approach. Dimensions remain assumptions; engineering and statutory review remain unverified.
