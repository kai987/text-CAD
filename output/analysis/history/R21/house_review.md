# R21 承重输入与空间利用率分析

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
