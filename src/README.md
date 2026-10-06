# Model catalog / 模型源码 / モデルソース

[简体中文](../README.md) | [日本語](../README.ja.md) | [English](../README.en.md)

R06 is a demonstration structural layout with a storage-only attic, maximum finished clear height 1350 mm. Member sizes and foundations are uncalculated; site and statutory recognition remain pending.

R06为纯储物阁楼与结构布置演示，最高完成净高1350 mm。构件截面与基础未计算，所在地和法定用途认定待核定。

R06は収納専用小屋裏・構造配置のデモで、最高仕上げ内法高さは1350 mmです。部材断面と基礎は未計算で、所在地と法規上の認定は未確定です。

| Source | Output | Purpose |
| --- | --- | --- |
| `generate_plans.py` | `DXF/001D0PL2-1FPLAN.DXF`, `DXF/002D0PL2-2FPLAN.DXF`, identical `house_1f_plan.dxf` / `house_2f_plan.dxf` aliases, `output/pdf/house_floor_plans_R02_JP.pdf` | R02 drawings with editable labels/dimensions and an A3 paper layout |
| `lib/house_plan.py` | shared data, no standalone output | Millimetre parameters, rooms, walls, openings and assumptions |
| `lib/jp_drafting.py` | shared style, no standalone output | Japanese drafting layer names, paper lineweights, nominal text sizes and drawing filenames |
| `lib/jp_sheet.py` | shared sheet, no standalone output | A3 frame, Tokyo-style title block, room areas and assumptions in DXF paper space and PDF |
| `house_3d.py` | `STEP/house_3d.step`, `GLB/house_3d.glb` | Named 3D assembly from the approved R01 plans |
| `lib/attic_geometry.py` | current attic model and metadata | R06 subfloor, hatch, flat ceiling, storage and deployed ladder / 阁楼参数 / 小屋裏パラメータ |
| `lib/structure_geometry.py` | named structural proposal | Columns, beams, sills, joists, headers, roof framing and candidate bearing walls / 结构布置 / 構造案 |
| `lib/engineering_inputs.py` | `output/review/engineering_inputs_R06.json` | Demonstration values and pending inputs / 演示与待定输入 / 仮定と未確定入力 |
| `generate_structural_scheme.py` | `DXF/house_structural_scheme.dxf`, `output/pdf/house_structural_scheme_R06_JP.pdf` | Editable structural layout supplement / 可编辑结构方案图 / 編集可能な構造案 |
| `lib/house_geometry.py` | shared geometry, no standalone output | Slabs, wall apertures, roof, doors/windows, storage and stairs |

Run `.venv/bin/python src/generate_plans.py` from the project root.

R02 adapts the common provisions of the Tokyo civil-engineering CAD drafting standard (April 2024) to this house concept. See `docs/tokyo_cad_standard_mapping_R02.md` for scope and section references. Run `checks/validate_plans.py` and `checks/validate_jp_drafting.py` after generation. The editable DXF sheet is in layout `JP_A3_1_50`; the browser viewer displays model space. SXF electronic delivery is outside this output.

The R01 floor plans are user-approved. Run `.venv/bin/python src/house_3d.py` to regenerate the STEP and named GLB, then `.venv/bin/python checks/validate_3d.py` to check the saved artifacts. Source/STEP units are millimetres; GLB follows glTF metres/Y-up.
