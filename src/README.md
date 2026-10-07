# Model catalog / 模型源码 / モデルソース

[简体中文](../README.md) | [日本語](../README.ja.md) | [English](../README.en.md)

The current house revisions are recorded in [`design_manifest.json`](../output/review/design_manifest.json) (`drawing_revision`) and [`house_3d_assumptions_R01.json`](../output/review/house_3d_assumptions_R01.json) (`revision`). Apartment revisions are independent in [`apartment_2ldk_manifest.json`](../output/review/apartment_2ldk_manifest.json). R05/R06/R10 output filenames are compatibility paths, not the current revision. / 当前一户建版本以以上清单字段为准，公寓版本独立；R05/R06/R10文件名是兼容路径。 / 戸建ての現行改訂は上記メタデータで確認し、マンションは別改訂です。R05/R06/R10のファイル名は互換パスです。

R07 introduced twelve city/system reference cases and three independent W / lightweight S / RC structural overlays. The overlay metadata retains its own revision; all capacities and permit results remain unfilled. / R07引入四地×三体系条件方案，结构叠加层保留独立版本，全部承载和许可结论待核定。 / R07で4都市×3構造の条件付き案を導入。構造モデルには独立した改訂があり、耐力・認定は未確定です。

R06 introduced a demonstration structural layout with a storage-only attic, maximum finished clear height 1350 mm. Member sizes and foundations are uncalculated; site and statutory recognition remain pending.

R06为纯储物阁楼与结构布置演示，最高完成净高1350 mm。构件截面与基础未计算，所在地和法定用途认定待核定。

R06は収納専用小屋裏・構造配置のデモで、最高仕上げ内法高さは1350 mmです。部材断面と基礎は未計算で、所在地と法規上の認定は未確定です。

| Source | Output | Purpose |
| --- | --- | --- |
| `lib/house_redesign_plan.py`, `generate_redesign_plans.py` | `DXF/house_redesign_R10_1f.dxf`, `house_redesign_R10_2f.dxf`, `output/pdf/house_floor_plans_R10_JP.pdf` | Current 3-bedroom/drying-balcony source; run `checks/validate_redesign_plans.py` / 当前三卧户型 / 現行3寝室平面 |
| `generate_plans.py` | `DXF/001D0PL2-1FPLAN.DXF`, `DXF/002D0PL2-2FPLAN.DXF`, identical `house_1f_plan.dxf` / `house_2f_plan.dxf` aliases, `output/pdf/house_floor_plans_R10_JP.pdf` | Compatibility entry point forwards to the current generator; editable labels/dimensions and A3 layouts / 兼容入口转发当前生成器 / 互換入口から現行生成へ |
| `lib/house_plan.py` | shared data, no standalone output | Millimetre parameters, rooms, walls, openings and assumptions |
| `lib/jp_drafting.py` | shared style, no standalone output | Japanese drafting layer names, paper lineweights, nominal text sizes and drawing filenames |
| `lib/jp_sheet.py` | shared sheet, no standalone output | A3 frame, Tokyo-style title block, room areas and assumptions in DXF paper space and PDF |
| `house_3d.py` | `STEP/house_3d.step`, `GLB/house_3d.glb` | Current named assembly from the approved room layout / 当前具名模型 / 現行の部材名付きモデル |
| `lib/attic_geometry.py` | current attic model and metadata | Subfloor, hatch, flat ceiling, storage and deployed ladder / 当前阁楼参数 / 現行小屋裏パラメータ |
| `lib/structure_geometry.py` | named structural proposal | Columns, beams, sills, joists, headers, roof framing and candidate bearing walls / 结构布置 / 構造案 |
| `lib/engineering_inputs.py` | `output/review/engineering_inputs_R06.json` | Demonstration values and pending inputs / 演示与待定输入 / 仮定と未確定入力 |
| `generate_structure_plan.py` | `DXF/house_structural_scheme.dxf`, `output/pdf/house_structural_scheme_R06_JP.pdf` | Current editable timber layout supplement / 当前木造补充图 / 現行木造補足図 |
| `lib/structural_variants.py`, `generate_structural_variants.py` | `STEP/structure_W.step`, `structure_S.step`, `structure_RC.step` and corresponding GLB | Independent uncalculated material-system overlays / 三体系独立结构草案 / 3構造の独立デモ |
| `generate_structural_cases.py` | `output/review/cases/*_R07.json`, `structural_cases_R07.json` | 12 city/system cases with official references and pending project inputs / 四地条件方案 / 都市別条件付き案 |
| `lib/house_geometry.py` | shared geometry, no standalone output | Slabs, wall apertures, roof, doors/windows, storage and stairs |

Run `.venv/bin/python src/generate_plans.py` from the project root.

R02 adapts the common provisions of the Tokyo civil-engineering CAD drafting standard (April 2024) to this house concept. See `docs/tokyo_cad_standard_mapping_R02.md` for scope and section references. Run `checks/validate_plans.py` and `checks/validate_jp_drafting.py` after generation. The editable DXF sheet is in layout `JP_A3_1_50`; the browser viewer displays model space. SXF electronic delivery is outside this output.

The current room layout is user-approved; R01 data is historical. Run `.venv/bin/python src/house_3d.py` to regenerate the STEP and named GLB, then `.venv/bin/python checks/validate_3d.py` to check the saved artifacts. Source/STEP units are millimetres; GLB follows glTF metres/Y-up.

Unified current release: run `python src/cad_pipeline.py --regenerate` to regenerate and validate the catalog; `--validate` checks saved files and source provenance. `python src/cad_release.py` is the dependency-free freshness gate. Concept checks do not certify engineering or regulations.
