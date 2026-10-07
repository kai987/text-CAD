# Parametric Japanese homes: detached house and 2LDK apartment

## R19 Attic opening references

Keep the centered 600 × 300 mm gross aperture (0.18 m²), now a fixed aluminium louver. Tokyo uses a named Edogawa example; Osaka references approximately 0.2 m² and louver specifications. No numerical Kyoto/Nagoya ceiling is invented. Current output is R19; effective ventilation, fire specification and approval remain pending. [R19 / 日本語 / English](docs/attic_opening_rules_R19.md).

## R18 centred attic north window and lighting

The north attic window moves to the ridge centre. Paired jamb posts, a header and an upper ridge post keep its opening clear in the concept frame. Two short pendants sit below the default 6900 mm attic cut plane and share the Indoor lights switch. Sections, capacity and lighting remain illustrative; current exports are R18. [R18](docs/attic_window_lighting_R18.md).

## R17 wall alignment, bedroom entries and visible lights

Both WC south walls align with the first-floor washroom; clear size 900×1820 mm. The F2 wardrobe enclosure is removed and open storage joins the master (14.760 m² net geometric area). Two separate 750 mm sliders at the hall corner enter the master and north bedroom. Their separation wall remains.

Open ring shades prevent their top caps from hiding the glowing diffusers in overhead views. All 14 indoor lights retain the shared switch. Dimensions, lighting and structure are illustrative. Current exports are R17; sections below are historical. [R17](docs/wall_lighting_R17.md).

## History: R16 second-floor redesign and indoor lighting

The long central passage joins the two south bedrooms (11.160/12.803 m²). Each bedroom has its own balcony slider. The WC forecourt joins the shared hall with a recessed basin and mirror. North bedroom windows are north 600 mm/east 1800 mm. All bedrooms have a desk, chair and bedside table. Open stairs use 60 mm treads and side stringers, retaining under-stair storage; reduced solid fill does not automatically reduce their footprint.

Fifteen indoor lamps (pendants, stair wall lamps, attic ceiling lamp) have one master switch, independent of furniture, outdoor lights and time of day. Hidden or clipped lamps stop illuminating. Dimensions and brightness are demonstration assumptions; capacity, connections, guards, fire safety, photometry and electrical installation remain unengineered. [R16 details / 中文 / 日本語](docs/interior_R16.md). R15 and earlier sections below are historical; current R17 exports take precedence.

## R15 Under-stair storage and four-person furnishings

The entry handle moves to the left as seen from outside. The enclosed first-floor WC lobby becomes part of the LDK. An 800×1760 mm storage room with a stepped ceiling fits below the upper stair flight. A 2600×1550 mm four-seat L sofa faces the south-wall TV, with a 950×550 mm coffee table, 1600×850 mm dining table and four chairs. The refrigerator is a 900×750 mm side-by-side model. Second-floor rooms and west stair windows remain. All dimensions are demo assumptions; stair capacity, connections and fire separation are unengineered.

[R15 dimensions and scope](docs/interior_R15.md)

Web downloads transport the complete STEP losslessly with gzip and restore a standard .step in supported browsers. Other browsers can extract the compressed download. Local STEP and appearance metadata remain complete.

Earlier revisions below are historical.

Three south living/main-bedroom/bedroom-2 windows now extend from FL+0 to FL+2200, retaining widths of 2100/1600/1800 mm. The main bed rotates and bedroom-2 bed moves north to retain a 650 mm demonstration approach. Safety glass, sash specifications, waterproofing, headers and thermal performance remain undesigned.

[简体中文](README.md) | [日本語](README.ja.md) | **English**

## Earlier proposal R14: mirrored floors and facing kitchen

Both floors are reflected left/right: southwest entrance and northwest stairs. East windows serve the LDK and both east bedrooms; west windows serve stairs only. Existing north/south windows and the full-width 8190×1000 mm south balcony remain. A 600×300 mm top-hung ventilation window is added to the north attic gable, sill at attic FL+850 mm.

The facing kitchen has a 2550×650 mm counter and a 900 mm main rear working aisle, with refrigerator, extractor hood, microwave and appliance cupboard. Foundation supports, entrance path, parking, lights and W/S/RC overlays share the same reflection. Three bedroom areas, the 8190×7280 mm footprint and 2800 mm storey heights remain. All dimensions are demonstration assumptions; products, exhaust ducts, ventilation, capacity and regulatory suitability remain undesigned.

[First-floor DXF](DXF/house_1f_plan.dxf) · [Second-floor DXF](DXF/house_2f_plan.dxf) · [STEP](STEP/house_3d.step) · [GLB](GLB/house_3d.glb) · [Parameters](src/lib/house_redesign_plan.py)

STEP export losslessly compacts whitespace for the Sites 25 MiB per-file limit. Numbers, named components and appearance metadata are retained and the saved CAD is revalidated.

R13 and earlier sections below are historical; the R15 section above and the current exported files take precedence.

## Earlier scheme (R13 balcony revision)

R13 retains the approved three-bedroom interiors and changes the south balcony to **8190 × 1000 mm**, with **7990 × 900 mm clear space (7.191 m²)**. Three support posts and their separate footings are removed; the drying rack moves east, clear of the door swing. The 1300 mm-deep entrance porch now projects 300 mm beyond the balcony, with no separate canopy. The R11 lot of 140.4182 m² and two side-by-side parking bays remain. Cantilever capacity, connections, waterproofing and drainage are unengineered; all dimensions are demonstration assumptions.

[Design and references](docs/house_facade_R13.md) · [Two-floor PDF](output/pdf/house_floor_plans_R10_JP.pdf) · [1F DXF](DXF/house_1f_plan.dxf) · [2F DXF](DXF/house_2f_plan.dxf) · [GLB](GLB/house_3d.glb) · [STEP](STEP/house_3d.step)

## Model day/night and outdoor fixtures (R08-3D)

The 3D viewer now switches between day and night independently of the page light/dark theme. The house adds seven named outdoor fixtures: one entrance wall light, two path lights, two garden lights and two gate-post lights. Choose “Night” and enable “Outdoor lights” for warm illumination; switching off retains the fixture geometry. Hidden categories, interior/structural presets and section cuts disable the corresponding sources. Lighting choices persist and can be shared by URL; day/night switching preserves the camera, furniture and section state.

Fixtures are included in STEP/GLB and retain editable parametric source. All sizes, positions and the 3000 K warm appearance are demonstration assumptions; illuminance, circuits, product weatherproof ratings and installation remain undetermined. Confirmed plans, apartment files and R07 structural files remain unchanged. [Parameters, usage and validation](docs/outdoor_lighting_R08.md).

## Four cities and three structural systems (R07)

Added 12 conditional cases: Tokyo / Osaka City / Kyoto City / Nagoya City × timber W / lightweight steel S / reinforced concrete RC. In “Structural scheme”, choose the city and system to inspect distinct named structural geometry, local review references, and download the corresponding STEP, GLB and case JSON. Official references include applicability, sources and verification dates. [Concepts and regeneration](docs/structural_comparison_R07.md) · [Official regulatory references](docs/regulations_R07.md).

Three independent overlays retain the existing building and user-confirmed plans. City selection changes references; it does not fabricate site-dependent member sizing. All sections are demonstration assumptions. Timber wall/connection checks, thin-wall steel buckling/bracing, RC reinforcement/self-weight, foundations and architectural coordination require further design. Capacity, statutory compliance and approval remain undetermined for all 12 cases. This is not construction-ready structural design.

## Structural layout and storage-use demonstration (R06-3D)

The structural layout introduced in R06 is a **demonstration concept**, with no actual building location specified. The 8190 × 7280 mm outline, two 2800 mm storeys and user-confirmed first- and second-floor plans remain. A physical flat ceiling limits the storage-only attic to **1350 mm maximum finished clear height**. Local use classification, statutory area, soil conditions and building approval remain pending. The height is a design target, not regulatory approval.

The separate `structure` root contains columns, beams, sills, attic joists, hatch headers, roof framing and candidate bearing walls. The “Structural scheme” preset shows timber and foundations while hiding finishes, doors/windows, furniture and roof cladding. Normal exterior and interior presets hide the timber proposal to avoid overlapping representations. Every member size is a demonstration assumption; wall candidates do not establish bearing capacity, seismic rating or calculation results. Original perimeter plinths retain their geometry under a separate `foundation` category. Internal foundation supports follow candidate column lines. Loads, materials, sizes, joints, reinforcement and soil capacity remain uncalculated.

Downloads include `DXF/house_structural_scheme.dxf`, `output/pdf/house_structural_scheme_R06_JP.pdf` and `output/review/engineering_inputs_R06.json`. The JSON records pending site, soil, load, material and regulatory inputs; it is not a calculation report. Source and STEP/GLB retain editable named structure. Construction use requires a Japanese architect to complete local compliance review, structural calculations, building approval and construction supervision. The apartment remains independent.

## Foundation, fence and yard (R13-SITE)

Independent `foundation`, `yard` and `fence` groups add a conceptual raft foundation with perimeter stem walls, entrance supports and a lower step, gravel, parking paving and wheel stops, three narrow lawns, two side-by-side parking bays with all shrubs removed, and fences with actual gaps between slats. The exterior preset shows the site; interior presets hide it. Each category can be hidden or viewed alone. Section heights remain measured from the first-floor finished datum, Z=0.

All added dimensions are **demonstration assumptions**: a **10190 × 13780 mm lot (140.4182 m² geometric area)**, outdoor grade at **Z=-500 mm**, a 150 mm raft, 140 mm perimeter stem walls, and two **2800 × 5000 mm side-by-side parking bays**. The 1200 mm-high fence has 24 open panels, 26 posts and 26 footings, with clear southern vehicle/pedestrian openings of 5675/1800 mm. Grade, lower step, existing step, existing porch and entrance floor are at -500/-330/-160/-25/0 mm. Dimensions, planting and materials are editable in `src/lib/site_geometry.py`; reinforcement, bearing capacity and ground treatment have not been designed.

R05 originally contained 537 named bodies after adding the site. The current export contains 891 named leaf bodies; see export validation for details. The supplemental `DXF/house_site_plan.dxf` and `output/pdf/house_site_plan_R05_JP.pdf` use A3, a 1:100 site plan and a labelled 1:25 conceptual foundation section, with editable text and dimensions. Approved floor drawings remain; the attic drawing is updated to R06. [Parameters and scope](docs/site_R11.md).

```bash
.venv/bin/python src/generate_site_plan.py
CADGEN_DAEMON=0 .venv/bin/python src/house_3d.py
.venv/bin/python checks/validate_3d.py
.venv/bin/python checks/validate_site.py
```

## Storage attic (R06-3D)

The attic remains inside the R03 gable envelope, with user-confirmed first- and second-floor boundaries unchanged. The attic interior preset shows floors, lining/knee walls, storage and hatch guardrails. Hide the deployed access ladder separately. It occupies the second-floor hall; hiding it does not simulate mechanical folding.

All dimensions are **demonstration assumptions**: a 3680 × 6880 mm deck, clear 1200 × 650 mm hatch and 24.5384 m² geometric projection after subtracting the opening. The previous 200 mm concept ceiling panel is replaced by a 24 mm subfloor at Z=5576–5600 mm. The 18 mm finish remains at Z=5618 mm. A physical flat ceiling with its underside at Z=6968 mm and 50 mm thickness limits maximum clear height to 1350 mm; deck-edge height is approximately 1233.93 mm. Space above the ceiling is excluded from usable storage. The upper standing area has approximately 1254 mm minimum headroom, showing low storage access only; actual ladder products, safe operation, insulation, ventilation and ceiling suspension remain undesigned.

Parameters are in `src/lib/attic_geometry.py`. Current `DXF/house_attic_plan.dxf` retains editable text and dimensions. The current supplement is `output/pdf/house_attic_plan_R06_JP.pdf`, A3 at 1:50 with an east–west section. The R04 PDF and notes remain historical and do not describe current headroom. The fixed ceiling is only a candidate treatment. Local measurement of the finished ceiling and residual cavity, and storey classification, remain pending; adding a ceiling alone does not establish area or storey exemption. Neither 1350 mm nor 24.5384 m² establishes local regulatory recognition. Approved R02 floor plans are unchanged.

```bash
.venv/bin/python src/generate_attic_plan.py
CADGEN_DAEMON=0 .venv/bin/python src/house_3d.py
.venv/bin/python checks/validate_3d.py
```

## Contemporary Japanese house exterior (R03-3D)

The house uses warm-white siding, a timber-tone entry door, a charcoal gable roof and black window frames. New named solids include roof standing seams, a ridge cap, bargeboards, soffits, gutters, floor-specific downpipes, a balcony sheltering the entrance and a porch, and individual sill flashings. Continuous siding covers the slab edges. Exterior dimensions, colours and texture repeat sizes are demonstration assumptions. The 8190 × 7280 mm finished building body, two 2800 mm storey heights, user-confirmed room layout and door/window rough openings are retained.

Parametric sources are `src/lib/exterior_geometry.py` and `src/lib/exterior_materials.py`. New components belong to the existing external-wall, door, window and roof categories, with Chinese, Japanese and English names, selection, visibility and section support. STEP contains solids and colours; GLB also embeds original siding and timber textures. [Official Nichiha, KMEW and YKK AP references](references/japanese-house-exterior.md) informed the design; no manufacturer photographs, textures or CAD models are redistributed.

## Furniture and detailed fixtures (R02-3D / A02-3D)

Both layouts now have a “Furniture” checkbox above the 3D canvas, enabled by default. Beds, sofas, coffee tables, dining tables/chairs and TV consoles have individual names under each floor’s `F#:furniture` group. Toggle them together or hide/isolate one floor’s furniture in the component tree. The toggle preserves the active floor, camera and section height; furniture choices also survive view preset, language and theme changes.

`F#:fixtures` includes detailed bathtub interiors, washbasins and taps, mirrors, toilets, washing-machine doors, kitchen sinks and hobs. Wood, fabric, ceramic, metal and glass have distinct colours and surface roughness; a locally generated studio environment supplies reflections. Furniture and fixtures are included in the downloadable STEP / GLB. Existing annotated plans keep their user-confirmed layout and do not change with the 3D furniture toggle.

All shapes are original parametric geometry generated by `src/lib/furniture_geometry.py` and `src/lib/fixture_geometry.py`. Public product information informs dimensions and shape only. No manufacturer model is imported or redistributed, and the geometry does not establish product selection or installation suitability. See [reference sources and scope](references/interior-furnishings.md).

## Loading and controls

Online models use lossless GZIP transport: the house shrinks from 8.03 MB to 3.08 MB and the apartment from 5.21 MB to 2.30 MB (decimal MB). Decompressed bytes match the original GLB exactly. Missing compressed files or browsers without decompression support fall back to the original GLB; downloads retain the original files. Structural overlays also support compression, deadlines and cancellation. This reduces transfer size; it does not establish a rendering frame-rate improvement.

Section controls appear first in the sidebar. Search components by Chinese, Japanese or English names and original IDs, or expand/collapse all groups. Search filters only the list; floor checkboxes still affect the entire floor. On mobile, the component list starts collapsed. Structural notes and parameters open on demand while visibility and selection state remain intact.

## Online viewer

[Open the house CAD viewer](https://kai987.github.io/text-CAD/). Above the canvas, switch between the complete exterior, first-floor interior, and second-floor interior. The component tree controls the visibility of floors, external walls, partitions, slabs, doors, windows, storage, stairs, and the roof. Click a name or a 3D component to highlight it and inspect its name in the selected language. Use “Only” to show only the selected category and the top presets to restore visibility. The browser also supports rotation, zoom, and horizontal section cuts. The plan page initially shows rooms and dimensions, with an option to display the complete R02 A3 sheet. It supports vector zoom and editable DXF downloads. The files page provides STEP, GLB, DXF, PDF, and parameter notes.

On entry, the selected layout’s 3D model and all floor plans load in parallel, including when the initial page is a plan or downloads. Tab changes reuse parsed drawings and retain the 3D camera, section and selection state. Changing layouts releases the previous 3D scene and prepares the new layout. Loading messages remain visible during the first download.

The language selector supports **简体中文, 日本語, and English**. Chinese is the default when no selection has been saved. Your choice is saved in the current browser and restored on your next visit. Interface text updates immediately while preserving the current page, floor, camera, section cut, component visibility and selection, and plan zoom. The web room table uses translated room names. Japanese labels in the original CAD, PDF, and SVG drawings, and original component names, remain unchanged. The links above switch between the repository’s README language versions.

The header’s “Color mode” selector offers Auto, Light, and Dark. The first visit follows the operating system’s appearance, and your choice is saved in the current browser. Auto continues to track system appearance changes. Switching preserves the camera, component visibility and selection, section height, and plan zoom. Dark mode changes the interface and 3D background; the original CAD, PDF, and SVG drawing sheets stay white for readability, and printed files are unchanged.

The web app is in `web/` and uses React, TypeScript, Three.js, and Vite. It does not require the local Python viewer. It reads the generated GLB directly without changing CAD geometry. STEP and DXF are available as original-file downloads. Online plans use SVG converted from the original PDF, with all text converted to glyph outlines so that visitors do not need Japanese or Chinese fonts. The complete sheet content is retained; the focused plan view uses a cropped viewport of the same SVG. Overall dimensions in both directions, room names, door references, door swing arcs, and the north arrow are preserved. The model retains the original `F1`, `F2`, `stairs`, and `roof` nodes and eight component categories within each floor. Original names are restored through the GLTFLoader node-index mapping. Phones support touch rotation and zoom. Browsers that cannot run WebGL show a static preview matching the current preset.

Use Node.js 24 or a later compatible version:

```bash
cd web
npm ci
npm test
npm run dev
# Production build and local preview
npm run build
npm run preview
```

The Rust/WASM geometry core is in `rust/section-caps/`. Section caps and CAD outlines for walls, cladding and gables run in a dedicated Worker by default. Three.js rendering buffers stay on the UI thread; the Worker receives independently copied geometry registered once. Rapid section-height changes retain one running batch and only the latest pending height; stale results are discarded. Switching models terminates the previous Worker. WASM or Worker initialization, communication and calculation failures or timeouts fall back to TypeScript. Existing `section=wasm` links remain compatible; `section=typescript` explicitly selects the original algorithm for comparison and persists across model and plan navigation. Changing the engine does not alter the CAD, plans, camera or component names.

Rust computes in `f64` and returns `f32`. Parity checks cover holes, cabinet caps, stair openings, normals, world transforms and coplanar wall seams. The benchmark uses the current house GLB and its first-floor finished datum, measuring direct TypeScript/WASM section and CAD-outline work separately. Node timings exclude Worker transfer and queueing, network, image decoding and GPU rendering, so they do not establish a browser frame-rate improvement. Run the following in `web/`; ordinary tests and publishing use committed WASM and do not require Rust.

The current model was measured locally with Node 23.7.0 on macOS arm64 after 30 warmup batches and across 150 trials. Each section batch processes 745 opaque meshes at four heights; median time including cap edges was 32.259 ms for TypeScript and 30.781 ms for Rust/WASM. A batch of 24 wall outlines took 2.500 ms and 0.886 ms respectively. These measure direct algorithm calls; UI-thread load also depends on Worker scheduling and rendering.

```bash
npm run bench:sections -- --edges
# Regenerate after changing the Rust core; uses pinned Rust 1.93.0
cargo install wasm-bindgen-cli --version 0.2.114 --locked
npm run build:wasm
npm test
npm run build
```

`build:wasm` runs native Rust tests and generates WASM/JS bindings plus source and output hashes. Ordinary tests and builds reject stale artifacts. A separate Rust workflow runs native tests, Clippy, and WASM compilation. The benchmark accepts `--output /absolute/path/result.json` to save its results.

### Native Rust spatial checks for Python

`rust/spatial-core/` connects to Python through PyO3. A Rust BVH batches bounding-box candidate filtering for furniture footprints, door swings, wardrobe approaches, kitchen working areas, paths and rooms. Shapely/GEOS still evaluates actual overlap areas and room coverage, preserving the existing semantics for boundaries, holes and tiny area thresholds. Structural components likewise use Rust candidate filtering followed by exact BRep intersections in the CAD kernel. Rust does not directly calculate polygon areas or coverage. Parametric modeling, STEP exports and DXF annotations retain the existing Python workflow. Dimensions, clearances and engineering conditions remain demonstration assumptions; switching computation engines does not certify structural or regulatory compliance.

Support checks for beams, columns, foundations and attic components now also use Rust contact candidate filtering, including touching faces and candidates within a 0.001 mm tolerance. The CAD kernel still computes final distances and shared face areas. Each check run caches immutable shapes' bounds and faces and preserves component order. This round compared the complete original reports: all 910 checks for the timber source model and all 2,987 checks for the saved W/S/RC models were identical.

GLB checks now read binary positions, normals and triangle indices directly. Rust validates finite values, index ranges, buffer spans and decoded bounds, which are compared with declared POSITION bounds. The supported profile covers the project's dense float32 triangle exports, interleaved buffers and all three unsigned index widths; sparse, compressed or other primitives produce explicit errors. Zero-area triangles are diagnostic entries. The audit does not assess manifold topology, normal direction or structural safety. The five existing GLBs contain 1,568 meshes, 373,811 vertices and 587,954 triangles; full Rust and independent Python decoder reports match exactly.

Build and verify from the repository root:

```bash
.venv/bin/python src/build_spatial_native.py
.venv/bin/python -m unittest checks/test_native_spatial.py checks/test_furniture_native.py checks/test_structural_native.py checks/test_contact_native.py checks/test_glb_native.py -v
cargo +1.93.0 test --manifest-path rust/spatial-core/Cargo.toml --locked
.venv/bin/python checks/validate_glb_native.py --backend rust --report /tmp/glb-audit.json
.venv/bin/python checks/benchmark_native_spatial.py --output /tmp/spatial.json
.venv/bin/python checks/benchmark_mesh_native.py --output /tmp/mesh-audit.json
```

`TEXT_CAD_SPATIAL_BACKEND` selects the candidate-filtering and GLB numeric-audit backend: `auto` (default; fall back to Python if the native extension is unavailable or cannot process the input), `python` (require Python), or `rust` (require native computation and raise an error on failure without fallback). For example: `TEXT_CAD_SPATIAL_BACKEND=rust .venv/bin/python checks/validate_furniture.py`. The GLB CLI also accepts `--backend`; by default it reads the five models and only writes a report when `--report` is specified. The extension binary is specific to the local platform, architecture and Python version. Local binaries and their source/output hash manifest are ignored by Git. Rebuild after changing the sources or bindings; an extension with a mismatched API, Python version or hashes is not loaded. The loader caches per process, so restart Python after rebuilding.

Local measurements on macOS arm64 with Python 3.13.14 used five warmups and 30 trials. Median times for complete furniture clearance reports include geometry preparation and binding overhead:

| Layout | Original Shapely (ms) | Batched Python (ms) | Rust-filtered GEOS (ms) |
|---|---:|---:|---:|
| House first floor | 3.6260 | 1.1742 | 1.1290 |
| House second floor | 2.2451 | 1.0251 | 1.1511 |
| Apartment | 6.8717 | 2.1705 | 1.7361 |

Small cases are not universally faster: the second-floor hybrid is slightly slower than batched Python. A synthetic test with seed 41007, 10,000 bounding boxes and 100 queries measured medians of 296.1490 ms for Python and 13.4709 ms for Rust, approximately 22 times faster including binding, BVH construction and query overhead. This does not establish a whole-CAD or browser speedup. The [native CI workflow](.github/workflows/rust-spatial.yml) builds the extension, rejects skipped mandatory native checks, then compares complete reports. Consult GitHub Actions for remote run results.

A separate GLB numeric-audit benchmark on the same platform used three warmups and ten trials. Files were read before timing. Median times below include JSON parsing, layout validation, numeric scanning and declared-bound checks; they exclude file reads, CAD generation and GPU rendering:

| GLB file | Python (ms) | Rust (ms) |
|---|---:|---:|
| house_3d.glb | 695.7725 | 32.4407 |
| apartment_2ldk.glb | 507.5495 | 11.0522 |
| structure_W.glb | 15.1299 | 6.3503 |
| structure_S.glb | 37.0454 | 11.6927 |
| structure_RC.glb | 3.5962 | 1.2933 |

This round passed 53 local Python tests, 15 Rust tests, fmt and Clippy under both feature configurations. Contact-filtering report parity is verified; a separate controlled performance benchmark has not been established for that path. CAD, drawings and existing acceptance reports were not regenerated for this migration.

Development and builds copy the current manifest of CAD, drawing, and reference assets from the repository, including vector previews for both floors, and generate a SHA-256 manifest. The production build verifies the copies again. Vector metadata also records the source PDF hash, SVG hashes, and annotation bounds within the crop. Builds fail if the source PDF has changed or an SVG does not match, requiring conversion first. `web/public/artifacts/`, derived data, and `web/dist/` are not committed to Git.

After changing the design, regenerate CAD and PDF and complete the relevant checks before updating vector previews. The converter uses Python locally; the GitHub Pages build reads the committed SVG files directly:

```bash
uv pip install --python .venv/bin/python PyMuPDF==1.26.7
.venv/bin/python web/scripts/generate-plan-svg.py
```

Commit `output/vector/house_1f_plan.svg`, `house_2f_plan.svg`, and `web/src/plan-preview-metadata.json`, then rebuild. The current crop and required labels correspond to the user-confirmed 7,280 mm demonstration design. Recheck the crop and annotations if the plan dimensions or sheet layout change.

On pushes to `main`, `.github/workflows/pages.yml` installs dependencies, runs model-control tests, checks TypeScript, builds the app, verifies file hashes, and publishes to GitHub Pages. Online dimensions remain demonstration assumptions. Outstanding structural and service-design items are listed below.

## Added 2LDK apartment concept (A01)

[Open the apartment](https://kai987.github.io/text-CAD/?model=apartment&view=3d). The header selector switches between the existing two-storey house and the apartment. The apartment opens with an interior section view and offers whole-unit, ceiling, balcony and fixture controls. Its single-floor plan, downloads, room areas and notes follow the selected model; language and appearance preferences are retained. The apartment also uses the Rust/WASM Worker by default; append `&section=typescript` to compare the original algorithm.

The **7800 × 8400 mm outline (65.52 m²)**, **2800 mm storey height** and **2500 mm clear height** are demonstration assumptions. The 65.52 m² figure is the outer rectangular footprint, **not net internal area or legally defined exclusive area**. Clear room polygons total **56.54 m²**, including furniture footprints. The south balcony slab has a separate **11.70 m²** projected area (7800 × 1500 mm). This is one apartment unit; the complete building, shared corridor and neighbouring units are outside the model.

The north entrance connects through a hallway to two bedrooms, the toilet, wash/changing room and south-facing LDK. The bathroom is accessed through the washroom; storage and the south balcony are accessed from the LDK. Plans include opening dimensions, door directions, clear room dimensions and areas. DXF text and native dimensions remain editable. Orientation, wall thicknesses, furniture, fixtures and opening sizes are assumptions; structure, services and regulatory compliance require further professional review.

- Generator: `src/apartment_2ldk.py`; plan and geometry parameters: `src/lib/apartment_plan.py`, `src/lib/apartment_geometry.py`.
- 3D: `GLB/apartment_2ldk.glb`, `STEP/apartment_2ldk.step`; groups: `F1` (unit interior), `ceiling`, `balcony`, with equipment under `F1:fixtures`.
- Plans: `DXF/apartment_2ldk_plan.dxf`, `output/pdf/apartment_2ldk_plan.pdf`, `output/vector/apartment_2ldk_plan.svg`.
- Parameters and drawing provenance: `output/review/apartment_2ldk_manifest.json`, `output/review/apartment_2ldk_preview.json`.

```bash
.venv/bin/python src/apartment_2ldk.py
.venv/bin/python checks/validate_apartment.py
cd web
npm test
npm run build
```

The apartment is generated and checked independently of the house. Generation requires the Python dependencies in `requirements.txt`; web publication consumes committed CAD, PDF and vector assets.

## Files

- `src/lib/house_plan.py`: shared millimetre parameters, clear room boundaries, walls, door and window openings, furniture placeholders, and assumptions for both floors.
- `src/generate_plans.py`: ezdxf generation of editable TEXT / DIMENSION annotations and house plans, plus a two-page landscape A3 review PDF at 1:50.
- `src/lib/jp_drafting.py`, `src/lib/jp_sheet.py`: adapted layer names, paper text heights and lineweights, and the shared A3 frame, title block, area table, and notes.
- `DXF/001D0PL2-1FPLAN.DXF`, `DXF/002D0PL2-2FPLAN.DXF`: floor plans with filenames adapted to the R02 naming rules.
- `DXF/house_1f_plan.dxf`, `DXF/house_2f_plan.dxf`: R2018 DXF, millimetres, model space at 1:1.
- `output/pdf/house_floor_plans_R10_JP.pdf`: current floor plans, frames, title blocks, area tables, and assumptions. Print at actual A3 size without automatic scaling. The R01 PDF is retained as a historical version.
- `docs/tokyo_cad_standard_mapping_R02.md`: source-standard sections and pages, residential adaptations, and items outside the scope.
- `checks/validate_jp_drafting.py`, `output/review/validation_jp_drafting.json`: checks of saved layers, text heights, colours, lineweights, native dimensions, and paper space.
- `output/review/design_manifest.json`: machine-readable parameters, all assumptions, and room areas.
- `checks/validate_plans.py`: checks of the current layout geometry, doors, stairs, and saved DXF files.
- `output/review/validation.json`: actual check results and unverified items.
- `src/lib/house_geometry.py`: 3D parameters using the user-confirmed plans, wall apertures, slabs, gable roof, doors, windows, and U-shaped stairs.
- `src/house_3d.py`: 3D assembly entry point for regenerating STEP and GLB.
- `STEP/house_3d.step`: precise millimetre solids, named by `F1`, `F2`, `stairs`, `roof`, and component. The adjacent `.step.json` stores CADgen viewer materials and other metadata.
- `GLB/house_3d.glb`: standard glTF 2.0 in metres with Y up, preserving component names and hierarchy for viewing and editing in Blender and other tools.
- `output/review/house_3d_assumptions_R01.json`: 3D demonstration parameters and specific assumptions.
- `checks/validate_3d.py`, `output/review/validation_3d.json`: checks of saved STEP solids and GLB units, names, hierarchy, and related properties.

## Previous plan (R01/R02 history)

Coordinates use X east and Y north. The south entrance and north direction are demonstration assumptions; no site or road information has been supplied.

First floor: an LDK living/dining/kitchen space to the south (20.17 m²), entrance and shoe storage to the southeast, bathroom, wash/changing room and pantry to the north, toilet to the east, and stairs to the northeast. The bathroom is entered through the wash/changing room.

Second floor: main bedroom (10.45 m²), bedroom 2 (L-shaped, exact area 8.895 m²), bedroom 3 (9.17 m²), storage room, toilet, and shared corridor. The toilet is entered from the north side of the corridor without passing through a bedroom. The original drawing labels are 「主寝室」「洋室 2」「洋室 3」「納戸」.

Toilets and stairs align between floors. The northeast U-shaped stairs have 16 risers at 175 mm, 260 mm treads, a clear width of 900 mm per flight, and a 900 mm intermediate landing. The reserved stairwell is 1,900 × 2,720 mm. The second-floor slab has an opening for the complete stairwell.

All visible DXF layers use ACI 7, with geometry inheriting colour through ByLayer and no fixed RGB. CAD viewers display white on dark backgrounds and black on light backgrounds, keeping room labels, door references, and furniture text readable. The PDF uses black lines and text on white. Changing the background does not require regenerating the model.

## R02 drafting-standard adaptation

The drawings adapt common provisions of the [Tokyo Metropolitan Government Construction Bureau CAD Drafting Standard, April 2024](https://www.kensetsu.metro.tokyo.lg.jp/documents/d/kensetsu/000067788). This document governs civil engineering. The house concept adopts its common drafting rules; the mapping record explains each decision and its source section. This does not establish compliance with all residential construction-drawing or electronic-delivery requirements.

Landscape A3 at 1:50 is retained. The standard normally uses A1 but allows other A-series sizes as appropriate. Margins are 7.5 mm on all sides, with a 0.70 mm frame line. A 60 × 45 mm title block sits at the bottom right and uses a Japanese-era date. General geometry uses 0.13 / 0.25 / 0.50 mm lineweights; dimension lines use 0.13 mm. Paper text heights are 3.5 mm for room names, 2.5 mm for dimensions and areas, 1.8 mm for small notes, and 5 mm for titles. Model-space text heights are 50 times their paper heights.

Layers such as `D-STR-WALL` and `D-STR-DIM` follow the responsibility / drawing-object / drafting-element naming structure. The meanings of added residential elements are recorded. Native DIMENSION entities and text remain editable.

The frame and title block are in the DXF’s **`JP_A3_1_50` paper-space layout**, with a locked 1:50 viewport. The PDF shows the complete sheet. The text-to-cad browser viewer displays model space, so it does not show the paper-space frame. Legacy-name DXFs and the DXFs using the adapted naming rules have identical content, and existing viewer links remain usable.

SXF(P21/P2Z), DRAWING.XML, and electronic-delivery folders have not been produced. Existing 3D STEP and GLB files are unchanged. STEP and the SXF(P21) format used for 2D electronic delivery are different formats.

## Explicit assumptions and unresolved items

1. The 7,280 × 7,280 mm outline and 2,800 mm storey height are user-specified **demonstration assumptions**.
2. External walls at 180 mm and internal walls at 100 mm are placeholders, not a designed timber structure or building assembly.
3. Room annotations use clear dimensions inside walls. Areas include furniture footprints. Stair areas describe the reserved stairwell, including the second-floor opening. The rounded 53.00 m² per floor and 106.00 m² total describe only the geometric outline area and cannot be used directly as statutory building or floor areas.
4. Door widths represent drawn openings before deducting frames. Bedroom doors swing into the rooms. Sliding doors are shown as placeholders that retract into wall pockets; actual pockets, hardware, and clear opening widths require further detailing.
5. The user-confirmed toilet layout is compact at 900 × 1,700 mm. The pantry has a 350 mm shelf placeholder on one side, leaving a 730 mm passage. It is not treated as a main circulation route.
6. The bathroom and wash/changing room are each 4.95 m², retaining the user-confirmed allocation.
7. Furniture, kitchen units, bathtub, sanitary fixtures, and windows are dimensional placeholders, not selected products. Storey height is not clear room height.
8. Additional 3D assumptions: slabs 200 mm thick; door openings 2,100 mm high; large windows with a 900 mm sill and 1,300 mm height; small windows with a 1,500 mm sill and 600 mm height; gable roof pitch 30°, eaves projection 450 mm, and vertical roof thickness 150 mm. These are not finalized construction assemblies.
9. Structure, site constraints, building services, statutory areas, and building-code compliance are unverified. Actual stair headroom must be checked after slabs, beams, and finishes are determined.

The 3D finished-floor datums are Z=0 and 2,800 mm, with slabs below those datums and a provisional clear wall height of 2,600 mm. R06 uses a 24 mm attic subfloor below Z=5600 mm and a separate timber structural proposal. The intermediate landing is 200 mm thick. Each half-flight has seven complete 260 mm treads; the landing and second-floor surface form the respective eighth risers. Stairs use conceptual stepped solids. Handrails, stair beams, and structural connections require further design.

Walls retain the material above doors and below and above windows. Openings reuse the user-confirmed plan positions. 3D door leaves are shown closed, while plan doors show their opening direction. Shoe storage and other cabinets are named dimensional placeholder solids.

## Regenerate and view

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

The last command returns the actual viewer URL. Open `URL?file=DXF%2Fhouse_1f_plan.dxf`, `URL?file=DXF%2Fhouse_2f_plan.dxf`, `URL?file=STEP%2Fhouse_3d.step`, or `URL?file=GLB%2Fhouse_3d.glb`. The viewer is read-only. After changing plan or 3D parameters, rerun the corresponding generator and checks. The STEP component tree can show or hide individual floors, walls, slabs, doors, windows, stairs, and the roof.

A background snapshot worker was observed to omit repeated text. The transient-worker commands above generated complete text. Original PDF and DXF TEXT entities have also been checked independently.

PDF generation uses macOS’s `Arial Unicode.ttf`. Update the generator’s font path when moving to another operating system. DXF text and dimensions are editable, but the CAD application still needs fonts that support Japanese and Chinese.

## text-to-cad workflow

The project follows the official [CAD](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/SKILL.md) and [DXF](https://github.com/earthtojake/text-to-cad/blob/main/skills/dxf/SKILL.md) guidance, with the runtime pinned to `cadgen[snapshot]==0.7.11`. The referenced upstream source revision is `8d795f56343edce7ef6b9413e02f7a92318f8229`; local reference material is in `.tools/text-to-cad/`.

The official `@dxf` output contract targets manufacturing geometry and converts text to outlines. As authorized by the user, this concept therefore uses ezdxf directly for editable architectural plan text, dimensions, and door/window layers, followed by cadgen checks and viewer review.

## Further design work

These files form a parametric concept model. The actual site, structural system, wall and roof assemblies, door and window products, sliding-door pockets, stair handrails, and building services require further design. The model cannot be used as construction drawings until the relevant professional checks are complete.

### CAD release checks and model recovery

This earlier optimization used R13; R14 subsequently reflects the layout. Key measurements in all three languages are rendered from exported model parameters, including storage heights, stairs, floor-height glazing, wall thicknesses and clear balcony area.

- Rebuild the current house/apartment catalog and validate it: `.venv/bin/python src/cad_pipeline.py --regenerate`.
- Check source/output provenance before validating saved artifacts: `.venv/bin/python src/cad_pipeline.py --validate`.
- Fast publication freshness check: `python3 src/cad_release.py`.

`output/review/cad_release.json` records source/output hashes, tools, font and completed generation/validation steps. Web builds reject stale CAD after source changes, and Pages deployment depends on CAD validation. Runtime timestamps in validation reports are excluded from artifact binding. Configure a licensed CJK TTF with `TEXT_CAD_CJK_FONT=/absolute/path/CJK.ttf`; the existing macOS font remains the default. Saved-artifact checks do not require the authoring font, but regenerating drawings does. R05/R06/R10 download paths remain compatibility aliases; the title blocks and manifests identify the actual revision.

The main model reports download progress and enforces a 60-second deadline across download and parsing. Failures offer retry; cancelled requests and late decode results are discarded. After WebGL recovery, the viewer rebuilds while preserving its camera, component visibility, section, day/night and structural choices. An uninitialized camera from an initial download failure is not restored.

These checks establish concept geometry, file consistency and viewer behavior. They do not certify structural capacity, regulatory compliance or construction readiness.
