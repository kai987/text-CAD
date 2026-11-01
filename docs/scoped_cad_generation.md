# モデル単位のCAD生成 / 按模型生成 / Scoped CAD generation

## 日本語

通常の対象は `house`、`apartment`、`river`、`tokyo-tower`、`tokyo-skytree` です。
`--model` を省略するか `all` を指定すると全モデルを生成します。

```bash
# 生成対象とコマンドの確認だけ。ファイルは変更しません。
.venv/bin/python src/cad_pipeline.py --regenerate --model tokyo-tower --dry-run

# 東京タワーだけを生成。最後の検証は全モデルに対して実行します。
.venv/bin/python src/cad_pipeline.py --regenerate --model tokyo-tower

# 共通の塔体パラメーターやエクスポーターを変更した場合は両方を指定します。
.venv/bin/python src/cad_pipeline.py --regenerate --model tokyo-tower --model tokyo-skytree

# チェックと生成パイプラインだけを変更し、保存済みCADが同一の場合。
.venv/bin/python src/cad_pipeline.py --refresh-validation

# 通常の読み取り専用リリース検証。
.venv/bin/python src/cad_pipeline.py --validate
```

生成はソース・既存成果物をコピーした一時作業ツリーで実行します。コピー先には
`.git`、`.venv`、`node_modules`、Rustの `target` を含めません。Python環境は呼び出し元と同じものを使用します。
全CADバリデーター、共有のPythonテスト、ソース／成果物のSHA-256照合を通過してから、変更された対象モデルの成果物を置き換えます。
生成・検証の失敗、または実行中のソース／成果物の編集が検出された場合、現在のCADとローカルプレビュー用ファイルを置き換えません。

複数ファイルを一度のファイルシステム操作で切り替えることはできないため、置き換え中は公開ゲートを無効にし、ゲートを最後に保存します。捕捉できた置き換えエラーでは旧ファイルと旧ゲートを復元します。
強制終了や電源断の場合も有効なゲートのない途中状態は公開できません。必要ならGitとの差分を確認し、再生成してください。

対象外モデルの成果物は前回リリースと一致している必要があります。共通ソースの変更は、そのソースを利用するモデルも選択する必要があります。
Pythonのローカルimportを保守的に追跡し、未知の生成依存や解析コードの変更を部分生成で承認しません。その場合は `--model all` を使用します。
`--refresh-validation` はチェックとパイプラインの変更に限定し、生成ソース・解析コード・CAD成果物の変更を拒否します。
以前の生成日時・生成コマンド・生成ツールチェーンを保持し、今回の検証日時と環境を別に記録します。

## 中文

使用上面的命令可按 `house`、`apartment`、`river`、`tokyo-tower`、`tokyo-skytree` 选择模型；重复 `--model` 可选择多个模型。
不指定时仍生成全部模型。先在独立临时目录生成，再运行所有CAD检查、共享Python测试和哈希核验，成功后才更新当前文件，最后写入发布凭据。
失败或检测到并行编辑时保留现有模型与本地预览；替换文件时发生可捕获错误则回滚。
共享源文件变动必须同时选择其依赖模型，未知依赖及分析源码变动需完整生成。
`--refresh-validation` 仅用于检查／管线代码的修改：拒绝模型源码及CAD字节变化，保留原生成记录，另外记录本次验证信息。
本流程不改变演示尺寸、几何模型或工程／法规未核定的状态。

## English

Use the commands above to select `house`, `apartment`, `river`, `tokyo-tower`, or `tokyo-skytree`; repeat `--model` for shared dependencies. Omitting the selector retains full generation.
Generators run in an isolated copied tree. All CAD validators, shared Python tests and source/artifact hashes must pass before changed outputs are promoted, with the publication gate written last.
Generation/validation failures and concurrent edits leave the current CAD and preview files untouched. Caught promotion failures roll back replaced files; an abrupt interruption leaves no valid gate authorizing mixed outputs.
Changes shared by other generators require those models to be selected too. Unknown generation dependencies and analysis-source changes require `--model all`.
`--refresh-validation` permits only pipeline/check changes and requires every saved CAD byte to remain unchanged. Original generation time, commands and toolchain are retained; the new validation time and environment are recorded separately.
These workflow improvements do not certify model dimensions, engineering capacity or regulatory compliance.
