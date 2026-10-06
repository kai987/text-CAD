# R06 low storage attic / 低天井の小屋裏収納 / 低净高储物阁楼

**Demonstration only. Every dimension is an assumed parameter; the building location, structural verification and statutory floor/storey classification remain pending.** The user selected storage use, not a bedroom or study. The approved one- and two-storey plans, 7280 × 7280 outline, two 2800 storeys and R03 gable exterior are preserved.

**演示方案。全部尺寸均为假设参数，所在地、结构验算、法规面积和楼层认定待核定。** 用户选择的是储物用途，不能通过该模型认定可住人、免计面积或符合施工要求。一、二层平面、7280 × 7280外轮廓、两层2800层高和R03切妻屋顶外形保持原方案。

**デモ計画です。全寸法は仮定値で、所在地・構造検証・法定面積と階数の取扱いは未確定です。** 用途は収納であり、居室ではありません。確認済みの1・2階平面、7280 × 7280の外形、階高2800の2層及びR03切妻屋根外形を維持しています。

| Item / 項目 / 项目 | R06 demonstration value, mm unless stated |
| --- | --- |
| Subfloor panel / 床下地板 / 楼面基层板 | 24 thick; Z5576-5600; through-hatch |
| Finish / 仕上板 / 饰面板 | 18 thick; X1800-5480, Y200-7080, Z5600-5618 |
| Finished deck / 板面内法 / 板面净范围 | 3680 × 6880 |
| Hatch / 検修口 / 检修口 | 1200 × 650; X2800-4000, Y3505-4155 |
| Projection less hatch / 開口控除後投影 / 扣开口几何投影 | 24.5384 m²; geometric only, not statutory area |
| Maximum finished clearance / 最大内法高さ / 最大完成净高 | 1350 above Z5618 deck |
| Flat ceiling / 平天井 / 平顶 | Z6968-7018; thickness50; X2456.048-4823.952 |
| Side clearance / 板面両端内法 / 两侧板面边缘净高 | 971.23 |
| Sloped lining allowance / 斜内張り表示余裕 / 斜内衬展示预留 | 50 vertically; not a selected insulation system |
| Deployed access / 展開検修梯子 / 展开检修梯 | Width600,65°,rise2818;10 treads,11 rises |
| Ladder foot / 梯子下端 / 梯脚 | X2685.945,Y3830,Z2800 |
| Ladder top / 梯子上端 / 梯顶 | X4000,Y3830,Z5618 |
| Upper access area / 上口立ち位置 / 上口站位 | X4000-4600,Y3505-4155; minimum finished clearance1350 |
| Cover and bracket / 蓋と下掛け金具 / 盖板与下挂支架 | Concept hingeZ5465.775;110.225 below panel underside;20 minimum vertical gap to treads/stringers |

## Finished space and parametric source

R04 reached about2034 at the ridge. R06 adds a real named solid `attic:lining:flat_ceiling` and shortens `attic:lining:west_slope` / `attic:lining:east_slope` to meet it. The inner gable linings meet this same finished profile. The resulting maximum1350 is a modelling target with margin below the common1400 reference; it is not a local-authority compliance conclusion. The roof void above the flat ceiling is inaccessible model space and is excluded from the represented usable storage space. A real building still needs ceiling suspension, roof/insulation layers, ventilation, fire and maintenance design.

R06新增实体平顶并缩短两侧斜内衬，山墙内衬采用同一完成剖面，真实几何净高上限为1350。它不是网页剖切效果，也不是法规认定。平顶上方剩余屋顶空间不表示可用储物区域。实际吊顶支承、保温通风、防火及维护仍待设计。

固定平顶是控制展示净高的候选做法。所在地对固定天花、上方残余空腔、检修可达性和面积/楼层计量的接受条件尚未确认，不能认定增设天花即可免计面积或楼层。 A fixed false ceiling is a candidate treatment requiring local acceptance of the ceiling and remaining roof void; adding it does not establish an exemption. 固定天井と上部の残余空間の扱いは所在地で確認が必要で、天井の追加だけで床面積・階数の不算入を判断できません。

R06は実体の平天井と両側の斜天井を接続し、妻側内張りも同じ内法断面で終了します。最大1350は表示上のクリップではなく実体寸法です。平天井上の屋根裏空間は使用可能な収納として扱いません。天井支持、断熱・換気、防火、点検の実施設計が必要です。

`src/lib/attic_geometry.py` owns the immutable `AtticParameters`, derived coordinates, finished-clearance function and manifest. `maximum_finished_clear_height` controls the cap; `subfloor_thickness` and `deck_thickness` control the floor layers. The flat-ceiling thickness must fit within the lining allowance, and the cap must intersect both slopes inside the finished deck. STEP is in millimetres; GLB is in metres and Y-up.

The stable leaf name `roof:attic_ceiling_slab` remains under `attic:floor_slab`, but now represents the **24 mm subfloor panel**, not the old200 mm solid slab. The finish shares the real through-hole. Separate demonstration beams/joists in the house structure group show a proposed load path; panel thickness, member dimensions and lack of intersections do not establish floor capacity.

## Access and regulatory scope

The hatch, ladder plan location and downstairs standing area remain in the second-floor hall. The lower finished ceiling reduces the upper access clearance to1350, so the model depicts low storage/inspection access, not upright normal circulation. The deployed ladder occupies the hall; it does not claim simultaneous passage. The frame, cover and drop brackets are demonstration geometry and do not prove a working folding mechanism, product suitability or safe operation. A selected ladder and its installation, handholds, opening protection and use clearances require separate review.

检修口和梯脚平面位置不变，上口净高降至1350，仅表达低净高储物检修关系。梯子展开时占用二层廊下。示意下挂支架使盖板避开梯梁；它不是可施工的机械方案。实际产品、安装、握持、防坠和使用净空需要另行确认。

検修口・梯子下端の平面位置は維持し、上口内法は1350になりました。低い収納への点検アクセスであり、直立通行を想定しません。展開中は2階廊下を占有します。蓋と下掛け金具は概念モデルで、実製品・取付・手掛かり・転落防止・使用時の安全空間は別途確認が必要です。

Neither the24.5384 m² geometric projection nor a reduced height determines legal exemption. No site has been selected. The authority's area measurement, total related storage areas, access, openings, equipment and actual intended use must be checked before the attic is classified. Storage loads still apply to structural design even if a future authority excludes it from statutory floor area.

## Supplemental editable drawing

`src/generate_attic_plan.py` generates current `DXF/house_attic_plan.dxf` and `output/pdf/house_attic_plan_R06_JP.pdf` from shared parameters. The A3,1:50 Japanese sheet includes the deck, shelves, boxes, hatch dimensions, deployed access footprint, physical flat-ceiling transition lines and an east-west section at Y2000. Its native DXF dimensions and labels are editable; model-space units are1:1 millimetres and the A3 viewport is locked to1:50. ACI7 visible DXF entities and black PDF text preserve legibility. This is a supplemental demonstration drawing, not a complete permit or structural construction set.

The R04 PDF remains historical at `output/pdf/house_attic_plan_R04_JP.pdf`. R02 one- and two-storey drawings and apartment assets are unchanged.
