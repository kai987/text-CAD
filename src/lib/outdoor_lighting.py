"""Original, parameterized demonstration exterior luminaires.

All CAD coordinates and sizes are millimetres, Z-up. These seven warm-white
fixtures are a visualization proposal; no illuminance, wiring, waterproofing
rating, product selection or electrical design is implied.
"""
from __future__ import annotations

from .orientation import orient_shape, orient_record

from copy import deepcopy
from dataclasses import asdict, dataclass
from math import sqrt

from cadgen import build123d as bd, srgb

from .site_geometry import S, fence_layout, site_dimensions


@dataclass(frozen=True)
class OutdoorLightingParameters:
    color_temperature_K: int = 3000
    body_color: str = "#252B30"
    diffuser_color: str = "#FFE7C6"
    light_color: str = "#FFDDB2"
    wall_width: float = 120
    wall_height: float = 320
    wall_projection: float = 84
    bollard_height: float = 800
    bollard_width: float = 100
    bollard_cap_width: float = 120
    bollard_base_width: float = 160
    bollard_diffuser_height: float = 100
    spotlight_radius: float = 50
    spotlight_length: float = 105
    spotlight_wall: float = 5
    gate_width: float = 45
    gate_height: float = 100
    gate_projection: float = 55


L = OutdoorLightingParameters()


def _named(shape, label, diffuser=False, l=L):
    shape.label = label
    shape.color = srgb(l.diffuser_color if diffuser else l.body_color)
    return shape


def _box(bounds, label, diffuser=False, l=L):
    from .house_geometry import cuboid
    return _named(cuboid(bounds), label, diffuser, l)


def _unit(vector):
    length = sqrt(sum(v*v for v in vector))
    return [v/length for v in vector]


def _glb_point(point):
    return [point[0]/1000, point[2]/1000, -point[1]/1000]


def _glb_direction(direction):
    return [direction[0], direction[2], -direction[1]]


@orient_record
def fixture_layout(p, g, s=S, l=L):
    """Named fixture locations derived from the unchanged entrance/site layout."""
    from .house_plan import floor_plan
    door = next(d for d in floor_plan(1, p).doors if d.a == "outside")
    site = site_dimensions(p, g, s)
    path = site["path"]
    fixtures = [
        {"category": "wall", "id": "entrance_01", "mount_center_mm": [door.start+door.width+210, 0, 1520],
         "light_position_mm": [door.start+door.width+210, -l.wall_projection-4, 1500],
         "target_mm": [door.start+door.width/2, -1000, -25], "beam_angle_degrees": 72,
         "visual_intensity": 3.0, "visual_range_m": 5.0,
         "mount_to": "F1:exterior:cladding:south"},
    ]
    for i, y in enumerate((-4050, -2550), 1):
        x = path[0]-280
        fixtures.append({"category": "path", "id": f"path_{i:02d}",
            "mount_center_mm": [x, y, s.ground_z],
            "light_position_mm": [x+56, y, s.ground_z+l.bollard_height-70],
            "target_mm": [(path[0]+path[2])/2, y, s.ground_z], "beam_angle_degrees": 95,
            "visual_intensity": 1.5, "visual_range_m": 3.2,
            "mount_to": "yard:ground_surfaces:gravel"})
    for i, (origin, target) in enumerate([
        ([s.parking_east+550, -4450, s.ground_z+160], [3450, -3800, s.ground_z]),
        ([s.parking_east+550, -2450, s.ground_z+160], [650, -2250, s.ground_z]),
    ], 1):
        direction = _unit([target[a]-origin[a] for a in range(3)])
        light = [origin[a]+direction[a]*(l.spotlight_length+4) for a in range(3)]
        fixtures.append({"category": "garden", "id": f"garden_{i:02d}",
            "mount_center_mm": [origin[0], origin[1], s.ground_z], "head_origin_mm": origin,
            "light_position_mm": light, "target_mm": target, "beam_angle_degrees": 48,
            "visual_intensity": 2.2, "visual_range_m": 3.4,
            "mount_to": "yard:ground_surfaces:gravel"})
    posts = fence_layout(s,p)["posts"]
    for i, desired_x in enumerate((s.pedestrian_opening_west-s.fence_post_width/2,
                                    s.pedestrian_opening_east+s.fence_post_width/2), 1):
        post = next(q for q in posts if q["x"] == desired_x and q["y"] == s.fence_south)
        front_y = post["y"]-s.fence_post_width/2
        fixtures.append({"category": "gate", "id": f"gate_{i:02d}",
            "mount_center_mm": [post["x"], front_y, s.ground_z+1050],
            "light_position_mm": [post["x"], front_y-l.gate_projection-4, s.ground_z+1050],
            "target_mm": [post["x"], s.lot_south, s.ground_z], "beam_angle_degrees": 80,
            "visual_intensity": 0.8, "visual_range_m": 2.5,
            "mount_to": f"fence:posts:{post['id']}"})
    for fixture in fixtures:
        fixture["group"] = f"lighting:{fixture['category']}:{fixture['id']}"
        fixture["diffuser_label"] = fixture["group"]+":diffuser"
        fixture["direction_cad"] = _unit([fixture["target_mm"][a]-fixture["light_position_mm"][a] for a in range(3)])
        fixture["light_position_glb_m"] = _glb_point(fixture["light_position_mm"])
        fixture["target_glb_m"] = _glb_point(fixture["target_mm"])
        fixture["direction_glb"] = _glb_direction(fixture["direction_cad"])
        fixture["color_temperature_K"] = l.color_temperature_K
        fixture["color_hex"] = l.light_color
    return fixtures


def _wall_parts(fixture, l=L):
    label = fixture["group"]
    x, _, z = fixture["mount_center_mm"]
    w, h, d = l.wall_width, l.wall_height, l.wall_projection
    a, b = z-h/2, z+h/2
    return [
        _box((x-w/2, -16, a, x+w/2, 0, b), label+":mount", l=l),
        _box((x-w/2, -d, a, x+w/2, -16, a+16), label+":lower_cap", l=l),
        _box((x-w/2, -d, b-16, x+w/2, -16, b), label+":upper_cap", l=l),
        _box((x-w/2, -d, a+16, x-w/2+8, -16, b-16), label+":left_trim", l=l),
        _box((x+w/2-8, -d, a+16, x+w/2, -16, b-16), label+":right_trim", l=l),
        _box((x-w/2+8, -d, a+16, x+w/2-8, -16, b-16), label+":diffuser", True, l),
    ]


def _bollard_parts(fixture, s=S, l=L):
    label = fixture["group"]
    x, y, z = fixture["mount_center_mm"]
    b, cap, w = l.bollard_base_width/2, l.bollard_cap_width/2, l.bollard_width/2
    top = z+l.bollard_height
    diffuser_top, diffuser_bottom = top-20, top-20-l.bollard_diffuser_height
    stem_w = l.bollard_width*.8/2
    stem = _box((x-stem_w, y-stem_w, z+16, x+stem_w, y+stem_w, diffuser_bottom), label+":body", l=l)
    from .house_geometry import cuboid
    stem = _named(stem.cut(cuboid((x-stem_w+3, y-stem_w+3, z+16,
                                  x+stem_w-3, y+stem_w-3, diffuser_bottom))), label+":body", l=l)
    return [
        _box((x-b, y-b, z, x+b, y+b, z+16), label+":base", l=l), stem,
        _box((x-w, y-w, diffuser_bottom, x+w, y+w, diffuser_top), label+":diffuser", True, l),
        _box((x-cap, y-cap, diffuser_top, x+cap, y+cap, top), label+":cap", l=l),
    ]


def _garden_parts(fixture, s=S, l=L):
    label = fixture["group"]
    x, y, z = fixture["mount_center_mm"]
    origin = fixture["head_origin_mm"]
    direction = _unit([fixture["target_mm"][a]-origin[a] for a in range(3)])
    plane = bd.Plane(origin=origin, z_dir=direction)
    shell = bd.Solid.make_cylinder(l.spotlight_radius, l.spotlight_length, plane)
    inside_origin = [origin[a]+direction[a]*8 for a in range(3)]
    bore = bd.Solid.make_cylinder(l.spotlight_radius-l.spotlight_wall, l.spotlight_length,
                                  bd.Plane(origin=inside_origin, z_dir=direction))
    shell = shell.cut(bore)
    stem = bd.Solid.make_cylinder(12, origin[2]-(z+12), bd.Plane(origin=(x, y, z+12)))
    pivot = bd.Sphere(20).moved(bd.Location(origin))
    body = _named(shell.fuse(pivot, stem), label+":body", l=l)
    lens_origin = [origin[a]+direction[a]*(l.spotlight_length-6) for a in range(3)]
    lens = bd.Solid.make_cylinder(l.spotlight_radius-l.spotlight_wall, 6,
                                  bd.Plane(origin=lens_origin, z_dir=direction))
    return [_box((x-45, y-45, z, x+45, y+45, z+12), label+":base", l=l),
            body, _named(lens, label+":diffuser", True, l)]


def _gate_parts(fixture, l=L):
    label = fixture["group"]
    x, y, z = fixture["mount_center_mm"]
    w, h, d = l.gate_width, l.gate_height, l.gate_projection
    a, b = z-h/2, z+h/2
    return [
        _box((x-w/2, y-10, a, x+w/2, y, b), label+":mount", l=l),
        _box((x-w/2, y-d, a, x+w/2, y-10, a+8), label+":lower_cap", l=l),
        _box((x-w/2, y-d, b-8, x+w/2, y-10, b), label+":upper_cap", l=l),
        _box((x-w/2, y-d, a+8, x-w/2+4, y-10, b-8), label+":left_trim", l=l),
        _box((x+w/2-4, y-d, a+8, x+w/2, y-10, b-8), label+":right_trim", l=l),
        _box((x-w/2+4, y-d, a+8, x+w/2-4, y-10, b-8), label+":diffuser", True, l),
    ]


@orient_shape
def outdoor_lighting_group(p, g, s=S, l=L):
    builders = {"wall": _wall_parts, "path": _bollard_parts, "garden": _garden_parts, "gate": _gate_parts}
    categories = {}
    for fixture in fixture_layout(p, g, s, l):
        builder = builders[fixture["category"]]
        parts = builder(fixture, l=l) if fixture["category"] in ("wall", "gate") else builder(fixture, s=s, l=l)
        categories.setdefault(fixture["category"], []).append(bd.Compound(children=parts, label=fixture["group"]))
    return bd.Compound(children=[bd.Compound(children=groups, label=f"lighting:{category}")
                                  for category, groups in categories.items()], label="lighting")


@orient_record
def outdoor_lighting_manifest(p, g, s=S, l=L):
    fixtures = fixture_layout(p, g, s, l)
    return {
        "revision": "R08", "units": "mm", "parameters": asdict(l), "fixture_count": len(fixtures),
        "fixture_group": "lighting", "fixtures": fixtures,
        "geometry_source": "src/lib/outdoor_lighting.py",
        "glb_axis_transform": "[X_mm, Y_mm, Z_mm] -> [X_mm/1000, Z_mm/1000, -Y_mm/1000]",
        "rendering_only": {"visual_intensity": "relative renderer value; no photometric/lumen/lux specification",
                           "visual_range_m": "visual attenuation range, not a verified lighting coverage radius",
                           "switching": "Day/night scene lighting; independent of page colour theme"},
        "engineering_results": {"illuminance_lux": None, "glare": None, "electrical_circuit": None,
                                "weatherproof_product_rating": None, "construction_installation": None},
        "assumptions": [
            "R08新增7盏原创室外灯具：1盏玄关壁灯、2盏步道灯、2盏庭院射灯及2盏门柱灯；位置、安装高度、外壳尺寸和3000K暖白色均为演示假设。",
            "玄关壁灯背板接触南侧外墙，门柱灯背板接触现有围栏柱；地面灯底座接触院子完成面Z=-500 mm，不改动原土层或基础。",
            "两盏步道灯位于1500 mm入口通道西侧；门柱灯宽45 mm，小于50 mm柱宽，保留1800 mm行人开口与5675 mm车辆开口。",
            "昼夜光照和发光扩散罩仅供模型查看；未完成照度、眩光、邻地溢光、灯具防水等级、电路、接地或施工安装设计。",
        ],
    }


def apply_outdoor_lighting_materials(document, p, g, s=S, l=L):
    """Clone only new-fixture materials; retained house materials stay exact."""
    material_variants = {}
    fixtures = {fixture["diffuser_label"]: fixture for fixture in fixture_layout(p, g, s, l)}
    for node in document["nodes"]:
        if not node.get("name", "").startswith("lighting:") or "mesh" not in node:
            continue
        diffuser = node["name"].endswith(":diffuser")
        if diffuser:
            node.setdefault("extras", {})["outdoorLight"] = fixtures[node["name"]]
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            original = primitive.get("material")
            if original is None:
                continue
            key = (original, diffuser)
            if key not in material_variants:
                material = deepcopy(document["materials"][original])
                material["name"] = "R08 frosted warm-white diffuser" if diffuser else "R08 coated charcoal luminaire"
                material.setdefault("pbrMetallicRoughness", {}).update(
                    roughnessFactor=.42 if diffuser else .38, metallicFactor=0 if diffuser else .42)
                material["emissiveFactor"] = [0, 0, 0]
                material_variants[key] = len(document["materials"])
                document["materials"].append(material)
            primitive["material"] = material_variants[key]
    document["asset"].setdefault("extras", {})["outdoorLighting"] = outdoor_lighting_manifest(p, g, s, l)
