# 模型昼夜与室外灯具 / モデルの昼夜と屋外照明 / Model day, night and outdoor lighting

## 简体中文

R08 为三维查看器增加白天／夜晚场景，并在一户建模型中增加 **7 盏参数化室外灯具、32 个具名实体**：玄关壁灯1盏、入口步道灯2盏、庭院投射灯2盏、行人门柱灯2盏。昼夜场景与网页深浅主题分别控制；公寓也可切换场景昼夜，但没有新增室外灯具。

选择「夜晚」并开启「室外灯光」可看到暖色扩散罩、光晕及照亮的表面。关闭灯光仍保留实体灯具。部件树的「室外灯具」及壁灯／步道灯／庭院灯／门柱灯分类可分别隐藏；隐藏的灯具不会继续发光。内部、阁楼和结构预设默认隐藏室外灯具。剖切时，位于切面上方的光源关闭，判断高度以一层完成面 Z=0 为基准。庭院灯光源位于 Z=0 以下，因此在0 mm剖切时仍可能可见和点亮。

切换昼夜、灯光、主题、语言、户型或页面会保留照明选择；昼夜切换保留当前相机、家具和剖切状态。可分享 `?model=house&view=3d&environment=night&lights=on`；支持 `environment=day|night` 和 `lights=on|off`。选择保存在 `text-cad.scene-lighting.v1`，有效URL参数优先于浏览器保存值。

全部尺寸、位置、**3000 K暖色效果**和光束参数均为**演示假设**。灯光强度、距离及光束只用于网页视觉表现，不对应厂商光度文件、流明或实测照度。照度、眩光、电路、防水产品等级和施工安装结果均为未核定的 `null`。

## 日本語

R08は3Dビューアに昼／夜のシーンを追加し、戸建てに **7灯・32個の名前付き実体**を追加します。玄関壁灯1灯、アプローチ灯2灯、庭の投光器2灯、歩行門の柱灯2灯です。モデルの昼夜とページのライト／ダークテーマは別の設定です。マンションでも昼夜を切り替えられますが、屋外灯具は追加していません。

「夜」と「屋外照明」を選ぶと、暖色の拡散部、光のにじみと照らされた面を表示します。消灯しても灯具の形状は残ります。「屋外灯具」と壁灯／アプローチ灯／庭園灯／門柱灯の分類を個別に非表示にでき、隠した灯具は点灯しません。内部・小屋裏・構造プリセットでは屋外灯具を初期非表示にします。切断面より上の光源は消灯し、切断高さの基準は1階仕上げ床のZ=0です。庭園灯の光源はZ=0より低いため、0 mmの切断でも表示・点灯が残る場合があります。

昼夜、照明、テーマ、言語、モデル、ページを切り替えても照明設定を保持します。昼夜切替は視点、家具表示、切断状態を保持します。共有URLは `?model=house&view=3d&environment=night&lights=on`。`environment=day|night`、`lights=on|off` を使用し、ブラウザの `text-cad.scene-lighting.v1` に保存します。有効なURL指定を保存値より優先します。

寸法、位置、**3000 Kの暖色表現**と光束設定はすべて**デモ用の仮定**です。光の強さ・距離・角度は画面表現用で、メーカーの配光データ、ルーメンや実測照度を示しません。照度、グレア、電気回路、製品の防水等級、施工方法は未確定の `null` です。

## English

R08 adds day/night scenes to the 3D viewer and **7 parametric outdoor fixtures with 32 named solids** to the detached house: one entrance wall light, two path lights, two garden spotlights and two pedestrian gate-post lights. Scene time and the page light/dark theme are independent. The apartment supports day/night scenes without added outdoor fixtures.

Choose “Night” and enable “Outdoor lights” to display warm diffusers, subtle glow and illuminated surfaces. Switching the lights off retains their physical geometry. The outdoor-fixture group and its wall/path/garden/gate categories can be hidden separately; hidden fixtures stop emitting. Interior, attic and structural presets hide them by default. Cutting disables sources above the section plane, using the first-floor finished datum Z=0. Garden sources sit below Z=0, so they may remain visible and active at a 0 mm cut.

Lighting choices persist when changing scene time, lights, page theme, language, model or page. Day/night changes preserve the camera, furniture and section state. Share `?model=house&view=3d&environment=night&lights=on`; supported parameters are `environment=day|night` and `lights=on|off`. Settings are saved under `text-cad.scene-lighting.v1`; valid URL values override saved choices.

All sizes, positions, the **3000 K warm appearance** and beam settings are **demonstration assumptions**. Intensity, distance and angles are presentation values, not manufacturer photometry, lumens or measured illuminance. Illuminance, glare, circuit design, product weatherproof rating and installation results remain `null`.

## 参数与文件 / パラメータとファイル / Parameters and files

Native CAD uses millimetres and Z-up. First-floor finished Z=0; outdoor ground Z=-500 mm. GLB uses metres and Y-up: `[X/1000, Z/1000, -Y/1000]`. Positions below are mount/base centres in native CAD coordinates. Each fixture contains a named `diffuser` component under `lighting:{category}:{fixture_id}:{component}`.

| Fixture ID | Category / 类别 / 分類 | Mount/base centre X, Y, Z (mm) | Demonstration size (mm) |
| --- | --- | --- | --- |
| entrance_01 | wall / 壁灯 / 壁灯 | 6490, 0, 1520 | body 120 × 320 × 84 |
| path_01 | path / 步道灯 / アプローチ灯 | 4800, -4050, -500 | ground height 800; diffuser 100 × 100; base 160 × 160 |
| path_02 | path / 步道灯 / アプローチ灯 | 4800, -2550, -500 | ground height 800; diffuser 100 × 100; base 160 × 160 |
| garden_01 | garden / 庭院灯 / 庭園灯 | 2500, -4450, -500 | tilting head Ø100 × 105 |
| garden_02 | garden / 庭院灯 / 庭園灯 | 4200, -1700, -500 | tilting head Ø100 × 105 |
| gate_01 | gate / 门柱灯 / 門柱灯 | 4905, -5325, 550 | body 45 × 100 × 55 |
| gate_02 | gate / 门柱灯 / 門柱灯 | 6755, -5325, 550 | body 45 × 100 × 55 |

`src/lib/outdoor_lighting.py` retains editable geometric and visual parameters. `GLB/house_3d.glb` and `STEP/house_3d.step` include the physical fixtures. GLB diffuser nodes contain `extras.outdoorLight`; asset extras and `output/review/house_3d_assumptions_R01.json.outdoor_lighting` retain positions, directions and presentation settings. Exported GLB materials start without emission; the viewer creates switchable illumination at runtime. STEP carries solids and colours, not the browser lighting simulation.

The independent CAD validation report is `output/review/outdoor_lighting_validation_R08.json`: **1742/1742 checks pass**, including 32 valid new solids, seven fixture mounting contacts, unchanged native/GLB geometry and material payloads for the original 729 solids, and no new fixture-volume obstruction of the existing entrance path, pedestrian/vehicle openings, parking bay or door clearance. These are geometric checks, not an engineering or regulatory lighting assessment. User-confirmed plans, apartment files and R07 structural comparison files remain unchanged.

The viewer keeps seven fixed light objects and uses one entrance shadow map; changing switches does not repeatedly allocate sources. The other six decorative sources have no separate shadow maps, so illumination is a presentation approximation rather than a physically verified occlusion or lighting calculation. Light effects stay outside the CAD hierarchy used for picking and camera fitting. Model disposal removes light effects and restores material ownership.

## 再生成 / 重新生成 / Reproduce

```bash
CADGEN_DAEMON=0 .venv/bin/python src/house_3d.py
.venv/bin/python checks/validate_outdoor_lighting.py
cd web
npm test
npm run build
```
