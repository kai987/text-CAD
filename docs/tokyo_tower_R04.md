# 東京タワー / 东京塔 / Tokyo Tower - LANDMARK-R04

[日本語](#日本語) · [中文](#中文) · [English](#english) · [R03 archive](tokyo_tower_R03.md)

## 日本語

R04は、R03の細密化よりも実塔との外観の整合を優先した修正です。宮地技報の全体立面とIHIの施工写真、竹中工務店の改修写真を比較し、浮いた高いアーチ、疎らな下部トラス、全主材を同じL形にした表現、20節点を同一板で表した点を変更しました。

アーチ頂部はH3のGL+40,000 mmを参照し、地際から連続する形へ変更しました。アーチ脇の腹材、40–80m帯の面内トラスと四面の脚缀条、非等間隔の上部節間を追加しています。主材は幅広の組立材を表す3群のH/I外観断面、20節点は塔脚・下部集合・両面継手・展望台支持の4群です。上部アンテナ支持部は開いた格構として分離しました。これらの断面形式・寸法は実測断面の復元ではありません。

**高さの記録を分けています。** 公式案内はメインデッキ150m、トップデッキ250mです。一方、施工報告の立面はH11=GL120m、H23=GL223.550m、H27=GL252.650mを明記しています。本モデルでは構架帯から展望台外殻の位置を解釈し、主展望台床をGL120/125m、上部をGL223.550mに配置します。+5m層間と床面の同定は仮定で、公式案内値との換算や現在の仕上げ床高さを独立に測量・検証したものではありません。CADの寸法とWebにはモデルGLを記載し、公式案内値は別記します。

全体は3,010個の具名部品です。20節点には24枚の板、24枚の肋・支持材、248個の代表頭部を含みます。600段の独自外階段、ガラス、灯具、節点近景、微細表示の自動/表示/非表示を維持し、STEP・GLB・編集可能DXF・SVG・3ページA3 PDFを同じパラメーターから生成します。スカイツリーR02の形状は変更しません。

## 中文

R03增加了细节，但“更多构件”并未解决与实物的差异。R04对照施工立面和施工、改修照片，修正了四项主要问题：悬空且过高的拱、稀疏的下部格构、所有主材统一单L截面，以及20处节点套用相同板件。

拱顶按图中H3的GL+40,000 mm控制，拱肋从近地面连续起步；补充拱侧腹杆、40–80m横向多格桁架、塔脚四面缀条及非等高上部分节。主材改为三组宽面组合材的H/I外观表达，20个节点按塔脚、下部汇交、双面接长、展望台支承分四组。上部天线支承塔改为通透格构。截面类型、尺寸和中间网格均是有参考依据的近似表达，未逐杆复原原设计。

**几何GL与官方案内高度分别记录。** 官网公布150m/250m；施工立面标注H11=GL120m、H23=GL223.550m、H27=GL252.650m。模型按结构带解释外壳位置，将主展望台双层布置在GL120/125m、上部参考层在GL223.550m。5m层距与楼板识别仍是假设，未独立测绘游客完成面，也不声称已核准两组高度的换算。图纸标注模型GL，网页另列官方案内值。

模型共3,010个具名部件。20处节点包含24块板、24块肋/支承件和248个代表头部。600级示意外楼梯、玻璃、灯具和节点近景功能保留；STEP、GLB、DXF、SVG与三页A3 PDF共用参数。晴空塔R02几何保持不变。

## English

R04 corrects reference mismatches that added detail in R03 did not resolve: a high floating arch, sparse lower framing, a single L section applied to every chord and one repeated connection template.

The arch crown now follows the published H3 GL+40m control and grows continuously from near ground. Spandrel webs, a multi-panel 40–80m lower truss, four-face leg lacing and nonuniform upper belts restore the visible framing hierarchy. Three graded built-up H/I appearance families replace the universal L. Twenty nodes use four plate/fastener families; the antenna support is an open lattice. Exact sections, bay sizes and connections remain approximations rather than recovered original details.

**Geometric GL and official guidance heights are separate.** The operator publishes 150 m/250 m. The contractor elevation explicitly labels H11=GL120m, H23=GL223.550m and H27=GL252.650m. The model interprets observation-shell placement from these structural bands, with main floors at GL120/125 m and an upper reference floor at GL223.550 m. Floor identification and the 5 m interval remain assumptions. Neither present-day visitor finished floors nor a conversion between these two records has been independently surveyed or verified. Drawings dimension modelGL; the viewer separately lists official guidance values.

There are 3,010 named parts, including 24 node plates, 24 ribs/supports and 248 representative heads across 20 nodes. The schematic 600-step route, glazing, lights and node inspection remain. STEP, GLB, editable DXF, SVG and the three A3 PDF pages share the same parameters. Skytree R02 geometry is preserved.

## 参照照合 / Reference comparison ledger

| Reference evidence | R03 mismatch | R04 correction and remaining approximation |
| --- | --- | --- |
| Miyaji No18 p86 Fig1: H3=GL40,000 | Arch crown67,000 with ends26,000 | Crown 40,000; near-ground ends and spandrel webs. Curve and rib dimensions assumed. |
| Fig1: dense lower face panels and nonuniform H belts | Mostly four narrow leg cages below80m; sparse long upper diagonals | Three lower face bands, multiple X panels and interpreted nonuniform upper belts. Unlabelled positions estimated. |
| IHI Tokyo Tower construction photograph; Takenaka strengthening close-up | Every chord a single L; same rectangle at all 20 nodes | Graded wide-face H/I appearance families and four different connection families. Not original section/joint schedules. |
| Fig1: 80,000 between leg datum axes | Base width treated as an assumed envelope |80,000 recorded as datum-axis spacing, not foundation extent or site area. |
| Fig1:H11/H23 structural elevations; operator150/250m guidance | Guidance heights directly drove CAD floors | Separate fields and explicit interpretation. Finished-floor heights and conversion remain unverified. |
| Miyaji No28 p65 Fig1:H27=252,650; SG top312,600 | Solid cone beginning270,000 | Open support lattice252,650–312,600 and separate tip. Member sizes/equipment stations assumed. |

## 未核定 / Still unverified

- Original and current member section schedules, built-up plate arrangements, rivet/bolt patterns and all connection capacities.
- Exact arch curve, intermediate H elevations, plan widths, deck shells, route, antenna equipment and paint boundaries.
- Current retrofit/as-built state. No18 is a2002 work report; No28 describes later strengthening. No28 labels H23 as223,500 whereas No18 uses223,550; this model consistently uses No18's control.
- No structural analysis or construction approval is implied. The model is an original reference-informed appearance study.

## ファイル / Files

- [STEP](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb)
- [Plan DXF](../DXF/tokyo_tower_plan.dxf) · [Elevation DXF](../DXF/tokyo_tower_elevation.dxf) · [Node DXF](../DXF/tokyo_tower_steel_nodes.dxf)
- [Three-page A3 PDF](../output/pdf/tokyo_tower_sheets.pdf) · [Model parameters and nodes](../output/review/tokyo_tower_manifest.json)
- [Envelope and parameters](../src/lib/tower_geometry.py) · [Frame geometry](../src/lib/tokyo_tower_detail.py) · [Steel profiles and nodes](../src/lib/tokyo_tower_steel.py)

Regenerate with `CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate`, then `cd web && npm run build`. Internal geometry/format/source checks establish consistency; visual reference comparison is a separate acceptance step.

## 出典 / Sources

Checked 2026-10-30. Reference images were inspected but are not redistributed in the project.

- [Miyaji No18, printed p85–91, especially Fig1 p86](https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf) — printed GL controls, structural bands and strengthening context; unlabelled proportions are interpreted.
- [Miyaji No28, p64–70, Fig1 p65](https://www.miyaji-eng.co.jp/technology/newsletter/media/28/no28-p064-070.pdf) — later retrofit and antenna support zones.
- [IHI historical structures](https://www.ihi.co.jp/technology/techinfo/contents_no/1200541_13491.html) — Tokyo Tower construction/current photographs. Angle-steel prose in the adjacent Tsutenkaku paragraph is not a Tokyo Tower section schedule.
- [Takenaka renewal case](https://www.takenaka.co.jp/solution/asset/project/07/) — built-up plate/fastener appearance and later strengthening.
- [Tokyo Tower operator guidance](https://www.tokyotower.co.jp/guidance/) — 333 m total height and official 150 m/250 m deck guidance.
- [Agency for Cultural Affairs listing](https://online.bunka.go.jp/heritages/detail/206677) — 333 m and80m leg spacing.
