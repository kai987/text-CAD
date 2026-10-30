# 東京スカイツリー / 东京晴空塔 / Tokyo Skytree — LANDMARK-R04

> R04 履歴 / 历史存档 / Historical archive — 現行の円管外周・塔脚格構 / 当前圆管外周与塔脚格构 / Current circular exterior and base framing: [LANDMARK-R05](tokyo_skytree_R05.md).

[日本語](#日本語) · [中文](#中文) · [English](#english) · [出典 / 来源 / Sources](#sources) · [R03 archive](tokyo_skytree_R03.md) · [Tokyo Tower R06](tokyo_tower_R06.md)

## 日本語

R04は、塔体の輪郭、二つの展望施設、ゲイン塔の外観を、設計者・事業者・製作施工者の公開資料に照合して修正します。現在のソース仕様は7,469個の名前付き部品を定義します。東京タワーは独立したR06です。本モデルは本プロジェクトによる参考外観モデルであり、実施設の原設計CAD、実測・竣工図、施工図、構造的に認定された複製ではありません。

**輪郭。** 地上の一辺約68mの正三角形、高さ315mの直径約32m、高さ495mの直径約18mを制御値とします。315m以上は直線的な円錐で、497mの塔体終端まで延長します。下部では角の「そり」と辺中央の「むくり」を独立した円弧とし、315mで同じ円錐の接線へ接続します。辺中央は低層で一度わずかに外へ膨らみます。三角形の各辺8等分と円周の15度刻みを対応させた24点のうち、中間点は二つの主円弧を満たす断面補間です。すべての原設計三次元曲線を復元したものではありません。丸められた制御寸法から求めたモデル円弧半径は約4,534m・5,761mで、設計者が記した「そり4,520m・むくり最大5,950m」と分けて記録します。

**架構。** 三組・各四柱の鼎トラス、約50mの下部接続、実際に孔を持つ円管・角管、鋼製中塔と独立したRC心柱を継承します。24本の外周ガイド軸を12辺形の中点へ引き込む処理をやめ、輪郭と実際の弦軸を一致させます。水平材の12.5/10/7.5mという順序と315m以上の5mピッチは設計者資料に従いますが、下部の切替高さ150/250mはモデル仮定です。25mの水平連結、断面割付、リングの奥行きやウェブ省略、柱組寸法、接合・基礎は選択的な外観表現です。主弦は直線区間を接続し、長い管の水平円環断面は近似です。RC心柱の公表外径8m・高さ375mと、天望デッキ屋上の高さ375mは別の要素です。制振応答や構造耐力は計算しません。

**天望デッキ。** 公開の340/345/350mの三階を保持し、350mの平面直径約47mと71度の外向きガラス勾配を参照します。335m付近の低いサービス用ガラス帯は第四の一般展望階ではありません。上部には不透明な設備帯と頂冠を加え、事業者が公表する屋上375mまで外形を表します。モデルの設備帯は355–371m付近で最大直径約58m、頂冠は371–375mです。これらの中間標高・半径、371mのモデル屋根、板厚・窓割りは写真に基づく仮定です。2010年の設計チーム解説にある上口最大直径約60mは建設中の参考記述であり、現在の実測寸法表とは扱いません。約47mは350m床の制御値で、設備外形の最大径ではありません。

**天望回廊。** 445mから450mへ上がる連続した外周スロープと、別の上部傾斜路を経て451.2mへ至るモデル経路を設けます。設計者の延長114mと外装パネル施工者の約110mを別々に記録し、通路幅約2.4m・外形直径約40mも施工者の概数として参照します。外側に広がる本体へガラスのチューブを付ける形とし、旧版の半径12.85m・幅1.8m・固定一周経路を置き換えます。モデルは114mを経路生成の制御値に用いますが、方位、周回角、断面半径、チューブの膨らみ、追加した上部経路は外観仮定です。二つの資料の差を解消した実測動線とは主張しません。

**ゲイン塔と塔頂。** 一般部外径約6mの六柱格構、段階的なアンテナ外装と保守帯、一般部より太い二層のTMD機械室、全高634mへ至る避雷針を分けます。497mの塔体終端と634mの先端は施工者資料によります。モデルのアンテナ区間、足場位置、TMDの620/626/632.5mの区切り、半径4.2m・張出し4.6mは写真を参照した仮定です。TMD内部機構・実際の設備配置・動的性能は再現しません。青白い局所照明と灯具位置も表示用の例です。

**ファイルと確認範囲。** STEP・GLB・平面/立面/構成DXF・三ページA3 PDFは共通部品仕様から生成します。CADはmm・Z-up、GLBはm・Y-up、GL0を塔高の起点とし、地下の模式基礎を塔高に算入しません。名前付き部品数7,469は現在のソース仕様の計数で、保存物の実際の改訂・ハッシュは下記マニフェストで確認します。検証は輪郭の端点・接線・凸性、部品の接続、空洞、図面編集性、保存物とソースの対応を対象とし、実建築への精度認定やオンライン公開完了を意味しません。資料写真は一時的な調査にのみ使い、このリポジトリには再配布しません。

Web表示は不透明な塔架・心柱だけを高さ帯ごとに合成し、元の名前付き部品・カメラ境界・照明・ダウンロード用STEP/GLBを保持します。操作を止めると描画も休止します。

## 中文

R04根据设计者、运营方及制造施工方的公开资料，修正塔身轮廓、两座展望设施和顶部增益塔的外观。当前源规格定义7,469个具名部件；东京塔为独立的R06。本模型是本项目原创的参考外观模型，不是原建筑CAD、实测或竣工图、施工图，也不构成经过结构核定的复原件。

**轮廓。** 采用地面边长约68m的正三角形、315m处直径约32m、495m处直径约18m三个控制截面。315m以上为直线圆锥，并延伸至497m塔身终点；下部角线的「そり」与边中线的「むくり」分别采用圆弧，在315m处与同一圆锥相切。边中线在低处先轻微外鼓。底部三角形每边八等分，与圆周每15度一点对应，得到24点；其中间点采用满足两条主圆弧的截面插值，不是原设计全部三维曲线的复原。由公开圆整控制尺寸拟合的模型圆弧半径约4,534m、5,761m，与设计者记载的「そり4,520m、むくり最大5,950m」分别记录。

**杆系。** 保留三组、每组四柱的鼎桁架、约50m的下部连接、实际中空的圆管与方管、钢制中塔以及独立RC心柱。24条外周导向轴不再被拉到十二边形边中点，轮廓与实际主弦轴一致。水平材12.5/10/7.5m的变化顺序和315m以上5m间距来自设计者资料；下部150/250m的切换标高是模型假设。25m水平连接、杆件截面分配、环深与部分腹杆省略、柱组尺寸、节点和基础仍为选择性外观表达。主弦按直节连接，长管采用水平圆环截面的近似。公开外径8m、高375m的RC心柱，与375m的天望甲板屋顶是两个不同构件，不模拟其制振响应或承载能力。

**天望甲板。** 保持340/345/350m三层，以350m平面直径约47m和玻璃向外倾斜71度为参考；335m附近的低位服务玻璃带不表示第四层公众展望层。上部补充不透明设备带和顶冠，外形延至运营方公开的375m屋顶高度。模型设备带约位于355–371m，最大直径约58m；顶冠位于371–375m。这些中间标高、半径、371m模型屋面、板厚和玻璃分格均为实景拟合。2010年设计团队解说的上口最大直径约60m属于施工期间的早期参考，不能当作当前实测尺寸表。约47m对应350m楼层，不是设备外壳的最大直径。

**天望回廊。** 设置445m至450m的连续外周坡道，并通过单独的上层斜坡到达451.2m。设计者记述的114m与外装板施工方的约110m分别保留；通道宽约2.4m、外形直径约40m也按施工方的概数记录。玻璃管廊附着在向上外扩的主体上，取代旧版半径12.85m、宽1.8m、固定一周的路线。模型以114m作为生成路径的控制值；朝向、周回角、断面半径、管廊鼓形和附加的上层路线仍为外观假设，不声称已解决不同资料口径或复原实测游览动线。

**增益塔与塔尖。** 分别表达一般部外径约6m的六柱格构、分段天线外壳与维护带、比一般段更宽的两层TMD机械室，以及达到634m的避雷杆。497m塔身终点和634m尖端来自施工者资料。模型天线区间、平台位置、TMD的620/626/632.5m分层、4.2m半径与4.6m挑缘是照片引导的假设，不复原TMD内部机构、真实设备布置或动力性能。局部青白灯光和灯位同样只是显示示例。

**文件与验收范围。** STEP、GLB、平面/立面/结构组成DXF与三页A3 PDF由共同部件规格生成。CAD采用mm、Z-up；GLB采用m、Y-up；塔高从模型GL0起算，不计地下示意基础。7,469是当前源规格的具名部件计数，保存资产的实际版本与哈希以下方清单为准。验证覆盖轮廓端点、切线、凸性、构件连接、内部空腔、图纸可编辑性及源文件与保存资产的对应，不表示实物精度核定或线上发布完成。参考照片仅作临时研究，不随仓库再分发。

网页仅将不透明塔架和心柱按高度带合并绘制，保留原具名部件、视角边界、照明以及下载用STEP/GLB；停止操作后停止重绘。

## English

R04 revises the body silhouette, both observation facilities and the gain tower using publications by the designer, operator and fabricators/builders. The current source specification defines 7,469 named parts; Tokyo Tower is a separate R06 model. This is an original reference appearance study, not original building CAD, a survey or as-built record, construction documentation, or a structurally certified replica.

**Outline.** Controls are an approximately 68m-sided ground triangle, a circle approximately 32m in diameter at 315m, and one approximately 18m in diameter at 495m. A straight cone above 315m extends to the 497m body interface. Separate circular guides describe corner sori and face-midpoint mukuri below 315m, tangent to the same cone. The face midpoint first bulges slightly outward. Eight equal intervals on each triangular edge correspond to 15-degree intervals on the circle, giving 24 points. Intermediate points use a section blend satisfying the two principal arcs; the full original three-dimensional guide construction is not recovered. The rounded controls give fitted model radii of approximately 4,534m and 5,761m, recorded separately from the designer's published 4,520m sori and maximum 5,950m mukuri radii.

**Frame.** Three four-column kanae groups, the approximately 50m lower joining interval, actual hollow circular/rectangular sections, a steel middle tower and an independent concrete core are retained. The 24 perimeter guide axes are no longer pulled inward to twelve-sided edge midpoints. The designer documents lower horizontal pitches of 12.5/10/7.5m and 5m above 315m; the model's lower switches at 150/250m are assumptions. The 25m horizontal links, member assignments, ring depth, selected omitted webs, group dimensions, joints and foundations remain selective appearance geometry. Main chords connect straight intervals, with horizontal annular sections approximating long tubes. The published 8m-diameter, 375m-high concrete core and the 375m Tembo Deck rooftop are distinct elements. Damping response and load capacity are not simulated.

**Tembo Deck.** The 340/345/350m public floors remain, guided by an approximately 47m diameter at 350m and 71-degree outward glazing. A low service glazing strip around 335m does not represent a fourth public observation floor. Opaque equipment bands and a crown extend the envelope to the operator's published 375m rooftop. The model's equipment shell occupies approximately 355–371m with a maximum diameter near 58m; its crown occupies 371–375m. These intermediate elevations, radii, the model roof at 371m, thicknesses and glazing divisions are image-based estimates. The design team's approximately 60m upper-mouth description from 2010 is an early construction-stage reference, not a current as-built dimension schedule. The approximately 47m control applies at the 350m floor, not to the maximum equipment envelope.

**Tembo Galleria.** A continuous outer ramp rises from 445m to 450m, followed by a separate upper incline to 451.2m. The designer's 114m length and the external-panel contractor's approximately 110m account remain separate; the contractor also reports an approximately 2.4m passage width and 40m diameter. A glass tube follows an outward-flaring body, replacing the old fixed one-turn route with a 12.85m radius and 1.8m width. The model uses 114m as a route-generation control. Azimuth, angular span, section radii, tube bulge and the additional upper route remain appearance assumptions; no exact surveyed visitor route or reconciliation of the two source accounts is asserted.

**Gain tower and tip.** The approximately 6m external-diameter six-chord general frame, segmented antenna enclosures, maintenance bands, wider two-storey TMD machine room and lightning rod reaching 634m are separate components. The 497m body interface and 634m tip follow builder references. Antenna-bank bounds, platform positions, the model's 620/626/632.5m TMD tiers, 4.2m radius and 4.6m flange radius are photo-guided assumptions. The internal TMD mechanism, actual equipment schedule and dynamic performance are not reconstructed. Local cool lighting and fixture locations are display examples.

**Files and acceptance scope.** STEP, GLB, plan/elevation/frame DXFs and a three-page A3 PDF derive from the same component specification. CAD uses mm/Z-up; GLB uses m/Y-up. Tower height starts at model GL0 and excludes illustrative underground foundations. The 7,469 count describes the current source specification; consult the manifest below for saved-asset revisions and hashes. Checks cover outline endpoints, tangency and convexity, attachments, bores, drawing editability and source-to-asset correspondence. They do not certify real-building accuracy or establish that an online release has completed. Reference photographs are inspected temporarily and are not redistributed in this repository.

The web viewer batches only opaque frame/core display geometry by height band. Original named parts, camera bounds, lighting and downloadable STEP/GLB remain authoritative; rendering returns to idle after interaction.

## ファイル / 文件 / Files

- [STEP](../STEP/tokyo_skytree.step) · [GLB](../GLB/tokyo_skytree.glb)
- [平面 / 平面 / Plan DXF](../DXF/tokyo_skytree_plan.dxf) · [立面 / 立面 / Elevation DXF](../DXF/tokyo_skytree_elevation.dxf) · [構成 / 组成 / Frame DXF](../DXF/tokyo_skytree_structure_zones.dxf)
- [A3 PDF](../output/pdf/tokyo_skytree_sheets.pdf) · [保存パラメーターと出典 / 保存参数与来源 / Saved parameters and sources](../output/review/tokyo_skytree_manifest.json)
- [輪郭 / 轮廓 / Outline](../src/lib/skytree_outline.py) · [架構・展望台・塔頂 / 杆系、展望台、顶部 / Frame, decks and spire](../src/lib/skytree_detail.py) · [共通仕様 / 共同规格 / Shared specification](../src/lib/tower_geometry.py)
- [表示合成 / 显示合批 / Display batching](../web/src/skytree-opaque-batches.ts) · [Behavior tests](../web/tests/skytree-opaque-batches.test.mjs)
- [再生成パイプライン / 重建流程 / Regeneration pipeline](../src/cad_pipeline.py) · [保存物の検証 / 保存资产验证 / Saved-asset validation](../checks/validate_towers.py)

<a id="sources"></a>

## 出典 / 来源 / Sources

確認日 / 核查日期 / Checked: 2026-10-30. Public reference controls and model assumptions are recorded separately above.

| 資料 / 资料 / Source | 参照箇所と範囲 / 位置与范围 / Location and scope |
| --- | --- |
| [日建設計 NIKKEN JOURNAL 12, 2012 Autumn](https://www.nikken.co.jp/ja/insights/publication/journal_archive/p4iusj0000001hyd-att/Journal-2012_Autumn.pdf) | Printed pp10–11: deck plan/section and 71° facade; pp12–13: gallery plan and 114m length; pp14–15: 6m gain tower; pp16–17, Figs1–4: 68m triangle, 315m/32m and 495m/18m controls, tangent arcs, 24-point correspondence and straight pipe segments. PDF pp6–9 contain these four spreads. |
| [土屋哲夫 / Tetsuo Tsuchiya, Design of TOKYO SKYTREE TOWN, 2012](https://www.jstage.jst.go.jp/article/ieiej/32/10/32_721/_pdf/-char/en) | Printed p722/PDF p2: approximately 47m floor350 and outward glazing. Printed p723/PDF p3: principal arcs, 24 section vertices and 12.5/10/7.5m lower pitches with 5m above315m. Lower switching elevations are not supplied. |
| [事業者 / 运营方 / Operator, 2024-10-15 rooftop announcement](https://www.tokyo-skytree.jp/pdf/pressreleases/02fc6924e036215dc33870cb108fdea823153520240310.pdf) | PDF p1 identifies the Tembo Deck rooftop at375m. This is separate from the three usual public floors. |
| [宮越工芸 / Miyakoshi Kogei, gallery exterior panels](https://www.miyakoshikogei.co.jp/works/81/) | Fabrication comments: approximately40m diameter,110m length and2.4m passage width; retained independently of the designer's114m account. |
| [大林組 / Obayashi, gain-tower head construction](https://www.obayashi.co.jp/solution_technology/detail/skytree23.html) · [Gain-tower lift-up](https://www.obayashi.co.jp/solution_technology/detail/skytree22.html) | Approximately6m general frame, wider two-storey TMD head,497m body interface and634m lightning-rod tip; construction and equipment photographs guide appearance estimates. |
| [設計チーム解説 / 设计团队解说 / Design-team commentary, 2010-09-28](https://www.1101.com/skytree/2010-09-28.html) | The approximately60m maximum upper-mouth diameter is an early construction-stage account, not an as-built measurement schedule. |
| [公式構造 / 官方结构 / Operator structure](https://www.tokyo-skytree.jp/about/spec/structure/) · [Parts and design](https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/parts.php) | Four-column kanae groups, approximately50m lower joining, direct pipe branching and published base-member maximum2300mm diameter/100mm wall. |
| [巴コーポレーション / Tomoe fabrication outline](https://www.tomoe-corporation.co.jp/steel-tower/works/skytree/outline.html) | Published section-family ranges; individual member assignments remain model assumptions. |
| [公式フロア / 官方楼层 / Operator floors](https://www.tokyo-skytree.jp/floor/) · [Tembo Galleria](https://www.tokyo-skytree.jp/floor/tembogalleria/) · [Core/body](https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/body.php) | Public340/345/350m and445/450m floors,451.2m highest public point,8m/375m concrete core; no original construction geometry is reproduced. |
