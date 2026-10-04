# 日本两层一户建参数化方案

当前图纸版本：R02（日本制图基准准用版）。**用户已确认的 R01 平面布局保持不变**，三维模型继续使用该布局。房间名、面积、尺寸、门编号及家具文字采用高对比显示。

## 在线查看

[打开房屋 CAD 查看页](https://kai987.github.io/text-CAD/)。画布上方可直接切换完整外观／一层内部／二层内部。部件树支持楼层、外墙、内隔墙、楼板、门、窗、收纳柜、楼梯和屋顶的显示与隐藏；点击名称或三维实体可高亮并查看原始部件名，“单独”按钮隔离选定分类，顶部预设恢复显示。浏览器还支持旋转、缩放和水平剖切。平面页默认展示房间与尺寸，可切换完整 R02 A3 图框，支持矢量放大和下载可编辑 DXF；文件页提供 STEP、GLB、DXF、PDF 和参数说明。

网页位于 `web/`，使用 React、TypeScript、Three.js 和 Vite；不依赖本地 Python 查看器。它直接读取已生成的 GLB，不改变 CAD 几何。STEP 和 DXF 提供原始文件下载，在线平面使用从原始 PDF 转换的 SVG，全部文字转为字形轮廓，不依赖访问者的中日文字体。完整纸面内容不变，平面范围采用同一 SVG 的裁切视口；两向总尺寸、房间名、门号、门弧和北向箭头均保留。模型内部保留原始 `F1`、`F2`、`stairs` 和 `roof` 及楼层内的六类节点，并通过 GLTFLoader 节点索引映射恢复原始名称。手机支持触摸旋转和缩放；浏览器无法运行 WebGL 时显示静态外观预览。

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

开发和构建时从仓库复制 15 个 CAD、图纸及说明文件（原13个加两层矢量预览），并生成 SHA-256 清单；生产构建再次核对副本。矢量元数据还记录来源 PDF 的哈希、SVG 哈希和裁切内的标注边界；源 PDF 变化或 SVG 不匹配时拒绝构建，要求先重新转换。`web/public/artifacts/`、派生数据和 `web/dist/` 不提交到 Git。

修改方案后先重建 CAD、PDF 并完成对应检查，再更新矢量预览；转换工具在本地使用 Python，GitHub Pages 构建直接读取已提交的 SVG：

```bash
uv pip install --python .venv/bin/python PyMuPDF==1.26.7
.venv/bin/python web/scripts/generate-plan-svg.py
```

提交 `output/vector/house_1f_plan.svg`、`house_2f_plan.svg` 与 `web/src/plan-preview-metadata.json` 后重新构建。当前裁切范围及必需标签对应已批准的7280毫米演示方案；若平面尺寸或纸面排版改变，需要重新核对裁切和标注。

`.github/workflows/pages.yml` 在 `main` 推送时执行安装、模型控制测试、TypeScript 检查、构建和文件哈希检查，然后发布到 GitHub Pages。在线尺寸仍是演示假设，现有结构和管线待定项见下文。

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

二层：主卧（10.45 m²）、洋室2（L形，8.90 m²）、洋室3（9.17 m²）、纳户、厕所和公共走道。厕所从走道北侧进入，不穿过卧室。

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
