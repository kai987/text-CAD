# 東京スカイツリー / 东京晴空塔 / Tokyo Skytree — LANDMARK-R05

[日本語](#日本語) · [中文](#中文) · [English](#english) · [出典 / 来源 / Sources](#sources) · [R04 archive](tokyo_skytree_R04.md) · [Tokyo Tower R06](tokyo_tower_R06.md)

## 日本語

R05は、外周水平材の断面と地上付近の鉄骨の広がりを修正します。外周に中空円管の水平材を設け、三組の鼎トラスから左右へ広がる格構翼を三面に補います。各面の中央には尖頭アーチ状の開口を残します。東京タワーは独立したR06です。本モデルは公開資料を参考に本プロジェクトで作成した外観モデルであり、実施設の原設計CAD、実測・竣工図、施工図ではありません。

**円管と角管。** 既存の主弦・斜材の円管を保持し、外周水平材を内部リングとは別の円管部材として扱います。製作者の断面表は外周等の水平材に円管、水平連結トラスとリングトラスに角形断面を示しているため、内側リングと放射方向の連結には角管（RHS）を残します。表は部材群の範囲であり、モデル内の一本ごとの径・板厚・配置が原設計と一致する証拠ではありません。円管はCADソリッドに実際の内孔を持ち、GLBもその部材形状から生成します。

**塔脚の三面。** 三組各四柱の鼎を保ち、それぞれの面に幅広い格構翼と中央開口の縁を追加します。事業者の説明と施工者の脚部写真・図が約50mで三本の脚がつながる構成を示します。翼の張出し、枝の位置、開口の曲線、分節数と接合位置は写真に基づく形状合わせです。地上付近を一様な円筒格子で塞ぐ構成にはせず、三面の格構と開口を区別します。接合部の耐力、工事時の仮受け、地下基礎は復元・計算していません。

**引き継ぐ輪郭と展望施設。** 円管という部材断面と塔体の平面形は別のものです。塔体は約68mの三角形基部から高さ315mで直径約32mの円形へ変化し、上部は495mで直径約18mとなる直線テーパーを保持します。全高は634mです。天望デッキの340/345/350m各階と375m設備屋上、445–450mの回廊と451.2m最高点、ゲイン塔とTMD外形はR04を継承します。円弧の近似、未公表の設備断面、回廊経路の仮定などは[R04の詳細と出典](tokyo_skytree_R04.md)に記録しています。実測による精度認定や構造計算は行っていません。

**ファイルと確認範囲。** STEP・GLB・平面/立面/構成DXF・三ページA3 PDFは共通部品仕様を使います。CADはmm・Z-up、GLBはm・Y-upです。名前付き部品数、保存物の改訂、ソースとファイルのハッシュは[マニフェスト](../output/review/tokyo_skytree_manifest.json)で確認できます。確認対象は円管/角管の区別、三面の追加部材と開口、既存輪郭の保持、編集可能な図面と保存物の対応です。この説明自体は保存物の検証完了やオンライン公開完了を意味しません。参考写真は調査用で、リポジトリに再配布しません。

## 中文

R05修正外周水平材的截面和近地面钢结构的展开形态：外侧采用中空圆管水平材，三组鼎桁架向两侧展开的宽翼格构补齐三个立面，各面中央保留尖拱形开口。东京塔仍为独立的R06。本模型是本项目依据公开资料制作的参考外观模型，不是原建筑CAD、实测或竣工图、施工图。

**圆管与方管。** 保持原有圆管主弦和斜撑，将外周水平圆管与内部环桁架分别建模。制造方的截面表把外周等水平材列为圆管，把水平连接桁架、环桁架列为方形截面，因此内侧环和放射连接仍保留方管（RHS）。该表给出的是部件家族的范围，不能证明模型中每根杆件的管径、壁厚和布置与原设计一致。圆管在CAD中具有真实内孔，GLB也由相同的部件形状生成。

**基部三面。** 保留三组、每组四柱的鼎结构，在三个面补充向两侧展开的宽翼格构和中央开口边缘。运营方说明和施工方的塔脚照片、图示提供了三条塔脚约在50m高度相连的参考。翼的展开宽度、分支位置、开口曲线、分段数量和节点位置均为实景引导的拟合。地脚以三面格构围合并保留开口，塔身不改成通高等宽圆筒格栅。节点承载力、施工临时支撑和地下基础没有复原或计算。

**保留的轮廓与展望设施。** 圆管指杆件截面，与塔身平面形状是不同概念。塔身仍由约68m边长的底部三角形，过渡至315m处约32m直径的圆形；上部保留到495m处约18m直径的直线锥度，总高634m。天望甲板340/345/350m楼层与375m设备屋顶、445–450m回廊和451.2m最高点、增益塔及TMD外形均继承R04。圆弧近似、未公开设备截面和回廊路径假设，见[R04详细说明与来源](tokyo_skytree_R04.md)。本模型未进行实测精度核定或结构计算。

**文件与验收范围。** STEP、GLB、平面/立面/结构组成DXF与三页A3 PDF使用共同的部件规格。CAD采用mm、Z-up，GLB采用m、Y-up。具名部件数量、保存资产的版本、源文件和资产哈希见[清单](../output/review/tokyo_skytree_manifest.json)。验证对象为圆管/方管分类、三面补充杆件与开口、既有轮廓保持、可编辑图纸和保存资产的对应。本说明本身不代表资产验证或线上发布已经完成。参考照片仅作调查，不随仓库再分发。

## English

R05 revises exterior horizontal sections and the spread of steelwork near ground level. Hollow circular exterior horizontals accompany broad lattice wings extending either side of the three kanae groups. Each face retains a central pointed-arch opening. Tokyo Tower remains an independent R06 model. This is an original reference appearance study informed by public sources, not the building's original CAD, a survey or as-built record, or construction documentation.

**Circular tubes and RHS.** Existing tubular main chords and braces remain. Exterior circular horizontals are modelled separately from the inner rings. The fabricator lists circular sections for exterior/related horizontals and rectangular sections for horizontal connecting and ring trusses, so the inner rings and radial links retain rectangular hollow sections (RHS). Those tables describe section families, not verified sizes or assignments for every model member. Circular CAD solids have actual bores; GLB derives from the same component shapes.

**Three base faces.** The three four-column kanae groups remain, with broad lattice wings and opening-edge members added across all three faces. Operator explanations and builder photographs/diagrams establish that the three legs join around 50m. Wing spread, branching positions, opening curves, subdivision counts and joints are photo-guided fits. The lattice surrounds the base while retaining the openings; the tower does not become a uniform cylindrical cage. Connection capacity, temporary construction supports and underground foundations are not reconstructed or analysed.

**Retained outline and facilities.** Circular member sections and the tower's plan shape are separate concepts. The body still changes from an approximately 68m-sided base triangle to an approximately 32m-diameter circle at 315m. A straight upper taper reaches an approximately 18m diameter at 495m, with an overall height of 634m. The 340/345/350m Tembo Deck floors and 375m equipment rooftop, 445–450m gallery and 451.2m high point, gain tower and TMD envelope carry forward from R04. See the [R04 details and sources](tokyo_skytree_R04.md) for fitted arcs, unpublished equipment sections and gallery-route assumptions. No surveyed-accuracy certification or structural analysis is included.

**Files and acceptance scope.** STEP, GLB, plan/elevation/frame DXFs and a three-page A3 PDF use a shared component specification. CAD uses mm/Z-up; GLB uses m/Y-up. The [manifest](../output/review/tokyo_skytree_manifest.json) records named-part counts, saved-asset revisions, source hashes and file hashes. Checks cover circular/RHS assignments, the added three-face members and openings, retained outline, editable drawings and saved-file correspondence. This document alone does not establish successful artifact validation or an online release. Reference photographs are inspected for research and are not redistributed in the repository.

## ファイル / 文件 / Files

- [STEP](../STEP/tokyo_skytree.step) · [GLB](../GLB/tokyo_skytree.glb)
- [平面 / 平面 / Plan DXF](../DXF/tokyo_skytree_plan.dxf) · [立面 / 立面 / Elevation DXF](../DXF/tokyo_skytree_elevation.dxf) · [構成 / 组成 / Frame DXF](../DXF/tokyo_skytree_structure_zones.dxf)
- [A3 PDF](../output/pdf/tokyo_skytree_sheets.pdf) · [パラメーター・出典 / 参数与来源 / Parameters and sources](../output/review/tokyo_skytree_manifest.json)
- [架構・展望台・塔頂 / 杆系、展望台、顶部 / Frame, decks and spire](../src/lib/skytree_detail.py) · [輪郭 / 轮廓 / Outline](../src/lib/skytree_outline.py) · [共通仕様 / 共同规格 / Shared specification](../src/lib/tower_geometry.py)
- [出版検証 / 出版验证 / Publication validation](../web/scripts/tower-artifact-validation.mjs) · [保存物の検証 / 保存资产验证 / Saved-asset validation](../checks/validate_towers.py)

<a id="sources"></a>

## 出典 / 来源 / Sources

確認日 / 核查日期 / Checked: 2026-10-30. Source controls and photo-guided model fits are distinguished above.

| 資料 / 资料 / Source | 範囲 / 范围 / Scope |
| --- | --- |
| [巴コーポレーション / Tomoe fabrication outline](https://www.tomoe-corporation.co.jp/steel-tower/works/skytree/outline.html) | Published section table: circular exterior/related horizontals; rectangular connecting and ring trusses. A section-family reference, not a member-by-member schedule for this model. |
| [事業者の構造図解 / 运营方结构图解 / Operator structural diagrams](https://www.tokyo-skytree.jp/about/spec/structure/) | Three four-column kanae groups, circular pipe branching, and separate exterior and inner framing. |
| [公式の部位・形状説明 / 官方部件与形状说明 / Operator parts and design](https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/parts.php) | Approximately 68m triangular base, legs joining around 50m and circular plan at 315m; circular steel pipes describe member sections. |
| [大林組：3本脚を地上50mで一体化 / Obayashi: joining the three legs at 50m](https://www.obayashi.co.jp/solution_technology/detail/skytree07.html) | Construction diagrams and photographs guide the lower wing/opening appearance. Construction-stage temporary supports are distinct from permanent tower members. |
| [R04 outline, observation facilities and spire reference record](tokyo_skytree_R04.md#sources) | Earlier designer, operator and fabricator sources for retained outline and upper facilities, with model assumptions recorded separately. |
