# R10 阳台扩展 / バルコニー拡張 / Balcony extension

2026-10-07。依据用户要求向右扩展到东侧外墙，并取消一层独立玄关雨棚。室内采用已确认的 [R09](house_redesign_R09.md)，保持全部房间边界、门洞、楼梯及屋顶。下列数据均为演示假设。

## 几何 / 寸法 / Geometry

| 项目 / 項目 / Item | R10 (mm) |
|---|---:|
| 主体 / 建物 / Body | 8190 × 7280 |
| 阳台西边 / 西端 / West edge X | 2010 |
| 阳台东边 / 東端 / East edge X | 8190 |
| 总宽深 / 外寸 / Gross width × depth | 6180 × 1500 |
| 净宽深 / 内寸 / Clear width × depth | 5980 × 1400 |
| 总面积 / 外寸面積 / Gross area | 9.27 m² |
| 净面积 / 内寸面積 / Clear area | 8.372 m² |
| 向东增加 / 東への延長 / East extension | 2540 |
| 支柱轴线 / 支持柱軸 / Support axes X | 2060 / 8140 / 5100 |

一层玄关平台完全处于阳台水平投影内；删除 `F1:D01:canopy`，保留门框、门扇、拉手、平台、台阶和照明。三根100 mm示意支柱与450 mm示意独立基础避开入口步道，编号1/2继续代表西/东侧，新增编号3为中间支柱。可在 Python 中调整 `balcony_left`、`balcony_width`、`balcony_depth` 和 `entrance_canopy`。

1階玄関ポーチをバルコニー投影で覆い、独立庇を省略。扉・枠・ポーチ・段・照明を保持。西端と室内間取りはR09と同じです。中央に支持柱案を追加し、入口歩道を避けています。

The balcony now covers the entrance porch. The separate canopy is omitted, while the door, frame, porch, steps and lighting remain. The west edge and R09 interiors stay fixed. An additional concept middle support is clear of the entrance path.

## 检查 / 検証 / Validation

平面168项、制图230项、保存后STEP/GLB几何3275项、外构827项、原有结构候选1152项、W/S/RC几何4035项均通过。网页完整测试初次133/134通过，新增中间支柱名称遗漏已修正，相关12项测试通过。Python/Rust原生53项通过。PDF共6页已逐页目视检查；网页已目视核对外观、一层、二层、4200 mm剖切及夜间切换，控制台无错误或警告。

历史R09图纸和记录保留。现行DXF、STEP、GLB、SVG及PDF同步为R10；部分补充文件保留R05/R06兼容文件名，内容标题为R10。

## 待定 / 未確定 / Pending

支承、连接、梁跨、荷载、挠度、防水、坡度、排水、雨水溅入、地基承载和当地法规均未计算或核定。平台投影覆盖不等于风雨条件下的实际防雨证明。既有RC结构候选与阳台的协调问题继续记录为待调整。三支柱方案不构成W/S/RC结构计算结论或施工图。

支持・接合・梁・荷重・たわみ・防水・勾配・排水・地盤・法規は未検証。投影の重なりのみで実際の防雨性能を認定しません。RC候補との干渉調整も未完了です。

Support sizing, connections, spans, loading, deflection, waterproofing, falls, drainage, wind-driven rain, ground capacity and local rules remain pending. Geometric porch coverage does not certify weather protection. Existing RC coordination issues remain unresolved; these are concept models, not construction documents.
