# 制图基准来源

本项目采用[東京都建設局 CAD製図基準](https://www.kensetsu.metro.tokyo.lg.jp/documents/d/kensetsu/000067788)中的共通制图项目。核对的正文封面版本为 **令和6年4月、土木202404-01**；适用于土木工程，住宅方案的准用范围见 `docs/tokyo_cad_standard_mapping_R02.md`。

下载原件及全文提取只保留在本地，不纳入 Git。生成 CAD 和运行检查不依赖这些参考输入。如需重新核对，可从上面的官方链接下载，并保存为 `references/tokyo_cad_drafting_standard_000067788.pdf`。

本次核对资料的 SHA-256：

| 本地文件 | SHA-256 |
| --- | --- |
| `tokyo_cad_drafting_standard_000067788.pdf` | `1ce429f1e691195ab9e8d406060917b26b2fdfbddf0bc5767d68b0f9476238b0` |
| `tokyo_cad_drafting_standard_000067788.txt` | `fc179ffcc8c31cfde9a778dc102aaffd1b8df57519fd6e72ee56603bba2ded6e` |

`.txt` 使用 pypdf 按页提取，并以 `=== PDF PAGE n ===` 标识实际 PDF 页序。正文印刷页码与 PDF 页序不同。
