"""Parametric landmark appearance models, millimetres and Z-up.

Explicitly cited controls and historical reference dimensions are recorded
separately from assumed section assignments, interpolation, glazing, foundations
and all other unreferenced geometry. This is
original concept geometry, not surveyed or original architectural CAD.

The parameter and component-specification API is dependency-free. build123d
is imported only when ``tower_assembly`` actually creates CAD solids; drawings
and tests can read exactly the same specification without a CAD environment.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from math import cos, sin, pi, sqrt

from .tokyo_tower_parameters import parameters as tokyo_tower_parameters
from .skytree_parameters import parameters as skytree_parameters
from .tower_parameters import validate_tower_parameters

REVISION = 'LANDMARK-R01'
CHECKED_ON = '2026-10-30'
GROUPS = ('base', 'structure', 'core', 'decks', 'antenna')
GROUP_NAMES = {
    'base': {'zh': '基座与地面', 'ja': '基壇・地盤', 'en': 'Base and ground'},
    'structure': {'zh': '塔身与桁架', 'ja': '塔体・トラス', 'en': 'Tower frame'},
    'core': {'zh': '中央核心与竖井', 'ja': '中央コア・シャフト', 'en': 'Central core and shafts'},
    'decks': {'zh': '展望台', 'ja': '展望施設', 'en': 'Observation decks'},
    'antenna': {'zh': '天线与塔尖', 'ja': 'アンテナ・塔頂', 'en': 'Antenna and spire'},
}
TOWERS = {
    'tokyo-tower': validate_tower_parameters('tokyo-tower', tokyo_tower_parameters()),
    'tokyo-skytree': validate_tower_parameters('tokyo-skytree', skytree_parameters()),
}


def _tower(tower_id):
    try:
        return TOWERS[tower_id]
    except KeyError as error:
        raise ValueError(f'Unknown landmark: {tower_id!r}') from error


def geometry_source_paths(tower_id):
    """Explicit per-model sources, including only that tower's parameter module."""
    _tower(tower_id)
    common = ['src/lib/tower_geometry.py', 'src/lib/tower_parameters.py']
    specific = {
        'tokyo-tower': [
            'src/lib/tokyo_tower_parameters.py', 'src/lib/tokyo_tower_detail.py',
            'src/lib/tokyo_tower_steel.py', 'src/lib/tokyo_tower_equipment.py',
            'src/lib/tokyo_tower_builtup.py', 'src/lib/tokyo_tower_integrated.py',
            'src/lib/tokyo_tower_grid.py',
        ],
        'tokyo-skytree': [
            'src/lib/skytree_parameters.py', 'src/lib/skytree_detail.py',
            'src/lib/skytree_outline.py',
        ],
    }
    return [*common, *specific[tower_id]]


def revision_for(tower_id):
    return _tower(tower_id).get('revision', REVISION)


def profile_radius(tower_id, z):
    """Return the active outline, including explicitly configured local fits (mm)."""
    if tower_id == 'tokyo-tower':
        from .tokyo_tower_detail import body_radius
        return body_radius(_tower(tower_id), z)
    from .skytree_outline import profile_radius as detailed_radius
    return detailed_radius(_tower(tower_id), z)


def circle_points(radius, divisions=24, angle=0):
    return [[radius * cos(angle + 2 * pi * i / divisions),
             radius * sin(angle + 2 * pi * i / divisions)] for i in range(divisions)]


def square_points(half_width):
    return [[-half_width, -half_width], [half_width, -half_width],
            [half_width, half_width], [-half_width, half_width]]


def ring_points(tower_id, z):
    """The actual frame-node positions used by both CAD and drawing exports."""
    p = _tower(tower_id)
    radius = profile_radius(tower_id, z)
    if p['profile_kind'] == 'square_half_width':
        return square_points(radius)
    from .skytree_outline import ring_points as outline_ring
    return outline_ring(p,z)


def profile_ring(tower_id, z):
    """Alias for clients projecting the common frame outline."""
    return ring_points(tower_id, z)


def base_vertices(tower_id):
    """Primary leg centres: four square or three equilateral vertices."""
    points = ring_points(tower_id, 0)
    return points if tower_id == 'tokyo-tower' else points[::8]


def _section(z, points):
    return {'z': z, 'points': points}


def _beam(group, name, a, b, radius, color):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'beam',
            'start': list(a), 'end': list(b), 'radius': radius, 'color': color}


def _loft(group, name, sections, color):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'loft',
            'sections': sections, 'color': color}


def _box(group, name, bounds, color):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'box',
            'bounds': list(bounds), 'color': color}


def _tower_paint(z):
    # Seven schematic bands above the model main deck, ending orange/red.
    if z < 125000:
        return '#E34C25'
    index = min(6, int((z - 125000) / ((333000 - 125000) / 7)))
    return '#E34C25' if index % 2 == 0 else '#F4F0E7'


def _tokyo_base_specs():
    from .tokyo_tower_detail import component_specs as detailed_specs
    return detailed_specs(TOWERS['tokyo-tower'],
                          lambda z: ring_points('tokyo-tower', z), _tower_paint)


def _tokyo_specs():
    from .tokyo_tower_steel import refine_steel
    from .tokyo_tower_builtup import refine_built_up
    from .tokyo_tower_integrated import refine_integrated
    from .tokyo_tower_grid import refine_grid
    p=TOWERS['tokyo-tower']
    return refine_grid(p,refine_integrated(p,refine_built_up(p,refine_steel(p,_tokyo_base_specs()))))


def _skytree_specs():
    from .skytree_detail import component_specs as detailed_specs
    return detailed_specs(TOWERS['tokyo-skytree'],
                          lambda z: ring_points('tokyo-skytree', z))


@lru_cache(maxsize=2)
def _component_specs_cached(tower_id):
    _tower(tower_id)
    return _tokyo_specs() if tower_id=='tokyo-tower' else _skytree_specs()


def component_specs(tower_id):
    """Return a private copy of exact beam/box/loft input records, in mm."""
    return deepcopy(_component_specs_cached(tower_id))


def assembly_specs(tower_id):
    """Alias for drawing clients: this is also the exact 3D source geometry."""
    return component_specs(tower_id)


def geometry_manifest(tower_id):
    p=deepcopy(_tower(tower_id));stem=p['file_stem'];specs=component_specs(tower_id)
    references=p.pop('source_references')
    for reference in references:reference.setdefault('checked_on',CHECKED_ON)
    assumed = {
        'zh':'除明确引用的总高、展望台高度及晴空塔三角形基脚/315m圆形控制截面外，底座、杆件截面、平面尺度、展望台外壳、色带位置及几何插值均为原创示意假设。不是测绘、原建筑CAD、结构计算或施工图。',
        'ja':'明示した総高さ・展望施設高さ・スカイツリー三角形基部と315m円形制御断面以外の、基壇・部材断面・平面寸法・展望施設外形・塗装境界・補間形状は独自の概念仮定です。測量図、原設計CAD、構造計算書、施工図ではありません。',
        'en':'Except for explicitly cited total/deck heights and Skytree triangular-base/315m circular controls, bases, member sizes, plan dimensions, deck shells, paint boundaries and geometric interpolation are original schematic assumptions. Not a survey, original-design CAD, structural calculation or construction drawing.',
    }
    assumptions = [assumed, {
        'zh':'地面基准为Z=0；演示地台位于负标高，总高从地面而非地台底部量取。杆件以八边形棱柱表达，不代表原塔选材或截面。',
        'ja':'地盤基準はZ=0です。概念基壇は負の高さに置き、総高さは基壇下面ではなく地盤から測ります。八角柱の部材表現は原塔の材料・断面仕様ではありません。',
        'en':'Ground datum is Z=0. The schematic base is below ground; landmark height is measured from ground, not the slab underside. Octagonal member prisms do not specify original tower materials or sections.',
    }]
    if tower_id == 'tokyo-tower':
        references.extend([
            {'title':'IHI Infra-square・東京タワー施工近景と現場継手の記録',
             'url':'https://www.ihi.co.jp/iis/en/gallery/historical_structures/index.html',
             'checked_on':'2026-11-04',
             'reference_notes':'Contractor history and construction photograph support built-up plates and riveted field splices. Not a complete current member schedule.'},
            {'title':'Nature Architects・東京タワー組立材の現地観察と近景写真',
             'url':'https://nature-architects.com/blog/1817/',
             'checked_on':'2026-11-04',
             'reference_notes':'Engineer-authored first-hand observations and photographs show angle/channel/plate assemblies with rectangular and triangular open webs. Observations are not original fabrication drawings; hidden sections and dimensions are unverified.'},
        ])
        assumptions.append({
            'zh':'R11将模型GL80–120m主展望台下方的旧整面大X和密集横圈，改为与GL40–80m下段一致的四列交叉格网、横带及竖材。新分带80/93/106/120m、杆件和短接件为照片引导的演示假设，不是原设计的逐杆复原。保留R10整体主脚、拱架与真实开孔，保留上方轮廓、展望台、核心、楼梯和天线。既有节点局部形状不变，其相关构件引用映射到实际存在的连接件。以下R10及更早记录作为历史。',
            'ja':'R11はモデルGL80–120mの主展望施設下にある旧一面大形X・細かい水平環を、GL40–80m下段と同じ四列の交差格子・横帯・縦材へ置換します。80/93/106/120mの分帯、部材と短い接合材は写真に基づくモデル仮定で、原設計の全材配置の復元ではありません。R10の一体主脚・アーチと実開口、上部輪郭・展望施設・コア・階段・アンテナを保持します。既存接合部の局部形状は保ち、関連材の参照を実在する新接合材へ対応させます。以下のR10以前は履歴です。',
            'en':'R11 replaces the model GL80–120m full-face X and closely spaced horizontal rings beneath the Main Deck with the same four-column crossed grid, belts and verticals as the GL40–80m lower section. The 80/93/106/120m stations, members and short connectors are photo-guided demonstration assumptions, not a reconstructed original member schedule. R10 gross legs, arches and real openings, upper outline, decks, core, stairs and antenna are retained. Existing node geometry remains; related-member references map to actual new connectors. R10 and earlier descriptions below are historical.',
        })
        assumptions.append({
            'zh':'R10修正下部主材的建模层级：每根塔脚及每面拱架按整体组合材表达，取消四根各自带小格构的独立小梁。连续宽盖板与带真实开口的整体腹面形成同一构件，原四角轴仅保留为定位参考。沿用既有塔脚位置、拱口和上部外形控制；宽度、板厚、孔形、缀板与接头均为照片引导的演示假设。这种整体组合材不是一根热轧实心钢材，也未恢复实物隐蔽结构。下面R09及更早说明为历史。',
            'ja':'R10は下部主材のモデル階層を修正します。各主脚と各面のアーチを一体の組立材で表し、それぞれ小さな格構を持つ四本の独立梁を置換します。連続する広い添板と実開口を持つ腹面が同じ部材を構成し、旧四隅の軸は位置参照のみとして残します。主脚位置・アーチ開口・上部外形の制御を継承しますが、幅・板厚・孔形・綴り板・継手は写真に基づくモデル仮定です。単一の圧延実体鋼材や隠れた実物構造を復元したものではありません。以下のR09以前は履歴です。',
            'en':'R10 corrects the lower-member modelling hierarchy: each leg and face arch is represented as one built-up assembly, replacing four separate miniature lattice beams. Continuous broad cover plates and webs with real openings belong to the same member; the former four corner axes remain location references. Existing foot locations, arch opening and upper outline controls are retained. Widths, plate thicknesses, openings, battens and joints are photo-guided demonstration assumptions. One built-up assembly does not mean one solid rolled-steel section or a recovered hidden structure. R09 and earlier descriptions below are historical.',
        })
        assumptions.append({
            'zh':'R09将下部主材、拱弦及横斜杆的统一H/I或八角实心近似改为连续盖板、角形边缘和矩形缀板/三角缀条的透空组合材。开口是STEP和GLB共有的真实几何；接点处的短隔板维持既有连接。主脚轴线、拱洞、上部塔身、展望台、天线和R08附属构件保持。继承的外包尺寸以及板厚、分格、隔板、截面族分配均为照片参考假设，不能据此判定实物隐蔽构造或钢材规格。以下R08及更早说明为历史记录，不再表示现行下部构件均为H形或箱管。',
            'ja':'R09は下部主材・アーチ弦材・横斜材の一律なH/I形・八角実体の近似を、連続する添板、山形の縁材、矩形の綴り板または三角形のラチスを持つ組立材に変更します。開口はSTEPとGLBで共通の実形状で、接点の短い隔板は既存の取付部をつなぎます。主脚軸線・大きなアーチ開口・上部塔体・展望施設・アンテナ・R08付属材を保持します。継承した外包寸法、板厚・割付・隔板・断面族の割当ては写真を参考にした仮定です。隠れた面や実物の鋼材規格の復元ではありません。以下のR08以前の記録は履歴であり、現行下部材を一律にH形鋼や箱形鋼管とするものではありません。',
            'en':'R09 replaces uniform lower H/I-like and octagonal-solid approximations with built-up cover plates, angle-like edges and rectangular battened or triangular laced open webs. Voids are shared native STEP/GLB geometry; short fitted diaphragms retain existing attachment contacts. Leg axes, gross arch openings, upper shaft, decks, antenna and R08 fittings remain. Inherited envelopes, plate thicknesses, subdivisions, diaphragms and family assignments are photo-guided assumptions, not a surveyed hidden-section or steel-grade schedule. Earlier R08 and older descriptions below are historical, not current lower-member H/box-tube classifications.',
        })
        references.extend([
            {'title':'東京タワー公式・塔体上部写真',
             'url':'https://www.tokyotower.co.jp/plan/towerpedia/img/img_006.jpg',
             'checked_on':'2026-11-03',
             'reference_notes':'Photo-guided outboard arms, small service floors and circular covers. Photo date/current equipment inventory, heights, orientations and section dimensions are not verified.'},
            {'title':'IHI・東京タワー外観写真（TOKYO TOWER提供）',
             'url':'https://www.ihi.co.jp/technology/techinfo/contents_no/__icsFiles/afieldfile/2024/01/25/09.PNG',
             'checked_on':'2026-11-03',
             'reference_notes':'Visual primary/secondary member hierarchy only; no measured lower-leg or arch section schedule is provided.'},
        ])
        assumptions.append({
            'zh':'R08按参考照片减细下部主材及腹杆：主弦截面为R07的0.70，地面宽720→504mm、续接段525→367.5mm，拱架H形外观450×600→320×420mm。主脚轴线、拱顶及拱架轴间深度保持。两展望台之间增加111个独立外挑支架、保守床及圆形设备罩，42处主安装点随实际直线主弦定位。尺寸、方向和布置为照片拟合；照片年代和现用设备表未核定，不分配广播系统名称。下列R07条目保留作历史控制说明；现行断面以R08参数为准。',
            'ja':'R08は下部の主材・腹材を写真に合わせて細くし、主弦断面をR07の0.70（地上720→504mm、継続部525→367.5mm）、アーチH外観を450×600→320×420mmとします。主脚軸線・アーチ頂部・弦軸間隔は保持。両展望施設間に別名の外挑支架・保守床・円形機器カバー111個を追加し、42の主要取付点を実際の直線主弦へ配置します。寸法・方向・割付は写真近似で、写真年代と現用設備表は未確認。以下のR07記録は履歴で、現行断面はR08の値を参照します。',
            'en':'R08 reduces lower primary and secondary appearance sections: primary sizes are0.70 of R07 (ground720→504mm, continuation525→367.5mm); arch H appearance450×600→320×420mm. Leg axes, arch crown and chord-axis separation stay fixed.111 separately named outboard brackets, service floors and circular covers are added between the decks, with42 primary mounts following actual straight chords. Dimensions, directions and inventory are photo-guided fits; photo date and current equipment schedule are unverified. The R07 notes below describe retained history; R08 parameters govern current section sizes.',
        })
        assumptions.append({
            'zh':'R07将下部四面拱架分为立面内的上下弦杆、三角腹杆与前后连接。主腿组合柱由地面连续延伸至模型GL125m主展望台下，消除80m处的中断；80–125m的525mm主材宽度及组合柱1000→450mm半宽收分属于照片引导的假设，腹杆仍保持较细层次。H3的GL40m及80m塔脚轴距沿用公开控制；拱深、板件截面、节点和分格为拟合。FootTown的48×44m外形、五段立面层高、墙窗比例及屋顶附属体也不是实测平面。特别展望台下的模型GL130–223.55m塔身采用局部单调收分，端部半宽9900/3950mm及两端切线衔接既有轮廓，中间线形为照片拟合；原profile数组仅保留为参考控制。相关支承随实际主材移动，展望台外壳、核心、楼梯、天线及区间外形状保持。',
            'ja':'R07は下部四面のアーチを立面内の上下弦・三角腹材・前後連結として分けます。主脚の組柱を地上からモデルGL125mの主展望施設下まで連続させ、80mでの打切りを除きます。80–125mの主材幅525mmと組柱半幅1000→450mmの収束は写真近似で、腹材は細い階層を保ちます。H3のGL40mと塔脚軸間80mは公表制御を継承し、アーチ成・断面・接合・割付は近似です。FootTownの48×44m外形・五段の立面階高・壁窓比・屋上付属体も実測平面ではありません。特別展望施設下のモデルGL130–223.55mは局所的な単調収束形状とし、端部半幅9900/3950mmと接線を既存輪郭に接続します。中間輪郭は写真近似で、元profile配列は参照制御として保持します。支持材は実主材に追従し、展望施設外装・コア・階段・アンテナと区間外を保持します。',
            'en':'R07 separates the four lower arches into in-plane chords, triangular webs and front/back links. Primary leg cages continue from ground to the modelGL125m Main Deck, removing the80m cutoff. The80–125m525mm member width and1000-to-450mm cage half-width taper are photo-guided assumptions; braces remain finer. Published H3GL40m and80m foot-axis spacing remain controls; arch depth, plate sections, joints and subdivision are fitted. FootTown48x44m, five facade bands, wall/glazing proportions and rooftop housing are not surveyed plans. A local monotone convex taper removes the shoulder beneath the special deck from modelGL130 to223.55m, matching9900/3950mm endpoint half-widths and retained tangents. Intermediate widths are photo-guided fits; the original profile array remains reference controls. Actual connected supports follow the frame; deck shells, core, stairs, antenna and geometry outside this interval remain.',
        })
        assumptions[0] = {
            'zh':'总高333m、脚基准轴距80m及施工图H3/H11/H23/H27标高有公开依据。未标注的宽度、H中间分节、拱曲线及截面仍是图面解释和建模近似；双层GL125000是从GL120000加5m层距的解释。官方150m/250m案内值与几何GL解释分列；H11外壳对应与H23屋顶的解释均未实测核定；R06内部GL220550楼板为假设。不是测绘或原设计复原。',
            'ja':'全高333m・脚基準軸間80mと施工図H3/H11/H23/H27は公表値。無記入の幅・中間H節間・アーチ曲線・断面は図面解釈と近似です。GL125000はGL120000から5mの層間を解釈。公式案内150m/250mとモデルGLを分離し、床位置との対応もモデル上の解釈で、実測・原設計復元ではありません。',
            'en':'Published controls cover333m overall height,80m leg-axis spacing and construction H3/H11/H23/H27 GL. Unlabelled widths, belts, arch curve and sections remain interpreted approximations; GL125000 interprets a5m upper-floor interval aboveGL120000. Official150m/250m guidance values are separate from geometricGL. H23 is treated as a historical roof band; the R06 internalGL220550 floor is an appearance assumption, not a surveyed present-day finished-floor conversion.',
        }
        assumptions[1] = {
            'zh':'地面GL=0、屋面Z=18300；主展望层GL120000/125000、上部H23屋顶GL223550（假设内部楼板220550），官方150m/250m案内值另列。24梯跑600踢面为约600阶公开描述的示意布置，路径、踢面、260mm踏面和平台尺寸均非原建筑实测。R04按宽面组合柱形态表达H/I主材，细部截面未核实。',
            'ja':'地盤GL=0、屋上Z=18300、モデルの主展望外殻・仮定床GL120000/125000・H23屋根GL223550（内部床220550は仮定）。公式案内150m/250mは別記。24折返し・600段は公表の約600段をもとにした独自配置です。経路、蹴上げ、踏面260mm、踊場寸法、H/I組立主材・八角副材は実測仕様ではありません。',
            'en':'Ground GL=0, roof Z=18300; interpreted model shell/floor GL120000/125000 and H23 roofGL223550 (assumed inner floorGL220550) are separate from official150m/250m visitor names. The 24-flight/600-rise staircase is an original schematic arrangement informed by the published approximate 600 steps; route, rises, 260 mm treads and landings are not measured specifications. R04 uses graded built-up H/I appearance chords with unverified sections; braces retain octagonal prisms.',
        }
        assumptions.append({
            'zh':'R05主展望台两层外轮廓分别参考历史H11的27m方形、H12的28m方形；H13的29×24m历史平面独立记录（功能未核定），不作为当前外幕墙边界。R06将H23的13m圆形细分为48面，H23作为屋顶控制；上部H24环形平台、上下白色钢架和小型抛物面设备参照照片拟合。2019改修窄窗、浅色底缘与清扫轨道参照供应商实景；分格、倾角、板厚、现况对应及H23附近塔身轴线收分仍为近似。',
            'ja':'R05は歴史的なH11の27m角・H12の28m角を各階の外形参考とし、H13の29×24m歴史平面（用途未確認）は現在の外装境界に流用せず別記します。R06はH23の直径13m円を48面で近似し、H23を屋根制御とします。H24の環状保守床・上下の白い架構・小型反射鏡は写真近似です。2019年改修の細い窓枠・明色の下面・清掃軌道は製作者写真を参照し、割付・勾配・板厚・現況との対応・H23付近の塔体軸線はモデル仮定です。',
            'en':'R05 uses historical H11 27m-square and H12 28m-square controls for separate deck levels. The H13 29x24m historical plan (function unverified) is recorded independently, not used as the current facade boundary. R06 samples the H23 13m circle with48 facets and treats H23 as a roof control. Its separate H24 ring platform, white framing and small reflectors are photo-guided fits. Supplier photographs guide2019 narrow glazing frames, pale soffits and cleaning tracks; divisions, slopes, thicknesses, current-state mapping and nearby tower-axis taper remain approximations.',
        })
        assumptions.append({
            'zh':'R05补充H25-H27数字天线分组与SG内外两层格构。宫地No28记载ST更换为450mm BOX角柱；模型墙厚、设备尺寸、节距、SG杆径、连接及H27承接均为假设，不含临时吊运平台，也不进行制振或结构计算。',
            'ja':'R05はH25-H27のデジタルアンテナ群とSGの内外架構を追加します。STは宮地No28の更新記録に基づく450mm BOX角柱です。壁厚・機器寸法・節間・SG部材径・接合・H27取合いは仮定で、仮設荷揚げ足場や制振・構造解析は含みません。',
            'en':'R05 adds H25-H27 digital antenna banks and separate inner/outer SG frames. The ST is a450mm BOX post following the Miyaji No28 replacement record; its wall, equipment dimensions, bay pitch, SG sections, joints and H27 interface remain assumptions. Temporary hoisting stages, damping response and structural capacity are not modelled.',
        })
    if tower_id == 'tokyo-skytree':
        assumptions.append({
            'zh':'R05将普通外周水平材改为真实中空圆管，内侧环桁架及放射连接保留方管。三组各四柱鼎结构之间补齐三面展开的宽翼钢架，中央保留尖拱形通行开口；不增加环绕地面的连续立柱。翼的开口曲线、分支位置、管径、壁厚与相接点为参考施工方图示的拟合，未复原逐杆施工规格、焊接节点或地下基础。',
            'ja':'R05は一般の外周水平材を実際に中空の円管とし、内側リングトラス・放射連結の角管を保持します。三組各四柱の鼎の間に三面の広がる格構翼を補い、中央の尖頭アーチ状通行開口を残し、地上に連続する周囲柱は加えません。開口曲線・分岐・管径・板厚・接合点は施工者図示を参考にした近似で、全材施工仕様・溶接接合・地下基礎の復元ではありません。',
            'en':'R05 uses actual hollow circular ordinary exterior horizontals while retaining rectangular inner ring trusses and radial links. Broad lattice wings extend across all three faces between the three four-column kanae groups, preserving central pointed-arch passages without adding a continuous ring of ground columns. Opening curves, branches, tube sizes, walls and fitted contacts are approximated from builder diagrams, not recovered member schedules, welded-joint design or underground foundations.',
        })
        assumptions[0] = {
            'zh':'R05沿用R04公开控制值：634m总高、约68m地面正三角形、315m处约32m直径和495m处约18m直径。上段为直锥，下段分别拟合与其相切的角部反り及面中むくり圆弧；为满足这些圆整控制值，拟合半径并不等于发表的4520m/最大5950m。24点截面之间的引导线、局部截面及连接为外观近似，不是原设计坐标、测绘CAD或施工图。',
            'ja':'R05はR04の公表制御値：全高634m・地上の約68m正三角形・315mで約32m径・495mで約18m径を継承します。上部を直円錐、下部の反りとむくりをそれに接する別々の円弧で近似します。丸めた制御値を満たすため、近似半径は公表の4520m・最大5950mとは一致しません。24点断面間のガイド・部材断面・接合は外観近似で、原設計座標や測量CAD・施工図ではありません。',
            'en':'R05 retains R04 published rounded controls:634m height,68m ground triangle,32m diameter at315m and18m at495m. Separate principal sori/mukuri arcs are fitted tangent to the upper cone. Satisfying these rounded controls gives fitted radii different from the published4520m/maximum5950m. Intermediate24-point guides, local sections and joints remain appearance approximations, not recovered original coordinates, survey CAD or construction drawings.',
        }
        assumptions[1] = {
            'zh':'地面GL=0，演示地台位于负标高，总高由地面量取。保留真实中空圆管、方管和独立钢筋混凝土心柱；长主弦采用水平圆环站点放样，未复原原塔逐杆法向截面及相贯端切。不模拟心柱制振或结构承载。',
            'ja':'地盤GL=0、概念基壇は負の高さに置き、全高は地盤から測ります。実際に中空の円管・角管と独立したRC心柱を保持します。長い主弦は水平円環ロフト近似で、原塔の各部材の法線断面や相貫端切を復元せず、心柱制振や構造耐力も解析しません。',
            'en':'Ground GL=0; the schematic base is below ground. Actual hollow circular/rectangular tubes and the separate RC core are retained. Long chords use horizontal annular loft stations without recovering member-normal sections or saddle cuts. Core damping and structural capacity are not simulated.',
        }
        assumptions.append({
            'zh':'主台保留340/345/350m三个公共楼层，335m服务带不另算公共层。71度外倾幕墙及350m处约47m直径有设计者资料；375m屋顶有运营方公开依据。上口约58m等设备壳体截面为参考施工阶段约60m描述与实景的拟合。回廊445→450m、451.2m最高点有官方依据；设计者114m与制造商约110m/宽2.4m的记述分别保留。模型采用114m变径路径，方位、上部衔接、玻璃分片及设备冠部尺寸仍为近似。',
            'ja':'主展望施設は340/345/350mの公共3階を保ち、335mのサービス帯を公共階には数えません。71度の外傾ガラスと350mで約47m径は設計者資料、375m屋上は運営者資料に基づきます。約58m径の設備外殻等は工事段階の上端約60mという説明と写真に基づく近似。回廊445→450m・最高451.2mは公式値、設計者の114mと製作者の約110m・幅2.4mは別々に記録します。114mの変径経路を採用し、方位・上部接続・ガラス割付・設備冠部寸法はモデル仮定です。',
            'en':'The main deck retains three public floors340/345/350m; the335m service band is not another public floor. Designer sources give71-degree outward glazing and about47m diameter at350m; the operator gives a375m rooftop. Equipment-envelope stations such as58m upper diameter are photo-guided fits informed by a construction-stage approximately60m upper diameter. Operator gallery levels445/450/451.2m are retained. Designer114m and fabricator approximately110m/2.4m width are recorded separately. The model uses a114m variable-radius route; azimuth, upper connection, glazing divisions and equipment-crown sections remain approximations.',
        })
        assumptions.append({
            'zh':'三组各四柱鼎桁架在50m连接。公开水平杆节距12.5/10/7.5m及315m以上5m用于24轴外圈；150m/250m切换高度、内12边环和稀疏腹杆属建模假设，不能当作真实逐杆布置。497m起六柱增益塔保持约6m外径，补充分段天线、维护平台和外扩双层TMD机房，避雷杆达到634m；天线高度分段、机房尺寸、支座及灯位均参考实景拟合。',
            'ja':'三組各四柱の鼎トラスは50mで接合。公表の水平材ピッチ12.5/10/7.5m・315m以上5mを24軸外周に用います。150/250mの切替高さ、内側12角リングと省略腹材はモデル仮定で、実際の全材配置ではありません。497mからの六柱ゲイン塔は外径約6mを保ち、分節アンテナ・保守床・外側へ広がる二層TMD機械室・634mの避雷針を表現。アンテナ区間、機械室寸法、支持具、灯具位置は写真に基づく近似です。',
            'en':'Three four-column kanae groups join at50m. Published horizontal pitches12.5/10/7.5m and5m above315m inform the24-axis outer frame. The150/250m switches, inner12-sided rings and sparse webs are modelling assumptions, not an original member schedule. The six-column gain tower above497m keeps approximately6m external diameter, with separate antenna banks, maintenance decks, a wider two-storey TMD head and a lightning rod reaching634m. Antenna stations, head dimensions, supports and light positions are photo-guided approximations.',
        })
    if tower_id == 'tokyo-tower':
        assumptions.append({
            'zh':'R06按2012年天线供应商Fig5表达上下两组环形阵列：每组30片/行、5行，高5300mm，间隔500mm，外径上12876mm、下13400mm，内支撑圈11800mm。总300片取代四方板片。绝对GL240550起点、板厚、缝隙、支撑、下方两行短阵列与设备平台为图像拟合。旧频道标签不表示当前运营用途；2014后SG补强与BOX450 ST保留。',
            'ja':'R06は2012年の製作者Fig5に基づく上下二組の環状配列です。各組30枚/段・5段・高さ5300mm、間隔500mm、上径12876mm・下径13400mm、支持円11800mmの計300枚で四方の板列を置換。絶対GL240550、板厚・目地・支持材・下部二段短配列・保守床は画像近似です。旧チャンネル表記を現用用途とは扱わず、2014年後のSG補強とBOX450 STは保持します。',
            'en':'R06 follows the supplier2012 Fig5: two circular arrays, each30 panels per row and5 rows,5300mm high,500mm apart, upper diameter12876mm, lower13400mm and support circle11800mm,300 panels total. Absolute startingGL240550, shell thickness, seams, supports, lower short arrays and service platform are image fits. Historical channels do not identify current use; post2014 SG reinforcement and BOX450 ST remain.',
        })
    steel_nodes = []
    if tower_id == 'tokyo-tower':
        from .tokyo_tower_steel import node_catalog
        steel_nodes = node_catalog(TOWERS[tower_id], _tokyo_base_specs())
        from .tokyo_tower_integrated import remap_node_catalog
        steel_nodes = remap_node_catalog(steel_nodes,specs)
        from .tokyo_tower_grid import remap_node_catalog as remap_grid_nodes
        steel_nodes = remap_grid_nodes(steel_nodes,specs)
        assumptions.append({
            'zh':'R04的20个钢结构节点、H/I外观截面、板厚、加劲肋、铆钉头数量/尺寸/间距与布置均为演示假设。铆接特征参考历史资料，未复原原设计或历次加固节点，也未验算节点/锚固承载力。',
            'ja':'R04の20箇所の鋼接合部、H/I外観断面、板厚、補剛材、リベット頭の数・寸法・間隔・配置はモデル仮定です。歴史資料を参考にした外観表現であり、原設計・改修接合部の復元や接合・定着の耐力照査ではありません。',
            'en':'The twenty R04 steel nodes, H/I appearance sections, plate/stiffener thicknesses and rivet-head counts, sizes, pitch and placement are demonstration assumptions. Historical riveting character informs appearance; original/retrofit connections and connection/anchorage capacities have not been reconstructed or calculated.',
        })
    return {'schema_version':1,'id':tower_id,'revision':revision_for(tower_id),'units':'mm','names':p['names'],
            **({'steel_nodes':steel_nodes} if steel_nodes else {}),
            'status':'reference_concept_only',
            'height_mm':p['height_mm'],'parameters':p,
            'groups':[{'id':group,'node_name':group,'names':GROUP_NAMES[group],
                       'component_count':sum(s['group']==group for s in specs)} for group in GROUPS],
            'component_count':len(specs),'assumptions':assumptions, 'source_references':references,
            'coordinates':{'CAD':'millimetres; Z-up; ground datum Z=0',
                           'GLB':'metres; Y-up; (X,Z,-Y)/1000; identity grouping transforms'},
            'engineering':{'structural_capacity':None,'member_design':None,'foundation_design':None,
                           'earthquake_or_wind':None,'statutory_compliance':None},
            'files':{'step':f'STEP/{stem}.step','glb':f'GLB/{stem}.glb',
                     'plan_dxf':f'DXF/{stem}_plan.dxf','elevation_dxf':f'DXF/{stem}_elevation.dxf',
                     'plan_svg':f'output/svg/{stem}_plan.svg','elevation_svg':f'output/svg/{stem}_elevation.svg',
                     'pdf':f'output/pdf/{stem}_sheets.pdf',
                     **({'steel_nodes_dxf':f'DXF/{stem}_steel_nodes.dxf',
                         'steel_nodes_svg':f'output/svg/{stem}_steel_nodes.svg'} if tower_id == 'tokyo-tower' else
                        {'structure_zones_dxf':f'DXF/{stem}_structure_zones.dxf',
                         'structure_zones_svg':f'output/svg/{stem}_structure_zones.svg'})}}


def _cad_shape(spec, bd):
    if spec['kind']=='built_up':
        from .tokyo_tower_builtup import shape
        return shape(spec, bd)
    if spec['kind']=='box':
        x1,y1,z1,x2,y2,z2=spec['bounds']
        return bd.Box(x2-x1,y2-y1,z2-z1,align=(bd.Align.MIN,)*3).moved(bd.Location((x1,y1,z1)))
    if spec['kind']=='loft':
        wires=[bd.Wire.make_polygon([(x,y,section['z']) for x,y in section['points']],close=True)
               for section in spec['sections']]
        return bd.Solid.make_loft(wires,ruled=True)
    if spec['kind']=='loft3d':
        # Planar end sections permit genuinely sloping gallery floors/glass.
        # Every end wire is retained as explicit CAD-space XYZ coordinates.
        wires=[bd.Wire.make_polygon(section,close=True) for section in spec['sections']]
        return bd.Solid.make_loft(wires,ruled=True)
    if spec['kind']=='tube':
        # Analytic circular hollow steel, with a section normal to its axis.
        a,b=spec['start'],spec['end'];d=[b[i]-a[i] for i in range(3)]
        length=sqrt(sum(x*x for x in d));r=spec['radius'];wall=spec['wall_thickness_mm']
        if length<=0 or not 0<wall<r:raise ValueError('Invalid circular tube')
        plane=bd.Plane(origin=tuple(a),z_dir=tuple(d))
        outer=bd.Solid.make_cylinder(r,length,plane=plane)
        inner=bd.Solid.make_cylinder(r-wall,length,plane=plane)
        return outer.cut(inner)
    if spec['kind']=='tube_loft':
        # Circular annuli at the recorded Z stations, not octagonal solid bars.
        # The ruled envelope follows the original straight frame intervals.
        outer=[];inner=[]
        for section in spec['sections']:
            r=section['radius'];wall=section['wall_thickness_mm']
            if not 0<wall<r:raise ValueError('Invalid tubular loft wall')
            plane=bd.Plane(origin=(*section['center'],section['z']))
            outer.append(bd.Wire.make_circle(r,plane=plane))
            inner.append(bd.Wire.make_circle(r-wall,plane=plane))
        return bd.Solid.make_loft(outer,ruled=True).cut(bd.Solid.make_loft(inner,ruled=True))
    if spec['kind']=='rhs':
        a,b=spec['start'],spec['end'];d=[b[i]-a[i] for i in range(3)]
        length=sqrt(sum(x*x for x in d));w,h,t=spec['width_mm'],spec['depth_mm'],spec['wall_thickness_mm']
        if length<=0 or not 0<2*t<min(w,h):raise ValueError('Invalid rectangular hollow section')
        z=[v/length for v in d];ref=[0.,0.,1.] if abs(z[2])<.95 else [1.,0.,0.]
        cross=lambda u,v:[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        u=cross(z,ref);norm=sqrt(sum(v*v for v in u));u=[v/norm for v in u];v=cross(z,u)
        def shell(width,height):
            rings=[]
            for c in (a,b):
                points=[[c[k]+u[k]*x+v[k]*y for k in range(3)] for x,y in
                        [(-width/2,-height/2),(width/2,-height/2),(width/2,height/2),(-width/2,height/2)]]
                rings.append(bd.Wire.make_polygon(points,close=True))
            return bd.Solid.make_loft(rings,ruled=True)
        return shell(w,h).cut(shell(w-2*t,h-2*t))
    if spec['kind']=='beam':
        # A genuine octagonal prism: explicit faceting controls draw cost and
        # avoids claiming that the assumed member profile is a selected tube.
        a,b=spec['start'],spec['end'];d=[b[i]-a[i] for i in range(3)]
        length=sqrt(sum(v*v for v in d));direction=[v/length for v in d]
        reference=[0.,0.,1.] if abs(direction[2])<.95 else [1.,0.,0.]
        cross=lambda u,v:[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        u=cross(direction,reference);norm=sqrt(sum(v*v for v in u));u=[v/norm for v in u]
        v=cross(direction,u);r=spec['radius'];rings=[]
        for centre in (a,b):
            points=[[centre[k]+r*(u[k]*cos(2*pi*i/8)+v[k]*sin(2*pi*i/8)) for k in range(3)] for i in range(8)]
            rings.append(bd.Wire.make_polygon(points,close=True))
        return bd.Solid.make_loft(rings,ruled=True)
    raise ValueError(f"Unknown primitive: {spec['kind']}")


def tower_assembly(tower_id):
    from cadgen import build123d as bd,srgb
    specs=component_specs(tower_id);groups=[]
    for group in GROUPS:
        children=[]
        for spec in specs:
            if spec['group']!=group:continue
            shape=_cad_shape(spec,bd);shape.label=spec['name'];shape.color=srgb(spec['color'])
            children.append(shape)
        groups.append(bd.Compound(children=children,label=group))
    return bd.Compound(children=groups,label='TokyoTower' if tower_id=='tokyo-tower' else 'TokyoSkytree')
