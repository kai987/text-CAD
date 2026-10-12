# 日本近郊河流 CAD 与 3D 示例 / 日本近郊河川デモ / Japanese suburban river demonstration

## 中文

RIVER-R01 是独立的日本城市近郊河流示范场景，包含弯曲河道、水体、石护岸、两岸步道、亲水阶梯、人行桥、树木、长椅和灯具。它是原创参数化景观方案，不对应实际河流、地块或测量地形。

**所有尺寸和标高均为演示假设**。场景南北投影长度180000 mm、东西宽80000 mm；常水面宽18000 mm、水底宽14000 mm、水深900 mm。水面标高Z=0、河床Z=-900、亲水平台Z=1000、堤顶步道Z=3000、桥面Z=3100 mm。桥梁示范跨径38000 mm、宽4000 mm，两岸堤顶步道宽3000 mm。180000 mm是南北投影长度，弯曲中心线实际长度不同；岸坡和步道宽度按X方向偏移定义。

CAD采用毫米与Z向上，X为东、Y为北；暂设水流由北向南。GLB采用米与Y向上，转换为 `(X, Y, Z) mm → (X, Z, -Y) / 1000 m`。模型分为地形、河床、水体、两岸、步道、桥面、梁、栏杆、桥台、引道、阶梯、树木、长椅及灯具等独立命名组。DXF保留可编辑TEXT及原生DIMENSION；A3平面缩尺1:1000、横断面1:250，模型空间始终为毫米实寸1:1。SVG是相同尺寸的浏览预览。

景观方向参考国土交通省的[河川景观指南](https://www.mlit.go.jp/river/shishin_guideline/kankyo/riverscape/index.html)，以及[北上川公开设施中的步道、石护岸和连接阶梯](https://www.thr.mlit.go.jp/iwate/kawa/kawamachi/morioka_facility/kitakamigawa.html)。这些资料用于景观关系参考，模型和尺寸没有复制北上川。治水、水理容量、洪水位、冲刷、桥梁承载、基础地盘、河川占用许可及法规符合性均未计算或核定；工程结果在清单中保留为`null`。

## 日本語

RIVER-R01は独立した日本近郊河川のデモ景観です。蛇行河道、水面、石護岸、両岸歩道、親水階段、人道橋、樹木、ベンチ、照明器具をパラメトリックに作成しています。実在の河川・敷地・測量地形の再現ではありません。

**全寸法と標高はデモ仮定**です。南北投影延長180000 mm・東西幅80000 mm、水面幅18000 mm、水底幅14000 mm、水深900 mm。水面Z=0、河床Z=-900、親水平台Z=1000、堤頂歩道Z=3000、橋面Z=3100 mm。人道橋の支間38000 mm・幅4000 mm、両岸の堤頂歩道幅3000 mmです。180000 mmは南北投影であり、曲線中心線の延長とは異なります。岸・歩道幅はX方向のオフセットで定義します。

CADはmm・Z-up、Xが東、Yが北、流れは北から南と仮定します。GLBはm・Y-upで、`(X, Y, Z) mm → (X, Z, -Y) / 1000 m`に変換します。地形、河床、水面、両岸、歩道、橋面・梁・欄干・橋台・取付路、階段、樹木、ベンチ、照明を別名で管理します。DXFは編集可能なTEXTとネイティブDIMENSIONを保持し、A3平面1:1000・横断面1:250。モデル空間はmmの実寸1:1で、SVGも同じ寸法を表示します。

景観構成の参考は国土交通省の[河川景観ガイドライン](https://www.mlit.go.jp/river/shishin_guideline/kankyo/riverscape/index.html)と、[北上川で公開されている散策路・石積護岸・接続階段](https://www.thr.mlit.go.jp/iwate/kawa/kawamachi/morioka_facility/kitakamigawa.html)です。北上川の形状・寸法を複製したモデルではありません。治水、水理容量、洪水位、洗掘、橋梁耐力、基礎・地盤、河川占用許可と法適合は未計算・未確定で、メタデータの工学結果は`null`です。

## English

RIVER-R01 is an independent Japanese suburban river landscape demonstration with a curved channel, water, stone revetments, riverside paths, access stairs, a pedestrian bridge, trees, benches and light fixtures. Its parametric geometry does not represent a real river, parcel or survey.

**All dimensions and elevations are demonstration assumptions**. The scene has a north–south projected length of 180000 mm and an east–west width of 80000 mm. Water-surface width is 18000 mm, bed width 14000 mm and water depth 900 mm. Elevations are water Z=0, bed Z=-900, riverside platform Z=1000, crest paths Z=3000 and bridge deck Z=3100 mm. The proposed bridge spans 38000 mm, is 4000 mm wide, and the crest paths are 3000 mm wide. The 180000 mm value is a north–south projection; the curved centreline has a different length. Bank and path widths use X-direction offsets.

CAD uses millimetres/Z-up, with X east and Y north; flow is assumed north to south. GLB uses metres/Y-up via `(X, Y, Z) mm → (X, Z, -Y) / 1000 m`. Separate named groups cover terrain, bed, water, banks, paths, bridge deck, beams, rails, abutments, approaches, stairs, trees, benches and lighting. DXF retains editable TEXT and native DIMENSION entities: A3 plan 1:1000 and section 1:250, with true-size millimetre model space. SVG previews display the same dimensions.

Landscape references are MLIT's [river landscape guidance](https://www.mlit.go.jp/river/shishin_guideline/kankyo/riverscape/index.html) and the [Kitakami River's published paths, stone revetments and connecting stairs](https://www.thr.mlit.go.jp/iwate/kawa/kawamachi/morioka_facility/kitakamigawa.html). The model does not copy the Kitakami River's geometry or dimensions. Flood management, hydraulic capacity, flood levels, scour, bridge strength, foundations, river-use permits and statutory compliance remain uncalculated or unverified. Engineering results remain `null` in the manifest.

## 文件与源码 / ファイルとソース / Files and source

| 内容 / 内容 / Content | 文件 / ファイル / File |
| --- | --- |
| 参数与几何 / パラメータ・形状 / Parameters and geometry | [river_geometry.py](../src/lib/river_geometry.py) |
| STEP与GLB生成 / 3D生成 / STEP and GLB generator | [river_3d.py](../src/river_3d.py) |
| 编辑标注绘图 / 編集可能な注記 / Editable drawing generator | [generate_river_plans.py](../src/generate_river_plans.py) |
| 三维CAD / 3D CAD | [river_demo.step](../STEP/river_demo.step) |
| 三维预览 / 3D表示 / 3D preview | [river_demo.glb](../GLB/river_demo.glb) |
| 三维图片 / 3D画像 / 3D image | [river_demo_iso.png](../output/review/river_demo_iso.png) |
| 平面与断面图片 / 図面画像 / Drawing images | [平面 / Plan](../output/review/river_demo_plan.png) · [断面 / Section](../output/review/river_demo_section.png) |
| 河川平面 / 河川平面 / River plan | [DXF](../DXF/river_demo_plan.dxf) · [SVG](../output/svg/river_demo_plan.svg) |
| A-A横断面 / A-A横断面 / A-A cross-section | [DXF](../DXF/river_demo_section.dxf) · [SVG](../output/svg/river_demo_section.svg) |
| 几何与假设 / 形状・仮定 / Geometry and assumptions | [river_demo_manifest.json](../output/review/river_demo_manifest.json) |
| 绘图来源与哈希 / 図面ソース・ハッシュ / Drawing bindings and hashes | [river_demo_drawings.json](../output/review/river_demo_drawings.json) |

完整河流文件包 / 河川ファイル一式 / River bundle: [river_demo_R01.zip](../output/river_demo_R01.zip)。包内说明列出独立生成步骤；包含CAD、3D模型、图片及必要Python源码，不包含网页查看器。 / ZIP内READMEに単独生成手順を記載し、CAD・モデル・画像・必要なPythonソースを同梱しています。Webビューアは含みません。 / The ZIP README provides standalone generation steps and includes CAD, models, images and required Python source; the web viewer remains in the repository.

## 本地生成与预览 / ローカル生成と表示 / Local generation and preview

在项目根目录运行以下命令，统一重建和校验模型目录后启动查看器。依赖准备沿用项目原有安装说明。 / プロジェクトのルートで全モデルを再生成・検証してからビューアを起動します。依存関係は既存のセットアップ手順に従ってください。 / From the repository root, regenerate and validate the full model catalog, then start the viewer. Use the project's existing dependency setup instructions.

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate
npm --prefix web run dev
```

打开终端显示的本地地址与`/text-CAD/`路径，再使用下面的查询参数；语言和主题通过界面选择器切换。 / ターミナルに表示されたローカルURLの`/text-CAD/`を開き、以下のクエリを指定します。言語・テーマは画面のセレクターで変更します。 / Open the local URL printed by Vite at `/text-CAD/` and use the following queries; select language and theme in the interface.

| 页面 / ページ / View | 查询参数 / クエリ / Query |
| --- | --- |
| 三维 / 3D / 3D | `?model=river&view=3d` |
| 平面 / 平面 / Plan | `?model=river&view=plan` |
| 横断面 / 横断面 / Section | `?model=river&view=section` |
| 文件 / ファイル / Files | `?model=river&view=files` |

单独检查保存的河流文件可执行 / 保存済み河川ファイルの個別検証 / To validate the saved river files independently:

```bash
CADGEN_DAEMON=0 .venv/bin/python checks/validate_river.py
```

校验覆盖实体有效性、命名部件、毫米至米转换、真实DXF尺寸、SVG可见数值以及源码和产物哈希；不构成工程批准。 / 検証対象はソリッド、部材名、mmからmへの変換、DXF寸法、SVG表示値、ソース・出力ハッシュであり、工学上の承認ではありません。 / Checks cover solids, part names, unit conversion, DXF measurements, visible SVG values and source/output hashes; they do not provide engineering approval.

官方参考资料核查日期 / 公式参考資料の確認日 / Official references checked: 2026-10-12（Asia/Tokyo）。
