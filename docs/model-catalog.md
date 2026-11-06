# ランドマークのモデル情報

東京タワーと東京スカイツリーの画面用カタログは、保存済みCADのマニフェストから生成します。
形状は変更しません。住宅・住戸・河川は既存の `house-data.json`、`apartment-data.json`、
`river-data.json` の生成経路を引き続き使用します。

瀬戸大橋は独立した `seto-ohashi` エントリーです。`BridgePage` は公開前に照合済みの
`seto_ohashi_manifest.json` を読み、公式寸法と3言語の仮定を表示します。
`bridge-artifact-validation.mjs` がモデル・図面・エクスポーターのハッシュと
橋長・中央支間の可編集寸法を検査します。塔専用カタログに橋を混在させません。

| 情報 | 編集元 |
| --- | --- |
| 改訂、モデル名3言語、全高、モデルGL、公式案内高さ、ファイルパス | `output/review/tokyo_*_manifest.json`。CAD再生成時に更新 |
| 寸法・改訂の独立した公開前検証 | `web/scripts/tower-artifact-validation.mjs` |
| 出典URLの役割、ファイル種別と表示キーの対応 | `web/scripts/landmark-catalog.mjs` |
| 写真近似の範囲など、3言語の編集文 | `web/src/landmark-model-notes.json` |
| 操作ボタン、分類、配布ファイル名の3言語訳 | `web/src/landmark-copy.ts` |
| 生成物（直接編集しない） | `web/src/landmark-catalog.json` |

通常は `web/` の `npm run prepare:artifacts`、`npm test`、`npm run build` が、
公開前のCAD照合に成功した後で画面用カタログも更新します。
カタログだけを更新・照合するコマンドは、リポジトリのルートで実行します。

```bash
node web/scripts/landmark-catalog.mjs
node web/scripts/landmark-catalog.mjs --check
node --test web/tests/landmark-catalog.test.mjs
```

`--check` は更新漏れを検出し、ファイルを書き換えません。
単独のカタログ生成はCADの検証済み判定を更新しません。
公開時は従来どおりソース・成果物のSHA照合と独立した寸法検証を通します。
東京タワーのモデルGLと公式案内の150 m/250 mは別の欄として保持します。

初回読み込み中の概形は、同じカタログの `loadingPreview.svg` に含まれる10 KB未満の
インラインSVGです。保存済みプロファイルの制御点と展望施設の幅・上下端を用います。
東京タワー上部はR07の輪郭近似パラメーターを反映し、スカイツリーは粗い制御点の
折れ線で概形を示します。断面変換・格構・設備を含む精密な立面図ではありません。
アンテナの幅を制御点から確定できない部分は中心線のみを表示します。
`sourceSha256` はID・改訂・選択した寸法制御値を一定順のJSONで直列化したSHA-256で、
マニフェストファイル全体のハッシュではありません。`sourceDigestScope` に方式を記録します。
軽量概形の表示は詳細GLBや平面図の先読みを遅らせません。

## 简体中文

地标的版本、名称、高度、模型GL、官方案内高度及下载路径，统一由CAD清单生成。
三语编辑说明保留在稳定的模型ID下；按钮与文件名的翻译继续由显示键管理。
`--check` 只检查生成目录是否过期，不改写文件，也不替代CAD来源、尺寸及成果物验证。

## English

Landmark revisions, translated names, heights, model GL levels, nominal visitor levels and download
paths are generated from the saved CAD manifests. Editorial notes remain keyed by stable model ID;
control and download labels use stable translation keys. `--check` detects stale generated metadata
without rewriting it. Standalone catalog generation does not certify CAD provenance, dimensions or
artifacts; independent publication checks remain mandatory.
