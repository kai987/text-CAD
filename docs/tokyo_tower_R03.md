# 東京タワー / 东京塔 / Tokyo Tower - LANDMARK-R03

> Historical stage. Current reference correction: [LANDMARK-R04](tokyo_tower_R04.md). R03 universal L sections and repeated node templates were schematic approximations, now revised.


[日本語](#日本語) · [中文](#中文) · [English](#english) · [R02 stage](tokyo_tower_R02.md)

## 日本語

R03は鋼接合部の外観を詳細化します。176本の主材は元の名前と軸線を保持し、向きのあるL形断面へ変更しました。下部の脚材・腹材、接長部、主展望台下の20箇所に節点板、2枚の補剛材、10個の代表リベット頭を追加しています。元の1,779部材に260部材を加え、全体は2,039部材です。

元の軸線はL形断面の肢が重なる実材内に配置し、既存の腹材や連結板との接触を保ちます。節点部材はCADの具名ソリッドで、STEPとGLBで同じ形状を保持します。600段の外階段、展望台、ガラス、灯具、全高333 mは継承しています。

節点番号はTT-N01〜20。Webの「鋼接合部」から選び、実際の部材に基づく近景へ移動できます。「自動」では拡大した視野内の微細部材を表示し、「表示」「非表示」で切り替えられます。リベット頭だけが微細表示の対象で、節点板や灯具はこの設定の影響を受けません。ダウンロード形状には全てのリベット頭を保持します。

図面はA3用紙3ページです。第3ページに20節点の位置索引と、TT-N01/05/13/17の局所正投影を追加しました。板幅とリベット間隔は編集可能な原生DIMENSIONで、板厚は可変パラメーターの注記です。斜めの板面は部材の局部座標系から投影し、模型上の実寸を使用します。

**断面、板厚、リベット数・間隔、20箇所の選択と接合形式はモデル用の仮定です。** 公開資料は東京タワー建設時のリベット接合という歴史的特徴を示しますが、このモデルは原設計や歴次改修の詳細を復元したものではありません。接合耐力・定着・補強設計の計算は行っていません。

## 中文

本版将176根主材改为有方向的L形截面，保留原部件名与轴线；在20处关键节点各增加节点板、2块加劲肋和10个代表性铆钉头。新增260个构件，模型合计2,039个具名部件。L形肢板的交叠区保留既有轴线，既有腹杆、短接板与主材的代表性接触已用原生CAD检查。

节点按塔脚4处、下部桁架8处、接长4处、主展望台下4处编号。网页可按编号选择真实节点并近看；微细节支持自动、显示、隐藏，自动模式根据视域大小及位置显示铆钉。STEP/GLB始终保留全部构件，网页显示开关不修改下载文件。

CAD新增独立的节点DXF/SVG，PDF扩展为三页A3。第三页包含20个位置索引和4张代表节点详图，板宽与铆钉间距为可编辑原生尺寸，板厚为动态注记。图面使用板件局部正交坐标投影实际三维顶点。

全部截面尺寸、板厚、铆钉头数量与间距、节点位置和连接形式均为演示假设。历史铆接特点参考公开技术资料，未复原原设计和历次加固节点，也未计算连接承载力或基础锚固性能。晴空塔R02几何保持不变。

## English

R03 replaces 176 primary chord placeholders with oriented L sections while preserving member names and axes. Twenty selected nodes each add a plate, two stiffeners and ten representative rivet heads: 260 additional parts and 2,039 named parts overall. The original axes remain inside the overlapping L legs to retain existing connections; representative native-CAD contacts are checked.

Node IDs cover four leg bases, eight lower-truss joints, four splices and four joints below the Main Deck. The viewer selects and frames each node from its actual geometry. Micro-detail Auto/On/Off controls rivet visibility; all parts remain in downloaded STEP/GLB files. Plates, lights and other categories retain their independent visibility.

The new editable node DXF/SVG and third A3 PDF page include a twenty-node index and four representative details. Native dimensions measure plate width and rivet pitch in the actual local plate plane; thickness is a parameter-driven note. The 600-step route, glazing, decks and lighting are retained. Skytree R02 geometry is preserved.

Section sizes, thicknesses, rivet counts/pitch, node selection and connection layouts are demonstration assumptions. Historical riveting character informs appearance; original and retrofit connections, connection capacity and anchorage performance have not been reconstructed or calculated.

## 節点 / 节点 / Nodes

| IDs | 区分 / 类型 / Type | Count |
| --- | --- | --- |
| TT-N01–04 | 塔脚 / Leg base | 4 |
| TT-N05–12 | 下部トラス / 下部桁架 / Lower truss | 8 |
| TT-N13–16 | 主材継手 / 主材接长 / Chord splice | 4 |
| TT-N17–20 | 主展望台下 / Below Main Deck | 4 |

## 仮定パラメーター / 演示参数 / Assumed parameters

All dimensions below are model assumptions, not original-building specifications. Edit the `steel_*` fields in [shared parameters](../src/lib/tower_geometry.py).

| Parameter | Default |
| --- | --- |
| L-leg thickness / leg width | 0.10 |
| Plate width × height × thickness | 1200 × 840 × 24 mm |
| Stiffener thickness / depth | 16 / 160 mm |
| Rivet-head radius / projection | 20 / 12 mm |
| Representative rivet pitch | 151.2 mm |
| Rivet heads per selected node | 10 |

## ファイル / 文件 / Files

- [STEP](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb)
- [Steel-node DXF](../DXF/tokyo_tower_steel_nodes.dxf) · [SVG](../output/svg/tokyo_tower_steel_nodes.svg) · [Three-page A3 PDF](../output/pdf/tokyo_tower_sheets.pdf)
- [Model and twenty-node catalog](../output/review/tokyo_tower_manifest.json) · [Drawing metadata](../output/review/tokyo_tower_drawings.json)
- [Steel geometry source](../src/lib/tokyo_tower_steel.py) · [Base geometry](../src/lib/tokyo_tower_detail.py) · [CAD exporter](../src/towers_3d.py) · [Drawing generator](../src/generate_tower_plans.py)

## 再生成 / 重建 / Regeneration

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate
cd web
npm run build
npm run preview -- --port 4199
```

The shared pipeline checks saved STEP solids, GLB names/materials/bounds and node catalog, editable dimensions, local projection metadata, PDF sheets and source/output hashes. Unit tests cover the twenty-node inventory, profile axes, positive thicknesses and representative connections. These checks establish internal consistency, not original-building accuracy or engineering approval.

## 出典 / 来源 / References

Checked on 2026-10-30. All geometry is authored in this repository; operator photographs and original construction models are not redistributed.

- [Japan Welding Engineering Society technical paper, page 2](https://www-it.jwes.or.jp/we-com/bn/vol_1/sec_2/2-1.pdf) - historical SS41/riveted construction description of Tokyo Tower; does not specify this model's node dimensions.
- [Takenaka renewal case](https://www.takenaka.co.jp/solution/asset/project/07/) - maintenance and strengthening context; model connections do not reproduce the retrofit design.
- [Tokyo Tower guide](https://www.tokyotower.co.jp/guidance/) - overall and observation-deck heights.
