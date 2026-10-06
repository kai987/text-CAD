# R12 阳台进深1m、取消支柱 / 柱なしバルコニー / Cantilever balcony proposal

2026-10-07，根据用户指示将阳台进深由1500改为1000 mm，移除三根支撑柱及其450方独立基础。房间、门窗位置、主体8190 × 7280、层高2800、屋顶、阁楼、R11敷地和双车位保持。全部尺寸均为**演示假设**。

| 项目 | R12 |
| --- | --- |
| 阳台外形 | 6180 × 1000 mm，6.18㎡ |
| 净空间 | 5980 × 900 mm，5.382㎡ |
| 西／东边界 | X=2010／8190 |
| 支柱与独立基础 | 全部取消；不增加虚构的已设计悬挑梁 |
| 晾衣架平面占位 | X=4480～6380、Y=-650～-450，避开D26阳台门 |
| 玄关平台 | 1300 mm深，外沿300 mm超出阳台投影 |
| 玄关独立雨棚 | 保持取消；实际风雨防护未核定 |
| 停车与敷地 | 并列两位各2800 × 5000；140.4182㎡，沿用R11 |

源码保留 `balcony_supports` 开关供后续方案修改，当前为false。移除基础后同时恢复土层、面层及车位划线，避免残留孔洞。平面晾衣架与三维实体共用参数；净900 mm深不构成通行或晾衣操作的法规认证。

STEP/GLB及两层平面、配置图、网页SVG与三语说明同步修改。为保持现有下载地址，PDF与部分DXF/JSON保留R10/R05兼容文件名，但现行平面图与配置图内容标为R12。阁楼及W/S/RC叠加层几何未改，仍引用原来的结构草案；它们并未包含经过计算的一米悬挑设计。

## 工程边界

当前无柱板面仅表达悬挑空间方案。木结构需核定挑梁与回跨、连接及挠度；轻钢需核定梁截面、节点、屈曲及防腐；RC需核定负弯矩钢筋、锚固、裂缝及热桥。各体系荷载、支承、防水坡度、排水和栏杆锚固尚未计算。此次修改不确认施工可行、承载、耐震或法定面积减免。

## 日本語

バルコニーは外形6180 × 1000 mm、内法5980 × 900 mm。支持柱3本と独立基礎を撤去し、物干しを東側へ移動。玄関ポーチ先端300 mmは露出し、独立庇はありません。柱なしの持出し案を表示するもので、W/S/RCの耐力・接合・たわみ・防水・排水は未設計です。

## English

The balcony measures 6180 × 1000 mm overall and 5980 × 900 mm clear. Three support posts and their footings are removed; the drying rack moves east. The outer 300 mm of the entrance porch is exposed, with no separate canopy. This models a cantilever proposal; capacity, connections, deflection, waterproofing and drainage are unengineered for all W/S/RC systems.
