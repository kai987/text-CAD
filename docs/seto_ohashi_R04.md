# 瀬戸大橋 R04 / 濑户大桥 R04 / Seto Ohashi R04

**2026-11-07 · BRIDGE-R04 · 主塔の実景合わせ / 主塔外形对齐 / Photo-informed tower correction**

## 日本語

提供された実景と施工資料に合わせ、南・北備讃瀬戸大橋の4主塔を修正しました。
上部は連続2段のX、中央は長い空腹区間、橋面下は完全なXと上部の山形横構を組み合わせます。
山形と下部Xの上半分が菱形の開口を形成します。上部Xの中間など、実景にない横梁を除き、
横断する梁を塔頂と桁下の支持部に限定しました。

| 項目 | R04のモデル |
| --- | --- |
| 塔柱 | 12頂点の十字形3セル箱形外包。横幅4,800 mm、橋軸方向の奥行は基部10,700から塔頂7,100 mmへ近似的に絞る |
| 傾斜 | 塔頂中心間35,000 mm、基部は約39,253 / 39,474 mm。A形ではなく、わずかに内傾した門形 |
| 横構 | 塔ごとに上部4斜材、下部Xの2斜材、山形2斜材。斜材の外包は2,000×2,000 mmの近似 |
| 接合部 | 柱内に定着する斜材端部、交差部の面取り節点、8枚の基部底板。すべて名前付きCAD実体 |
| 図面 | 立面シートへ北橋3P型・南橋5P型の1:2000正面図を追加。橋面位置と編集可能な塔頂標高・35,000 mm寸法を表示 |
| Web | 「主塔を拡大」の視線を橋軸方向に近づけ、上下の横構を確認しやすくした |

### 資料と近似の範囲

- [本四公団「北備讃瀬戸大橋塔架設工事」](https://jcmanet.or.jp/bunken/wp-content/uploads/1986/jcma-1986_05.pdf)：『建設の機械化』1986年5月、印刷34頁Fig.3と表1。3セルの塔柱外包、上部2X、下部Xと山形を参照。
- [駒井鉄工「南備讃瀬戸大橋の概要と施工試験」](https://www.komaihaltec.co.jp/tec/komai/1986/vol5-12.pdf)：印刷124頁Fig.1の塔正面。
- [JB本四高速の実景と諸元](https://www.jb-honshi.co.jp/seto-ohashi/shoukai/6kyou6.html)。提供写真も上下の横構の接続関係の確認に使用。写真・図版は転載しない。

塔柱は中空壁厚・内部隔壁まで復元したものではなく、3セルの外形を示す実体です。
北橋資料の外形を南橋へ準用し、足元の標高T.P.+10,050 mm、横構の位置・節点寸法を
現行の簡略橋面へ合わせる部分はモデル用仮定です。既存の名目塔頂184/194 mと主缆制御を
使っており、資料にある個別2P/3P等の厳密な施工標高を再現した測量モデルではありません。

R03の4,450定義を独立して凍結し、変更集合を塔の主要部材64個と橋脚上部4個に限定します。
そのうち実景にない横梁16個を削除し、底板・山形・節点28個を追加して4,462部材とします。
残る4,382定義は名前・寸法・属性をまとめたハッシュで保護します。浮動小数点はCAD mmの
小数6桁だけを正規化し、車両・船・電車・橋面・主ケーブル・アンカレイジの形状を保持します。

### ファイル

[STEP](../STEP/seto_ohashi.step) · [GLB](../GLB/seto_ohashi.glb) ·
[平面DXF](../DXF/seto_ohashi_plan.dxf) · [立面DXF](../DXF/seto_ohashi_elevation.dxf) ·
[断面DXF](../DXF/seto_ohashi_section.dxf) · [3頁PDF](../output/pdf/seto_ohashi_sheets.pdf)。
[共通形状・塔パラメーター](../src/lib/seto_bridge_geometry.py)と
[描画生成器](../src/generate_seto_bridge_plans.py)を保管します。
生成・Webのコマンドと動く船・電車・水面の仕様は[R03](seto_ohashi_R03.md)を参照してください。
単位mm、STEP/GLBはt=0の静止形状で、動きはWeb表示です。

### 検証（2026-11-07）

統一CAD生成は294単体＋25解析テストに成功し、保存された橋梁13,745項目が成功しました。
4,462個の有効なCAD実体とGLBメッシュ、86,748三角形を照合しています。387件のWeb単体、
デスクトップ／モバイル48件が成功し、重複ダウンロードなど4件を意図的に省略しました。
全斜材64端部のCAD体積による接触、4車線・鉄道全線の通行包絡、実GLBでの24車両×4主塔の
96通行組合せを確認。3頁PDFを逐頁確認し、実ブラウザーの主塔近景も確認しました。
既存他モデル97出力は変更前と同じSHA-256です。構造耐力・耐震性能の認定ではありません。

## 简体中文

主塔按提供的实景和施工资料改为：上方两层连续X、中间长空腹段、桥面下完整X接上方山形撑，
形成菱形开口；移除多余横梁。塔柱改为带侧向翼部的三单元箱形外轮廓，并补齐撑端、交叉节点和底板。
立面图新增两种主塔的正面详图及可编辑尺寸，网页主塔视角更接近正面。

4,382个其他构件定义受到基线哈希保护；汽车、游船、电车、桥面、主缆与锚碇几何保持原定义。
柱截面以北桥资料为参考，南桥沿用、节点细节和横撑落位仍为外观近似；184/194m名义塔顶
不等同于分别复原全部主塔的原施工标高。源码、CAD和三页图纸见上文链接。

## English

The four towers now follow the supplied photograph and original general drawings: two upper X stages,
a long open portal, and a lower full X plus an upper chevron forming a diamond opening. Unsupported
horizontal bars are removed. The columns use a tapered cruciform three-cell outer envelope, with named
brace ends, intersection plates and base plates. Two frontal details with editable dimensions are added
to the elevation sheet, and the tower camera looks more nearly along the bridge axis.

A frozen baseline protects the other 4,382 component definitions. Cars, boats, trains, decks, main cables
and anchorages retain their geometry. South column sections borrowed from North drawings, node details
and fitting to the simplified deck remain appearance assumptions. Nominal 184/194m tower controls do
not individually reconstruct the original surveyed levels of every tower. Sources and outputs are linked above.
