# R09 delivery checks / 納品確認 / 交付检查

2026-10-07. The user approved the R09 floor plans before 3D regeneration.

The 8190 × 7280 mm body, two 2800 mm storeys, three bedrooms and south drying balcony are demonstration inputs. The balcony is 3640 × 1500 mm outside and 4.816 m² inside its rail footprint. Statutory floor area is not established by these geometric areas.

## Saved CAD and drawing checks

- 147 floor-plan geometry and editable-file checks passed.
- 230 drawing/unit/revision checks passed. Floor drawings use A3 / 1:50, native DXF text and dimensions, and high-contrast text.
- 3188 house STEP/GLB checks passed: 879 named mesh occurrences and 896 native solids. Doors, window apertures, stairs, attic opening and named balcony parts are checked against source geometry.
- 1152 saved timber-frame checks and 4035 W/S/RC coordination checks passed. The timber/steel attic beam at the relocated hatch is cut and routed through named B12–B14 demonstration members. Geometry validity and face contact do not establish structural capacity.
- 825 site/foundation geometry checks passed, including the widened parcel and balcony footing exclusions in the ground layers.
- 53 Python/Rust parity and adversarial regression tests passed; all five dense GLB audits passed using the Rust backend.
- 134 frontend regression tests passed, including actual CAD section caps, cabinet sections, stair/hatch holes, TypeScript/WASM parity, language switching, visibility presets and apartment regressions. Build verification checks 54 published asset hashes.

Browser checks cover desktop and narrow layouts, 1F/2F vector plans, exterior and interior presets, attic, structural selection, day/night lighting, and Chinese/Japanese/English switching. No console errors or warnings were observed during local QA. Current raster fallbacks are regenerated from the approved PDF and actual viewer.

## Explicit pending coordination

All city/material cases retain null strength and approval results. Tokyo, Osaka, Kyoto and Nagoya selectors change reference conditions; they do not prove compliance for a real parcel. W/S/RC are conceptual alternatives, not three calculated construction designs.

The RC envelope extends 120 mm beyond the architectural body. One south RC column occupies 36000 mm² of the balcony footprint; this is reported as pending architectural coordination rather than a passing clearance conclusion. Balcony supports, waterproofing, drainage, guard connections, opening products, stair headroom, foundation bearing and structural connections require further design and engineering.

The attic hatch starts at X=4100 mm. Minimum headroom at the upper standing area is about 1254 mm; maximum storage headroom is 1350 mm. These are geometric demonstration values, not safe ladder-operation or floor-area-exemption certification.

Existing supplemental download filenames contain R05/R06/R07 for route compatibility; their current drawing/geometry content identifies R09. Historical R01/R02/R04 drawings remain historical. The apartment's saved CAD files are unchanged.

中文：新版平面已确认，具名三维和可编辑图纸已更新。以上检查仅验证几何、文件和软件行为；RC阳台占位、承载、地盘与法規核定仍待完成。

日本語：R09間取りは承認済み。具名3Dと編集可能図面を更新しました。確認対象は幾何・保存ファイル・ソフトウェア動作です。RC柱のバルコニー占有、荷重・地盤・法規認定は未完了です。
