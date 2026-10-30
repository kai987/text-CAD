# 東京タワー / 东京塔 / Tokyo Tower — LANDMARK-R02

> Historical stage. Current reference correction: [LANDMARK-R04](tokyo_tower_R04.md). R03 universal L sections and repeated node templates were schematic approximations, now revised.


> 現行 / 当前 / Current: [R03 steel detail](tokyo_tower_R03.md). 本文保留R02阶段说明，当前下载已升级为R03，PDF增加第3页节点详图。This document retains the R02 stage; current exports use R03 and a third PDF sheet.

[日本語](#日本語) · [中文](#中文) · [English](#english) · [Landmark catalog](tokyo_landmarks_R01.md)

## 日本語

東京タワーの外観参考モデルを詳細化しました。全高333 m、展望施設150 m・250 mを保持し、塔脚と下部トラスを曲線状の制御断面から構成しています。接合板、分割ガラスと方立、展望台の床・外殻、Foot Townの入口・庇・屋上手すり、エレベーターのガイド架構と模式的なかごを独立した部材に分けました。

Foot Town屋上から150 mメインデッキまで、600段・24折返しの外階段を連続させ、展望台床に実際の開口を設けています。**公式資料で確認できるのは屋上から150 mまで約600段の外階段があることです。** 本モデルの経路・24フライト・屋上高さ18,300 mm・蹴上219.5 mm・踏面260 mm・中間床145,000 mm・開口位置は、編集可能なモデル上の仮定です。実施設の階段や構造を復元したものではありません。

夜景では投光器、入口灯、航空障害灯と一部の窓に局所的な表現を使い、照明位置・数・配光はモデル用の設定です。表示用の光源は最大5灯。Webでは「塔脚」「メインデッキ」の近景を追加し、600個の踏板を1つの表示バッチにまとめます。元の部材名とCAD/GLBの形状は保持します。東京タワーの形状は、後続の[スカイツリーR02](tokyo_skytree_R02.md)更新でも維持しています。

平面図は1:500、全体立面図は1:1500、メインデッキ詳細は1:300。DXFのモデル空間はmm・1:1、詳細図は同じ形状を映すロック済みビューポートです。SVG/PDFも同じ部材仕様から生成します。

## 中文

本版补充弧线塔脚与下部桁架、节点连接板、展望台分片玻璃及窗框、楼板和分层外壳，完善 Foot Town 入口、雨棚和屋顶栏杆，并用导轨架与示意轿厢表达电梯。模型保留总高333 m、展望台150 m和250 m。

新增从 Foot Town 屋顶到150 m主展望台的连续外楼梯，包含600个踏步、24段梯跑和平台，展望台楼板留有真实几何洞口。**官方依据是约600级外楼梯连接屋顶与150 m主展望台；** 24段梯跑、18,300 mm屋顶高度、219.5 mm踏步高、260 mm踏步深、145,000 mm中间楼层和具体开口位置均为演示假设，不代表原塔实测。

网页增加“塔脚”和“主展望台”近景。夜景按灯具、部分窗片分别点亮，使用最多5个显示光源；灯具布置和配光为示意。600个踏步合并成1个显示批次以减少绘制调用，下载文件仍保留具名构件。晴空塔已在后续[独立的R02更新](tokyo_skytree_R02.md)中详细化。

图纸包含1:500平面、1:1500整体立面和1:300主展望台详图，共两页A3。DXF模型空间为毫米、1:1，详图使用锁定视口；可编辑文字和原生尺寸标注保留。玻璃、节点和楼梯的尺寸、结构截面均为外观建模参数，未进行承载、抗震、抗风或照度验算。

## English

R02 adds curved lower legs, open approach frames, representative connection plates, segmented observation glazing and mullions, separate deck floors and shells, a Foot Town entrance/canopy/roof guard, and an elevator guide frame with schematic cabins. Published heights remain 333 m overall and 150/250 m for the observation decks.

A continuous external stair connects the Foot Town roof to the 150 m Main Deck, with 600 individually named treads, 24 flights, landings and an actual opening in the deck floors. **The official reference confirms approximately 600 steps from the roof to 150 m.** Our route, flight arrangement, 18,300 mm roof level, 219.5 mm rise, 260 mm tread, 145,000 mm intermediate floor and opening location are modelling assumptions, not measured original geometry.

New base and main-deck camera presets expose these details. Local fixture/window lighting uses at most five viewer lights; fixture positions and illumination are illustrative. The viewer batches 600 treads into one display draw while retaining named source parts and downloadable geometry. Skytree has since received a [separate R02 detail update](tokyo_skytree_R02.md).

The two A3 sheets provide a 1:500 plan, 1:1500 elevation and 1:300 main-deck inset. Editable DXF uses millimetres and 1:1 model space; the detail is a locked viewport onto the same geometry. SVG/PDF use the same component specifications. This is an original appearance study; structural, seismic, wind and lighting performance have not been calculated.

## ファイル / 文件 / Files

- [STEP solids](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb)
- [Plan DXF](../DXF/tokyo_tower_plan.dxf) · [Elevation DXF](../DXF/tokyo_tower_elevation.dxf) · [A3 PDF](../output/pdf/tokyo_tower_sheets.pdf)
- [Parameters and provenance](../output/review/tokyo_tower_manifest.json) · [Drawing metadata](../output/review/tokyo_tower_drawings.json)
- [Shared parameters](../src/lib/tower_geometry.py) · [R02 geometry](../src/lib/tokyo_tower_detail.py) · [CAD export](../src/towers_3d.py) · [Editable drawing generator](../src/generate_tower_plans.py)

## 再生成 / 重建 / Regeneration

From the repository root, the following commands regenerate only Tokyo Tower:

```bash
CADGEN_DAEMON=0 .venv/bin/python src/towers_3d.py --tower tokyo-tower
.venv/bin/python src/generate_tower_plans.py --model tokyo-tower
.venv/bin/python checks/validate_towers.py
```

After changing any CAD sources, regenerate the complete source-bound release before building the website:

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate
cd web
npm run build
npm run preview -- --port 4199
```

The pipeline checks saved STEP solids, GLB mesh names/materials/bounds, drawing dimensions/viewports, PDF sheets and source/output hashes. These checks establish internal consistency, not as-built accuracy. CAD uses mm/Z-up; GLB uses m/Y-up.

## 出典 / 来源 / References

Official operator pages checked on 2026-10-30. Geometry is authored in this repository; no operator images or third-party tower models are redistributed.

- [Facility guide](https://www.tokyotower.co.jp/guidance/) — published tower and observation heights.
- [Main Deck](https://www.tokyotower.co.jp/maindeck/) — two observation floors; the model's intermediate height is assumed.
- [Foot Town](https://www.tokyotower.co.jp/foottown/) — entrance and rooftop access context.
- [Open-air stairs](https://www.tokyotower.co.jp/plan/open_air_stair/) — approximately 600 steps from Foot Town roof to the 150 m Main Deck.
- [Light-up](https://www.tokyotower.co.jp/lightup/) — appearance reference; model fixtures are schematic.
