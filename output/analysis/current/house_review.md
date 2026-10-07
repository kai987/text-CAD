# R22 承重输入与空间利用率分析

这是演示方案的计算准备与几何统计。整体承重、基础承载和法规合规均未判定。

## 空间面积

全部毫米尺寸为演示假设。面积按房间多边形并集重算，分母为建筑外轮廓投影。

| 楼层 | 外轮廓投影㎡ | 室内分配投影㎡ | 排除楼梯区㎡ | 排除楼梯比例 |
| --- | ---: | ---: | ---: | ---: |
| 1F | 59.6232 | 52.1746 | 48.6446 | 81.59% |
| 2F | 59.6232 | 52.0336 | 46.8656 | 78.60% |
| 合计 | 119.2464 | 104.2082 | 95.5102 | 80.09% |

包含楼梯投影的分配比例为 **87.39%**。LDK及三卧室合计 **74.3806㎡**。

阁楼储物板面另计 **24.5384㎡**，扣除检修口；最高净高 **1350 mm**，不加入两层分母或分子。二层阳台也单列排除。

这些指标不是法定延床面积，也不是扣除家具的自由通行面积。楼梯区包含楼梯洞口投影；外轮廓余量包含墙带、门槛和间隙。尚未给出效率优劣等级。

### 1F 房间

| 房间 | 净分配投影㎡ |
| --- | ---: |
| LDK | 33.9500 |
| 玄関 | 3.0400 |
| 浴室 | 3.3124 |
| 洗面・脱衣 / 洗濯 | 5.2962 |
| トイレ | 1.6380 |
| 階段 | 3.5300 |
| 階段下収納 | 1.4080 |

### 2F 房间

| 房间 | 净分配投影㎡ |
| --- | ---: |
| 主寝室 | 14.7600 |
| 洋室 2 | 12.8030 |
| 洋室 3 | 12.8676 |
| ホール / 洗面 | 4.7970 |
| トイレ | 1.6380 |
| 階段 | 5.1680 |
| バルコニー（室外，排除） | 7.1910 |

## 门、房间与阁楼入口关系

读取保存后的CAD清单，沿每个名义洞口的全宽测量墙面外2 mm处的房间覆盖。关联图只表示房间之间存在对应洞口，不代表无障碍通行、门扇操作或疏散合格。门宽未扣除实际门框、把手及安装间隙。

| 楼层 | 洞口 | 关联房间 | 名义宽mm | 全宽对应关系 | 家具包络重叠数 |
| --- | --- | --- | ---: | --- | ---: |
| 1F | D01 | outside ↔ foyer | 900 | 对应 | 0 |
| 1F | D02 | foyer ↔ ldk | 900 | 对应 | 0 |
| 1F | D03 | ldk ↔ wash | 800 | 对应 | 0 |
| 1F | D04 | wash ↔ bath | 750 | 对应 | 0 |
| 1F | D05 | ldk ↔ wc | 700 | 对应 | 0 |
| 1F | O02 | ldk ↔ stairs | 900 | 对应 | 0 |
| 1F | D07 | ldk ↔ under_stairs | 700 | 对应 | 0 |
| 2F | D21 | hall ↔ master | 750 | 对应 | 0 |
| 2F | D22 | hall ↔ bed2 | 800 | 对应 | 0 |
| 2F | D23 | hall ↔ bed3 | 750 | 对应 | 0 |
| 2F | D25 | hall ↔ wc | 700 | 对应 | 0 |
| 2F | O22 | hall ↔ stairs | 900 | 对应 | 0 |
| 2F | D26 | master ↔ balcony | 1600 | 对应 | 0 |
| 2F | D27 | bed2 ↔ balcony | 1800 | 对应 | 0 |

房间关联路径：

- 1F bath：outside → foyer → ldk → wash → bath
- 1F foyer：outside → foyer
- 1F ldk：outside → foyer → ldk
- 1F stairs：outside → foyer → ldk → stairs
- 1F under_stairs：outside → foyer → ldk → under_stairs
- 1F wash：outside → foyer → ldk → wash
- 1F wc：outside → foyer → ldk → wc
- 2F balcony：stairs → hall → bed2 → balcony
- 2F bed2：stairs → hall → bed2
- 2F bed3：stairs → hall → bed3
- 2F hall：stairs → hall
- 2F master：stairs → hall → master
- 2F stairs：stairs
- 2F wc：stairs → hall → wc

检修梯展开包络与底端站位合计占用二层走廊投影 **0.8430㎡**。以下为占用区域各X区间中点的局部南北向截线，不是连续绕行路径的最小净宽：

| X区间mm | 剩余南北向线段长度mm |
| --- | --- |
| 2199.92–2799.92 | 125.00 / 1025.00 |
| 2799.92–3380.00 | 150.00 / 1050.00 |
| 3380.00–3555.00 | 150.00 / 150.00 |

展开期间的同时通行、上下口净高和选定产品安全操作仍待核定。不能因房间关联图连通或局部余留投影存在，就认定检修梯展开时可安全绕行。

几何关系冲突记录 **0 项**。阁楼口/上下站位范围、楼梯和厕所的跨层投影差值、每扇门两侧的实际覆盖长度保留在JSON。

家具检查采用保存的矩形包络，转角沙发内空及桌下空间也包含在包络中；尚未计入全部厨房、浴室、收纳固定设备，也未模拟门扇开合、人体通行或高度。投影对齐不能证明设备管线、结构支承或传力连续。

## 承重计算准备

未填写工程资料 **22 项**。

| 部位 | 候选简化模型 | 输入状态 |
| --- | --- | --- |
| ldk_transfer_beam | W / simple | awaiting_inputs |
| balcony_candidate | W / cantilever | awaiting_inputs |
| attic_joist_or_header | W / simple | awaiting_inputs |

JSON保留每项缺失输入、原始输入、源文件SHA-256和计算程序SHA-256。每个部位必须重新确认构件、实际支承、有效跨距、分担荷载和材料参数；候选简支/悬臂类型也须复核。

工具只支持等截面小挠度弹性梁：全跨向下均布荷载，加简支梁跨中或悬臂梁自由端点荷载。输出弯矩、剪力、弹性挠度、弹性弯曲应力和支座反力。支座弯矩按绝对值报告。输入单位为mm、kN/m、kN、N/mm²、mm⁴和mm³，1 kN/m = 1 N/mm。

输入必须完整、支承/荷载来源非空并显式确认假设，才计算该单梁弹性需求。用户可提供弯曲应力和挠度限值，结果只比较这两个限值。即使二者满足，整体承载结论仍为null。RC案例要求专用配筋/裂缝/刚度模型，本工具不计算其承载。

不能把展示梁截面、阳台进深、房间跨度或楼板厚度直接当作工程选型。尤其悬臂阳台还需支座、回跨梁、连接、挠曲转角及防水细节设计。

未完成的整体验算：

- gravity/wind/snow/seismic combinations and actual tributary load paths
- wall resistance/distribution/torsion, diaphragm and storey drift
- column stability, shear, vibration and long-term deformation
- joints, anchorage, uplift, balcony backspan and connection rotation
- attic hatch reinforcement and concentrated storage/support loads
- foundation reactions, soil bearing/settlement and reinforcement
- fire, site/road/zoning and statutory floor/storey classification

## 下一项设计工作

先由结构设计者确认LDK梁、阳台和阁楼床组的传力与支承，选择实际W/S/RC材料体系，再填写工程输入。几何面积统计可现在复算；承重计算不以未知荷载代入默认值。当地法规适配仍待真实地块、道路和用途分区。

方法依据及边界见 [使用说明](../../../analysis/README.md)。本报告没有变更STEP、GLB或已确认户型。
