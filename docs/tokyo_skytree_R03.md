# 東京スカイツリー / 东京晴空塔 / Tokyo Skytree - LANDMARK-R03

> 旧版 / 历史版本 / Archive: 現行 / 当前 / Current [東京スカイツリー R04](tokyo_skytree_R04.md) · [東京タワー R05](tokyo_tower_R05.md). The following records the R03 specification; consult the linked guides and manifests for current geometry and actual saved-asset revisions.

[日本語](#日本語) · [中文](#中文) · [English](#english) · [R02 archive](tokyo_skytree_R02.md)

## 日本語

R03は、構造説明図と製作・施工写真に照合して鋼管架構の外観を修正します。旧R02の三本の単柱と正弦曲線のアーチを、三組・各四柱の立体的な鼎トラスへ置き換えました。GL0–50mは三脚の接続を表すモデル区間です。鼎トラス全体の高さを50mと断定するものではありません。

外周の採形と構造節間を分離し、12.5mのリング層と25mの水平連結層を独立に配置します。リングには放射方向の奥行きを与え、鋼製の中塔とつなぎます。直径8m・高さ375mのRC心柱と鋼製中塔を分離し、上部可動域の心柱を鋼管へ剛結した表現は避けています。これは制振応答の解析ではありません。

主材・斜材は実際に孔を持つ円形鋼管、リングと連結材は角形鋼管としてCADを作成します。従来の中実八角棒と異なり、解析円筒と円環断面の放樣で管壁を保持します。長い主弦の放樣断面は水平円環の近似で、すべての原設計法線断面を復元したものではありません。基部最大径2300mm・厚100mmと製作者が公表した部位別範囲を参照し、その範囲内の径・厚さ割付はモデル仮定です。

上部は六柱の開放格構へ変更し、旧版の中実円錐を撤去しました。495mの既存接続と499mからの露出格構、部材・アンテナ・保守帯の位置は近似です。340/345/350mの天望デッキ、445–450mの傾斜回廊と薄いガラスは継承しています。接合は鋼管の直接分岐を表現し、東京タワーのリベット板を流用しません。全溶接部の開先・余盛・相貫切断面を復元したものではありません。

新たな第3 A3ページに、基部の全体と一組四柱の斜向き投影、モデルの50000/12500/25000mm寸法を追加します。DXFの文字・寸法は編集可能です。STEP、GLB、平面・立面・構成図は同じ部品仕様を使います。東京タワーR04のパラメーターと形状は変更しません。

## 中文

R03根据官方结构图和制造、施工资料修正杆系。旧版“三根单柱加三道正弦拱”改为三组、每组四柱的立体鼎桁架；GL0–50m为三脚与塔身连接的模型区间，不把鼎桁架的完整高度认定为50m。

轮廓采样与结构分节分别控制：12.5m设置环桁架层，25m设置水平连接层，补充环的径向深度和钢制中塔。RC心柱与钢制中塔保持分离，避免将上部活动域的混凝土心柱刚性焊入钢框架。模型不模拟制振、承载或抗风性能。

圆管和方管在原生CAD中具有真实管壁和内部空腔。长主弦使用水平圆环站点放样，属于外观近似，不是每根杆件的原设计法向截面。塔脚最大直径2300mm、壁厚100mm及各部位范围有公开依据；具体哪根杆取什么直径、壁厚，以及柱组宽深、环深和斜杆布置，仍是模型参数。

上部改成六柱通透格构，取消实心锥体；495m既有接口与499m起露出格构为模型近似。天望甲板三层、坡道回廊和薄玻璃保留。连接按圆管直接分岐的特征表达，未逐个复原焊口、坡口及相贯端切。第三页A3新增钢构组成与四柱局部投影，保留可编辑原生尺寸。东京塔R04几何保持不变。

## English

R03 corrects framing mismatches using operator diagrams and fabrication/construction references. Three single legs and invented sine arches become three four-column spatial kanae groups. GL0–50m is the model's lower joining interval, not a claim that the entire kanae system ends there.

Contour sampling is separate from structural spacing. Ring tiers occur at 12.5 m and horizontal links at 25 m, with radial depth and a steel middle tower. The hollow 8 m/375 m concrete core remains separate; the movable upper core is not depicted as rigidly welded to the steel links. No damping response or structural capacity is simulated.

Circular and rectangular hollow sections contain actual CAD bores. Long chords use horizontal annular loft stations as an appearance approximation, not recovered member-normal sections. The published 2300 mm/100 mm base maximum and manufacturer family ranges guide the model; assignment to individual members, group widths/depths, ring depth, intermediate positions and connections remain assumptions.

An open six-chord upper lattice replaces the solid cone. The 495 m interface and exposed lattice from 499 m are approximate. Observation floors, the sloping gallery and thin glazing are retained. Pipe branching informs the joints without reusing Tokyo Tower rivet plates; individual weld preparations and saddle cuts are not reconstructed. A third A3 sheet adds steel-frame composition, an oblique four-column view and editable dimensions. Tokyo Tower R04 geometry is preserved.

## 参照照合 / Reference comparison ledger

| Evidence | R02 mismatch | R03 treatment / remaining approximation |
| --- | --- | --- |
| Official kanae definition: four columns at each triangular vertex | Three single ground-reaching columns and invented sine arches | Three four-column groups, direct ties and braces; group width/depth and local routing assumed. |
| Official parts guide: three legs join at about 50 m | Secondary perimeter begins 45 m | Explicit 50 m joining control; not the complete kanae extent. |
| Operator/Nikken ring 12.5 m, horizontal links 25 m | Rings follow mixed silhouette/floor control stations | Separate ring/link levels and radially deep rings; member layout between controls is approximated. |
| Manufacturer family ranges; base maximum 2300 mm × 100 mm | Ground chord diameter 2900 mm; solid octagonal bars | Role-based hollow circular/rectangular families, with source ranges recorded separately from assigned model sizes. |
| Operator/Nikken pipe branching | Cubic arch nodes | Direct overlapping pipe junctions; weld bead/preparation and every saddle-cut surface remain unverified. |
| Manufacturer gain-tower assembly photo | Solid 16-sided taper with four external lines | Six-chord open steel lattice; exact antenna equipment, bay schedule and envelope are unmeasured. |

The 24 contour points and 12 polygon ring bays are model sampling choices, not declarations of the original tower's column count. Analytical CAD curves are sampled only for drawing projection and GLB tessellation.

The historical R03 specification contained 4,120 named components, including 1,500 circular tubes, 201 annular loft chords and 1,548 rectangular tubes. This is a selective appearance study, not a reconstruction of every original steel member. Current saved parameters follow the revision identified by their manifest; the figures on this archive page describe R03.

## ファイル / Files

- [STEP](../STEP/tokyo_skytree.step) · [GLB](../GLB/tokyo_skytree.glb)
- [Plan DXF](../DXF/tokyo_skytree_plan.dxf) · [Elevation DXF](../DXF/tokyo_skytree_elevation.dxf) · [Steel-frame DXF](../DXF/tokyo_skytree_structure_zones.dxf)
- [Three-page A3 PDF](../output/pdf/tokyo_skytree_sheets.pdf) · [Parameters and source record](../output/review/tokyo_skytree_manifest.json)
- [Frame source](../src/lib/skytree_detail.py) · [Parameters and hollow CAD primitives](../src/lib/tower_geometry.py) · [Drawing generator](../src/generate_tower_plans.py)

Regenerate with `CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate`, then `cd web && npm run build`. Internal validity, names, bounds, hollow volumes, editable dimensions and provenance checks establish consistency; visual reference comparison is a separate check.

## 出典 / Sources

Checked 2026-10-30. Reference images are inspected but not redistributed.

- [Operator structural design, with Nikken diagrams](https://www.tokyo-skytree.jp/about/spec/structure/) - four-column kanae groups, 12.5/25 m hierarchy, 2300 mm/100 mm base maximum and direct pipe welding.
- [Operator parts/design guide](https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/parts.php) - approximately50m joining, 68 m triangular base, 315 m circular transition and observation/core controls.
- [Tomoe fabrication outline](https://www.tomoe-corporation.co.jp/steel-tower/works/skytree/outline.html) - member-family diameter/wall ranges and pipe-branch fabrication context.
- [Tomoe fabrication works](https://www.tomoe-corporation.co.jp/steel-tower/works/skytree/) - gain-tower factory assembly photographs.
- [Nikken project history](https://www.nikken.co.jp/ja/about/projects_history/corporate_history/12_03.html) - structural separation of steel body and concrete shinbashira.
