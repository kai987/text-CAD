# R04 storage attic / 小屋裏収納 / 储物阁楼

> Historical R04 record. R06 supersedes the current geometry and editable attic DXF with a1350 mm maximum finished ceiling and24 mm subfloor panel; see `docs/attic_R06.md`. The R04 PDF is preserved for revision comparison. The generator now outputs the R06 PDF rather than reproducing this sheet. 历史R04记录；当前模型以R06为准。R04の履歴です。現行モデルはR06を参照してください。

All dimensions below are millimetre-based demonstration assumptions. The user selected storage use. This supplements the approved two-storey plan and keeps the R03 gable envelope.

| Item / 項目 / 项目 | Value |
| --- | --- |
| Building body / 建物本体 / 房屋主体 | 7280 × 7280; two 2800 storeys |
| Deck / 板面 | X1800–5480, Y200–7080, Z5600–5618 |
| Deck net rectangle / 板面内法 / 板面净范围 | 3680 × 6880 |
| Hatch clear opening / 検修口内法 / 检修口净开口 | X2800–4000, Y3505–4155; 1200 × 650 |
| Deck projection less hatch / 開口控除後投影 / 扣开口投影 | 24.5384 m²; not statutory area |
| Lining display allowance / 内張り表示余裕 / 内衬展示预留 | 50 vertically |
| Ridge / 棟下 / 屋脊 clear height | 2033.55 above deck |
| Deck-edge / 板面両端 / 板面两侧 clear height | 971.23 above deck |
| Deployed ladder / 展開梯子 / 展开检修梯 | Width600, 65°, rise2818, ten treads / eleven rises |
| Ladder foot / 梯子下端 / 梯脚 | X2685.945, Y3830, Z2800 |
| Ladder top / 梯子上端 / 梯顶 | X4000, Y3830, Z5618 |
| Upper landing / 上口立ち位置 / 上口站位 | X4000–4600, Y3505–4155; minimum geometric clear height 1479.30 |
| Shelf / 棚 / 收纳架 | Two original open shelves, 650 high |
| Boxes / 箱 / 储物箱 | Two original boxes, 450 high |
| Opening guardrail / 開口手すり / 入口护栏 | Three sides, east entry open, 750 high |

## Coordinates and editing

Source X is east, Y north, Z upward. `src/lib/attic_geometry.py` owns the immutable `AtticParameters`, shared derived coordinates and proposal manifest. `src/lib/house_geometry.py` incorporates it into the existing assembly. STEP uses millimetres; the GLB adapter converts to metres, Y up, retaining labels and hierarchy.

The existing `roof:attic_ceiling_slab` leaf moves to `attic:floor_slab` and receives a real hatch cut. It remains the 200 mm concept ceiling/slab, not an engineered load-bearing floor. `attic:deck_finish` has the same through-hole. Real child groups are `attic:floor_slab`, `attic:partition_walls`, `attic:storage_fixtures`, `attic:guardrails`. `attic_access` contains the separately named deployed hatch lid, trim, mounts, stringers and treads. The viewer can hide the access assembly independently; individual naming does not imply individual checkboxes or animated mechanical folding.

## Access relationship and scope

The hatch is over the second-floor hall. The deployed ladder and its 600 mm bottom standing area fit inside the hall boundary and do not intersect the existing main stairwell. It occupies the hall while deployed; simultaneous routine passage is not claimed. Storage is low towards both roof slopes. Only the narrow central band has at least 1800 mm geometric clear height.

The model includes display lining and original storage placeholders. It does not establish structural support, ceiling/slab load capacity, connections, a selected ladder product, real use headroom, insulation, ventilation, fire/escape provisions, statutory attic classification or permit area. Dimensions and use must be redesigned for any actual building.

## Supplemental drawing

`src/generate_attic_plan.py` uses the same shared attic parameters to generate `DXF/house_attic_plan.dxf` and `output/pdf/house_attic_plan_R04_JP.pdf`. The supplemental A3, 1:50 sheet includes Japanese room, hatch and storage labels, editable native DXF dimensions and an east-west clearance section. Model-space units remain 1:1 millimetres; the DXF A3 viewport is locked to 1:50. Visible entities inherit ACI7 colours, with black PDF lines/text. This reuses the project's drafting conventions; it does not assert complete regulatory drawing conformity. Approved R02 house floor drawings and all apartment assets are preserved.
