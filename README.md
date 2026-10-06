# 日本住宅参数化方案：一户建与 2LDK 公寓

**简体中文** | [日本語](README.ja.md) | [English](README.en.md)

一户建当前图纸版本：R02（日本制图基准准用版）。**用户已确认的 R01 平面布局保持不变**，三维模型继续使用该布局。房间名、面积、尺寸、门编号及家具文字采用高对比显示。

## 地基、围栏与院子（R05-3D）

新增独立 `foundation`、`yard`、`fence` 分组：概念贝塔基础底板与周圈立墙、入口支承和低阶、砂石院子、停车铺装与车挡、四块草坪、三株简化灌木，以及有真实空隙的横栅围栏。完整外观显示外构；内部预设隐藏外构，也可展开分类独立隐藏或单独查看。剖切高度始终以一层完成面 Z=0 为基准。

新增尺寸均为**演示假设**：地块 **11280 × 14780 mm（几何面积166.7184㎡）**，室外地面 **Z=-500 mm**，概念底板厚150 mm、周圈立墙宽140 mm，停车划线范围 **2800 × 5000 mm**。围栏地上高1200 mm，共28片透空面板、30根柱及30个柱脚；南侧车口净宽3000 mm、行人开口1800 mm。入口地面、低阶、原台阶、原门廊、玄关标高依次为-500／-330／-160／-25／0 mm。尺寸、植栽及材料均可在 `src/lib/site_geometry.py` 修改，基础不代表已设计的配筋、承载或地盘处理方案。

STEP / GLB 共537个具名实体，其中原424个房屋与阁楼实体保持。另附 `DXF/house_site_plan.dxf` 和 `output/pdf/house_site_plan_R05_JP.pdf`：A3、配置图1:100、概念基础断面1:25，保留可编辑文字和尺寸。确认的两层平面和阁楼图不重写。[参数与范围记录](docs/site_R05.md)。

```bash
.venv/bin/python src/generate_site_plan.py
CADGEN_DAEMON=0 .venv/bin/python src/house_3d.py
.venv/bin/python checks/validate_3d.py
.venv/bin/python checks/validate_site.py
```

## 储物阁楼（R04-3D）

在既有切妻屋顶内增加储物阁楼；确认的两层房间边界与 R03 屋顶外形保持。网页新增“阁楼内部”预设和阁楼楼板、内衬与低墙、收纳、入口护栏分类。检修入口组合独立显示，包含分别命名的盖板、梯梁和10级踏板；图中显示展开状态，隐藏表示关闭展示，不是折叠机械模拟。展开梯子会占用二层走廊。

新增尺寸均为**演示假设**：中央板面 **3680 × 6880 mm**，净检修口 **1200 × 650 mm**；扣除开口的板面几何投影为 **24.5384㎡**，不作为法定面积。板面 Z=5618 mm，内衬采用50 mm竖向展示预留，屋脊净高约 **2034 mm**、板面两侧边缘约 **971 mm**。这是低矮储物空间，尚未设计承重、实际梯具净空、保温通风或法规用途。

参数源为 `src/lib/attic_geometry.py`；STEP / GLB 包含 `attic` 和 `attic_access` 命名分组。补充图 `DXF/house_attic_plan.dxf` 保留可编辑文字和尺寸，`output/pdf/house_attic_plan_R04_JP.pdf` 为 A3、1:50 黑白审阅图，附东西净高断面。已确认的 R02 两层图纸不重写。三语界面、下载及 WebGL 不可用时的阁楼静态预览同步更新。[参数与范围记录](docs/attic_R04.md)。

```bash
.venv/bin/python src/generate_attic_plan.py
CADGEN_DAEMON=0 .venv/bin/python src/house_3d.py
.venv/bin/python checks/validate_3d.py
```

## 日式新建一户建外立面（R03-3D）

一户建采用暖白挂板、灰色与木色玄关、深灰切妻屋面和黑色窗框。新增屋面立缝、屋脊盖板、破风、檐底、檐沟、分层落水管、玄关雨棚与平台以及独立窗台水切；楼板外缘由连续外饰面包覆。外装尺寸、颜色与材质重复尺度均为演示假设，保留7280 × 7280 mm主体完成外轮廓、两层2800 mm层高及已确认的平面与门窗毛洞。

参数化源码在 `src/lib/exterior_geometry.py` 和 `src/lib/exterior_materials.py`。新增部件分别归入现有外墙、门、窗及屋顶分类，支持中日英名称、点选、隐藏与剖切；STEP包含实体与颜色，GLB另内嵌原创挂板及木纹材质。参考 [Nichiha、KMEW与YKK AP官方资料](references/japanese-house-exterior.md)，未再分发厂商图片、纹理或CAD模型。

## 家具与精细设备（R02-3D / A02-3D）

两套户型的三维画布上方均有「显示家具」选项，默认开启。床、沙发、茶几、餐桌椅和电视柜在每层 `F#:furniture` 下独立命名；可以统一开关，也能通过部件树按楼层隐藏或单独查看。开关保持当前楼层、视角和剖切高度，切换视图预设、语言或主题时保留家具选择。

`F#:fixtures` 细化了浴缸内胆、洗面盆与龙头、镜面、马桶、洗衣机舱门、厨房水槽和灶具。木材、布料、陶瓷、金属及玻璃使用不同颜色和表面粗糙度，网页用本地生成的环境光表现反光。家具和设备都包含在可下载的 STEP / GLB 中；原有标注平面图保留已确认布局，不随三维家具开关变化。

所有形状由 `src/lib/furniture_geometry.py`、`src/lib/fixture_geometry.py` 原创参数化生成，公开产品资料只用于尺寸和形态参考，未导入或再分发厂商模型，不代表实物选型或可安装性。参考来源及使用边界见 [家具与设备参考](references/interior-furnishings.md)。

## 在线查看

[打开房屋 CAD 查看页](https://kai987.github.io/text-CAD/)。画布上方可直接切换完整外观／一层内部／二层内部。部件树支持楼层、外墙、内隔墙、楼板、门、窗、收纳柜、楼梯和屋顶的显示与隐藏；点击名称或三维实体可高亮并查看所选语言的部件名，“单独”按钮隔离选定分类，顶部预设恢复显示。浏览器还支持旋转、缩放和水平剖切。平面页默认展示房间与尺寸，可切换完整 R02 A3 图框，支持矢量放大和下载可编辑 DXF；文件页提供 STEP、GLB、DXF、PDF 和参数说明。

进入页面时并行加载当前户型的三维模型及全部楼层平面图；从平面页或下载页进入也会准备三维场景。标签切换复用已解析图纸并保留三维视角、剖切和选择状态。切换户型时释放旧三维场景并预加载新户型，首次下载期间显示加载提示。

页面语言选择器支持**简体中文、日本語、English**。没有已保存选择时默认显示中文；选择保存在当前浏览器，下次访问恢复。切换后界面文案立即更新，保留当前页、楼层、视角、剖切、部件显示与选择以及平面缩放状态。网页房间表使用所选语言的房间名；原始 CAD、PDF、SVG 图纸中的日语标注及原始部件名保持不变。上方链接可切换本仓库 README 的语言版本。

页头的「颜色模式」提供系统／浅色／深色。首次访问跟随操作系统外观，选择保存在当前浏览器；选择「系统」时持续跟随系统外观变化。切换保留视角、部件显示与选择、剖切高度和平面缩放。深色模式调整界面和三维背景；原始 CAD、PDF 和 SVG 图纸的纸面保持白色，便于阅读，打印文件保持不变。

网页位于 `web/`，使用 React、TypeScript、Three.js 和 Vite；不依赖本地 Python 查看器。它直接读取已生成的 GLB，不改变 CAD 几何。STEP 和 DXF 提供原始文件下载，在线平面使用从原始 PDF 转换的 SVG，全部文字转为字形轮廓，不依赖访问者的中日文字体。完整纸面内容不变，平面范围采用同一 SVG 的裁切视口；两向总尺寸、房间名、门号、门弧和北向箭头均保留。模型内部保留原始 `F1`、`F2`、`stairs` 和 `roof` 及楼层内的八类节点，并通过 GLTFLoader 节点索引映射恢复原始名称。手机支持触摸旋转和缩放；浏览器无法运行 WebGL 时显示与当前预设匹配的静态预览。

使用 Node.js 24 或更新的兼容版本：

```bash
cd web
npm ci
npm test
npm run dev
# 生产构建与本地预览
npm run build
npm run preview
```

Rust/WASM 剖切试点位于 `rust/section-caps/`。默认继续使用 TypeScript；[启用 Rust 试验](https://kai987.github.io/text-CAD/?view=3d&mode=second&section=wasm)会按需加载 WASM，下载或初始化失败时回退到 TypeScript。切换页面保留试验参数，剖切计算不改动原始 CAD。Rust 使用 `f64` 计算、`f32` 输出，并与现有实现对照检查孔洞、收纳柜封口、楼梯开口、法线和坐标变换。Rust/WASM 暂未使用 Worker，仍在界面线程计算。

新增家具前模型的基准（Apple M1 Pro、Node 24.18.0，150次预热后测量）：每批处理111个不透明网格、四个高度（1200／2700／4200／5600 mm），包含几何适配、轮廓线和释放，中位数 TypeScript 3.360 ms、Rust/WASM 2.379 ms。79,235字节的 WASM 冷编译及初始化为15.199 ms；此数据不包含网络、浏览器帧或GPU渲染，不能推断页面帧率。以下命令在 `web/` 运行；普通测试和发布使用已提交的 WASM，不要求安装 Rust。

```bash
npm run bench:sections -- --edges
# 修改 Rust 核心后重建；工具链固定为 Rust 1.93.0
cargo install wasm-bindgen-cli --version 0.2.114 --locked
npm run build:wasm
npm test
npm run build
```

`build:wasm` 执行原生 Rust 测试并生成 WASM／JS绑定及源码和产物哈希。普通测试和构建拒绝过期产物；独立 Rust 工作流执行原生测试、Clippy 和 WASM 编译。基准脚本支持 `--output /绝对路径/result.json` 保存结果。

开发和构建时从仓库复制 28 个 CAD、图纸及说明文件（含两层矢量预览），并生成 SHA-256 清单；生产构建再次核对副本。矢量元数据还记录来源 PDF 的哈希、SVG 哈希和裁切内的标注边界；源 PDF 变化或 SVG 不匹配时拒绝构建，要求先重新转换。`web/public/artifacts/`、派生数据和 `web/dist/` 不提交到 Git。

修改方案后先重建 CAD、PDF 并完成对应检查，再更新矢量预览；转换工具在本地使用 Python，GitHub Pages 构建直接读取已提交的 SVG：

```bash
uv pip install --python .venv/bin/python PyMuPDF==1.26.7
.venv/bin/python web/scripts/generate-plan-svg.py
```

提交 `output/vector/house_1f_plan.svg`、`house_2f_plan.svg` 与 `web/src/plan-preview-metadata.json` 后重新构建。当前裁切范围及必需标签对应已批准的7280毫米演示方案；若平面尺寸或纸面排版改变，需要重新核对裁切和标注。

`.github/workflows/pages.yml` 在 `main` 推送时执行安装、模型控制测试、TypeScript 检查、构建和文件哈希检查，然后发布到 GitHub Pages。在线尺寸仍是演示假设，现有结构和管线待定项见下文。

## 新增日本 2LDK 公寓（A01）

[直接打开公寓](https://kai987.github.io/text-CAD/?model=apartment&view=3d)。页头可在原两层一户建与公寓之间切换；公寓默认显示室内剖视，提供完整户型、天花、阳台及厨卫设备的独立显示控制。单层平面、下载文件、房间面积和说明均随户型切换；语言与明暗偏好保留。加上 `&section=wasm` 可对公寓使用 Rust 剖切试点。

公寓外轮廓 **7800 × 8400 mm（65.52㎡）**、层高 **2800 mm**、净高 **2500 mm**均为演示假设。65.52㎡是外轮廓矩形面积，**不是室内净面积或法定专有面积**。房间净边界合计 **56.54㎡**（含家具占地），南侧阳台板投影 **11.70㎡**（7800 × 1500 mm）单独列出。公寓为单个住户的方案，不包含整栋楼、公共走廊或邻户。

北侧玄关经厅廊到两间卧室、厕所、洗面脱衣室和南侧 LDK；浴室经洗面脱衣室进入，LDK 通向收纳和南阳台。图纸记录门窗尺寸、开启方向、房间净尺寸及面积，DXF 保留可编辑文字和原生尺寸。所有朝向、墙厚、家具设备和门窗尺寸均为方案假设，结构、设备管线及建筑法规仍待专业核查。

- 参数化入口：`src/apartment_2ldk.py`；平面与几何参数：`src/lib/apartment_plan.py`、`src/lib/apartment_geometry.py`。
- 三维：`GLB/apartment_2ldk.glb`、`STEP/apartment_2ldk.step`；节点为 `F1`（单元室内）、`ceiling`、`balcony`，厨卫占位为 `F1:fixtures`。
- 平面：`DXF/apartment_2ldk_plan.dxf`、`output/pdf/apartment_2ldk_plan.pdf`、`output/vector/apartment_2ldk_plan.svg`。
- 参数及图面追踪：`output/review/apartment_2ldk_manifest.json`、`output/review/apartment_2ldk_preview.json`。

```bash
.venv/bin/python src/apartment_2ldk.py
.venv/bin/python checks/validate_apartment.py
cd web
npm test
npm run build
```

公寓独立生成与检查，不需重新生成一户建。生成器需要 `requirements.txt` 中的 Python 依赖；网页发布只读取已提交的 CAD、PDF 与矢量资产。

## 文件

- `src/lib/house_plan.py`：两层共享的毫米参数、房间净边界、墙体、门窗、家具占位和假设。
- `src/generate_plans.py`：用 ezdxf 生成可编辑的 TEXT / DIMENSION 标注与房屋平面；同时输出两页 A3 横向、1:50 的审阅 PDF。
- `src/lib/jp_drafting.py`、`src/lib/jp_sheet.py`：规范式图层、纸面字高与线宽，以及共用的 A3 图框、表题栏、面积表和注记。
- `DXF/001D0PL2-1FPLAN.DXF`、`DXF/002D0PL2-2FPLAN.DXF`：R02 规范式文件名的两层平面。
- `DXF/house_1f_plan.dxf`、`DXF/house_2f_plan.dxf`：R2018、毫米、模型空间 1:1。
- `output/pdf/house_floor_plans_R02_JP.pdf`：当前两层平面、图框、表题栏、面积表和假设。打印时使用 A3 实际尺寸，不要自动缩放。R01 PDF 保留为历史版本。
- `docs/tokyo_cad_standard_mapping_R02.md`：所引用基准的章节、页码、住宅准用方式和未覆盖项。
- `checks/validate_jp_drafting.py`、`output/review/validation_jp_drafting.json`：保存后图层、字高、色彩、线宽、原生尺寸及纸空间的检查。
- `output/review/design_manifest.json`：机器可读参数、所有假设与房间面积。
- `checks/validate_plans.py`：针对当前布局的几何、门、楼梯和真实 DXF 文件检查。
- `output/review/validation.json`：实际检查结果及尚未验证的内容。
- `src/lib/house_geometry.py`：复用确认平面的三维参数、墙体开洞、楼板、切妻屋根、门窗和 U 型楼梯。
- `src/house_3d.py`：三维装配入口，重建 STEP 与 GLB。
- `STEP/house_3d.step`：毫米制精确实体，按 `F1`、`F2`、`stairs`、`roof` 及部件命名。旁边的 `.step.json` 保存 CADgen 查看器材质等元数据。
- `GLB/house_3d.glb`：米制、Y 向上的标准 glTF 2.0；保留部件名称与层级，可在 Blender 等工具中查看和编辑。
- `output/review/house_3d_assumptions_R01.json`：三维演示参数和具体假设。
- `checks/validate_3d.py`、`output/review/validation_3d.json`：保存后的 STEP 实体和 GLB 单位、名称、层级等检查。

## 方案

坐标 X 向东、Y 向北。南入口和北向都是演示假设，尚无地块或道路资料。

一层：南侧 LDK（20.17 m²），东南玄关和鞋柜，北侧浴室、洗面脱衣及食品库，东侧厕所，东北楼梯。浴室通过洗面脱衣室进入。

二层：主卧（10.45 m²）、卧室2（L形，精确面积8.895 m²）、卧室3（9.17 m²）、储藏室、厕所和公共走道。厕所从走道北侧进入，不穿过卧室。原始图纸房间名分别为「主寝室」「洋室 2」「洋室 3」「納戸」。

两层厕所与楼梯对齐。东北 U 形梯：16 个踢面、175 mm/级、260 mm 踏面、每跑 900 mm 净宽、900 mm 中间平台，梯间预留 1900 × 2720 mm。二层楼板为整个梯间设置开口。

DXF 的全部可见图层使用 ACI 7，图形以 ByLayer 继承颜色，不指定固定 RGB；CAD 查看器在深色背景显示白色、浅色背景显示黑色。房间标注、门编号及家具文字均清晰可见。PDF 使用白底黑色线条和文字。改变背景无需重新生成模型。

## R02 制图基准准用

依据[東京都建設局 CAD製図基準（令和6年4月）](https://www.kensetsu.metro.tokyo.lg.jp/documents/d/kensetsu/000067788)的共通项目调整图面。该文件针对土木工程，本住宅方案采用其共通制图规则；具体判断和章节依据见对应记录，不表示住宅施工图或电子纳品全部合规。

纸面保留 A3 横向、1:50；基准默认 A1，也允许按需要选用 A 列尺寸。四边余白 7.5 mm、轮廓线 0.70 mm，右下使用 60 × 45 mm 表题栏和和历日期。一般图形线宽为 0.13／0.25／0.50 mm，尺寸线 0.13 mm；室名纸面字高 3.5 mm、尺寸和面积 2.5 mm、小注记 1.8 mm、标题 5 mm。模型空间文字高度为纸面高度 × 50。

图层采用 `D-STR-WALL`、`D-STR-DIM` 等责任主体／图面对象／作图要素命名，住宅追加要素的含义已记录。原生 DIMENSION 和文字仍可编辑。

图框和表题栏在 DXF 的 **`JP_A3_1_50` 纸空间布局**中，带锁定的 1:50 视口；PDF 显示完整纸面。text-to-cad 浏览器查看器显示模型空间，因此查看器中不显示纸空间图框。旧名 DXF 与规范式文件名 DXF 内容相同，已有查看器链接仍可使用。

本次未输出 SXF(P21/P2Z)、DRAWING.XML 或电子纳品目录。现有三维 STEP、GLB 保持不变；STEP 与二维电子纳品用的 SXF(P21) 是不同格式。

## 明确的假设与待定项

1. 外轮廓 7280 × 7280 mm、层高 2800 mm 是用户指定的**演示假设**。
2. 外墙 180 mm、内墙 100 mm 是占位参数，不代表已设计的木结构或建筑构造。
3. 所有房间标注使用墙内净尺寸。面积包含家具占地。楼梯显示的是梯间预留面积；二层含楼板开口。53.00 m²/层、106.00 m²合计只表示外轮廓几何面积，不能直接作为法定建筑/楼面面积。
4. 门宽表示绘制开口，尚未扣除门框。卧室门向室内开，移门以墙内门袋收纳占位；真实门袋构造、五金和开口净宽待深化。
5. 已确认方案的厕所为900 × 1700 mm，偏紧凑。食品库采用单侧搁架，占位350 mm，剩余通道730 mm；不作为主通行路线。
6. 浴室和洗面脱衣室各4.95 m²，保留确认方案的分配。
7. 家具、厨具、浴缸、卫生器具和窗户均为尺度占位，不是选定产品。层高不等于室内净高。
8. 三维额外演示假设：楼板厚200 mm、门洞高2100 mm；大窗窗台900/窗高1300 mm，小窗窗台1500/窗高600 mm；切妻屋根坡度30°、屋檐450 mm、竖向屋面厚150 mm。它们均不是已确定的施工构造。
9. 结构、地块约束、设备管线、法规定义面积及建筑法规尚未验证。楼梯的真实头部净空须在楼板、梁和完成面确定后校核。

三维完成面基准为 Z=0、2800 mm，楼板置于基准面以下；墙体净高暂定2600 mm。屋顶下另有200 mm概念顶板，顶部Z=5600 mm。中间平台厚200 mm；各半梯7个完整260 mm踏面，平台和二层地坪形成各自第8个踢面。楼梯采用概念阶梯实体，扶手、梯梁和结构连接待深化。

墙体保留门上过梁区和窗上下墙体，门窗位置复用确认平面。三维门扇以关闭位置表达；平面门扇展示开启方向。鞋柜及收纳柜为有名称的尺度占位实体。

## 重建与查看

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python src/generate_plans.py
.venv/bin/python checks/validate_plans.py
.venv/bin/python checks/validate_jp_drafting.py
.venv/bin/python src/house_3d.py
.venv/bin/python checks/validate_3d.py
.venv/bin/python -m playwright install chromium
CADGEN_DAEMON=0 .venv/bin/cadgen dxf snapshot DXF/house_1f_plan.dxf output/review/house_1f_cad.png --appearance light
CADGEN_DAEMON=0 .venv/bin/cadgen dxf snapshot DXF/house_2f_plan.dxf output/review/house_2f_cad.png --appearance light
.venv/bin/cadgen viewer --host 127.0.0.1 --json --detach
```

最后一个命令返回真实查看器 URL。分别打开 `URL?file=DXF%2Fhouse_1f_plan.dxf`、`URL?file=DXF%2Fhouse_2f_plan.dxf`、`URL?file=STEP%2Fhouse_3d.step` 或 `URL?file=GLB%2Fhouse_3d.glb`。查看器只读；修改平面参数或三维参数后重新运行对应生成器及检查。STEP 的部件树可以分别显示或隐藏各楼层、墙体、楼板、门窗、楼梯和屋顶。

本次发现后台快照任务有漏绘重复文字的情况，使用上面的临时工作进程生成快照后文字完整。PDF和DXF原始TEXT均已独立核查。

PDF使用macOS的 `Arial Unicode.ttf`；若迁移到其他系统，更新生成器的字体路径。DXF中的文字与尺寸均可编辑，但在CAD软件中仍需可用的中日文字体。

## text-to-cad 工作流

采用官方 [CAD](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/SKILL.md) 和 [DXF](https://github.com/earthtojake/text-to-cad/blob/main/skills/dxf/SKILL.md) 指引，运行时固定 `cadgen[snapshot]==0.7.11`。读取的上游源代码版本为 `8d795f56343edce7ef6b9413e02f7a92318f8229`，本地参考位于 `.tools/text-to-cad/`。

由于官方 `@dxf` 输出合同针对制造几何、文字转为轮廓，本方案按照用户许可直接用 ezdxf 实现建筑平面的可编辑文字、尺寸和门窗图层，再使用 cadgen 检查及查看器进行审阅。

## 后续深化

当前文件是参数化方案模型。实际地块、结构体系、墙屋面层次、门窗产品、门袋、楼梯扶手及设备管线仍需深化；相关专业核查完成前不能作为施工图。
