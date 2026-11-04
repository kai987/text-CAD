# 東京タワー / 东京塔 / Tokyo Tower — LANDMARK-R11

[日本語](#日本語) · [中文](#中文) · [English](#english) · [出典 / Sources](#sources) · [R10履歴](tokyo_tower_R10.md)

改訂日 / 修改日期 / Revision date: **2026-11-04**。単位 / 单位 / Units: **mm**。

## 日本語

R11はメインデッキ下の**モデルGL80–120 mの面格構**を、下方GL40–80 mと同じ4列の格構につなぎます。旧来の面全体にまたがる大きなX材と密な短い水平材を、区画ごとの交差斜材・鉛直材・帯材へ置き換え、80 m境界で列の節点をそろえます。

新しい格構はモデル80/93/106/120 mに割り付け、下方の40/53/66/80 m格構から連続させます。格構端部は短い連結材でR10主脚の実際の板面に取り付きます。114 m付近の必要な接合部支持は、面全体を横切る旧帯材の代わりに独立した短い支持材として残します。これらの高さはモデル上の制御値で、来場者用フロアを示すものではありません。

R10の主脚・アーチの全体組立材、実際の開口、上部の滑らかな輪郭、展望施設、上部設備、中央コア、外階段を継承します。鋼接合部の識別と局部形状も保持し、関連する宿主参照を実在する新しい連結材へ対応させます。東京スカイツリーR05は変更しません。

**格子間隔、幅、板厚、開口寸法、部材断面と接合は表示用の仮定**です。4列への連続は本モデルの外観修正であり、実物の全構面を採寸して製作図どおりに再現したという意味ではありません。構造計算・耐力評価は行っていません。モデルGL125/223.55 mと公式案内150/250 mは引き続き別記します。

部品数は[現行マニフェスト](../output/review/tokyo_tower_manifest.json)の`component_count`を参照してください。R10の総数を引き継いだり、内部の板片を名前付き部材数へ加算したりしません。[R10](tokyo_tower_R10.md)以前の数値・説明は各時点の履歴です。

### 80 m接続部の確認

東京タワーの3D画面で「**80 m 格構の接続部**」を選ぶと、80 m境界の上下各2帯を含む正面近景になります。下方は実際の53–80 m部材、新設側は80–106 m部材の包囲範囲から画角を合わせます。モデル内の部材を隠したり切断したりせず、4列の対応、80 mの接続、周囲の部材を同じ条件で確認できます。標準の正面・塔脚・展望台・鋼接合部の視点も引き続き使用できます。

## 中文

R11将主展望台下方**模型GL80–120 m**区段续接为与GL40–80 m相同的四列面网格。旧整面大X和过密短横杆由分格交叉斜材、立杆与带状构件取代，在80 m边界对齐分列节点。

新增控制层位为80/93/106/120 m，下方原有控制层位为40/53/66/80 m。短连接件把新网格接到R10主脚的真实盖板表面；114 m附近仍需承担局部接合关系的支承单独保留。这些是模型层位，不是游客楼层。

R10整体主脚和拱架、真实开口、平滑上部塔身、展望台、设备、核心、楼梯及既有钢节点局部形状保留，相关引用对应到新的实际连接件；晴空塔R05保持。当前具名部件总数见[最新清单](../output/review/tokyo_tower_manifest.json)，不使用旧版本计数。

新增三语“**80 m 格网衔接**”按钮，以实际53–106 m网格包围盒提供正面近景，包含80 m上下各两带，不隐藏或剖切实体。格距、宽度、板厚、孔洞、断面和接合仍是演示假设，不是实物逐杆测绘、原始制造图复原或结构计算结果。

## English

R11 continues the four-column face grid from **model GL40–80 m into the 80–120 m band** below the Main Deck. Subdivided crossed diagonals, verticals and belts replace the former full-face X patterns and dense short horizontals. The column nodes align across the 80 m boundary.

New model stations are 80/93/106/120 m; the retained lower grid uses 40/53/66/80 m. Short connectors attach to the actual R10 leg cover plates. Required local support near 114 m remains as separate short members rather than a full-face belt. These stations are model controls, not visitor floors.

R10 whole leg and arch assemblies, real openings, smooth upper profile, observation facilities, equipment, core, stairs and steel-node local geometry carry forward. Related-member references map to actual new connectors. Skytree R05 remains unchanged. Named part counts follow `component_count` in the [current manifest](../output/review/tokyo_tower_manifest.json), not historical totals or internal plate-piece counts.

The trilingual **80 m grid transition** button frames the actual 53–106 m upper/lower grid bounds in front view, including two complete bands on each side of 80 m. No geometry is hidden or sectioned for this view. Grid spacing, widths, plate thicknesses, openings, sections and connections remain demonstration assumptions, not a complete member survey, recovered fabrication drawing or structural calculation. Model GL125/223.55 m remains separate from official visitor guidance at 150/250 m.

## データと検証対象 / 数据与校验范围 / Data and validation scope

- [STEP](../STEP/tokyo_tower.step) · [GLB](../GLB/tokyo_tower.glb) · [A3 PDF](../output/pdf/tokyo_tower_sheets.pdf)
- [平面DXF / Plan](../DXF/tokyo_tower_plan.dxf) · [立面DXF / Elevation](../DXF/tokyo_tower_elevation.dxf) · [接合部DXF / Steel nodes](../DXF/tokyo_tower_steel_nodes.dxf)
- [Manifest](../output/review/tokyo_tower_manifest.json) · [Drawing provenance](../output/review/tokyo_tower_drawings.json) · [格構ソース / Grid source](../src/lib/tokyo_tower_grid.py)

新しい処理は`detail.lower_grid_continuity.enabled`で有効になり、R10の全体組立材の処理後に適用します。旧パラメーターを再生するときは無効にして、R10以前の履歴を保ちます。

新しい格構は`structure:grid_panel_a/b_...`、`structure:grid_vertical_...`、`structure:grid_belt_...`で識別します。部材は`built_up`として実際の開口を持ち、短い取付材・支持材は別に名前を持ちます。これは本モデルの編集用識別で、実施設の製作番号ではありません。

公開ゲートは新しい`src/lib/tokyo_tower_grid.py`をモデルと図面のSHA-256束縛へ含め、ソースの欠落・改変、古いR10以前の改訂、保存物との不一致を拒否します。GLB検証は四面・四列と旧X材の置換、保持する全体組立材、局部節点参照を確認します。カメラ検証は上下の実部材範囲と正面方向を照合します。

デスクトップとモバイルの視覚回帰に新しい80 m接続部を含めます。追加した視点ボタンによるツールバーの折返しや画布寸法の変化も目視対象とし、標準カメラや画像差分の許容値を変えて差を隠しません。STEP・GLB・DXFは必要に応じてgzipのみを配信しますが、論理ファイル名と原生バイトのSHA-256を保持し、ダウンロード時に復元します。静的配信物の展開後総量にも256 MiBのビルド上限を適用します。

<a id="sources"></a>

## 出典 / 来源 / Sources

Reference review date: **2026-11-04**. Reference photographs are linked for research and are not redistributed here.

| 出典 / Source | 用途と限界 / Use and limits |
| --- | --- |
| [宮地技報No.18、印刷p86](https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf) | 全体軸線、層位、メインデッキ付近の資料対応。今回の4列格構・未公開断面を実測した資料ではない。 / Historical overall framing and level context, not a measured schedule for this fitted four-column layout. |
| [IHI Infra-square: Historical Structure](https://www.ihi.co.jp/iis/en/gallery/historical_structures/index.html) · [東京タワー施工写真](https://www.ihi.co.jp/iis/en/gallery/historical_structures/i/img_tokyo-tower2.jpg) | 継承する板材・組立材・鋲接合の外観を確認する。R11の細かな割付寸法を断定しない。 / Built-up framing and connection appearance; not exact R11 grid dimensions. |
| [Nature Architects: 散歩しながら考える構造力学２](https://nature-architects.com/blog/1817/) · [ラチス近景](https://nature-architects.com/wp-content/uploads/2024/02/Untitled.png) · [綴り板近景](https://nature-architects.com/wp-content/uploads/2024/02/Untitled-1.png) | 現地で見える板面・縁材・透空腹面の参考。一次の現地観察で、原設計図・製作図ではない。 / First-hand observations of plates, edges and open webs, not original fabrication drawings. |
| [R10履歴](tokyo_tower_R10.md) · [R09履歴](tokyo_tower_R09.md) | 保持する全体組立材と以前の小部材表現を区別する。各履歴の部品数や検証結果はR11の実測精度・公開反映を証明しない。 / Distinguishes retained whole assemblies from earlier representations; historical counts and checks do not attest the R11 release. |
