# 東京タワー / 东京塔 / Tokyo Tower — LANDMARK-R08

[日本語](#日本語) · [中文](#中文) · [English](#english) · [Sources](#sources) · [R07 archive](tokyo_tower_R07.md) · [Skytree R05](tokyo_skytree_R05.md)

## 日本語

R08は塔脚の主材・アーチ・細い腹材の太さを見直し、メインデッキとトップデッキの間に外側へ張り出すブラケット、小さな保守床、円形カバーを追加します。運営者の外観写真を参照した形状の調整であり、公開されていない実物の部材断面・設備位置を復元したものではありません。

4組の主脚の中心線、節点、組柱の軸間、地上からモデルGL125 mまでの連続性を保持します。そのまま主脚H/I形外観の幅・せいをR07の70%にし、細い腹材を別の寸法で細くします。アーチはH形の外観断面320×420 mm・ウェブ16 mm・フランジ20 mmへ変更します。アーチ頂部のモデルGL40 m、上下弦軸間1,800 mm、前後の二面±650 mmは保持します。これらの断面寸法は**写真に合わせたモデル仮定**で、実際の部材表や耐力計算の結果ではありません。

上部の張り出しは塔身そのものの輪郭を膨らませず、`structure:upper_equipment_...`という別名の部品として表します。四隅の持出しブラケットを4段、小さな保守床と手すり、3つの閉じた円形カバーを配置します。円形カバーは実測した放物面反射器ではありません。取付位置・向き・張出し量はこのモデルのGL座標における外観近似です。写真の撮影日と現在の設備配置は未確認で、放送事業者・チャンネル・周波数や現在の運用機能は割り当てません。

R07の滑らかに細くなる上部塔身、展望施設の外装・床・ガラス・屋根、H24の環状保守床、上方アンテナ、中央コアと600段の外階段は保持します。20か所の鋼接合部は名称と分類を継承し、細くなった宿主主材に付くTT-N05〜TT-N16の接合板・鋲だけが実際の表面に追従します。TT-N01〜TT-N04の基部接合部、TT-N17〜TT-N20の展望台支持接合部は保持します。東京スカイツリーR05の形状・パラメーターは変更しません。

## 中文

R08缩细塔脚主材、拱架与腹杆，并在主展望台和特别展望台之间补充向外伸出的支架、小型维护平台和圆形罩体。参考的是运营方的外观照片，不是原始钢结构施工图或现状设备清单。

四组主腿的中心线、节点、组合柱轴距与地面至模型GL125 m的连续关系保持。主腿H/I形外观的宽度和截面高度改为R07的70%，细腹杆另行缩细。拱架采用320×420 mm的H形外观、腹板16 mm、翼缘20 mm；模型GL40 m拱顶、上下弦轴距1,800 mm和前后两片拱架的±650 mm位置保持。上述截面仍是**照片引导的演示假设**，不代表实测尺寸或结构选型结果。

上部新增构件使用独立名称`structure:upper_equipment_...`，不把既有平滑塔身轮廓重新向外鼓出。构件包括四段外挑支架、一圈窄维护平台及栏杆、3个封闭圆形罩体。罩体不声称是按实测抛物线恢复的反射器。安装高度、方向、外挑长度均按当前模型GL坐标拟合；照片拍摄日期、当前设备清单及具体用途未核定，不标注广播公司、频道或频率。

保留R07上部塔身、展望台外壳、楼板、玻璃与屋顶、H24维护平台、顶部天线、核心及600级外部楼梯。20处钢节点保留命名和分类，其中TT-N05〜TT-N16的接合板与铆钉随变细后的宿主表面移动；基部TT-N01〜TT-N04及展望台支承TT-N17〜TT-N20保持。晴空塔R05的参数和形状保持不变。

## English

R08 reduces the visual weight of the lower primary framing, arch ribs and finer lacing, and adds separate outboard brackets, small service surfaces and circular covers between the Main Deck and Top Deck. These are operator-photo-guided appearance changes, not recovered fabrication drawings or a verified current equipment inventory.

The four leg assemblies retain their centre lines, stations, cage-axis spacing and continuity from ground to the model GL125 m junction. H/I appearance widths and depths become 70% of R07; lacing has separate reduced sections. Arch ribs use a fitted 320×420 mm H-like profile with a 16 mm web and 20 mm flanges. The model GL40 m crown, 1,800 mm chord-axis separation and ±650 mm arch planes remain. These section sizes are **appearance assumptions**, not surveyed dimensions or structurally selected members.

The smooth main-shaft outline remains unchanged. New parts use `structure:upper_equipment_...` names: four corner-bracket tiers, a narrow service gallery and guards, and three closed circular covers. The covers do not claim a measured parabolic reflector shape. Installation heights, directions and projections are fits in the existing model GL datum. The photograph date and present inventory remain unverified; no broadcaster, channel, frequency or current operating function is assigned.

R07 deck shells, floors, glazing and roofs, the H24 annular service platform, antenna above the Top Deck, core and 600-step outdoor route remain. The 20 steel-node identities and types are retained; only TT-N05–TT-N16 plates/rivets follow their smaller actual host sections. Base nodes TT-N01–TT-N04 and deck-support nodes TT-N17–TT-N20 remain. Skytree R05 parameters and geometry are unchanged.

## パラメーター / 参数 / Parameters

Units: **mm**. All new section and equipment values below are photo-guided modelling assumptions.

| Control | R08 value | Scope |
| --- | --- | --- |
| Primary-leg section width/depth | R07 × 0.70 | Fitted section reduction; existing axes and frame stations stay fixed. |
| Arch H-like profile | 320 × 420; web16, flange20 | Fitted rib profile; not an original section schedule. |
| Leg lacing / ties | radius95 / radius110 | Separate fine-member hierarchy. |
| Arch diagonal / in-plane tie / transverse tie | radius60 / radius48 / radius55 | Fitted members between retained chord axes. |
| Spandrel ties / diagonals | radius90 / radius75 | The original crown bridge and anchors remain. |
| Corner-bracket tiers, model GL | 158,000 / 166,000 / 174,000 / 182,000 | Internal model levels; not surveyed installation elevations. |
| Corner-tip additional X/Y half-width | 2,600 / 3,000 / 3,200 / 2,800 | Per-axis outward extension; not a measured radial projection. |
| Gallery model GL / outward width | 182,000 / 650 | Fitted narrow service surface and guards. |
| Circular-cover centres, model GL | 146,000 / 200,000 / 209,000 | Three photo-guided examples; directions are assumed. |
| Circular-cover diameters | 1,600 / 1,700 / 1,400 | Closed shallow covers; internal equipment is not reconstructed. |
| Direct-mount inward lap | 180 | Display geometry connects positively to real named host chords. |

The model GL reference is distinct from the official visitor guidance heights 150/250 m. R08 does not establish a measured conversion between them.

## 保存・検証 / 保存与验证 / Saved outputs and checks

- [STEP](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb) · [A3 PDF](../output/pdf/tokyo_tower_sheets.pdf)
- [Plan DXF](../DXF/tokyo_tower_plan.dxf) · [Elevation DXF](../DXF/tokyo_tower_elevation.dxf) · [Steel-node DXF](../DXF/tokyo_tower_steel_nodes.dxf)
- [Manifest](../output/review/tokyo_tower_manifest.json) · [New equipment source](../src/lib/tokyo_tower_equipment.py) · [R08 checks](../checks/test_tokyo_tower_r08.py)

The 6,374 existing names are retained and 111 separately named fittings are added, for 6,485 parts. The frozen pre-edit R07 reference is commit `fa20614b5b4ceb3d37b0e60f08ae2c553c04b90c`. Checks protect 4,814 unchanged specifications exactly, preserve the axes/local bases of 1,384 resized frame parts, and constrain the identities of 176 surface-following steel-node parts. The complete R07 replay, all 7,649 Skytree specifications and its parameters have independent fixed hashes. Numeric fingerprints use a 10 nm grid only to remove machine-level floating-point tails; names, roles, colour and metadata stay exact.

Native checks cover positive-volume contact for all 42 direct mounts and the three circular-cover supports. STEP, GLB and editable drawings derive from the same named component specification. Geometry/contact and saved-file consistency checks do not establish measured accuracy, structural capacity, equipment operation or construction suitability.

<a id="sources"></a>

## 出典 / 来源 / Sources

Reference review date: **2026-11-03**. Reference photographs are inspected for research and are not redistributed in this repository.

| Source | Use and limits |
| --- | --- |
| [Tokyo Tower operator: Towerpedia](https://www.tokyotower.co.jp/plan/towerpedia/) | Exterior framing hierarchy and visible outboard equipment. No complete original member schedule or dated current equipment inventory is provided. |
| [Operator reference photograph, img_006.jpg](https://www.tokyotower.co.jp/plan/towerpedia/img/img_006.jpg) | Bracket, gallery and circular-cover appearance. Elevations, projections, directions and sections in this model are photo fits. |
| [Miyaji Technical Reports No18, printed p86](https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf) | Retained historical construction controls; this is not a source for the new fitted equipment dimensions. |
| [R07 reference record](tokyo_tower_R07.md#sources) | Existing smooth-shaft fit, arch geometry, FootTown and retained height conventions. |
