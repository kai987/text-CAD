"""Parametric landmark appearance models, millimetres and Z-up.

Only the cited landmark/deck heights and cited Skytree control section are
reference facts. Member sizes, interpolation, glazing, foundations and all
other unreferenced dimensions are illustrative design assumptions. This is
original concept geometry, not surveyed or original architectural CAD.

The parameter and component-specification API is dependency-free. build123d
is imported only when ``tower_assembly`` actually creates CAD solids; drawings
and tests can read exactly the same specification without a CAD environment.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from math import cos, sin, pi, sqrt

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
    'tokyo-tower': {
        'file_stem': 'tokyo_tower',
        'revision': 'LANDMARK-R04',
        'names': {'zh': '东京塔', 'ja': '東京タワー', 'en': 'Tokyo Tower'},
        'height_mm': 333000,
        'deck_levels_mm': [125000, 223550],
        'nominal_deck_levels_mm': [150000, 250000],
        'geometry_datum': 'Construction-GL-informed appearance model; official published deck guidance values are recorded separately. Floor identifications are interpreted, not surveyed.',
        'base_width_mm': 80000,
        'detail': {
            'leg_stations_mm': [0, 9000, 18000, 28000, 40000, 52000, 65000, 80000],
            'foot_town_roof_mm': 18300,
            'arch_crown_mm': 40000,
            'lower_belt_levels_mm': [40000, 53000, 66000, 80000],
            'main_floor_levels_mm': [120000, 125000],
            'steel_main_support_z_mm': 115000,
            'external_stair_risers': 600, 'external_stair_flights': 24,
            'external_stair_tread_mm': 260,
            'external_stair_bounds_mm': [4700, -8000, 18300, 9300, 1500, 125000],
            'main_deck_stair_opening_mm': [4700, -8000, 9300, 1800],
            'glazing_thickness_mm': 90,
            'member_profiles': 'graded built-up H/I appearance chords; four schematic connection families at twenty selected nodes',
            'steel_node_count': 20,
            'steel_profile_families': {
                "lower": {
                    "type": "H",
                    "width_factor": 1.0,
                    "depth_factor": 0.85,
                    "web_thickness_mm": 24.0,
                    "flange_thickness_mm": 30.0
                },
                "middle": {
                    "type": "H",
                    "width_factor": 0.9,
                    "depth_factor": 0.8,
                    "web_thickness_mm": 18.0,
                    "flange_thickness_mm": 24.0
                },
                "upper": {
                    "type": "I",
                    "width_factor": 0.62,
                    "depth_factor": 1.0,
                    "web_thickness_mm": 14.0,
                    "flange_thickness_mm": 18.0
                }
            },
            'steel_node_families': {
                "base": {
                    "width_mm": 1200.0,
                    "height_mm": 1000.0,
                    "plate_thickness_mm": 30.0,
                    "stiffener_thickness_mm": 16.0,
                    "stiffener_depth_mm": 160.0,
                    "rivet_radius_mm": 18.0,
                    "rivet_projection_mm": 12.0
                },
                "lower_truss": {
                    "width_mm": 1100.0,
                    "height_mm": 1200.0,
                    "plate_thickness_mm": 20.0,
                    "stiffener_thickness_mm": 16.0,
                    "stiffener_depth_mm": 140.0,
                    "rivet_radius_mm": 18.0,
                    "rivet_projection_mm": 12.0
                },
                "splice": {
                    "width_mm": 620.0,
                    "height_mm": 1050.0,
                    "plate_thickness_mm": 16.0,
                    "stiffener_thickness_mm": 14.0,
                    "stiffener_depth_mm": 100.0,
                    "rivet_radius_mm": 18.0,
                    "rivet_projection_mm": 12.0
                },
                "deck_support": {
                    "width_mm": 1100.0,
                    "height_mm": 1000.0,
                    "plate_thickness_mm": 24.0,
                    "stiffener_thickness_mm": 16.0,
                    "stiffener_depth_mm": 180.0,
                    "rivet_radius_mm": 18.0,
                    "rivet_projection_mm": 12.0
                }
            },
            'scope': 'Original appearance detail; route, risers, sections, connections, glass and light positions are schematic assumptions.',
        },
        # Square axis half-widths: traced broad proportions, unlabelled
        # radii remain approximations, not measured dimensions.
        'profile': [[0, 40000], [25000, 30500], [40000, 25000], [53000, 21000],
                    [66000, 18000], [80000, 15500], [100000, 13000],
                    [120000, 10800], [130000, 9900], [150000, 8800],
                    [170000, 7900], [190000, 7000], [210000, 6000],
                    [223550, 5300], [238000, 4200], [252650, 3100]],
        'profile_kind': 'square_half_width',
        'deck_specs': [
            {'id': 'main', 'level_mm': 125000, 'bottom_mm': 119500,
             'glass_bottom_mm': 121000, 'top_mm': 130000, 'half_width_mm': 17000, 'support_mm': 115000},
            {'id': 'top', 'level_mm': 223550, 'bottom_mm': 219050,
             'glass_bottom_mm': 220550, 'top_mm': 227550, 'half_width_mm': 6500, 'support_mm': 216550},
        ],
        'antenna_start_mm': 252650,
        'antenna_lattice_top_mm': 312600,
        'base_slab_thickness_mm': 2000,
        'source_references': [
            {'title': '宮地技報 No18 東京タワー塔体補強報告 p86 図1',
             'url': 'https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf',
             'confirmed_values_mm': {'leg_axis_spacing':80000,'H3_GL':40000,'H11_GL':120000,'H23_GL':223550,'H27_GL':252650,'tip_GL':333000},
             'reference_notes': 'The model interprets observation-shell positions from H11/H23 structural bands at GL120000/223550, with an assumed 5000mm main-floor interval. These are not independently verified visitor finished-floor levels; unlabelled H belts, widths and arch curvature are traced approximations. Historical retrofit figure, not a current surveyed as-built model.'},
            {'title': '宮地技報 No28 東京タワー耐震改修報告 p65 図1',
             'url': 'https://www.miyaji-eng.co.jp/technology/newsletter/media/28/no28-p064-070.pdf',
             'confirmed_values_mm': {'support_tower_top_GL':312600},
             'reference_notes': 'Later retrofit drawing confirms H27 GL252650 and upper SG/ST zones. Its H23 label reads223500, versus223550 in No18; this model consistently uses the earlier223550 control, not both.'},
            {'title': 'IHI 東京タワー施工写真',
             'url': 'https://www.ihi.co.jp/technology/techinfo/contents_no/1200541_13491.html',
             'reference_notes': 'Tokyo Tower construction photograph shows built-up wide plate chords, lacing and a hierarchy of bracing. Nearby angle-steel prose refers to Tsutenkaku, not a section schedule for Tokyo Tower. Exact H/I member sections below remain appearance assumptions.'},
            {'title': '東京タワー 施設案内', 'url': 'https://www.tokyotower.co.jp/guidance/',
             'confirmed_nominal_values_mm': {'height': 333000, 'main_deck': 150000, 'top_deck': 250000}},
            {'title': '東京タワー タワペディア', 'url': 'https://www.tokyotower.co.jp/plan/towerpedia/',
             'reference_notes': 'Official 270m painting limit excludes the top antenna; this is not the construction H27 support-tower start. International Orange and white, with seven schematic bands above the main deck.'},
            {'title': '東京タワー メインデッキ', 'url': 'https://www.tokyotower.co.jp/maindeck/',
             'reference_notes': 'Main Deck has 1F and 2F; the model intermediate floor and all plan dimensions are schematic.'},
            {'title': '東京タワー オープンエア外階段ウォーク', 'url': 'https://www.tokyotower.co.jp/plan/open_air_stair/',
             'reference_notes': 'Outdoor stairs connect Foot Town roof to the Main Deck (official published guidance150m) with approximately 600 steps. The model route and flight configuration are original assumptions.'},
            {'title': '東京タワー フットタウン', 'url': 'https://www.tokyotower.co.jp/foottown/',
             'reference_notes': 'Public entrance and rooftop outdoor-stair access inform the schematic base building; no original floor plan is reproduced.'},
            {'title': '日本溶接協会 東京スカイツリー製作現場見学雑感（東京タワーとの比較）',
             'url': 'https://www-it.jwes.or.jp/we-com/bn/vol_1/sec_2/2-1.pdf',
             'reference_notes': 'Page2 describes the original Tokyo Tower as rivet-assembled SS41 steelwork. This establishes historical connection character only; model section sizes, twenty selected nodes, rivet counts, pitch, plate/stiffener sizes and local coordinates are assumptions, not original drawings or retrofit design.'},
            {'title': '竹中工務店 東京タワー改修',
             'url': 'https://www.takenaka.co.jp/solution/asset/project/07/',
             'reference_notes': 'The tower has undergone maintenance and strengthening. This appearance study does not reconstruct every original or later connection or certify present-day structural capacity.'},
        ],
    },
    'tokyo-skytree': {
        'file_stem': 'tokyo_skytree',
        'revision': 'LANDMARK-R02',
        'names': {'zh': '东京晴空塔', 'ja': '東京スカイツリー', 'en': 'Tokyo Skytree'},
        'height_mm': 634000,
        'deck_levels_mm': [350000, 450000],
        'base_width_mm': 68000,
        'base_triangle_side_mm': 68000,
        'transition_height_mm': 315000,
        'transition_diameter_mm': 32000,
        'ring_divisions': 24,
        'detail': {
            'tembo_floors_mm': [340000, 345000, 350000],
            'galleria_start_mm': 445000, 'galleria_end_mm': 450000,
            'galleria_segments': 32, 'galleria_centre_radius_mm': 12850,
            'galleria_width_mm': 1800, 'galleria_side_height_mm': 2200,
            'galleria_floor_thickness_mm': 250, 'galleria_glass_thickness_mm': 80,
            'galleria_arch_rise_mm': 900, 'galleria_arch_panels': 4,
            'sorakara_level_mm': 451200,
            'shinbashira_height_mm': 375000, 'shinbashira_diameter_mm': 8000,
            'shinbashira_wall_lower_mm': 400, 'shinbashira_wall_upper_mm': 600,
            'scope': 'Original appearance study; interpolated frame, gallery route/turns/radii, panels, connections, footings and fixture layout are modelling assumptions, not surveyed construction geometry.',
        },
        # Triangle circumradius at ground; circular radius from z=315m.
        'profile': [[0, 68000 / sqrt(3)], [45000, 35000], [90000, 30500],
                    [135000, 26400], [180000, 22900], [225000, 19900],
                    [270000, 17600], [315000, 16000], [350000, 13900],
                    [390000, 11700], [430000, 10100], [460000, 8800],
                    [495000, 6100]],
        'profile_kind': 'triangle_to_circle_radius',
        'deck_specs': [
            {'id': 'tembo_deck', 'level_mm': 350000, 'bottom_mm': 333000,
             'glass_bottom_mm': 340000, 'top_mm': 357000, 'radius_mm': 23000},
            {'id': 'tembo_galleria', 'level_mm': 450000, 'bottom_mm': 443000,
             'glass_bottom_mm': 445000, 'top_mm': 455000, 'radius_mm': 14500},
        ],
        'antenna_start_mm': 495000,
        'base_slab_thickness_mm': 2500,
        'source_references': [
            {'title': '東京スカイツリー アウトライン', 'url': 'https://www.tokyo-skytree.jp/about/outline/',
             'confirmed_values_mm': {'height': 634000, 'tembo_deck': 350000, 'tembo_galleria': 450000}},
            {'title': '東京スカイツリー フロアガイド', 'url': 'https://www.tokyo-skytree.jp/floor/',
             'confirmed_values_mm': {'galleria_start': 445000, 'galleria_end': 450000}},
            {'title': '日建設計 NIKKEN JOURNAL 2012 Autumn',
             'url': 'https://www.nikken.co.jp/ja/about/p4iusj0000001hyd-att/Journal-2012_Autumn.pdf',
             'confirmed_values_mm': {'approximate_base_triangle_side': 68000,
                                     'circular_transition_height': 315000,
                                     'approximate_transition_diameter': 32000},
             'reference_notes': 'Archived designer publication, independently visible in the search index; legacy PDF URL can return 404. The approximately 32m transition control is retained from this publication; shape interpolation and members are schematic.'},
            {'title': '東京都 地域資源 東京スカイツリー',
             'url': 'https://www.chiikishigen.metro.tokyo.lg.jp/introduction/details/introduction_26.html',
             'confirmed_values_mm': {'approximate_base_triangle_side':68000,'circular_transition_height':315000}},
            {'title': '東京スカイツリー 天望デッキ / 天望回廊',
             'url': 'https://www.tokyo-skytree.jp/floor/',
             'confirmed_values_mm': {'tembo_floor_340':340000,'tembo_floor_345':345000,'tembo_floor_350':350000},
             'reference_notes': 'Floor levels are public references; model radii, glazing divisions, floor/roof thickness and roof heights are assumptions.'},
            {'title': '東京スカイツリー 天望回廊',
             'url': 'https://www.tokyo-skytree.jp/floor/tembogalleria/',
             'confirmed_values_mm': {'galleria_start':445000,'galleria_end':450000,'sorakara_point':451200},
             'reference_notes': 'The glass tube gallery slopes upward from Floor445 to Floor450. Model radius, turns, ramp width and entrance/exit positions are original assumptions.'},
            {'title': '東京スカイツリー 塔体のしくみ',
             'url': 'https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/body.php',
             'confirmed_values_mm': {'shinbashira_height':375000,'shinbashira_diameter':8000,'lower_wall_thickness':400,'upper_wall_thickness':600},
             'reference_notes': 'Published concrete cylinder dimensions inform the visible core. Model joints, guide frames and spatial representation are schematic; no damping behaviour or structural capacity is simulated.'},
        ],
    },
}


def _tower(tower_id):
    try:
        return TOWERS[tower_id]
    except KeyError as error:
        raise ValueError(f'Unknown landmark: {tower_id!r}') from error


def geometry_source_paths(tower_id):
    """Explicit per-model source dependency list for reproducible export binding."""
    _tower(tower_id)
    return ['src/lib/tower_geometry.py', *(['src/lib/tokyo_tower_detail.py', 'src/lib/tokyo_tower_steel.py'] if tower_id == 'tokyo-tower' else ['src/lib/skytree_detail.py'])]


def revision_for(tower_id):
    return _tower(tower_id).get('revision', REVISION)


def profile_radius(tower_id, z):
    """Interpolate the recorded control radius/half-width at height z (mm)."""
    profile = _tower(tower_id)['profile']
    if tower_id == 'tokyo-tower':
        from .tokyo_tower_detail import profile_radius as detailed_radius
        return detailed_radius(profile, z)
    from .skytree_detail import profile_radius as detailed_radius
    return detailed_radius(profile, z)


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
    fraction = max(0., min(1., z / p['transition_height_mm']))
    amount = fraction*fraction*(3 - 2*fraction)
    # Uniform perimeter samples of the equilateral base are paired with a
    # circle. This interpolation is intentionally explicit and schematic.
    vertices = circle_points(radius, 3, pi / 2)
    count = p['ring_divisions']
    result = []
    for index in range(count):
        side = index * 3 // count
        t = (index % (count // 3)) / (count // 3)
        a, b = vertices[side], vertices[(side + 1) % 3]
        theta = pi / 2 + 2 * pi * index / count
        triangle = [(1 - t) * a[k] + t * b[k] for k in range(2)]
        circular = [radius * cos(theta), radius * sin(theta)]
        result.append([(1 - amount) * triangle[k] + amount * circular[k] for k in range(2)])
    return result


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
    return refine_steel(TOWERS['tokyo-tower'], _tokyo_base_specs())


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
    for reference in references:reference['checked_on']=CHECKED_ON
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
        assumptions[0] = {
            'zh':'总高333m、脚基准轴距80m及施工图H3/H11/H23/H27标高有公开依据。未标注的宽度、H中间分节、拱曲线及截面仍是图面解释和建模近似；双层GL125000是从GL120000加5m层距的解释。官方150m/250m案内值与几何GL解释分列；H11/H23对应外壳位置的解释及楼板识别均未完成实测核定。不是测绘或原设计复原。',
            'ja':'全高333m・脚基準軸間80mと施工図H3/H11/H23/H27は公表値。無記入の幅・中間H節間・アーチ曲線・断面は図面解釈と近似です。GL125000はGL120000から5mの層間を解釈。公式案内150m/250mとモデルGLを分離し、床位置との対応もモデル上の解釈で、実測・原設計復元ではありません。',
            'en':'Published controls cover333m overall height,80m leg-axis spacing and construction H3/H11/H23/H27 GL. Unlabelled widths, belts, arch curve and sections remain interpreted approximations; GL125000 interprets a5m upper-floor interval aboveGL120000. Official150m/250m guidance values are separate from geometricGL. Floor identification is a modelling assumption, not a survey or original-design reconstruction.',
        }
        assumptions[1] = {
            'zh':'地面GL=0、屋面Z=18300；主展望层GL120000/125000、上部GL223550，官方150m/250m案内值另列。24梯跑600踢面为约600阶公开描述的示意布置，路径、踢面、260mm踏面和平台尺寸均非原建筑实测。R04按宽面组合柱形态表达H/I主材，细部截面未核实。',
            'ja':'地盤GL=0、屋上Z=18300、モデルの主展望外殻・仮定床GL120000/125000・上部GL223550。公式案内150m/250mは別記。24折返し・600段は公表の約600段をもとにした独自配置です。経路、蹴上げ、踏面260mm、踊場寸法、H/I組立主材・八角副材は実測仕様ではありません。',
            'en':'Ground GL=0, roof Z=18300; interpreted model shell/floor GL120000/125000 and GL223550 are separate from official150m/250m visitor names. The 24-flight/600-rise staircase is an original schematic arrangement informed by the published approximate 600 steps; route, rises, 260 mm treads and landings are not measured specifications. R04 uses graded built-up H/I appearance chords with unverified sections; braces retain octagonal prisms.',
        }
    if tower_id == 'tokyo-skytree':
        assumptions[0] = {
            'zh':'明确列在来源记录中的总高、楼层、三角/圆形控制截面及心柱尺寸来自公开资料；其他平面尺度、插值、回廊路线、圈数、截面、外壳、连接与灯位均为原创建模假设，不是测绘、原建筑CAD或施工图。',
            'ja':'出典記録に明記した総高・階高さ・三角/円形の制御断面・心柱寸法は公表資料に基づきます。それ以外の平面寸法・補間・回廊経路・周回数・断面・外殻・接合・灯具位置は独自のモデル仮定で、測量図・原設計CAD・施工図ではありません。',
            'en':'The explicitly cited total/floor heights, triangular/circular controls and core-cylinder dimensions follow public references. Other plan sizes, interpolation, gallery route/turns, sections, shells, connections and fixture positions are original modelling assumptions, not survey, original CAD or construction drawings.',
        }
        assumptions.append({
            'zh':'340/345/350m楼层、445→450m坡道玻璃回廊和451.2m最高点参考官方说明。回廊半径、圈数、路线、宽度、屋面高度与玻璃分片均为假设；心柱公开尺寸用于外观表达，不模拟制振性能。',
            'ja':'340/345/350mの階、445→450mのガラス張りスロープ回廊、451.2mの最高点は公式資料に基づきます。回廊の半径・周回数・経路・幅・屋根高さ・ガラス分割は仮定です。心柱の公表寸法は外観表現に用い、制振性能は解析しません。',
            'en':'The 340/345/350m floors, 445-to-450m sloping glass gallery and 451.2m highest point follow operator references. Gallery radius, turns, route, width, roof heights and glazing divisions are assumptions. Published core-cylinder dimensions inform appearance only; damping performance is not simulated.',
        })
    steel_nodes = []
    if tower_id == 'tokyo-tower':
        from .tokyo_tower_steel import node_catalog
        steel_nodes = node_catalog(TOWERS[tower_id], _tokyo_base_specs())
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
                         'steel_nodes_svg':f'output/svg/{stem}_steel_nodes.svg'} if tower_id == 'tokyo-tower' else {})}}


def _cad_shape(spec, bd):
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
