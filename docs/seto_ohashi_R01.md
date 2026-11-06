# 瀬戸大橋・南北備讃瀬戸大橋 / 濑户大桥双桥 / Seto Ohashi twin bridges

**BRIDGE-R01 · 2026-11-06 · reference appearance model**

R01の寸法・出典の記録です。現在の共通出力ファイルは[船・電車・海面と通廊を修正したR04](seto_ohashi_R04.md)に更新しています。

## 日本語

対象は瀬戸大橋を構成する南・北備讃瀬戸大橋の連続2橋です。6長大橋を含む
瀬戸大橋全線のモデルではありません。橋梁所有者の実景写真・側面図と参加施工会社の
技術資料を参照し、門形の4主塔、主ケーブルとハンガー、道路上層・鉄道下層、
開放された補剛トラス、共用アンカレイジBB4Aを別々の部材として作成します。

### 出典のある寸法とモデルの仮定

| 項目 | 北備讃瀬戸大橋 | 南備讃瀬戸大橋 | 出典・適用範囲 |
| --- | --- | --- | --- |
| 吊橋区間・支間割 | 1,538 m = 274 + 990 + 274 m | 1,648 m = 274 + 1,100 + 274 m | JB公式側面図 [北](https://www.jb-honshi.co.jp/corp_index/technology/introduction/introduction_kitabisan.html)・[南](https://www.jb-honshi.co.jp/corp_index/technology/introduction/introduction_minamibisan.html) |
| アンカー端部を含む案内橋長 | 約1,611 m | 約1,723 m | JB橋梁紹介 [北](https://www.jb-honshi.co.jp/seto-ohashi/shoukai/6kyou5.html)・[南](https://www.jb-honshi.co.jp/seto-ohashi/shoukai/6kyou6.html)。上段の吊橋区間とは端点の定義が異なる |
| 主塔頂標高 | T.P. +184 m | T.P. +194 m | 同橋梁紹介。海面からの高さとは扱わない |
| 主ケーブル径・各橋2本 | 998 mm | 1,062 mm | 同橋梁紹介。被覆を除く公表値をモデル断面に使用 |
| 主桁間隔・桁高・主缆間隔 | 30 m・13 m・35 m | 北橋の断面を準用 | [川崎製鉄技報18巻4号](https://www.jfe-steel.co.jp/archives/ksc_giho/18-4/j18-372-378.pdf)、PDF4頁・印刷373頁 Fig.3。南橋の細部が同一とは保証しない |
| トラスの標準格点間隔 | 13.2 m | 北橋の値を準用 | 同資料本文2.1。端部パネルは公表支間に合わせて調整 |
| 共用BB4A | 軸方向79 m・横方向62 m、天端T.P. +86 m | 同一アンカー | [原工事担当者の施工報告](https://www.jstage.jst.go.jp/article/coj1975/22/11/22_49/_pdf)、PDF1–2頁。細かな傾斜面・内部は簡略化 |

公式側面図のBB4A付近にある49 mは共用区間で、2橋分として二重加算しません。
BB4A中心をX=0、北を負、南を正とし、吊橋区間を北X=-1,562.5～-24.5 m、
南X=+24.5～+1,672.5 mに配置します。両外端の接続区間48.2/50.6 mを含む
モデル端点間は3,333.8 mです。これは公表側面図を組み合わせた導出値で、
案内値1,611+1,723=3,334 mとの丸め差を含みます。測量座標ではありません。

次の項目はモデル用の仮定としてパラメーター一覧にも保存します。

- ケーブル曲線は放物線による外観近似です。張力・たわみ・荷重計算の結果ではありません。
- [公団の施工概要側面図](https://www.jstage.jst.go.jp/article/coj1975/22/11/22_12/_pdf/-char/en)にある南側1%勾配を参考に、BB4Aの道路頂点から両側へ下がる簡略縦断線形を使います。北側の対称勾配、曲線接続、鉄道との鉛直差はモデル用の近似です。
- BB4A上の49 m接続床は両端断面を結ぶ簡略形状です。X=0の数学的な頂点より245 mm低く、実橋の縦曲線・支承の納まりは再現していません。
- 海面は表示用のT.P. 0相当です。公式航路高65 mの基準N.H.H.W.L.とは区別し、航路の法定有効高さを検証したとは扱いません。
- 部材断面、塔の横構の配置、ハンガーの納まり、支承、接合部、海中基礎の深さは簡略形状です。原施工図の復元ではありません。
- 島、海底、陸岸、舗装、照明は景観用の仮定です。GISや深浅測量を使用していません。
- 下層は在来線2線と新幹線留保空間を区別します。現役4線の鉄道として表示しません。

### 実際に確認した写真

[南橋・航空写真](https://www.jb-honshi.co.jp/corp_index/technology/introduction/img/minamibisan.jpg)、
[北橋・斜め全景](https://www.jb-honshi.co.jp/corp_index/technology/introduction/img/kitabisan.jpg)、
[南橋・BB4A側の全景](https://www.jb-honshi.co.jp/seto-ohashi/shoukai/img/6kyou6-cap.jpg)、
[北橋・島と主塔](https://www.jb-honshi.co.jp/seto-ohashi/shoukai/img/6kyou5-cap.jpg)。
写真は参考元へのリンクとして扱い、配布成果物に転載しません。

### ファイルと再生成

| 種類 | ファイル |
| --- | --- |
| CAD・3D | [STEP](../STEP/seto_ohashi.step)・[GLB](../GLB/seto_ohashi.glb) |
| 編集可能な原図 | [平面DXF](../DXF/seto_ohashi_plan.dxf)・[側面DXF](../DXF/seto_ohashi_elevation.dxf)・[横断面DXF](../DXF/seto_ohashi_section.dxf) |
| 閲覧・印刷 | [3枚のPDF](../output/pdf/seto_ohashi_sheets.pdf)・[SVG](../output/svg/) |
| 出典・ハッシュ・部材 | [形状マニフェスト](../output/review/seto_ohashi_manifest.json)・[図面マニフェスト](../output/review/seto_ohashi_drawings.json) |
| パラメーター・生成器 | [共通形状](../src/lib/seto_bridge_geometry.py)・[3D](../src/seto_bridge_3d.py)・[図面](../src/generate_seto_bridge_plans.py) |

CADとDXFのモデル空間はmm・Z-up、GLBはm・Y-upです。DXFは日文の文字と
ネイティブDIMENSIONを保持します。主塔、基礎、主缆、吊索、桁、道路、鉄道、海・島は
名前を保持し、ビューアーで分類ごとに表示を切り替えられます。

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate --model seto-ohashi
.venv/bin/python checks/validate_seto_bridge.py
cd web
npm test
npm run build
npm run preview
```

2026-11-06のローカル検証では、橋梁の保存成果物8,974項目、CAD単体285件・解析25件、
Node 24.18.0のWeb単体373件が成功しました。デスクトップ1280×900とモバイル390×844の
ブラウザー回帰は42件成功・4件の重複ダウンロード等を意図的にスキップし、失敗はありません。
原有CAD成果物のSHA-256は変更されていません。STEP・GLB・DXFのダウンロード復元後の
SHA-256一致、3言語、5視点、部材表示、3図面、遅延読込後の初回適合を確認しています。
表示は19描画呼出し・52,076三角形で、元の命名済みCAD部材は保持します。

ローカルビューアーの `?model=seto-ohashi&view=3d` から開きます。
この資料とモデルは外観・学習用で、実橋の耐力、基礎支持力、耐震・耐風性能、
航路のクリアランス、施工適合性を検証した設計資料ではありません。

## 简体中文

本次范围为南、北备赞濑户大桥双悬索桥，采用官方照片、侧面图和施工技术资料，
区分四座门型主塔、两根主缆、吊索、开放式钢桁架、上层道路、下层铁路和共用BB4A锚碇。
北桥悬索区1,538 m、主跨990 m；南桥1,648 m、主跨1,100 m。
包含锚碇端部的案内桥长约1,611/1,723 m，不能混用这两种长度口径。
塔顶T.P. +184/+194 m与航路净空的N.H.H.W.L.基准分别记录。

原始DXF保留日文名称和可编辑尺寸，提供三张SVG、三页PDF、具名STEP和GLB，
查看器支持中日英、部件显隐、整体和近景、昼夜显示。编辑参数位于上表链接的Python源码，
可用 `--model seto-ohashi` 单独重建。照片拟合的主缆曲线、纵坡简化、截面细节、
海底基础及岛屿形状均记录为假设；模型不代表实桥的测绘、结构计算或施工图。

## English

This study covers the North and South Bisan-Seto twin suspension bridges, with four portal towers,
main cables, hangers, open stiffening trusses, upper road decks, lower conventional railway tracks,
reserved railway space and one shared BB4A anchorage. It does not represent all six major bridges
in the Seto Ohashi system. Official suspended lengths are 1,538/1,648 m and central spans 990/1,100 m.
Published overall bridge intervals of approximately 1,611/1,723 m include anchorage endpoint zones;
they are a different length convention. Tower tops use T.P. elevations, distinct from the N.H.H.W.L.
navigation-clearance datum.

Named STEP/GLB, three editable Japanese DXFs, three SVGs and a three-page PDF share the parametric
Python sources linked above. The viewer supports Chinese, Japanese and English, component visibility,
overview/detail cameras and illustrative day/night lighting. Rebuild with `--model seto-ohashi`.
Cable curves, simplified grade, section details, marine foundations and island context remain documented
appearance assumptions. This is not a survey, structural analysis, navigation-clearance certification
or reconstruction of the original construction drawings.
