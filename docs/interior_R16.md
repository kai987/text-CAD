# R16 / 二层空间、开放楼梯与室内照明 / 2階再配置・室内照明 / Second floor and room lighting

单位 mm；8190×7280 主体、2800 层高及所有家具、设备、踏板、灯具尺寸均为演示假设。保持西南入口、西北楼梯、南侧8190×1000阳台及三间卧室。

二层中央长走廊被两间南向卧室吸收，主卧11.160㎡、卧室2为12.803㎡。阳台通过两间卧室各自的1600/1800宽双扇玻璃推拉门进入，门高2100。没有独立公共阳台通道。公共厅兼洗手区6.201㎡；厕所前隔间取消，在北向卧室角部预留凹入式600×450盆柜和镜子，750宽侧向通行空间为几何假设。两层厕所保留900×1700及上下对齐。北向卧室北窗600、东窗1800；三卧室分别配书桌、椅子、床边桌。

两跑楼梯踏板厚60、侧梁宽40/概念竖向深200，开放踢面间隙115；16段×175、踏面260、梯宽900保持。保留楼梯下储物间及侧梁下方的斜顶。镂空不会自动减少楼梯投影面积；主要减少实体填充并开放视线。连接、栏护、防坠落、防火、实际净空和荷载计算未完成，不能用于施工。

15盏室内灯按房间单独命名：一层7盏、二层7盏、阁楼1盏。一般房间吊灯、楼梯壁灯、阁楼吸顶灯。`indoorLights=on|off`独立于`lights=on|off`室外灯与`environment=day|night`；一键关闭全部室内灯，隐藏楼层、设备或切掉发光点后停止照明。家具开关不影响灯具。相对亮度、暖白色、尺寸只是渲染假设；未选灯具、未计算照度/眩光，未设计配线、防水或电路。

日本語：南2寝室は11.160/12.803㎡、中央廊下を統合。バルコニーは各寝室の引違い戸からアクセス。トイレ前室を共用ホールに統合し、凹部に600×450の手洗いと鏡を追加。北寝室の北窓600・東窓1800。3寝室にデスク・椅子・ベッドサイド。階段は踏板60、蹴込み開口115、ささら桁40×200の概念案。室内15灯を一括操作し、家具・屋外灯とは独立。耐力・接合・防火・照度・電気は未設計。

English: The south bedrooms absorb the central passage, with net areas 11.160/12.803 m² and separate balcony sliders. The former WC lobby joins the shared hall, with a recessed 600×450 wash basin and mirror. North bedroom windows are north 600/east 1800. All bedrooms have a desk, chair and bedside table. Open stairs use 60 mm treads, 115 mm riser gaps and conceptual 40×200 mm stringers; no floor-area saving is claimed. Fifteen indoor lamps have an independent master switch and follow visibility/cutting. All dimensions are demonstration assumptions; structural connections, guards, fire safety, photometry and electrical installation remain unengineered.

源码：`src/lib/house_redesign_plan.py`、`house_geometry.py`、`furniture_geometry.py`、`fixture_geometry.py`、`indoor_lighting.py`。STEP/GLB、DXF/PDF、SVG与W/S/RC叠加层从同一方案生成；结构层仍为候选布置，未据房间变化完成抗震或承载复核。兼容输出文件名中的旧修订号保留，内容修订由manifest标识。
