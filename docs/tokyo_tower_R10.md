# 東京タワー / 东京塔 / Tokyo Tower — LANDMARK-R10

**履歴 / 历史 / Historical record:** このページはR10の全体組立材を記録しています。R11はこれを継承し、メインデッキ下の面格構を修正します。此页保留R10整体组合材说明，当前格网修正见[R11](tokyo_tower_R11.md)。This page records the retained R10 whole assemblies; R11 updates the face grid below the Main Deck.

[日本語](#日本語) · [中文](#中文) · [English](#english) · [出典 / Sources](#sources) · [R09履歴](tokyo_tower_R09.md) · [R08履歴](tokyo_tower_R08.md)

改訂日 / 修改日期 / Revision date: **2026-11-04**。単位 / 单位 / Units: **mm**。

## 日本語

R10は**各主脚と各アーチを一つの全体組立材として表現**します。薄いカバープレート、山形の縁材、綴り板・ラチスを備えた腹面を大きな外包の中で組み合わせ、矩形・三角形の大きな開口を実際の形状として設けます。主脚の内部やアーチの前後・上下に、小さな透空梁を重ねて並べる構成を置き換えます。

これは単一の圧延鋼材という意味ではありません。複数の薄い鋼板・縁材・綴り材からなる**組立材の外観モデル**です。高さ方向やアーチ曲線に沿う分節は全体組立材のモデル上の区分で、実物の製作長、工場継手、現場継手の位置を確定するものではありません。

[R09](tokyo_tower_R09.md)は個々の小部材に板と開口を設けましたが、主脚の4隅やアーチの二面・上下弦という既存の大きな構成を残していました。R10はその大きな構成単位を統合します。遠景の外形だけでなく、塔脚を見上げた際に見える幅広い板面、大きな透空、縁材と接合の関係を修正します。

主脚軸線、アーチの通りと開口、滑らかに収束する上部塔体、展望施設、上部設備、中央コアと外階段は既存のモデル制御を継承します。鋼接合部の識別と部品形状を保持し、宿主への参照を新しい全体組立材へ対応させます。東京スカイツリーR05は別のモデルとして保持します。

**外包の幅・せい、板厚、開口の寸法・割付、縁材、接合は写真に基づく表示用の仮定**です。原設計の部材表や製作図、竣工実測図の復元ではなく、構造計算・耐力評価も行っていません。写真で隠れた面の構成、原建設と後年の補強の境界、個々の接合頭の種類は未確定です。

部品数は固定した過去の数字ではなく、[現行マニフェスト](../output/review/tokyo_tower_manifest.json)の`component_count`を参照してください。名前付き部材を統合するため、R09の総数や変更部材数をR10へ転記しません。内部の板片や開口の数は、名前付き部材数とは別に扱います。

モデルGL125/223.55 mと公式来場者案内150/250 mは引き続き分けて記録します。実測による完成面の換算や、現況設備の機能・放送事業者の割当ては追加しません。

## 中文

R10将**每根主脚、每道拱架作为一套整体组合构件**表达：连续薄盖板、角形边缘、缀板或格构腹面共用整体外包络，形成真实的大开口。沿高度和拱线的分段属于同一整体构件的模型划分，不代表实物制造接缝。

R09虽已为小杆件增加盖板和孔洞，但仍保留主脚四角及拱架前后、上下的小梁层级。R10调整的是这一宏观组合关系，避免把整体主脚与拱架重复建成四根小透空梁。**整体组合材不等于单根轧制钢**，它仍由薄板、边缘材和缀材组成。

主脚轴线、拱洞、平滑上部塔身、展望台、上部设备、核心和外部楼梯继续使用既有控制。钢节点身份和局部形状保留，宿主引用对应到新的整体构件；晴空塔R05保持独立。具名部件数量以[当前清单](../output/review/tokyo_tower_manifest.json)为准，不使用旧R09的总数推断。

宽度、深度、板厚、孔洞尺寸与分格、边缘及接合均为照片引导的演示假设。IHI施工侧资料与Nature Architects现场照片用于形态核对；后者是现场观察，并非原始施工详图。未逐件实测，未进行结构计算或承载验证，隐藏面与原建、补强边界也未完全核定。

## English

R10 represents **each primary leg and each arch as one overall built-up assembly**. Thin continuous cover plates, angle-shaped edges and battened or laced webs share the gross envelope and form large real openings. Segments along the height or arch curve are model divisions of that assembly, not verified fabrication or erection joints.

R09 added plates and holes to smaller members while retaining the four-corner leg cage and paired arch chord layers. R10 changes this overall hierarchy so the primary leg or arch does not become four repeated miniature perforated beams. **One overall assembly does not mean one rolled steel section**: it remains an arrangement of thin plates, edges and connecting members.

Existing leg axes, arch alignment and openings, smooth upper profile, observation facilities, upper equipment, core and outdoor stairs carry forward. Steel-node identities and local geometry remain, with host references mapped to the new assemblies. Skytree R05 remains independent. Named part counts follow `component_count` in the [current manifest](../output/review/tokyo_tower_manifest.json), rather than historical R09 totals. Internal plate pieces and openings are not additional named members.

Envelope width and depth, plate thickness, opening sizes and subdivisions, edges and connections remain photo-guided demonstration assumptions. IHI construction records and Nature Architects site photographs guide appearance; the latter are first-hand observations, not original fabrication drawings. Hidden faces, original-versus-retrofit boundaries and individual fastener types remain unverified. No individual member survey, structural analysis or capacity assessment is included. Model GL125/223.55 m remains separate from official visitor guidance at 150/250 m.

## データと検証範囲 / 数据与验证范围 / Data and validation scope

- [STEP](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb) · [A3 PDF](../output/pdf/tokyo_tower_sheets.pdf)
- [平面DXF / Plan](../DXF/tokyo_tower_plan.dxf) · [立面DXF / Elevation](../DXF/tokyo_tower_elevation.dxf) · [接合部DXF / Steel nodes](../DXF/tokyo_tower_steel_nodes.dxf)
- [Manifest](../output/review/tokyo_tower_manifest.json) · [Drawing provenance](../output/review/tokyo_tower_drawings.json) · [全体組立材ソース / Integrated source](../src/lib/tokyo_tower_integrated.py)

`detail.integrated_lower.enabled`で全体組立材を有効にします。形状の種別は`built_up`を継承し、主脚の分節は`structure:leg_XX_assembly_YY`、アーチは`structure:arch_assembly_side_segment`として識別します。これは編集・参照用の名称で、実施設の製作部材番号ではありません。

公開ゲートは新ソースをモデルと図面のSHA-256束縛へ含め、欠落・改変や古いR09以前の改訂を拒否します。GLB検証では、4組の主脚と4面のアーチが全体組立材の名称・役割を持ち、旧小部材の並列構成が残っていないことを確認します。総数は保存GLBと現行マニフェストの間で照合します。

ブラウザーの回帰対象には、標準UIの「塔脚」視点による全体表示と、TT-N05の接合部近景を含めます。部材を隠して外観を整えることや、スクリーンショットの許容差を広げることは形状確認の代わりにしません。STEP転送量・分割数は公開マニフェストに従い、全分割の順序・ハッシュと復元後のネイティブSHA-256を照合します。整合性検証は実物の形状精度や構造安全性の証明ではありません。

<a id="sources"></a>

## 出典 / 来源 / Sources

Reference review date: **2026-11-04**. Reference photographs are linked for research and are not redistributed in this repository.

| 出典 / Source | 用途と限界 / Use and limits |
| --- | --- |
| [IHI Infra-square: Historical Structure, Tokyo Tower section](https://www.ihi.co.jp/iis/en/gallery/historical_structures/index.html) | 製作側による主柱の現場継手・鋲検査の記録。直前の通天閣に関する鋼材説明を東京タワーへ転用しない。 / Fabricator's account of main-column joints and rivet inspection; preceding Tsutenkaku details are a separate case. |
| [IHI施工近景](https://www.ihi.co.jp/iis/en/gallery/historical_structures/i/img_tokyo-tower2.jpg) · [IHI技報掲載写真](https://www.ihi.co.jp/technology/techinfo/contents_no/__icsFiles/afieldfile/2024/01/25/10.PNG) | 幅広い板面、開いた主脚、横斜材とアーチの全体関係を確認する。同一歴史写真の掲載違いであり、寸法測量や現状断面表ではない。 / One historical photograph in two publications; useful for overall assembly relationships, not measured current sections. |
| [Nature Architects: 散歩しながら考える構造力学２](https://nature-architects.com/blog/1817/) | 形鋼と鉄板からなる組立材と腹面構成の現地観察。原設計図・製作図ではない。 / First-hand observations of built-up members and their webs, not original fabrication drawings. |
| [三角形ラチスの現地近景](https://nature-architects.com/wp-content/uploads/2024/02/Untitled.png) · [矩形綴り板の現地近景](https://nature-architects.com/wp-content/uploads/2024/02/Untitled-1.png) | 板面、縁材、綴り材、大きな透空と局部接合の外観を参考にする。板厚・開口寸法・隠れた面は実測していない。 / Visible plates, edges, openings and connections; no measured thicknesses or hidden-face reconstruction. |
| [宮地技報No.18、印刷p86](https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf) | 全体軸線、アーチ開口、層位の継承に用いる。仮設足場や荷受けステージは恒久部材として扱わない。 / Overall framing and level controls; temporary staging is not permanent structure. |

[R09](tokyo_tower_R09.md)の小部材表現・計数と検証、[R08](tokyo_tower_R08.md)の部材縮小・設備追加、[R07](tokyo_tower_R07.md)の輪郭修正は各時点の履歴です。R09のローカル検証通過は、R10の形状確認や公開反映の証明ではありません。
