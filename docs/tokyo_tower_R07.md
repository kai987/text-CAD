# 東京タワー / 东京塔 / Tokyo Tower — LANDMARK-R07

[日本語](#日本語) · [中文](#中文) · [English](#english) · [出典 / 来源 / Sources](#sources) · [R06 archive](tokyo_tower_R06.md) · [Skytree R05](tokyo_skytree_R05.md)

## 日本語

R07は4組の主脚架構を地上からメインデッキ下まで連続させ、上方へ緩やかに細くする外観に修正します。太い主材と細い腹材を区別し、中間の高さだけで急に断面が変わる表現を解消します。主展望施設以下の既存主脚軸を保持し、追加架構の配置と断面は外観近似として記録します。4面のアーチとフットタウンも修正します。施工立面と実景を参考に、アーチの上下弦材を同じ立面内で分け、その間に三角形の腹材と局部接合を配置します。奥行き方向に並べた同形の曲線だけで表す従来の構成から、立面でせいが見える格構アーチへ変更します。公開立面のH3付近の高さを参照し、詳細曲線、アーチせい、分節数と部材断面は写真に基づくモデル仮定として記録します。

フットタウンは壁・開口・屋根の組合せを写真に合わせて修正します。外周のすべてを同じガラス面にせず、壁面と開口を区別します。建物の平面寸法、外装の割付、壁厚や局部高さは外観の近似で、実施設の平面図や現況寸法を復元するものではありません。

モデルGL130,000–223,550mmの塔体輪郭を、端部の半幅9,900→3,950mmと既存の接線を保つ凸型のべき関数積分ブレンドで近似します。単調に細くし、外側への膨らみを抑え、両端で勾配を連続にします。主材・斜材・二次材・水平リングと特別展望台下面の支持リング・ブラケットも同じ輪郭に追従します。中間断面とその取合いは写真に基づく外観近似です。

R06の展望施設の外殻・床・ガラス・屋根は保持し、特別展望台は直径13mを参考にした48面を継承します。モデルGL223,550mm以上の塔体、別体のH24環状保守床、二組300枚の環状アンテナと塔頂も保持します。主展望施設の27/28m二層外形、600段の外階段、20箇所の鋼接合部、中央コアも継承します。歴史的H23の屋根GL223,550mm、仮定内部床GL220,550mm、公式案内250mの意味は分けて記録します。現来場者床の仕上げ面との換算関係は実測検証していません。

STEP・GLB・編集可能なDXF3枚・A3 PDF3ページは同じ名前付き部品仕様から生成します。CADはmm・Z-up、GLBはm・Y-upです。部品数、パラメーター、出典、ソースと保存物のハッシュは[マニフェスト](../output/review/tokyo_tower_manifest.json)を参照してください。確認対象は形状・接触・名前・図面と保存物の対応で、構造耐力、接合耐力、実測精度や施工適用の認定ではありません。

## 中文

R07将四组主要支腿从地面连续延伸至主展望台下方，随高度平缓收分，区分粗壮主材与较细腹杆，使主受力构架的外观连续。主展望台以下的既有支腿轴线保留，新增格构布置和截面尺寸仍记录为外观拟合。四面塔脚拱架及FootTown也同步修正。参考施工立面和实景，将拱架上下弦杆分开设置在同一立面内，之间配置三角腹杆和局部连接，使拱形骨架具有可见的桁架高度。旧版仅在前后深度方向平移相同曲线的表达被替换。高度参考公开立面H3附近的控制，详细曲线、桁架高度、分段数量和杆件截面均明确记录为照片引导的模型假设。

FootTown调整墙面、开窗和屋顶的组合，区分实体墙与玻璃开口。建筑平面尺寸、外装分格、墙厚及局部高度仍为外观近似，不代表原建筑平面或现况尺寸的复原。

模型GL130,000–223,550mm的塔身轮廓采用凸型幂函数积分切线混合拟合，保留两端9,900→3,950mm的半宽及原有端部切线，使宽度单调减小、没有向外鼓出，并在两端保持一阶导数连续。相关主材、斜撑、次杆、水平环与特别展望台下方支持环及托架同步追随新轮廓。中间截面及连接关系仍为照片引导的外观拟合。

R06的展望台外壳、楼板、玻璃与屋顶保留，特别展望台仍按13m直径参考作48面近似。模型GL223,550mm以上的塔身、独立H24环形维护平台、双组共300片环形天线和塔尖也保持。主台27/28m双层外形、600级外阶梯、20处钢结构节点和中央核心也保留。历史H23屋顶GL223,550mm、假设内部楼板GL220,550mm与官方250m案内高度分别记录，尚未实测核定它们与当前游客楼面完成面的换算关系。

STEP、GLB、三张可编辑DXF与三页A3 PDF由共同的命名部件规格生成。CAD采用mm、Z-up，GLB采用m、Y-up。具名部件数量、参数、来源及源文件和保存资产哈希见[清单](../output/review/tokyo_tower_manifest.json)。验证覆盖形状、接触、命名以及图纸与保存资产的对应，不构成结构、节点承载力或实测与施工适用性的认证。

## English

R07 carries the four primary leg assemblies continuously from ground to beneath the Main Deck, with gradual taper and a hierarchy of broad primary members and finer braces. Existing model lower-leg axes remain; added framing positions and section sizes are appearance fits. The four lower arch frames and the appearance of FootTown are also revised. Construction elevations and photographs guide separate arch chords within each elevation plane, with triangular webs and local connections between them. The arches now have visible truss depth in elevation, replacing the previous pair of identical curves offset only front-to-back. The published H3 vicinity guides the height control; detailed curves, arch depth, subdivisions and member sections remain explicitly recorded photo-guided model assumptions.

FootTown combines opaque wall areas, glazed openings and roof treatment informed by photographs. Plan dimensions, facade divisions, wall thicknesses and local levels remain appearance approximations rather than recovered original plans or surveyed present dimensions.

The model GL130,000–223,550 mm shaft uses a convex integrated power tangent blend. It retains endpoint half-widths of 9,900→3,950 mm and the existing endpoint tangents, narrows monotonically without an outward bulge, and joins the reference with continuous first derivatives. Main chords, braces, secondary members, horizontal rings and the special deck’s lower support rings and brackets follow the same fitted outline. Intermediate sections and their attachments are photo-guided appearance approximations.

R06 observation-deck outer envelopes, floor slabs, glazing and roofs remain, including the 48-facet special deck informed by a 13 m diameter. The frame at and above model GL223,550 mm, independent H24 annular service platform, twin circular arrays totalling 300 panels and the tower tip also remain. The 27/28 m two-storey Main Deck, 600-rise external staircase, 20 steel nodes and central core also remain. Historical H23 roof GL223,550 mm, assumed internal floor GL220,550 mm and official 250 m visitor guidance remain distinct; no measured conversion to the present finished visitor floor is established.

STEP, GLB, three editable DXFs and a three-page A3 PDF use the same named-part specification. CAD uses mm/Z-up; GLB uses m/Y-up. The [manifest](../output/review/tokyo_tower_manifest.json) records part counts, parameters, references, source hashes and saved-asset hashes. Checks cover geometry, contact, naming and drawing/saved-model correspondence, without certifying structural or connection capacity, surveyed accuracy or construction suitability.

## パラメーター / 参数 / Parameters

単位 / 单位 / Units: **mm**. Fitted controls are under `detail.base_appearance` and `detail.upper_shaft_outline`; the existing arch and roof height controls are listed separately. The historic H3 control is distinct from the fitted section and building dimensions.

| Parameter | Value | 区分 / 范围 / Scope |
| --- | --- | --- |
| `leg_cage_transition_start_mm` / `leg_cage_top_mm` | 80,000 / 125,000 | 既存主脚を連続延長するモデル高さ / 既有主腿连续延伸的模型高度 / Model transition and termination levels, with the top inside the Main Deck. |
| `leg_continuation_chord_half_width_mm` | 262.5 | H形外観の全幅525を維持 / 保持H形外观全宽525 / Retains a fitted 525-wide appearance section across the former cutoff. |
| `leg_cage_top_half_width_mm` | 450 | 80,000で1,000から上端450へ緩やかに縮小 / 80,000处1,000平缓收至顶端450 / Fitted assembly half-width tapers smoothly from 1,000 to 450; not a surveyed section schedule. |
| `detail.upper_shaft_outline` | GL130,000–223,550; half-width 9,900→3,950 | 凸型べき関数積分ブレンド・両端C1接続 / 凸型幂函数积分切线混合、端部C1连续 / Convex integrated power tangent blend; retained endpoints and tangents, fitted intermediate sections. |
| `detail.arch_crown_mm` | 40,000 | H3付近の歴史的立面制御 / 历史H3附近立面控制 / Historical H3 vicinity reference for the outer arch axis. |
| `arch_rib_depth_mm` | 1,800 | 立面内の弦材軸間の近似 / 立面内弦杆轴间距假设 / Fitted in-plane chord separation; the inner crown axis is 38,200. |
| `arch_plane_half_depth_mm` | 650 | 二つのアーチ面の軸間1,300 / 两拱架平面轴间1,300 / Fitted arch planes at ±650, not the overall steel envelope. |
| `arch_profile_width_mm` / `arch_profile_depth_mm` | 450 / 600 | H形外観の近似 / H形外观截面假设 / Fitted H-like appearance section; web 20 and flange 24 are also assumptions. |
| `foot_town_width_mm` / `foot_town_depth_mm` | 48,000 / 44,000 | 建物平面の近似 / 建筑平面拟合 / Fitted building plan, not dimensions derived from a published project area. |
| `foot_town_floor_levels_mm` | 0 / 3,600 / 7,200 / 10,800 / 14,400 / 18,300 | 外観分節用の仮定 / 外观分段假设 / Five model facade bands; no mapping to public floor names or recovered internal floors is asserted. |
| `detail.foot_town_roof_mm` | 18,300 | 従来のモデル屋根高さを保持 / 保留既有模型屋顶高度 / Retained model roof-height assumption. |

## ファイル / 文件 / Files

- [STEP](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb)
- [平面 / 平面 / Plan DXF](../DXF/tokyo_tower_plan.dxf) · [立面 / 立面 / Elevation DXF](../DXF/tokyo_tower_elevation.dxf) · [接合部 / 节点 / Steel-node DXF](../DXF/tokyo_tower_steel_nodes.dxf)
- [A3 PDF](../output/pdf/tokyo_tower_sheets.pdf) · [パラメーター・出典 / 参数与来源 / Parameters and sources](../output/review/tokyo_tower_manifest.json)
- [形状・部品 / 形状与部件 / Geometry and components](../src/lib/tokyo_tower_detail.py) · [共通制御 / 共同控制 / Shared controls](../src/lib/tower_geometry.py) · [鋼部材・接合 / 钢材与节点 / Steel sections and nodes](../src/lib/tokyo_tower_steel.py)
- [出版検証 / 出版验证 / Publication validation](../web/scripts/tower-artifact-validation.mjs) · [保存物の検証 / 保存资产验证 / Saved-asset validation](../checks/validate_towers.py)

<a id="sources"></a>

## 出典 / 来源 / Sources

確認日 / 核查日期 / Checked: 2026-11-01. Published controls and photo-guided details are distinguished above. Reference photographs and scanned source-paper pages are inspected for research and are not redistributed in this repository.

| 資料 / 资料 / Source | 範囲 / 范围 / Scope |
| --- | --- |
| [宮地技報 No18, printed p86 / Miyaji construction elevation](https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf) | Historical elevation bands and the lower arch-truss character. Unlabelled intermediate curves and member sections are model fits. |
| [IHI technical history / 東京タワーの建設](https://www.ihi.co.jp/technology/techinfo/contents_no/1200541_13491.html) | Construction photograph showing broad arch chords and triangulated web members; it does not provide a complete member-section schedule. |
| [竹中工務店 東京タワー改修 / Takenaka renovation photographs](https://www.takenaka.co.jp/solution/asset/project/07/) | FootTown wall, glazing and roof appearance. Published project area is not treated as the building's measured plan dimensions. |
| [東京タワー公式 Towerpedia / Operator reference photographs](https://www.tokyotower.co.jp/plan/towerpedia/) | Exterior framing and the distinction between the closed special deck, open service platform and upper antenna equipment. |
| [東京タワー フットタウン / Official FootTown guide](https://www.tokyotower.co.jp/foottown/) | Public building use and appearance references; no original architectural plan is reproduced. |
| [R06 upper-deck and antenna source record](tokyo_tower_R06.md#sources) | Retained historical H23, 48-facet exterior, separate H24 platform and supplier-dimensioned twin circular antenna arrays. |
