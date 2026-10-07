# 承重输入与空间统计 / 構造入力と面積集計 / Engineering inputs and space review

[中文](#中文) · [日本語](#日本語) · [English](#english)

## 中文

本目录是现有CAD的只读分析工具。当前图纸、STEP、GLB和已确认户型不变。先验证CAD生成记录，再读取保存后的平面、模型假设和工程缺失项。生成报告记录三份源JSON、输入和程序的SHA-256；模型改动后旧输入表会被拒绝，必须重新核对。

在仓库根目录运行：

```sh
.venv/bin/python analysis/house_review.py --init-inputs output/analysis/current/engineering_inputs.json
.venv/bin/python analysis/house_review.py --inputs output/analysis/current/engineering_inputs.json
.venv/bin/python -m unittest analysis.test_house_review -v
```

第一条创建未填写的JSON，拒绝覆盖已有输入。第二条输出`house_review.json`和`house_review.md`。不带参数运行则使用全空工程输入生成几何面积统计。仓库内报告输出限定在`output/analysis`，不覆盖CAD生成物。报告不是新的CAD发布证明。

面积：以保存的房间多边形并集为分子、外轮廓投影为分母；分别给出包含/排除楼梯区的两种比例。阳台和阁楼单列，不加入两层合计。检查多边形、面积记录、范围、重叠、楼层编号和房间分类。面积含家具及设备占地，楼梯区含洞口投影，余量含墙带/门槛/间隙；法定面积、自由通行面积和效率等级不推定。结构体系W/S/RC改动墙厚及截面后须重新统计。

计算表：先填写所在地、地盘、材料、荷载和所选体系的专项资料。LDK转移梁、无柱阳台、阁楼根太/洞口梁分别预留案例；默认的简支/悬臂模型只是候选，实际支承与传力须由设计者确认。禁止直接把房间尺寸、阳台进深或展示截面当作有效跨度或工程选型。`assumptions_reviewed`、荷载/材料来源、构件/支承来源和六个基本数值全部齐全才执行单梁弹性计算。

支持等截面、小挠度Euler–Bernoulli梁，全跨向下均布荷载，可叠加简支梁跨中点荷载或悬臂自由端点荷载。跨度L用mm；均布w用kN/m（数值等于N/mm）；点荷载P用kN并内部转为N；E用N/mm²；I用mm⁴；截面模量W用mm³。这里的截面模量W不是结构体系W造。P=0必须显式填写，null不能当作零。点荷载任意位置、连续梁、框架、扭转、剪切变形、材料非线性及二阶效应不支持。

| 理想模型 | 弯矩绝对值（N·mm，P转为N） | 最大挠度（mm） |
| --- | --- | --- |
| 简支＋跨中点荷载 | wL²/8 + PL/4 | 5wL⁴/(384EI) + PL³/(48EI) |
| 悬臂＋自由端点荷载 | wL²/2 + PL | wL⁴/(8EI) + PL³/(3EI) |

弯曲应力为M/W。选填的许用弯曲应力与挠度限值仅用于该案例需求/用户限值比；不自动采用日本法规限值。输出弯矩、剪力、支座反力、弹性挠度和弯曲应力，无整体“通过”标记。RC案例不运行此梁模型，保留配筋、裂缝、有效刚度与徐变的专用计算要求。木材徐变/荷载持续时间、薄壁钢局部/整体屈曲、连接刚度等均未包括。填完表也不会自动证明建筑承重。

仍须完成整体荷载组合、抗震/抗风、耐力壁和水平构面、柱稳定、梁剪切、振动/长期变形、节点/抗拔、阳台回跨和连接、阁楼洞口加固、基础/地盘，以及法规和地块审查。所有当前模型尺寸均为演示假设；正式设计须由日本具备相应资格的建筑士完成。

## 日本語

保存済みCADを読み取る補助ツールです。図面・STEP・GLB・確認済み間取りは変更しません。CADの生成履歴を先に検証し、平面・モデル条件・不足する構造入力を読み込みます。入力と出力は元データのSHA-256に結び付けられ、モデル更新後の古い入力は拒否されます。上記コマンドで空欄の入力JSON、面積と構造準備のMarkdown/JSONを生成できます。入力作成時は上書きしません。

面積比は室ポリゴンの和集合を外形投影面積で割ったものです。階段区画を含む/除く両方を表示し、バルコニーと小屋裏は別集計とします。家具・設備の占有を差し引いた自由通行面積や、壁芯による法定床面積ではありません。階段には開口の投影が含まれます。重複・範囲・記録面積を検証し、W/S/RCの壁厚・断面が確定した後は再集計が必要です。

LDK梁・柱なしバルコニー・小屋裏床組の候補ケースを用意します。支点条件、実際の有効スパン、分担荷重、材料と出典、仮定の確認が揃うまで計算しません。部屋寸法や表示用断面を構造入力に自動転用しません。単純支持梁は全長等分布荷重＋中央集中荷重、片持ち梁は全長等分布荷重＋先端集中荷重に限定した一定EI・小変形の弾性計算です。単位と式は上表を参照してください。null荷重をゼロとは扱いません。

曲げ・せん断・反力・たわみ・弾性曲げ応力度と、利用者が指定した限界値との比を出力します。日本法令の限界値は自動設定せず、建物の構造合否は出しません。RCは配筋・ひび割れ・有効剛性・クリープの専用モデルが必要なため、この計算を実行しません。耐震・耐風、接合、座屈、長期変形、基礎・地盤、敷地と法規は別途設計・審査が必要です。現モデル寸法は全てデモ仮定です。

## English

This companion tool reads the saved CAD without changing drawings, STEP, GLB or the accepted layout. It first verifies CAD provenance. Source JSON, inputs and analysis code are SHA-256 bound; stale input templates are rejected after model changes. Run the commands above from the repository root to create an unfilled input JSON and Markdown/JSON reports. Template initialization refuses to overwrite existing inputs.

Space ratios use the union of room polygons divided by exterior-outline projection. Both stair-inclusive and stair-exclusive metrics are reported. Balcony and attic are separate. These are neither statutory wall-centre floor areas nor unobstructed walkable areas: furniture/equipment are not deducted and stairs include openings in projection. Polygon validity, containment, overlap and recorded areas are checked. Recalculate after actual W/S/RC wall thicknesses and member sizes are selected.

LDK transfer beams, the unsupported balcony and attic joists/headers have separate candidate cases. Effective span, supports, tributary loads, materials and references require explicit review. Display geometry is never automatically treated as engineering input. The limited constant-EI, small-deflection Euler–Bernoulli calculator supports a full-span downward UDL plus a midspan point load for simple supports or a free-end point load for a cantilever. Units and equations are in the table above. Unknown loads stay null; zero must be entered explicitly.

Results contain moments, shear, reactions, elastic deflection and bending stress. Optional user-supplied stress/deflection limits produce demand-to-limit ratios; no Japanese code limit or whole-building pass is inferred. RC cases require dedicated reinforcement, cracking, effective-stiffness and creep analysis and are not calculated. Global load combinations, lateral resistance, joints, buckling, long-term deformation, foundation/soil and site/regulatory review remain outstanding. All current model dimensions are demonstration assumptions.

## 方法来源 / 参考資料 / Method references

- [MIT Unified Engineering: beam standard solutions, p.4](https://ocw.mit.edu/courses/16-01-unified-engineering-i-ii-iii-iv-fall-2005-spring-2006/4c41fc048425a6db74633c1da8a3d9cc_spring04_pset3.pdf). Educational elastic formulas; no Japanese code/design approval is inferred. Verified 2026-10-07.
- [MLIT wall/column requirements reflecting actual building weight](https://www.mlit.go.jp/jutakukentiku/build/jutakukentiku_house_tk_000166.html). Actual building load/material data are required; display geometry does not determine resistance. Verified 2026-10-07.
- [MLIT 2025 timber planning/design standard](https://www.mlit.go.jp/common/001880381.pdf). Government-facility design guidance used as a method reference; not asserted as mandatory private-house approval criteria. Verified 2026-10-07.
