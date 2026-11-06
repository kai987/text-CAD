# 瀬戸大橋 R02 / 濑户大桥 R02 / Seto Ohashi R02

**2026-11-06 · BRIDGE-R02 · 外観・交通のデモ / 外观与交通示意 / Appearance and activity study**

R02の履歴です。現在の共通出力は[横断航路・電車・海面・通廊を修正したR03](seto_ohashi_R03.md)です。

## 日本語

R01の南・北備讃瀬戸大橋に、検査用の小さなプラットフォーム・手すり・短い梯子、
橋脚の継目、道路灯具を追加しました。元の2,966部材のうち2,962部材は名称と
集約SHA-256で同一性を検証します。4主塔の道路直上の横梁だけを3,000 mm上げ、
モデル上の通行有効高さを2,100から5,100 mmへ修正しました。これはバン・バスが
横梁と交差しないためのモデル用配置で、実橋を測量した高さや法定高さの認定ではありません。
この4部材は元の定義を保存し、両端Z座標以外を変更しないことを検査します。
公式の支間、主塔の高さ、主ケーブル、橋面の配置は
[R01の寸法・出典](seto_ohashi_R01.md)を継承します。

### 車両と遊覧船

| 項目 | R02のモデル |
| --- | --- |
| 車両 | 24台：乗用車18・バン4・バス2。左右各2車線。タイヤ、ホイール、斜めの窓、前照灯・尾灯を独立命名 |
| 遊覧船 | 4隻：小型クルーズ船3・やや大きな船1。尖った船首、船底、水線の飾り、客室窓、上部甲板、手すり、操舵室、マスト |
| 車両寸法 | 乗用車4,500×1,820×1,560 mm、バン5,250×1,950×2,250 mm、バス10,500×2,450×3,300 mm。すべて仮定 |
| 船の寸法 | 24,000×6,400×6,400 mmを3隻、34,000×9,000×8,100 mmを1隻。仮定の喫水850 mm |
| 動く対象の分類 | `traffic` と `vessels` を独立して表示・非表示 |
| 保存モデル | STEP/GLBとDXFはt=0の静止状態。すべての部品名・分類を保持 |
| Web表示 | 車両・船の移動、船の微小な揺れ・航跡。再生／一時停止と専用の近景視点 |

車両は進行方向から見て左側を走ります。Xの正方向はモデルの南方向で、
正方向の車両をY=+3,500/+8,500 mm、負方向をY=-3,500/-8,500 mmに配置します。
路面高さは `93000 - 0.01 * max(abs(X), 24500)` mmです。中央49 mの平らな
接続床と両側1%の簡略勾配に合わせ、車体も傾斜します。同じ車線の車両は同じ速度を
使い、初期の車間を保ちます。速度は22.5/23/23.5/24 m/sのモデル用仮定値です。

船はY=±210,000/±270,000 mm、X=-1,350,000～+1,450,000 mmの
仮定の海上区間を往復方向に循環します。速度は6～7.05 m/sのモデル用仮定値です。
島・基礎と船の外包寸法の間に余裕があることを確認します。これは本物の航路、
運航便、現在の交通量や許可された速度を示すものではありません。

遊覧船の外観要素は、[瀬戸内Finderの現地取材写真](https://www.setouchi.travel/jp/trip-ideas/f20544/)
と[岡山県観光連盟の写真案内](https://www.okayama-kanko.jp/business/photos/detail_1680.html)を
参考にした独自形状です。実船の船型・型式・商標を採寸して再現したものではなく、
写真を成果物へ転載していません。追加した橋梁細部の寸法も外観用の仮定です。

### 再生と省電力

「車両の近景」「遊覧船の近景」は対象を追う視点です。ドラッグで通常の視点操作に
戻れます。一時停止、図面への切替、非表示のタブ、画面外、動く2分類の非表示では
移動を停止します。再表示時に非表示時間をまとめて進めません。
OSが動きの抑制を指定した場合は一時停止から開始し、利用者が再生できます。

Webの動きはCADを置き換えません。GLBに同梱した版付きの`activity`が
動く対象の位置・車線・方向・速度・名前を定め、元のCAD部品を対象ごとの表示用に
まとめます。車両・船の部品色を保ちつつ描画回数を抑えます。

### ファイルと再生成

[STEP](../STEP/seto_ohashi.step)・[GLB](../GLB/seto_ohashi.glb)・
[平面DXF](../DXF/seto_ohashi_plan.dxf)・[側面DXF](../DXF/seto_ohashi_elevation.dxf)・
[横断面DXF](../DXF/seto_ohashi_section.dxf)・[3頁PDF](../output/pdf/seto_ohashi_sheets.pdf)。
平面図にはt=0の船車の配置と、車1:100・船1:500の編集可能な詳細図を追加しています。

パラメーターは[橋梁形状](../src/lib/seto_bridge_geometry.py)と
[船車の仕様](../src/lib/seto_bridge_activity.py)、表示の運動は
[bridge-motion.ts](../web/src/bridge-motion.ts)で管理します。モデル空間はmm・Z-up、
GLBとWebはm・Y-upです。各出力とすべての生成依存をSHA-256で照合します。

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate --model seto-ohashi
cd web
npm test
npm run build
npm run preview
```

Node.js 24を使用します。ローカルの`?model=seto-ohashi&view=3d`で確認できます。

2026-11-06の最終ローカル検証：CAD289件・解析25件、Node 24のWeb380件が成功。
デスクトップ1280×900とモバイル390×844のブラウザー回帰は46件成功・4件の
重複ダウンロード等を意図的に省略し、失敗はありません。24車両×4塔の実頂点による
通行チェック96組も成功し、モデル内の最小余裕は約1.754 mです。
STEP・GLB・DXFのダウンロード復元後のSHA-256は元ファイルと一致します。
既存モデルの画像回帰と、アプリ内ブラウザーの移動・一時停止・再開・近景を確認しました。
Web表示は最大59描画呼出し・72,756描画三角形（透明航跡の両面パスを含む）、
元のGLBは72,740三角形で、CAD部材3,856個を保持します。


## 简体中文

R02 增加主塔检修平台、护栏与短梯、墩身接缝和桥面灯具，保留原有2,962个构件的
定义及主要跨度，仅将四处主塔道路上方横梁提高3m，使演示模型净高达到5.1m，
避免厢式车和巴士穿梁。这不是实桥测绘或法规高度认定。新增24辆车（18辆轿车、
4辆厢式车、2辆巴士）和4艘游船，模型含
轮胎轮毂、斜窗、前后灯、尖船艏、连续舱窗、上层甲板、栏杆、驾驶舱和桅杆。

网页里可以独立隐藏车辆或游船、播放／暂停，并使用车辆或游船近景。车辆按左侧通行，
沿桥面1%纵坡及中央49m平接段运动；船只轻微起伏，并显示示意航迹。隐藏页面或查看
图纸时停动，恢复后不追赶后台经过的时间；系统要求减少动态效果时默认暂停。

STEP、GLB、DXF和三页PDF保存t=0的静态布置，新增的车辆／游船尺寸、位置、数量、
速度、循环路线和桥梁细节均为演示假设，不代表实桥的实时交通或航路。Python参数、
可编辑日文标注和全部具名部件继续保留，文件与来源链接见上表。

## English

R02 adds tower inspection platforms, rails, short ladders, pier seams and road lights while preserving
2,962 original infrastructure specifications and the published span controls. Only four above-road
tower crossbeams are raised 3 m to provide 5.1 m of illustrative model clearance for vans and buses.
Their original definitions are retained and all fields except endpoint Z coordinates must remain unchanged.
This adjustment is not a surveyed height or a statutory-clearance certification. The scene includes 24
vehicles (18 sedans, four vans and two buses) and four original sightseeing boats with individually
named tyres, hubs, glazing, lamps, pointed hulls, decks, rails, wheelhouses and masts.

The viewer offers independent traffic/vessel visibility, play/pause and close-up tracking cameras.
Cars use left-hand carriageways and follow the existing 1% deck grade and flat 49 m central connector.
Boats have gentle motion and illustrative wakes. Animation stops while paused, hidden, offscreen or
viewing drawings, and does not catch up after resuming. Reduced-motion preferences start playback paused.

STEP, GLB and the three editable drawings retain a static t=0 snapshot; only the web presentation moves.
All vehicle/vessel dimensions, density, speeds, loops and added bridge details are explicit modelling
assumptions, not live traffic records, navigation information or surveyed construction details.
