# 日本新建一户建外装参考 / 新築戸建ての外装参考 / Japanese house exterior references

Checked 2026-10-06. These official pages inform an original concept; their
photographs, textures and proprietary CAD models are not redistributed.

| Official reference | Adopted visual idea / 採用した意匠 / 采用的视觉要点 |
| --- | --- |
| [Nichiha: timber-accent modern house, Kumamoto](https://www.nichiha.co.jp/works/residential/367) | White siding with a timber entry accent; a clear, restrained two-storey form. 白いサイディングと玄関の木目アクセント。白色挂板与木色玄关。 |
| [Nichiha: two-storey gable house, Saitama](https://www.nichiha.co.jp/works/residential/894) | Simple gable silhouette and orderly wall finishes. 簡潔な切妻の輪郭と外壁の割付。简洁切妻轮廓与规整外墙。 |
| [KMEW Japanese modern exterior coordination](https://www.kmew.co.jp/design/images/pdf_jm_lifestyle.pdf) | Pale primary walls, dark roof/frame accents and coordinated sharp gutters. 明るい外壁と濃色の屋根・サッシ・雨とい。浅色墙体与协调的深色屋顶、窗框、雨樋。 |
| [YKK AP APW 330 colour options](https://www.ykkap.co.jp/business/products/window/apw330/variation) | Black exterior window-frame colour. 外側ブラックの窓枠。黑色外窗框。 |
| [YKK AP Venato D30 colour options](https://www.ykkap.co.jp/business/products/door/venato_d30/variation) | Natural timber-tone entrance door. 木目調玄関ドア。木色玄关门。 |

## 采用方案 / 採用案 / Selected concept

暖白挂板为主，南侧玄关区域使用灰色与木色；深灰切妻屋面增加立缝、棟包み、檐底与破风；黑色窗框配独立窗台水切，檐沟与落水管统一深灰。外装替换原墙厚内的外侧薄层并包住楼板边缘，主体完成外轮廓仍为7280 × 7280 mm。玄关雨棚、平台与水切等附件的外挑另行记录。原平面、室内净边界、门窗毛洞与楼梯参数沿用确认方案。

暖白色サイディングを基調に、南側玄関へグレーと木目を配置します。濃灰色の切妻屋根に立ちはぜ・棟包み・軒天・破風を追加し、黒い窓枠と個別の窓台水切り、同色の雨といを組み合わせます。外装を既存壁厚の外側に組み込み、床スラブ端を覆います。建物本体の仕上げ外形7280 × 7280 mmと、承認済み間取り・有効境界・開口・階段パラメータを保持します。庇・ポーチ・水切りなどの張り出しは別記します。

Warm-white siding is combined with grey and timber accents at the south entry.
The charcoal gable roof has standing seams, a ridge cap, soffits and bargeboards;
black window frames have individual sill flashings, with matching rain gutters.
The finish replaces the outer layer within the existing wall depth and wraps the
slab edges. The finished building body remains 7280 × 7280 mm. Canopy, porch and
other projecting accessories are recorded separately. Approved room boundaries,
rough openings and stair parameters are retained.

## 材质与参数 / 仕上げとパラメータ / Finishes and parameters

- `src/lib/exterior_geometry.py` defines all exterior dimensions and named solids.
  All new dimensions are demonstration assumptions; the scheme is not a product
  specification, drainage design or installation detail.
- Source units remain millimetres; STEP uses millimetres and GLB uses metres/Y-up.
  The existing 2800 mm storey heights, 30° roof pitch, 450 mm overhang and 150 mm
  vertical roof thickness remain demonstration assumptions.
- `src/lib/exterior_materials.py` creates deterministic original PNG finishes and
  embeds them with UVs in GLB. Siding repeats every 1820 × 455 mm, with an
  illustrative 3.6 mm horizontal joint; timber repeats every 150 × 2800 mm.
  These repeat dimensions are visual assumptions, not manufacturer dimensions.
- Roof standing seams are an original metal-roof concept. They do not reproduce
  the KMEW products pictured in the coordination reference.
- STEP stores the original solid geometry and colours; the procedural textures
  are a GLB rendering finish. No network request is needed for the textures.
- Final dimensions, air gap and attachments are recorded in
  `output/review/house_3d_assumptions_R01.json` under `exterior`. Colours are
  defined in `src/lib/house_geometry.py`; GLB finish metadata records texture scales.
