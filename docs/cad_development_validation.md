# モデル別の開発検証 / 模型开发验证 / Model development validation

## 日本語

`--validate-model` は、選択モデルの保存済みCADとモデル固有のテストを確認する開発用コマンドです。
共通のリリース・パイプライン・座標・STEP・GLBテストも実行します。瀬戸大橋だけを選ぶと、
東京タワーR09–R11の重い実体接続テストは実行しません。

```bash
# 実行するチェックを確認する。生成・検証・ファイル更新は行わない。
.venv/bin/python src/cad_pipeline.py --validate-model --model seto-ohashi --dry-run

# 保存された橋モデルだけを開発検証する。
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --validate-model --model seto-ohashi
```

このコマンドは元のCAD、プレビュー、`output/review/cad_release.json`を更新しません。
検証は一時コピー内で行い、検証器のレポートも元のディレクトリへ書き戻しません。
結果には`development_only: true`、`release_ready: false`を表示します。
合格結果は公開可能なリリース記録ではありません。

### 形状を試す場合

以下は選択モデルを直接出力してから、関連するチェックだけを実行する例です。
直接生成は選択したCAD出力を上書きします。現在のCADを残す必要がある場合は別のチェックアウトで実行します。
通常の安全な生成・公開準備は、後述のステージング付き`--regenerate`を使用してください。

```bash
CADGEN_DAEMON=0 .venv/bin/python src/seto_bridge_3d.py
.venv/bin/python src/generate_seto_bridge_plans.py
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --validate-model --model seto-ohashi
```

生成ソース・CADの変更により以前の公開ゲートは古くなります。開発検証に合格しても、
本番Webビルドは古いゲートを拒否します。公開前に完全なチェックを行います。

```bash
# 形状・図面を変更した場合：選択出力を安全に再生成し、全体検証後に反映する。
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate --model seto-ohashi

# チェック／パイプラインだけを変更し、全CAD出力が同一の場合。
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --refresh-validation
```

既定の`--regenerate`・`--validate`とCIグループの内容は変わりません。
共有ソースを変更した場合は、その生成依存を使うモデルをすべて選択する必要があります。
未選択モデルのCAD変更や依存元不明の生成ソースは拒否します。
共有の検証ソースだけを変更した場合も、公開ゲートの再検証が必要です。

瀬戸大橋の生成前には、CADカーネルを読み込まずにメタデータを事前確認します。
JSON往復時の型変化、非有限数、名前の重複、未対応形状、ゼロ寸法などを検出します。
この事前確認は、生成後の実体・接触・通行包絡の検証に置き換わるものではありません。

## 简体中文

使用`--validate-model --model seto-ohashi`，仅运行桥梁保存文件检查、桥梁测试及公共基础测试。
命令在临时副本中执行，不更新原CAD、预览或生产发布记录；输出明确标为开发用途、不可直接发布。
可重复`--model`选择共享依赖所需的模型。未选择模型的源文件或CAD发生变化时会拒绝执行。

直接生成器适合在独立工作副本中试验，会覆盖所选模型的输出。正式发布前仍须运行完整
`--regenerate --model seto-ohashi`；只修改检查代码时可运行`--refresh-validation`。
开发检查不会让旧生产记录重新生效。瀬户大桥另有生成前JSON、有限数值、命名和形状控制检查。

## English

`--validate-model --model seto-ohashi` runs the bridge's saved-artifact validator and model tests,
plus lightweight common release/pipeline/orientation/STEP/GLB tests. Checks run in a temporary copy;
live CAD, previews and the production release record remain unchanged. The result is explicitly
development-only and never release-ready. Repeat `--model` when generation dependencies are shared.
Changes to unselected outputs or unselected generation consumers are rejected.

For local experiments, direct model generators can be followed by this scoped check. They overwrite
selected CAD outputs, so use a separate checkout when preserving the current CAD matters. Before
publication, run the complete staged `--regenerate --model seto-ohashi`; use `--refresh-validation`
only for verification-code changes with unchanged CAD. Production Web builds keep rejecting stale gates.
Seto metadata preflight catches JSON type drift, nonfinite data, duplicate names and invalid shape
controls before loading a native CAD kernel. Saved-solid/contact/clearance checks remain mandatory.
