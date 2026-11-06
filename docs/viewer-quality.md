# ビューアーの比較・回帰テスト・性能計測

[日本語 README](../README.ja.md) · [简体中文](../README.md) · [English](../README.en.md)

## 写真との比較

東京タワー／東京スカイツリーの3D画面で「写真と比較」を開き、手元の参考画像を選びます。PNG・JPEG・WebP、12 MiB・32メガピクセル・各辺16384 pxまで。画像はブラウザー内で処理し、サーバーに送信・保存しません。

1. 「正面」「側面」など比較する視点を選びます。写真の方向と撮影条件が分かる資料を優先します。
2. 画像の倍率・上下左右・回転・不透明度を調整し、塔脚、展望台、塔頂の輪郭を比較します。チェックボックスで画像を一時的に非表示にもできます。
3. 出典・撮影条件を記入し、「比較条件を保存」でJSON、「比較画像を保存」で合成PNGを保存します。
4. 保存条件を再利用するときは、同じ参考画像を選び、「比較条件を読み込む」でJSONを指定します。モデルID・改訂・モデルのSHA-256と、写真のSHA-256・画素寸法が一致すると、位置合わせ、表示状態、出典、カメラ姿勢・画角を復元します。モデルIDと写真が同じで、改訂やモデルのハッシュだけが異なる場合は、保存時と現在の改訂・ハッシュを表示し、「現在のモデルに写真・カメラ条件を適用」の明示操作を待ちます。適用時に旧モデル側の基準点を解除し、以後のJSONに元の改訂・モデルハッシュを記録します。JSONは128 KiB以下です。旧schema 1も読み込めます。旧記録に画角情報がない場合は、現行のプリセット画角にカメラ姿勢を適用します。
5. 「対応する基準点を追加」で写真上の点、続いてモデル上の対応点を選びます。矢印キーとEnterでも選択でき、最大16組を保存します。写真の点は原画像座標、モデルの点は画面座標として記録し、差をCSS pxと画面対角線に対する割合で表示します。写真の位置合わせを変えると差も更新します。視点や表示サイズを変えた場合は、古い画面座標を使わないよう基準点を解除します。保存JSONを別の縦横比で復元するときは正射影の横幅に合わせて点を移し、画面外のモデル点を除きます。

JSONはモデルの改訂・SHA-256、画像のSHA-256・画素数、実際のカメラ位置・正射影の縦幅、画面寸法、画像変換値と基準点を記録します。写真自体は含みません。元画像とJSONを一緒に保管してください。画像の利用・共有は権利条件に従ってください。

モデルGLと公式案内高さは別に保存します。東京タワーのGL 125/223.55 mを、公式案内150/250 mと同じ基準に自動変換しません。写真の遠近感・レンズ歪み・撮影年代は未補正です。実物への一致や実測精度を証明するものではありません。自動テストの入力画像には本モデル自身の画面を使い、実景との一致の証拠とは扱いません。

## ブラウザー回帰テスト

`web/`で実行します。

```bash
npm ci
npx playwright install chromium
npm run build
npm run test:e2e
```

専用の127.0.0.1:4213で本番ビルドを起動し、デスクトップ1280×900とモバイル390×844を検証します。既存プレビューは再利用しません。Browserプラグインが利用できない環境でも、Playwrightの独立したChromiumで実行できます。

全5モデルの表示、タワーの昼夜・部材・3言語、図面切替、ローカル画像の比較と保存、バッチ化有無の同一視点、東京タワーSTEPの分割復元とSHA-256一致を検証します。復元サイズと分割数は現行の`artifacts/manifest.json`に従います。大きなSTEPを一度復元するため、十分なメモリーと一時保存領域が必要です。

画像基準は`web/e2e/snapshots/`に保存します。固定バージョンのソフトウェア描画・視点・画面寸法で3Dキャンバスを比較します。OS差を考慮した小さな画素差許容があります。基準更新時は理由と差分をレビューし、失敗の解消だけを目的に更新しないでください。

```bash
npm run test:e2e:update
```

CIはPRでもCAD・Web・ブラウザー検証を行い、PRからは公開しません。失敗時のトレース、画像、HTMLレポートはActionsの`browser-regression-report`から確認できます。ローカルの`web/test-results/`と`web/playwright-report/`はGit対象外です。

CADの検証グループは`src/cad_pipeline.py`の共通カタログからCIへ渡します。保存成果物、一般の単体検証、東京タワーR09/R10/R11の実体検証、住宅解析の6グループを最大4ジョブで並列実行し、各グループの前後で同じリリースのソース・成果物ハッシュを照合します。Web検証は独立して進め、すべてのCADグループとWeb検証が成功してからPagesを公開します。ローカルの`--validate`と再生成時の検証は全カタログを実行します。

```bash
# CIと同じグループを読み取り専用で検証する例
.venv/bin/python src/cad_pipeline.py --validate --validation-group tokyo-r11
```

`npm test`の前処理と`npm run build`は同じ成果物準備処理を使います。入力ソース・CAD・配信ヘルパー・依存ロックと、生成済み配信ファイル・表示メタデータのSHA-256がすべて一致する場合、圧縮と輪郭生成を再利用します。公開前のCAD鮮度検証は毎回実行し、入力・出力・カタログ・Node実行環境の変更、欠落、破損では再生成します。端末内の`web/.artifact-preparation-cache.json`はGit対象外です。

## 描画負荷と初期表示

塔の読み込み中は、同じマニフェストから生成した小さな概形を表示します。詳細GLB・平面・立面の先読みは並行して継続します。この概略図はCADや詳細GLBの代用ではありません。

不透明な塔体を材質・高さ帯ごとの表示メッシュにまとめます。元の名前付き部材、形状、分類、20か所の接合部、独立した鋲、STEP/GLBは保持します。

```bash
npm run bench:landmarks -- --samples 3 --output /tmp/landmark-batches.json
```

Node計測は可視メッシュ数、三角形数、結合準備のCPU時間です。FPSやGPU時間ではありません。2026-11-01の東京タワーR07計測では、可視メッシュ5,775個が3,352個に減り、2,440個の対象鋼材が17個の表示メッシュになりました。三角形254,660枚は同じです。これはR07の記録であり、R08以降の現行モデルの値ではありません。「自動」鋲表示や画角でも数値は変わります。

2026-11-01の東京タワーR07・Chromium 156・SwiftShader・デスクトップ正面視点（昼・鋲は自動）では、実際の描画呼出数が5,865から3,442へ約41%減りました。同じ環境で変更前後のキャンバス画素も直接比較しています。これは当該条件での描画呼出数の結果であり、端末一般のFPS改善率ではありません。

実ブラウザーでは`?model=tokyo-tower&view=3d&renderBatching=off`と通常表示を同一視点・昼夜・鋲設定で比較できます。`data-render-calls`は実際のThree.js描画呼出数、`data-render-cpu-ms`はCPU側のrender呼出時間で、GPU完了時間ではありません。転送展開、GLB解析、準備、初回描画の各時間もキャンバスのdatasetに記録します。Rust追加移植は計測結果から判断します。

## 简体中文

新增本地照片叠加、位置/缩放/透明度调整和PNG/JSON导出。照片不会上传；手动对比不代表实测精度。Playwright覆盖桌面/移动端、五种模型、三语言、昼夜、图纸和分块STEP。东京塔仅合并显示网格，保留CAD部件与几何。CAD验证按共享目录分成6组、最多4组并行，Web独立验证，全部成功后发布。前处理仅在所有输入与生成输出的哈希都匹配时复用，CAD鲜度检查每次执行。命令及限制见上文。

## English

Device-local photo overlays support alignment and PNG/JSON review exports. Photos are never uploaded; manual comparison does not establish surveyed accuracy. Playwright covers desktop/mobile, five models, localization, lighting, drawings and reconstructed STEP downloads. Display batching preserves CAD parts and geometry. Six CAD groups share the authoritative catalog and run up to four at a time. Web checks run independently; publication requires every CAD and Web check to succeed. Artifact preparation is reused only when all input and generated-output hashes match; CAD freshness is checked on each invocation. Commands and measurement limits are documented above.
