# 瀬戸大橋 R05 / 濑户大桥 R05 / Seto Ohashi R05

**2026-11-07 · BRIDGE-R05 · 共用アンカレイジの実景合わせ**

## 日本語

南・北備讃瀬戸大橋の中央にあるBB4A共用アンカレイジを、原施工一般図と管理者の
維持管理写真に合わせました。端部BB7Aの形状を中央へ転用せず、BB4A固有の収束部、
広い折線のV溝、端面中央の盲くぼみをモデル化しています。

| 項目 | R05 |
| --- | --- |
| 下部と基脚 | TP+5mで躯体縦53m、基脚縦57m。躯体はTP+33mまでに最大79mへ広がる |
| 上部 | TP+75.190m付近で縦約73mへ収分。頂部TP+86m、V底TP+52.5m |
| 横幅 | 躯体58m、両側各2mの基脚縁を含む外包62m |
| 端面 | 中央幅12m、深さ4.5m、床TP+12mの盲くぼみ。背壁と床を残す写真合わせの仮定 |
| 表面 | 約3mピッチの打継ぎ帯、下部の濃色保護面。208個の名前付きCAD実体を追加 |
| 図面 | 3頁A3を保持。外形1:2000、編集可能な79,000 / 53,000 / 86,000mm寸法を追加。鉄道断面は端面くぼみも反映 |
| Web | 中・日・英の「共用アンカレイジの近景」。実モデルの外包から取景 |

### 一次資料と仮定

- [本四公団「南北備讃瀬戸大橋共用アンカレイジの施工」](https://www.jstage.jst.go.jp/article/coj1975/22/11/22_49/_pdf)：1984年、印刷49–50頁、Fig.2。原一般図の外包、53m収束部、基脚、標高、V溝を参照。
- [JB本四高速「長大橋の維持管理」講習資料](https://www.j-cma.jp/jcma-pics/10022220_HjZm38.pdf)：2025年度、PDF11頁・スライド10のBB4A写真。端面くぼみ、水平打継ぎ、下部保護面を参照。

頂部折線の細かいX位置、最上部縦71.5m、端面くぼみの幅・深さ・底標高、打継ぎ帯の
寸法と色は写真からの外観近似です。基脚底TP-14mは従来の未測量仮定を保持します。
施工時のTP+5m幅5m足場を、現在の恒久歩廊としては復元していません。写真は転載しません。
原図内部の定着装置・中空構造・配筋は復元していません。道路・鉄道は従来の表示用
通行包絡を残します。構造計算・安全認定・測量モデルではありません。

### 保持とファイル

R04の4,462部材を独立した凍結基線から照合し、既存の変更をBB4Aの基礎・本体2個に限定。
残る4,460定義、四主塔、公鉄桁、ケーブル、車・船・電車の定義を保護しています。
追加208個を含むR05は4,670部材です。R01–R04の歴史的な照合も継続します。

[STEP](../STEP/seto_ohashi.step) · [GLB](../GLB/seto_ohashi.glb) ·
[平面DXF](../DXF/seto_ohashi_plan.dxf) · [側面DXF](../DXF/seto_ohashi_elevation.dxf) ·
[断面DXF](../DXF/seto_ohashi_section.dxf) · [3頁PDF](../output/pdf/seto_ohashi_sheets.pdf)。
[形状パラメーター](../src/lib/seto_bridge_geometry.py)・[図面生成器](../src/generate_seto_bridge_plans.py)を保持。
単位mm、STEP/GLBはt=0、車・船・電車と波のアニメーションはWeb表示です。
再生成コマンドは[R03](seto_ohashi_R03.md)、主塔の資料と近似は[R04](seto_ohashi_R04.md)を参照。

### 検証（2026-11-07）

保存済みSTEP/GLB・図面14,387項目、CAD単体296件、解析25件が成功。
4,670個の有効な名前付きCAD実体と同数のGLBメッシュ、89,344三角形を照合しました。
盲くぼみの空間と背壁・底面、実際の通行包絡をCAD体積で検査し、R01–R04基線も保持。
他モデル97出力のSHA-256を変更前と照合し、3頁PDFを逐頁確認しています。
Web単体388件と本番ビルドが成功。168資産のハッシュを照合しました。
デスクトップ1280×900／モバイル390×844の回帰は48件成功・4件を意図的に省略し、失敗はありません。
3言語の近景、動作、ダウンロード復元後の実ファイルも確認しています。
実ブラウザー666×825でR05・36actorのロード、近景、環境切替・回転を確認し、警告とエラーはありません。
模式的な三子島地形が基脚の一部を隠すため、地形を隠した状態でも足元を確認しています。

## 简体中文

中央BB4A共用锚碇按原施工图和运营方维修近照修正：下部收腰、上部微收分，
宽口折线平底槽、两端中央带背墙和底面的凹槽，并增加混凝土分层接缝和深色保护面。
保留四座主塔及4,460个其他原构件定义；仅修改两个原锚碇实体，增加208个具名细节，
合计4,670个构件。网页增加中日英锚碇近景，三页图纸增加可编辑外形尺寸。

最大纵长79m、V底52.5m、顶部86m等参考原总图；凹槽12m宽/4.5m深、分缝和色彩为
外观近似，水下深度仍是原演示假设。通行开口为演示净空包络，不表示实桥内部构造。
文件和一次来源见上文。

## English

R05 aligns the central shared BB4A anchorage with its original general drawing and an owner maintenance
photograph: a narrowed lower body, slight upper batter, flared flat-bottom trough, blind recesses on both
bridge-axis faces, concrete courses and darker lower protection. Two existing anchorage solids change;
4,460 other R04 definitions are protected. There are 208 named additions and 4,670 components in total.
The viewer gains a trilingual close-up; the three A3 sheets gain editable full-profile dimensions.

Published general-drawing controls include the 79m maximum length, 52.5m trough floor and 86m top.
The 12m-wide/4.5m-deep recesses, finish courses and colours remain appearance assumptions; submerged
depth and transport passage envelopes retain demonstration assumptions. Internal anchoring hardware,
reinforcement and structural capacity are not reconstructed. Primary sources and output links are above.
