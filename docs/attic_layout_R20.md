# R20 / 阁楼 / 小屋裏 / Attic

## 中文

北侧中央保留一根90 mm概念屋脊柱；两侧窗中心距屋脊轴线各350 mm。两个200×450 mm固定铝百叶洞口合计0.18㎡，窗台为阁楼完成面FL+650 mm。尺寸均为演示假设，洞口面积包含边框，不等于有效通风面积。双窗与居中柱的实体间隙、百叶间隙、屋顶及RC山墙开口已检查。

江户川区规则以开口合计面积控制，当前双窗可作为该示例下的演示布局。大阪约0.2㎡和百叶规格条文未明确本模型的开口数量解释；京都、名古屋的面积和数量仍待核定。不得将这套共享模型认定为四地批准。防火、实际产品、有效通风量与建筑确认未完成。

`src/lib/attic_geometry.py` 的 `north_vent_count=1` 可建立偏心300×600 mm单扇竖长百叶，面积仍为0.18㎡；目前网页及STEP/GLB导出采用两扇，单扇备选仅保留在参数源码与实体测试中。

检修口1200×650 mm位置保持不变，检修梯、盖板、铰链和护栏入口围绕其中心镜像。世界坐标下从东侧进入，上端X=4090 mm、梯脚X≈3334.9 mm；展开包络和600 mm下方站位仍在二层公共走廊内，上口站位最低净高1350 mm。展开期间占用廊下。以上是几何检查，楼梯产品、安全操作、柱梁承载及连接仍未设计。

## 日本語

北側棟柱を中央1本（概念90 mm）に戻し、棟軸から左右350 mmに200×450 mmの竪長固定アルミガラリを各1箇所設けます。洞口合計0.18㎡、窓台FL+650 mm。すべてデモ用仮定で、有効換気面積ではありません。柱・屋根との干渉、百葉の隙間、RC妻壁の開口を幾何検査済みです。

江戸川区例は開口合計で扱います。大阪の約0.2㎡・ガラリ仕様から複数開口が認められるとは判断できません。京都・名古屋も面積・開口数を確認してください。防火、製品、換気量、確認申請は未完了です。

Pythonの `north_vent_count=1` は偏心300×600 mmの単窓案（0.18㎡）を生成します。現行ウェブ・STEP/GLBは双窓で、単窓はパラメータと実体テストのみです。

既存1200×650 mm点検口は移動せず、展開はしご・蓋・ヒンジ・手すり入口を開口中心で反転。世界座標では東から入ります。梯脚と奥行600 mmの足元立ち位置は2階廊下内、上部立ち位置の最低高さ1350 mm。展開中は廊下を占有します。実製品、安全操作、耐力・接合は未設計です。

## English

Restore one centred north ridge post (conceptual 90 mm), with two vertical 200×450 mm fixed aluminium louvers centred 350 mm either side. Total gross wall apertures are 0.18 m²; sill is attic FL+650 mm. All dimensions are demonstration assumptions. Gross aperture is not certified ventilation area. Solid geometry checks cover post/roof clearance, blade gaps and RC gable apertures.

The Edogawa example uses aggregate openings. Osaka's approximately 0.2 m²/louver provision does not establish permission for two openings here. Kyoto and Nagoya area/count treatment remains pending. Fire specifications, products, ventilation performance and permit review are unfinished.

Python `north_vent_count=1` constructs an offset 300×600 mm single-opening alternative, also 0.18 m². Current web/STEP/GLB exports use two openings; the alternative exists only in parameter source and solid tests.

The 1200×650 mm hatch remains in place. Reflect the deployed ladder, lid, hinges and guardrail entry about its centre. World entry is now east. Ladder top X=4090 mm and foot X≈3334.9 mm; deployed footprint and 600 mm lower standing zone remain in the public second-floor hall. Upper standing minimum clearance is 1350 mm. Deployment occupies the hall. Geometry checks do not establish safe operation or structural capacity.

## References / 参考

- [江户川区 / Edogawa §9(7), printed p14](https://www.city.edogawa.tokyo.jp/documents/1028/toriatukai20260401.pdf)
- [大阪市 / Osaka 2026, p21](https://www.city.osaka.lg.jp/toshikeikaku/cmsfiles/contents/0000021/21604/260401.1-1-1-23.pdf)
- [京都市 / Kyoto general 5-6](https://www.city.kyoto.lg.jp/tokei/cmsfiles/contents/0000165/165090/HB0504Kijunsousoku2.pdf)
- [名古屋市 / Nagoya](https://www.city.nagoya.jp/jigyou/toshikeikaku/1018015/1018684/1018916/1034621.html)
