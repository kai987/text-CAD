# 四地 × 三种结构比较 / 4都市 × 3構造比較 / Four cities × three systems

## 简体中文

R07 将东京、大阪市、京都市、名古屋市的官方法规参考与 W、轻钢 S、RC 三套独立参数化结构草案组合为 **12 套条件方案**。原一户建建筑模型、公寓和确认过的一、二层图纸继续保留。三套结构文件是同一坐标系内的结构与概念基础叠加层，不包含原建筑饰面、家具或场地外构。

| 结构 | 草案表示 | 必须进一步设计的内容 |
| --- | --- | --- |
| W 木结构 | 柱、梁、土台、候选耐力墙、阁楼搁栅及屋架 | 现行重量对应壁量、墙分布、柱梁截面、水平构面、抗拔件和连接 |
| S 轻钢结构 | 薄壁空心构件、支撑及节点示意 | 厂商／工法选择、局部屈曲、支撑与反向荷载、节点、锚固、防火与防腐 |
| RC 钢筋混凝土结构 | 混凝土柱、梁、楼板和候选剪力墙 | 自重、柱梁墙板承载、节点、配筋及锚固、变形、抗震与建筑净空间协调 |

**城市选择不是截面验算。** 四地共用国家法规，并叠加地区风雪条件、地方处理基准和地块指定。没有地址、地勘、材料等级和实际荷载时，同一种结构在四地共用几何；城市选择改变审核依据与输入清单，不凭城市名称任意放大或缩小柱梁。基础必须按每种体系重新确定反力、地基承载、沉降、抗滑抗倾覆和配筋。

7280 × 7280 mm、层高2800 mm、阁楼最高完成净高1350 mm及全部构件尺寸仍为**演示假设**。RC 草案采用300×300 mm柱和300×400 mm梁，保持原室内周圈边界并向外伸出120 mm，结构周圈为7520 × 7520 mm；外墙、建筑面积和场地退界需重新协调，实际影响记录在结构清单中。既有建筑壳体不能直接视为 RC 或轻钢结构的正式围护构造。阁楼低于1.4 m也不能单独证明免计楼层或面积，须检查地方余剩空间、面积、开口、楼梯、天花及使用条件。

详细官方出处、适用范围和核查日期见 [四地法规参考](regulations_R07.md)。`output/review/regulatory_profiles_R07.json` 保存可追溯的法规参考；`structural_variants_R07.json` 保存三种结构几何与待核定事项；`structural_cases_R07.json` 索引12份独立条件方案。每份方案的结构承载、法规适合和建筑确认结果均为 `null`，不是“合格”。本项目未出具结构计算书或施工图。

## 日本語

R07は東京都・大阪市・京都市・名古屋市の公式参考資料と、W造・軽量S造・RC造の独立したパラメトリック構造案を組み合わせた **12の条件付きデモ案**です。確認済みの1・2階間取り、既存の戸建て・マンションモデルは保持します。各STEP／GLBは同じ座標系の構造・仮基礎レイヤーで、仕上げ・家具・外構は含みません。

都市の切替は断面の検証ではありません。全国共通の法令に地域の風・積雪条件、行政の取扱いと敷地指定が加わります。所在地・地盤・材料・実荷重が不明なため、同一構造の形状は都市間で共用し、参考基準と未確定入力を切り替えます。W造は必要壁量・壁配置・接合、軽量S造は薄板の座屈・ブレース・接合と工法選定、RC造は柱梁壁板・配筋・定着と重量増への対応が必要です。基礎反力・支持力・沈下・配筋は構造ごとに再設計します。

外形7280 × 7280 mm、階高2800 mm、小屋裏最高仕上げ内法高さ1350 mmと部材断面はすべて**デモ用仮定**です。RC案の300×300 mm柱と300×400 mm梁は室内周圈の境界を保持して外側へ120 mm突出し、構造外形は7520 × 7520 mmです。外壁・建築面積・敷地境界との調整が必要です。既存外壁をそのまま実構造の壁仕様とはみなしません。小屋裏の高さだけで階数・面積の除外は確定できません。出典・適用範囲・確認日は[公式参考資料](regulations_R07.md)に記載。12件のJSONで耐力、法適合、建築確認の結果は `null` です。構造計算書・施工図ではありません。

## English

R07 combines official reference profiles for Tokyo, Osaka City, Kyoto City and Nagoya City with three independent parametric structural concepts: timber W, lightweight steel S and reinforced concrete RC. This produces **12 conditional demonstration cases**. User-confirmed architectural plans, the original house and the apartment remain unchanged. The new STEP/GLB files are structural and conceptual foundation overlays in the same coordinate system, without finishes, furniture or landscaping.

Selecting a city does not verify member sizing. National law is supplemented by regional wind/snow conditions, local interpretations and parcel-specific designations. Without an address, ground investigation, material grades and actual loads, each material system shares geometry across cities. City selection changes review references and missing inputs. W needs current weight-based wall/column checks, diaphragm and connection design; lightweight S needs system selection, thin-wall buckling, bracing and connection checks; RC needs member/joint capacity, reinforcement, anchorage and architectural clearance coordination. Each system requires new foundation reactions, bearing, settlement and reinforcement design.

The 7280 × 7280 mm outline, 2800 mm storey height, 1350 mm maximum finished attic height and all sections are **demonstration assumptions**. The assumed 300×300 mm columns and 300×400 mm perimeter beams retain the interior perimeter faces and project 120 mm outward, producing a 7520 × 7520 mm structural perimeter. Façade, statutory area and site setbacks need further coordination. Existing architectural envelopes are not engineered steel or RC wall assemblies. Attic height alone does not establish exemption from storey or floor-area counting. [Official references](regulations_R07.md) state the jurisdiction, applicability and verification date. Capacity, statutory compliance and building-confirmation results remain `null` in all 12 case records. No structural calculation report or construction documents are issued.

## Reproduce / 重新生成 / 再生成

```bash
CADGEN_DAEMON=0 .venv/bin/python src/generate_structural_variants.py
.venv/bin/python src/generate_structural_cases.py
.venv/bin/python checks/validate_structural_variants.py
.venv/bin/python checks/validate_structural_cases.py
cd web
npm test
npm run build
```

`src/lib/structural_variants.py` contains geometric inputs; editable case records retain pending engineering inputs. Official references are curated rather than fetched silently during generation. Update their verification date and evidence when regulations change.
