# 瀬戸大橋 R03 / 濑户大桥 R03 / Seto Ohashi R03

**2026-11-07 · BRIDGE-R03 · 外観と交通のデモ / 外观与交通示意 / Appearance and activity study**

## 日本語

R03は船の進行方向、海面、道路・鉄道とアンカレイジの干渉を修正し、下層の電車を追加します。
[R01の公開寸法](seto_ohashi_R01.md)と[R02の道路車両・橋梁細部](seto_ohashi_R02.md)を継承します。

| 変更 | モデル・表示の内容 |
| --- | --- |
| 遊覧船 | 4隻の航跡を橋軸X方向から横断Y方向へ変更。北・南の中央支間を各2隻が橋の下から通過 |
| 海面 | Web専用の多周波の波法線、視線角に応じた反射色、細かな水面のきらめき、距離に応じた波の間引き。昼夜と航跡に対応 |
| アンカレイジ | BB1A・中央BB4A・BB7Aの実体をBooleanで切り抜き、橋面・桁・電車の通路を確保。中央V溝底は原図のT.P.+52.500 mに修正 |
| 鉄道横桁 | 元の122本を1,200 mm下げ、レール面を突き抜けていた部分を修正。両端Z座標以外の定義を保持 |
| 電車 | 2列車×4両、計8両。車体・窓・ドア・台車・車輪・パンタグラフを具名部品としてSTEP/GLBに収録 |
| 操作 | 電車の独立表示、追従する近景視点、海面の波の切替、全体の再生／停止。日本語・中国語・英語 |

### 仮定と出典

船の横断位置Xは−825,000 / −765,000 / +820,000 / +880,000 mm、Yは−300,000〜+300,000 mmです。
船首は進行方向に向け、橋下の水面を通ります。航跡・速度・船型は演示用で、指定航路ではありません。

電車は独自の4両編成を2列、25 m/sで反対方向に循環させます。各車の外包は
20,000×2,850×5,300 mm、車両中心間隔20,500 mm、台車中心間隔13,800 mmです。
1列車の先頭位置を共通の時計で動かし、周回しても編成を分断しません。
レール頂は下層床版基準+420 mmとし、2台車の位置のレール高さから車体の高さと傾斜を求めます。
JR西日本の[マリンライナー公式車両写真](https://www.jr-odekake.net/railroad/train/marineliner/)を
銀色の車体・帯・窓の外観参考にしています。実車の型式、編成数、運行記録を再現するものではありません。

中央アンカレイジのV溝底と外包は、[本四公団による施工報告](https://www.jstage.jst.go.jp/article/coj1975/22/11/22_49/_pdf)
の印刷50頁Fig.2を参照します。道路・鉄道通廊の33 m幅や切抜き高さ、追加車両・波の寸法はモデル用仮定です。
実体の相交検査はモデル内の干渉を確認するもので、実橋の耐力や通行有効高さを認定するものではありません。
写真や第三者の3D素材を成果物へ転載していません。

### 保存形式と動作

STEP/GLB/DXF/PDFはt=0の静止配置です。CADの平均海面はT.P.0の平面を保持し、
波や移動はWeb表示で加えます。外部画像・テクスチャ配信には依存しません。
GLB内の`activity.schema_version=2`がルート軸、位置、速度、方向、編成と部品名を対応づけます。

一時停止、画面外、非表示タブ、図面への切替でアニメーションを止め、復帰時に経過時間をまとめて進めません。
非表示の車両分類も個別に停止します。OSの「視差効果を減らす」では停止状態から開始します。
波だけを止めたい場合は「海面の波」を無効にします。

### ファイルと再生成

[STEP](../STEP/seto_ohashi.step) · [GLB](../GLB/seto_ohashi.glb) ·
[平面DXF](../DXF/seto_ohashi_plan.dxf) · [立面DXF](../DXF/seto_ohashi_elevation.dxf) ·
[断面DXF](../DXF/seto_ohashi_section.dxf) · [3頁PDF](../output/pdf/seto_ohashi_sheets.pdf)。
図面はmm単位、日文の編集可能な文字・寸法です。平面に船の横断方向と電車配置、断面に鉄道と通行部を示します。

生成元：[橋梁形状](../src/lib/seto_bridge_geometry.py)・[船車・電車](../src/lib/seto_bridge_activity.py)・
[3D出力](../src/seto_bridge_3d.py)・[図面出力](../src/generate_seto_bridge_plans.py)。
表示：[運動](../web/src/bridge-motion.ts)・[海面](../web/src/bridge-water.ts)。

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate --model seto-ohashi
cd web
npm test
npm run build
npm run preview
```

WebはNode.js 24を使用します。`?model=seto-ohashi&view=3d`で表示できます。
生成・出力ファイルとPython依存のSHA-256を照合してからWebへ複製します。
R02の3,856部材のうち3,583個を集約ハッシュで保護し、変更は船148部品、アンカレイジ3実体、
鉄道横桁122本に限定して独立した旧定義と比較します。新しい電車を追加しても既存の主要寸法を変えません。

### ローカル検証記録（2026-11-07）

- 統一CAD生成とリリース照合に成功。CAD単体292件・解析25件、保存橋梁13,706項目が成功。
- STEPは有効な4,450実体、GLBは同数の名前付きメッシュと86,092三角形。既存他モデル97出力は変更前のSHA-256と一致。
- 保存STEPの全線鉄道包絡6分割・465候補で体積干渉0。24道路車両×4主塔の96組も成功。
- Node.js 24のWeb全測386件成功。全体ブラウザー回帰は48件成功・重複ダウンロード等4件を意図的省略。
- 水面の最終見た目調整後、関連9単体とデスクトップ／モバイル橋梁11件を再検証し成功（重複ダウンロード1件省略）。
- 最終buildは168配信ハッシュに一致。展開247,139,229 bytes、上限268,435,456 bytes以内。
- 実際のアプリ内ブラウザーで昼夜の水面、電車近景、中央通廊、停止／再開を確認。コンソール警告・エラー0。

これらは幾何・ファイル整合と表示動作の検証であり、実橋の構造認証ではありません。

## 简体中文

R03把4艘游船改为垂直桥轴航行，从南、北主跨的桥下穿过。网页海面增加连续波纹、
反光、昼夜颜色和随船转向的航迹，水波可单独开关。下载的CAD保留平均海平面，网页负责动态效果。

BB1A、中央BB4A、BB7A锚碇在真实CAD实体中留出上下层通廊；中央V槽底按原施工图改为
T.P.+52.500 m。122根原来高于轨面的横梁下移1,200 mm，避免穿过轨道和电车。
另增加两列相向行驶的四节电车，可独立隐藏、跟随查看、播放和暂停。每列共享先头位置，
保持20,500 mm车距，按两处转向架下的轨面高度调整姿态。

电车为参考JR官方照片制作的原创通勤车示意，车厢20,000×2,850×5,300 mm、速度25 m/s，
数量、尺寸、速度、航线与通廊细节均为演示假设，不代表实桥运营、测绘或结构认证。
STEP、GLB、三张可编辑DXF及三页PDF同步保留t=0静态布置和全部具名部件；文件、参数源码和官方来源见上文链接。

## English

R03 sends four boats across the bridge axis, beneath the North and South main spans. The viewer adds
procedural multi-scale ripples, view-dependent water highlights, day/night colours and heading-aware
wakes. Water motion has its own switch; downloaded CAD retains a flat mean sea level.

Boolean openings in the BB1A, shared BB4A and BB7A solids clear the road/rail corridor. The shared
V-notch bottom follows T.P.+52.500 m in the cited construction drawing. All 122 existing rail floorbeams
are lowered 1,200 mm to remove their intrusion above rail level. Two opposing four-car electric trains
follow the lower tracks, with independent visibility and a tracking camera. Each consist shares one
leader clock; carriage height and pitch follow the rail at its two bogie centres.

The original generic train takes exterior cues from the official JR photograph. Its 20,000×2,850×5,300 mm
carriages, 20,500 mm spacing and 25 m/s speed are demonstration assumptions, as are boat routes and
model corridor details. They do not reproduce a specific operating formation or certify the real bridge.
STEP, GLB, three editable DXFs and the three-page PDF retain the named t=0 snapshot. Sources and outputs
are linked above and checked by SHA-256 before publication.
