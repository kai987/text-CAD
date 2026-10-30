# 東京のランドマーク / 东京地标 / Tokyo landmarks — LANDMARK-R01

> 現行 / 当前 / Current: [東京タワー R06](tokyo_tower_R06.md) · [東京スカイツリー R04](tokyo_skytree_R04.md). This document retains the initial R01 overview; use the current guides for geometry controls, assumptions and three-page drawing sets.

## 中文

新增两个独立的参数化外观模型：东京塔和东京晴空塔。原有住宅、公寓和河流保留为独立方案。网页模型选择器可切换两塔，URL分别使用 `?model=tokyo-tower&view=3d` 和 `?model=tokyo-skytree&view=3d`；`view=plan`、`view=elevation`、`view=files` 对应平面、立面和下载。

| 项目 | 有来源的参考尺寸 | 本项目处理 |
| --- | --- | --- |
| 东京塔 | 总高333 m，主要展望台150 m、250 m | 保留这些标高；四支塔腿、红白桁架、展望台壳体和天线采用参数化示意几何 |
| 东京晴空塔 | 总高634 m，天望甲板350 m、天望回廊445–450 m | 采用350 m、450 m控制标高；表达展望台、顶部天线和渐变塔身 |
| 晴空塔塔身控制截面 | 基脚正三角形边长约68 m；高315 m处为直径约32 m的圆形 | 共用24点截面插值，明确属于本项目的简化方法，不复现原设计全部曲线 |

本模型**不是原建筑CAD、实测图、施工图或结构设计成果**。东京塔80 m基脚控制宽度，以及未列明的杆件、截面、连接、展望台半径、基础、配筋、色带分界和朝向，均为示意假设。地面基准为Z=0；塔高从该基准量至塔尖，不把地下示意基座计入塔高。DXF和STEP使用毫米、Z轴向上；GLB使用米、Y轴向上。

每座塔分为 `base`、`structure`、`core`、`decks`、`antenna` 五类，部件独立命名。网页支持分类显隐、部件选择、旋转缩放、正视/侧视/俯视/等轴测，以及场景昼夜和中日英界面。夜景仅为显示效果，不是原建筑灯光配置或照度设计。

每塔提供平面和立面DXF、对应SVG、两页A3 PDF、STEP、GLB和来源/参数清单。图纸注记使用日文，DXF保留原生TEXT与DIMENSION；ACI 7 / ByLayer用于在深浅CAD背景上保持文字对比。纸面比例见各页，模型空间为1:1。CAD图中的平面轴线表示模型自身坐标，不是测绘北向。

## 日本語

東京タワーと東京スカイツリーを、独立したパラメトリック外観モデルとして追加しました。公式施設資料の全高・展望施設の高さと、設計者資料のスカイツリー基部・移行断面を参照しています。図面と3Dは同じ部材仕様から生成し、図面は編集可能な文字・寸法を保持します。

東京タワーは全高333 m、展望台150 m・250 m。東京スカイツリーは全高634 m、天望デッキ350 m、天望回廊445～450 mです。スカイツリーは地上の約68 m正三角形から、高さ315 mで直径約32 mの円形へ移行する制御断面を使います。ただし、その間の補間・部材配置は本プロジェクト独自の簡略表現です。

**実施設の原設計CAD・実測図・施工図ではありません。** 東京タワーの基部幅、柱・梁・接合部、展望台外殻、基礎、色分け位置、向きなど、出典で確定していない値はモデル用の仮定です。構造計算、耐震・耐風、法適合、配筋、照度の検討は行っていません。図面上にも参考外観モデルである旨を記載します。

モデル選択から両塔を切り替え、3D・平面・立面・ダウンロードを表示できます。5分類の部材表示、4方向の視点、昼夜、3言語に対応します。CADはmm・Z-up、GLBはm・Y-upです。各PDFは平面・立面のA3用紙2枚で、記載した縮尺に従って印刷してください。

## English

Two independent parametric exterior studies are provided: Tokyo Tower and Tokyo Skytree. Published landmark and observation heights are retained: 333 m with 150/250 m observation levels, and 634 m with 350/450 m observation levels respectively. Skytree's approximately 68 m triangular base and approximately 32 m circular control section at 315 m follow the designer's publication. Interpolation between them is an original simplified model, not a reconstruction of the complete original geometry.

These are **reference appearance models, not original architectural CAD, surveys, construction drawings or engineered replicas**. Unreferenced dimensions, members, connections, foundations, deck shells, paint boundaries and orientation are assumptions. Structural capacity, wind/seismic response, reinforcement and lighting performance are not calculated.

Named groups separate bases, lattice frames, cores, observation decks and antennas. Each model includes editable Japanese DXF plan/elevation drawings, SVG previews, a two-page A3 PDF, STEP solids, GLB and provenance manifests. CAD uses millimetres/Z-up; GLB uses metres/Y-up. Heights are measured above model ground Z=0, excluding the illustrative underground base. Viewer URLs use `model=tokyo-tower` or `model=tokyo-skytree`, with `view=3d`, `plan`, `elevation` or `files`.

## ファイル / 文件 / Files

| | 東京タワー / Tokyo Tower | 東京スカイツリー / Tokyo Skytree |
| --- | --- | --- |
| STEP | [tokyo_tower.step](../STEP/tokyo_tower.step) | [tokyo_skytree.step](../STEP/tokyo_skytree.step) |
| GLB | [tokyo_tower.glb](../GLB/tokyo_tower.glb) | [tokyo_skytree.glb](../GLB/tokyo_skytree.glb) |
| 平面 / Plan DXF | [DXF](../DXF/tokyo_tower_plan.dxf) | [DXF](../DXF/tokyo_skytree_plan.dxf) |
| 立面 / Elevation DXF | [DXF](../DXF/tokyo_tower_elevation.dxf) | [DXF](../DXF/tokyo_skytree_elevation.dxf) |
| A3 PDF | [PDF](../output/pdf/tokyo_tower_sheets.pdf) | [PDF](../output/pdf/tokyo_skytree_sheets.pdf) |
| パラメータ / Parameters | [JSON](../output/review/tokyo_tower_manifest.json) | [JSON](../output/review/tokyo_skytree_manifest.json) |

## 再生成 / 重建 / Regeneration

Run from the repository root using the existing Python 3.13 CAD environment:

```bash
CADGEN_DAEMON=0 .venv/bin/python src/towers_3d.py
.venv/bin/python src/generate_tower_plans.py
.venv/bin/python checks/validate_towers.py
```

These three commands regenerate and inspect only the two landmarks. To refresh the complete source-bound release used by the web build, run the shared pipeline after editing the parameters:

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate
cd web
npm test
npm run build
npm run preview
```

The shared [geometry specifications](../src/lib/tower_geometry.py) drive CAD, drawings and metadata. The [saved-asset validator](../checks/validate_towers.py) reads actual STEP solids, decoded GLB coordinates, editable DXF dimensions and PDF pages. Source/output hashes are checked again before copying assets to the web build. These checks establish internal consistency, not real-building accuracy or engineering approval.

## 出典 / 来源 / References

Checked 2026-10-30. Facts are recorded with their source URLs in each manifest. Geometry is authored for this project; no operator photographs, logos or third-party downloadable models are redistributed.

1. [東京タワー公式・施設案内](https://www.tokyotower.co.jp/guidance/) — tower and observation-deck heights.
2. [東京タワー公式・タワペディア](https://www.tokyotower.co.jp/plan/towerpedia/) — International Orange/white appearance and tower/antenna description.
3. [東京スカイツリー公式・アウトライン](https://www.tokyo-skytree.jp/about/outline/) — 634 m height and observation levels.
4. [東京スカイツリー公式・フロアガイド](https://www.tokyo-skytree.jp/floor/) — 350 m deck and 445–450 m galleria.
5. [日建設計・NIKKEN JOURNAL 2012 Autumn](https://www.nikken.co.jp/ja/about/p4iusj0000001hyd-att/Journal-2012_Autumn.pdf) — approximate 68 m base triangle and 315 m circular transition, with approximately 32 m transition diameter; original design discussion of triangle-to-circle transformation.
