# 東京タワー / 东京塔 / Tokyo Tower - LANDMARK-R05

> Historical R05 archive. Current upper-deck and circular-antenna guide: [R06](tokyo_tower_R06.md).

[日本語](#日本語) · [中文](#中文) · [English](#english) · [R04 archive](tokyo_tower_R04.md)

## 日本語

R05はメインデッキ、特別展望台と塔頂を修正します。主展望施設は歴史的なH11の27m角・H12の28m角を各階の制御寸法とし、旧34m一律外殻を廃止しました。H13の29×24m平面は別記し、用途・現在の外装との対応は未確認です。2019年改修写真に合わせ、細い縦枠と横枠、明色の下面と肋、薄い軒、清掃軌道を追加します。割付・厚さ・現在の仕上げ寸法は近似です。

上部展望施設は直径13mの円を16面で近似し、主台とは別の冠形外装にしました。デジタルアンテナ群、SGの内外二重架構、H27の取合いを分離します。STは改修記録の450mm BOXに基づく中空方柱で、壁厚・機器配置・節間・接合は仮定です。仮設吊運設備は再現しません。

モデルGL120/125m・223.55mと、公式案内150/250mを区別します。換算関係と現況の完成面は未確認です。600段の階段と開口、20接合部と248個の代表頭部、照明、下部架構を保持します。円形外殻と干渉しないよう上部塔体軸線のみを調整しました。この軸線は実測値ではありません。航空灯は各屋面へ再配置し、灯具底面の接触と円形屋根内への収まりを確認しています。

## 中文

R05集中修正展望台与顶部。主台用历史H11的27米方形、H12的28米方形分别控制两层，替换旧版统一34米外壳。H13的29×24米平面单独记录，功能及其与当前幕墙的对应未核定。参考2019年改修实景增加密竖框、细横框、浅色底面与底肋、薄檐和清扫轨道；具体分格、厚度和现况尺寸仍为近似。

特别展望台按直径13米的圆形作16面采样，使用独立冠形外壳。补充数字天线设备组、SG内外两层格构和H27承接。ST改为有内腔的450毫米方箱柱；其壁厚、设备位置、分节及连接均是假设，不复原施工临时吊运设备。

继续分列模型GL120/125米、223.55米与官方150/250米案内高度，不假定已知换算关系。保留600级楼梯及洞口、20处节点与248个代表头部、灯具和下部架构。圆台附近的塔身轴线为避免穿窗作局部调整，该收分属于模型假设。航空灯已按各自屋面重新放置，并检查灯座接触及其在圆顶内的位置。晴空塔R03几何保留。

## English

R05 targets the decks and upper steelwork. Separate historical H11/H12 controls of 27m/28m replace the former uniform 34m main-deck envelope. The 29×24m H13 plan is recorded separately; its function and mapping to the current facade are unverified. Narrow mullions, fine transoms, pale ribbed soffits, shallow eaves and cleaning tracks follow 2019 renovation photographs; their detailed layout and dimensions remain approximate.

The upper deck samples a 13m circle with 16 facets and an independent crown. Digital antenna banks, inner/outer SG frames and the H27 interface are distinct. The ST uses a hollow 450mm BOX; wall thickness, equipment, bays and joints remain assumptions. Temporary hoisting structures are excluded. Nearby tower axes are adjusted for glass clearance, not presented as original section coordinates.

Model GL120/125m and 223.55m remain separate from official 150/250m guidance. Their conversion and present finished-floor levels are unverified. The 600-rise route and void, 20 inspection nodes, 248 representative heads, lighting and lower frame are retained. Obstruction fixtures are relocated onto their respective roofs, with contact and footprint checks. Skytree R03 geometry is preserved.

## 参照照合 / Reference comparison

| Evidence | R04 mismatch | R05 correction / limit |
| --- | --- | --- |
| JAEE-hosted historical Fig.3: H11/H12 plans | Uniform 34m deck | Independent 27m/28m controls; current envelope mapping remains approximate. |
| Historical H13 29×24m plan | No separate reference record | Recorded independently; function and current-facade mapping unverified. |
| H23 circular plan | Main/top share chamfered-square template | 13m circle, faceted for display; crown/trim heights assumed. |
| LIXIL 2019 exterior | Sparse glazing, orange apron, heavy fascia | Fine frames, pale soffit/ribs, shallow eaves and cleaning rail; no measured facade schedule. |
| Miyaji SG reinforcement / ST replacement | One slender lattice and round tapered tip | Inner/outer SG frame and 450mm BOX; detailed section assignments and equipment remain approximate. |

## パラメーター / Parameters

- `detail.main_floor_half_widths_mm`: independent main-floor controls, with the existing stair void.
- `detail.deck_appearance`: curtain-wall divisions, mullions, transoms, soffit and top-deck sampling; deck-only GLB glass alpha is adjustable.
- `detail.antenna_appearance`: digital panels, SG inner/outer frame and ST BOX wall/equipment controls.
- `detail.historical_section_controls_mm`: historical dimensions recorded independently of current appearance assumptions.
- `profile`: tower-axis controls; the upper-deck neighbourhood is an explicitly assumed fit to the circular envelope.

The current model has 4,143 named components. STEP solids, GLB and editable drawing projections use the same component specifications. This is an appearance study, without structural, damping or connection-capacity analysis.

## ファイル / Files

- [STEP](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb)
- [Plan DXF](../DXF/tokyo_tower_plan.dxf) · [Elevation DXF](../DXF/tokyo_tower_elevation.dxf) · [Node DXF](../DXF/tokyo_tower_steel_nodes.dxf)
- [Three-page A3 PDF](../output/pdf/tokyo_tower_sheets.pdf) - main deck, circular upper deck and antenna close-ups are included in the elevation sheet.
- [Parameters and references](../output/review/tokyo_tower_manifest.json) · [Frame/deck source](../src/lib/tokyo_tower_detail.py) · [Shared parameters](../src/lib/tower_geometry.py)

Regenerate with `CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate`, then `cd web && npm run build`. Source binding, native validity, hollow volume, deck clearance and drawing checks establish internal consistency; visual reference review is separate.

## 出典 / Sources

Checked 2026-10-30. Reference photographs and source-paper scans are inspected but not redistributed with the project.

- [JAEE-hosted volume, printed pp96-97 / PDF pp105-106](https://www.jaee.gr.jp/jp/wp-content/uploads/2015/04/vibration_characteristics.pdf) - reproduction of Naito et al. 1962 Fig.3, historical deck plans and observation levels.
- [LIXIL curtain-wall project](https://www.biz-lixil.com/case/curtainwall/B190037/) - manufacturer description and exterior images of the 2019 renovation.
- [LIXIL Renewal before/after](https://www.lixil-renewal.co.jp/business/case/archives/15) - current facade character, distinct from historical structural dimensions.
- [Miyaji No28, printed pp65-66 and p69](https://www.miyaji-eng.co.jp/technology/newsletter/media/28/no28-p064-070.pdf) - structural zones, external SG strengthening and ST replacement.
- [Miyaji No18, printed p86](https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf) - construction GL reference bands.
- [Tokyo Tower operator](https://www.tokyotower.co.jp/plan/towerpedia/) - current nominal heights and public route information.
