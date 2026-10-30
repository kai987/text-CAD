# 東京スカイツリー / 东京晴空塔 / Tokyo Skytree — LANDMARK-R02

> 東京タワーは後続の [R03鋼構造詳細](tokyo_tower_R03.md) に更新しました。东京塔已在后续独立升级R03。Tokyo Tower has since received a separate R03 steel update; this Skytree geometry stays R02.

[日本語](#日本語) · [中文](#中文) · [English](#english) · [Landmark catalog](tokyo_landmarks_R01.md)

## 日本語

東京スカイツリーの外観参考モデルを詳細化しました。3本の主脚、開放的な下部架構、三角形から円形へ移る塔体、階ごとの天望デッキ、ガラス張りのらせん回廊、心柱と独立した上部ガイド架構、ゲイン塔のアンテナ・保守リングを具名部材として分けています。東京タワーR02のパラメーターと部材形状は保持しています。

天望デッキは340/345/350 mの3層です。床・外周帯・屋根を環状の部材に分け、ガラスは薄いパネルとして配置しました。天望回廊は445 mから450 mへ上がる連続したスロープで、32区間の傾斜した実体床、分割ガラス、4面で近似したアーチ形ガラス天井、曲線に沿う肋、上下の入口開口と接続床を含みます。同じ傾斜形状をSTEPとGLBへ出力します。

本モデルの回廊は**半径12,850 mm・幅1,800 mmの1周経路**です。区間数、周回数、幅、経路、入口方向、アーチ形断面、甲板半径・屋根高さ・部材寸法は、編集可能なモデル上の仮定です。公表の約110 mの来場者動線全体を復元したものではありません。公式の最高到達点451.2 mは参考情報として記録し、本モデルのスロープ終点450 mと区別します。

心柱は公表資料の外径8 m・高さ375 mをもとに中空の壁として表し、それより上のガイド架構と分離しました。壁厚の公表値400/600 mmも記録しています。制振機構・ダンパー・接合部の設計や動的性能を解析するモデルではありません。

Webでは従来の4方向に加え、塔脚・350 m天望デッキ・445〜450 m天望回廊・塔頂の4つの近景を用意します。夜景は青白い灯具と一部の窓の局所表現を使い、6個の表示用光源を部材の表示状態に連動させます。公式の点灯プログラムや照度を再現するものではありません。図面は平面1:500・全体立面1:3000、甲板/回廊の1:500詳細図2枚を含むA3用紙2ページです。

## 中文

本版细化三脚塔身、开放的下部桁架、三角形向圆形的平滑过渡、展望台分层楼板与薄玻璃、玻璃螺旋回廊、中央心柱及独立上部导轨架，以及顶部天线和维护环。各部件分别命名，东京塔R02的参数和几何保持不变。

天望甲板按340/345/350 m分为三层，楼板、外缘、屋面采用环形分片，保留中央空间。天望回廊采用从445 m到450 m的连续倾斜实心坡道，分32段，用4片折面近似拱形玻璃顶，配有环肋和上下入口。平面图、立面图和详图由相同的三维部件规格投影生成，DXF保留可编辑文字、原生尺寸和锁定详图视口。

**回廊中心半径12,850 mm、宽1,800 mm、一周路线**属于演示假设，不是原塔实测，也没有复原官方约110 m的完整游览动线。玻璃、杆件、节点、屋顶高度、展望台半径及入口方向同样为建模假设。451.2 m最高到达点作为官方参考值记录，与模型450 m坡道终点区分。

心柱按公开的8 m外径、375 m高度和400/600 mm壁厚表达为空心墙体；上部导轨架单独建模，不模拟心柱制振、结构承载或动力响应。网页增加塔脚、天望甲板、天望回廊和塔尖近景，夜景使用6个显示光源及局部灯片/窗片。青白配色、灯位和配光为外观示意。

## English

R02 adds three primary legs, an open lower frame, smoother triangular-to-circular control sections, separate observation floors and thin glazing, a sloping glass gallery, a hollow concrete core, an independent upper guide frame, and detailed antenna/maintenance rings. All parts remain named in STEP/GLB. Tokyo Tower R02 parameters and geometry are preserved.

The Tembo Deck has separate 340/345/350 m floors, annular floor/roof pieces and segmented glazing. The Tembo Galleria is a continuous 445-to-450 m ramp with 32 genuinely sloping solid segments, thin glass walls, a four-facet approximation of an arched glass roof, ribs and open entrance connections. CAD drawings project these same parts; DXF retains editable text, native dimensions and locked detail viewports.

**The 12,850 mm centre radius, 1,800 mm width and one-turn route are modelling assumptions.** This does not reconstruct the operator's approximately 110 m complete visitor route. Floor/roof thickness, deck radii, roof heights, glass divisions, member sections, connections and entrance orientation are also assumed. The published 451.2 m highest point is recorded as reference information, separately from our 450 m ramp endpoint.

The hollow core follows the published 8 m diameter, 375 m height and 400/600 mm wall thicknesses, with the upper guide frame named separately. Damping response, structural capacity and connection design are not simulated. Four new close-ups cover the base, deck, gallery and spire. Local cool night illumination uses six display lights and selected lenses/windows; it does not reproduce the operator's lighting programme or photometry.

The two A3 sheets contain a 1:500 plan, 1:3000 elevation and two 1:500 detail insets. CAD uses millimetres/Z-up; GLB uses metres/Y-up.

## ファイル / 文件 / Files

- [STEP solids](../STEP/tokyo_skytree.step) · [GLB](../GLB/tokyo_skytree.glb)
- [Plan DXF](../DXF/tokyo_skytree_plan.dxf) · [Elevation DXF](../DXF/tokyo_skytree_elevation.dxf) · [A3 PDF](../output/pdf/tokyo_skytree_sheets.pdf)
- [Parameters and provenance](../output/review/tokyo_skytree_manifest.json) · [Drawing metadata](../output/review/tokyo_skytree_drawings.json)
- [Shared parameters](../src/lib/tower_geometry.py) · [R02 detail geometry](../src/lib/skytree_detail.py) · [CAD exporter](../src/towers_3d.py) · [Drawing generator](../src/generate_tower_plans.py)

## 再生成 / 重建 / Regeneration

Run in the repository root using the existing CAD Python environment:

```bash
CADGEN_DAEMON=0 .venv/bin/python src/towers_3d.py --tower tokyo-skytree
.venv/bin/python src/generate_tower_plans.py --model tokyo-skytree
```

The full source-bound release must be regenerated before a website build:

```bash
CADGEN_DAEMON=0 .venv/bin/python src/cad_pipeline.py --regenerate
cd web
npm run build
npm run preview -- --port 4199
```

The shared pipeline validates saved native STEP solids, GLB names/bounds/materials, drawing dimensions/viewports, PDF sheets and source/output hashes. Pure geometry tests cover route continuity, openings, thin panels and reference controls. These checks establish model consistency, not surveyed accuracy or engineering approval.

## 出典 / 来源 / References

Operator and public-body pages checked on 2026-10-30. Geometry is authored in this repository. Operator photographs, logos and downloadable building models are not redistributed.

- [Operator specifications](https://www.tokyo-skytree.jp/about/spec/) — 634 m total height.
- [Operator floor guide](https://www.tokyo-skytree.jp/floor/) — 340/345/350 m floors and 445/450 m gallery levels.
- [Tembo Galleria](https://www.tokyo-skytree.jp/floor/tembogalleria/) — sloping glass gallery and 451.2 m highest point.
- [Operator educational structure guide](https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/body.php) — 8 m × 375 m hollow core and wall thicknesses.
- [Tokyo Metropolitan Government landmark guide](https://www.chiikishigen.metro.tokyo.lg.jp/introduction/details/introduction_26.html) — approximately 68 m triangular base and circular section at 315 m, with the traditional silhouette context.
- [Operator design concept](https://www.tokyo-skytree.jp/about/design/) — triangular-to-circular form and design intent.

The approximately 32 m transition diameter retains the original catalogue's reference to the designer's NIKKEN JOURNAL 2012 Autumn. Its legacy PDF remains search-indexed but returned 404 on direct access during this update; the manifest records that limitation. The currently accessible official/public sources above support the other reference controls.
