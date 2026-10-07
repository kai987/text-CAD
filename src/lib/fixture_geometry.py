"""Original parametric residential fixtures, in millimetres.

The five fixture types reuse the approved plan footprints exactly. Each named
leaf is a closed solid; cavities are real subtractive CAD geometry, not dark
painted rectangles. Fronts face south (-Y), matching the current north-wall
fixture arrangements. No product meshes or manufacturer CAD are included.
"""
from __future__ import annotations

from math import sqrt
from cadgen import build123d as bd, srgb

FIXTURE_KINDS = {'浴槽': 'bath', '洗面': 'vanity', 'WC': 'toilet',
                 '洗濯': 'washer', '洗濯機': 'washer', 'キッチン': 'kitchen',
                 '対面キッチン': 'kitchen', '冷蔵庫': 'fridge', 'カップボード': 'cupboard'}
COLORS = {'ceramic': '#F6F3EA', 'chrome': '#ADB7BD', 'wood': '#B69876',
          'counter': '#E4E0D7', 'dark': '#333D43', 'rubber': '#313A40',
          'glass': '#9DBAC7', 'mirror': '#BCD2D8', 'steel': '#929DA2',
          'white': '#E8EBE8', 'screen': '#172E38'}


def _named(shape, label, material, opacity=1):
    shape.label = label
    shape.color = srgb(COLORS[material], opacity)
    return shape


def _round(width, depth, height, radius, x=0, y=0, z=0):
    """A vertical rounded rectangular prism, centred in XY, bottom at Z."""
    profile = bd.RectangleRounded(width, depth, min(radius, width/2-1, depth/2-1))
    return bd.extrude(profile, amount=height).moved(bd.Location((x, y, z)))


def _ellipse(width, depth, height, x=0, y=0, z=0):
    return bd.extrude(bd.Ellipse(width/2, depth/2), amount=height).moved(bd.Location((x, y, z)))


def _box(x1, y1, z1, x2, y2, z2):
    return bd.Box(x2-x1, y2-y1, z2-z1,
                  align=(bd.Align.MIN, bd.Align.MIN, bd.Align.MIN)).moved(bd.Location((x1, y1, z1)))


def _round_sections(sections, x, y):
    return bd.loft([bd.RectangleRounded(w, d, min(r, w/2-1, d/2-1)).moved(bd.Location((x, y, z)))
                    for w, d, r, z in sections], ruled=True)


def _ellipse_sections(sections, x, y):
    return bd.loft([bd.Ellipse(w/2, d/2).moved(bd.Location((x, y, z)))
                    for w, d, z in sections], ruled=True)


def _cylinder(radius, height, x, y, z):
    return bd.Solid.make_cylinder(radius, height, bd.Plane(origin=(x, y, z)))


def _cylinder_y(radius, depth, x, y, z):
    return bd.Solid.make_cylinder(radius, depth,
                                 bd.Plane(origin=(x, y-depth/2, z), z_dir=(0, 1, 0)))


def _pipe(points, radius):
    """Closed, fused chrome tube with round elbows and capped ends."""
    parts = []
    for a, b in zip(points, points[1:]):
        delta = tuple(b[i]-a[i] for i in range(3))
        length = sqrt(sum(d*d for d in delta))
        parts.append(bd.Solid.make_cylinder(radius, length, bd.Plane(origin=a, z_dir=delta)))
    parts.extend(bd.Sphere(radius).moved(bd.Location(point)) for point in points[1:-1])
    return parts[0].fuse(*parts[1:])


def _panel(width, height, depth, x, y_back, z_bottom, radius=8):
    # Rounded XZ panel; thickness projects toward the front (-Y).
    return _round(width, height, depth, radius).rotate(bd.Axis.X, 90).moved(
        bd.Location((x, y_back, z_bottom+height/2)))


def _faucet(parts, prefix, x, y, z, reach=110, rise=190):
    parts.append(_named(_cylinder(25, 12, x, y, z), prefix+':faucet_base_chrome', 'chrome'))
    pipe = _pipe([(x, y, z+12), (x, y, z+rise),
                  (x, y-reach, z+rise), (x, y-reach, z+rise-35)], 13)
    parts.append(_named(pipe, prefix+':faucet_chrome', 'chrome'))
    parts.append(_named(_pipe([(x+38, y, z+8), (x+38, y, z+60),
                               (x+70, y, z+75)], 8), prefix+':mixer_lever_chrome', 'chrome'))


def _bath(w, d, prefix, model_id):
    parts = []
    cx, cy = w/2, d/2
    # A deep soaking tub with tapered inner walls and a generous rounded rim.
    outer = _round_sections([(w-44, d-38, 70, 12), (w-12, d-12, 100, 515)], cx, cy)
    # A rounded cavity prism avoids a STEP round-trip tolerance defect in
    # the long tapered inner loft at R09's new bath dimensions.
    cavity = _round(w-130,d-135,450,100,cx,cy,130)
    parts.append(_named(outer.cut(cavity), prefix+':tub_shell_ceramic', 'ceramic'))
    rim = _round(w-8, d-8, 32, 102, cx, cy, 518).cut(cavity)
    parts.append(_named(rim, prefix+':tub_rim_ceramic', 'ceramic'))
    parts.append(_named(_cylinder(26, 4, cx-w*.26, cy, 131), prefix+':drain_chrome', 'chrome'))
    # Put the standing shower rail near the end, clear of the house bath high window.
    sx, sy = w*.88, d-34
    _faucet(parts, prefix, sx-60, sy, 552, reach=85, rise=140)
    rail = _pipe([(sx, sy, 555), (sx, sy, 1780), (sx, sy-100, 1780)], 11)
    parts.append(_named(rail, prefix+':shower_rail_chrome', 'chrome'))
    parts.append(_named(_cylinder(47, 13, sx, sy-100, 1767), prefix+':shower_head_chrome', 'chrome'))
    parts.append(_named(_cylinder(39, 3, sx, sy-100, 1763), prefix+':shower_face_dark', 'dark'))
    return parts


def _vanity(w, d, prefix, model_id):
    parts = []
    cabinet = _round(w-12, d-38, 705, 10, w/2, d/2+13, 80)
    cabinet = cabinet.cut(_box(28, 31, 105, w-28, d-24, 792))
    parts.append(_named(cabinet, prefix+':cabinet_wood', 'wood'))
    parts.append(_named(_box(50, 70, 12, w-50, d-35, 76), prefix+':toe_plinth_dark', 'dark'))
    for i in range(2):
        pw = (w-24)/2
        x = 10+pw*(i+.5)+i*4
        parts.append(_named(_panel(pw-4, 686, 16, x, 31, 90), f'{prefix}:door_{i+1}_wood', 'wood'))
        parts.append(_named(_pipe([(x-40, 29, 701), (x-40, 12, 701),
                                   (x+40, 12, 701), (x+40, 29, 701)], 5), f'{prefix}:handle_{i+1}_chrome', 'chrome'))
    basin_w, basin_d = min(w-70, 670), d-85
    cx, cy = w/2, d*.46
    countertop = _round(w, d, 30, 14, w/2, d/2, 790)
    outer_cut = _round(basin_w+4, basin_d+4, 220, 65, cx, cy, 610)
    parts.append(_named(countertop.cut(outer_cut), prefix+':counter_ceramic', 'ceramic'))
    bowl = _round_sections([(basin_w-110, basin_d-100, 50, 650), (basin_w, basin_d, 68, 820)], cx, cy)
    hollow = _round_sections([(basin_w-153, basin_d-143, 40, 667), (basin_w-48, basin_d-48, 60, 829)], cx, cy)
    parts.append(_named(bowl.cut(hollow), prefix+':basin_ceramic', 'ceramic'))
    parts.append(_named(_cylinder(21, 4, cx, cy, 668), prefix+':drain_chrome', 'chrome'))
    _faucet(parts, prefix, cx, d-40, 821, reach=95, rise=165)
    # A low mirror also avoids the existing north-facing high window in the house.
    mw, mh = min(w-60, 800), 440
    mirror = _panel(mw, mh, 14, w/2, d-7, 1000, 20)
    inset = _panel(mw-18, mh-18, 2, w/2, d-23, 1009, 16)
    parts.append(_named(mirror, prefix+':mirror_frame_chrome', 'chrome'))
    parts.append(_named(inset, prefix+':mirror', 'mirror'))
    return parts


def _toilet(w, d, prefix, model_id):
    parts = []
    cx, cy = w/2, d*.405
    shell = _ellipse_sections([(w*.46, d*.52, 8), (w*.55, d*.59, 175),
                                (w*.88, d*.77, 386)], cx, cy)
    hollow = _ellipse_sections([(w*.25, d*.27, 245), (w*.64, d*.56, 410)], cx, cy)
    parts.append(_named(shell.cut(hollow), prefix+':bowl_ceramic', 'ceramic'))
    seat = _ellipse(w*.91, d*.79, 26, cx, cy, 391).cut(_ellipse(w*.65, d*.57, 30, cx, cy, 389))
    parts.append(_named(seat, prefix+':seat_ceramic', 'ceramic'))
    parts.append(_named(_ellipse(w*.21, d*.23, 3, cx, cy, 246), prefix+':bowl_trap_dark', 'dark'))
    tank = _round(w*.77, d*.21, 440, 28, cx, d*.864, 383)
    parts.append(_named(tank, prefix+':cistern_ceramic', 'ceramic'))
    parts.append(_named(_round(w*.79, d*.23, 25, 28, cx, d*.864, 827), prefix+':cistern_lid_ceramic', 'ceramic'))
    parts.append(_named(_cylinder(20, 5, cx+w*.22, d*.864, 853), prefix+':flush_chrome', 'chrome'))
    # Upright lid keeps the sculpted bowl and actual seat aperture visible.
    lid = _ellipse(w*.86, 382, 22).rotate(bd.Axis.X, 90).moved(bd.Location((cx, d*.747, 622)))
    parts.append(_named(lid, prefix+':open_lid_ceramic', 'ceramic'))
    return parts


def _washer(w, d, prefix, model_id):
    parts = []
    cx, cz = w/2, 438
    radius = min(w*.31, 190)
    body = _round(w-20, d-60, 855, 21, cx, d/2+20, 15)
    opening = _cylinder_y(radius-10, 145, cx, 94, cz)
    parts.append(_named(body.cut(opening), prefix+':body_white', 'white'))
    door = _cylinder_y(radius+16, 25, cx, 23, cz).cut(_cylinder_y(radius-15, 30, cx, 23, cz))
    parts.append(_named(door, prefix+':porthole_chrome', 'chrome'))
    seal = _cylinder_y(radius-16, 8, cx, 46, cz).cut(_cylinder_y(radius-28, 12, cx, 46, cz))
    parts.append(_named(seal, prefix+':porthole_seal_rubber', 'rubber'))
    parts.append(_named(_cylinder_y(radius-29, 5, cx, 59, cz), prefix+':washer_glass', 'glass', .52))
    drum = _cylinder_y(radius-29, 12, cx, 140, cz).cut(_cylinder_y(radius-47, 10, cx, 131, cz))
    parts.append(_named(drum, prefix+':drum_steel', 'steel'))
    parts.append(_named(_cylinder_y(22, 10, w*.24, 29, 764), prefix+':dial_chrome', 'chrome'))
    parts.append(_named(_panel(w*.28, 57, 5, w*.68, 34, 736, 7), prefix+':control_screen', 'screen'))
    parts.append(_named(_panel(w*.26, 76, 9, w*.24, 38, 655, 5), prefix+':detergent_drawer_white', 'white'))
    parts.append(_named(_panel(w-60, 39, 7, cx, 38, 42, 6), prefix+':lower_service_panel_white', 'white'))
    return parts


def _kitchen(w, d, prefix, model_id):
    parts = []
    body = _box(7, 35, 90, w-7, d-8, 809).cut(_box(30, 60, 116, w-30, d-32, 813))
    parts.append(_named(body, prefix+':cabinet_wood', 'wood'))
    parts.append(_named(_box(45, 75, 12, w-45, d-35, 85), prefix+':toe_plinth_dark', 'dark'))
    count = max(3, round(w/500))
    for i in range(count):
        panel_w = (w-20)/count
        cx = 10+panel_w*(i+.5)
        parts.append(_named(_panel(panel_w-5, 710, 17, cx, 31, 92, 5), f'{prefix}:front_{i+1}_wood', 'wood'))
        parts.append(_named(_pipe([(cx-55, 29, 750), (cx-55, 12, 750),
                                   (cx+55, 12, 750), (cx+55, 29, 750)], 5), f'{prefix}:handle_{i+1}_chrome', 'chrome'))
    sx, sy = w*.285, d*.465
    sw, sd = min(650, w*.34), d*.70
    top = _round(w, d, 40, 12, w/2, d/2, 814)
    top = top.cut(_round(sw+6, sd+6, 45, 55, sx, sy, 812))
    parts.append(_named(top, prefix+':counter_stone', 'counter'))
    basin = _round_sections([(sw-80, sd-70, 40, 639), (sw, sd, 52, 856)], sx, sy)
    cavity = _round_sections([(sw-105, sd-95, 34, 656), (sw-32, sd-32, 44, 863)], sx, sy)
    parts.append(_named(basin.cut(cavity), prefix+':sink_steel', 'steel'))
    rim = _round(sw+3, sd+3, 8, 54, sx, sy, 856).cut(_round(sw-32, sd-32, 12, 44, sx, sy, 854))
    parts.append(_named(rim, prefix+':sink_rim_steel', 'steel'))
    parts.append(_named(_cylinder(26, 5, sx, sy, 657), prefix+':drain_chrome', 'chrome'))
    _faucet(parts, prefix, sx, d-35, 855, reach=145, rise=225)
    hx, hy = w*.79, d*.5
    hw, hd = min(595, w*.29), d*.77
    parts.append(_named(_round(hw, hd, 9, 14, hx, hy, 857), prefix+':hob_dark', 'dark'))
    for i, (dx, dy, rad) in enumerate([(-hw*.23, -hd*.16, 69), (hw*.23, -hd*.16, 69), (0, hd*.24, 52)], 1):
        ring = _cylinder(rad, 2, hx+dx, hy+dy, 868).cut(_cylinder(rad-3, 4, hx+dx, hy+dy, 867))
        parts.append(_named(ring, f'{prefix}:hob_ring_{i}_steel', 'steel'))
    return parts


def _fridge(w, d, prefix, model_id):
    parts=[_named(_round(w-20,d-30,1790,18,w/2,d/2+10,10),prefix+':body_white','white')]
    for i,cx in enumerate((w/4,3*w/4),1):
        parts.append(_named(_panel(w/2-22,1750,20,cx,25,25,10),f'{prefix}:door_{i}_white','white'))
        hx=w/2-35 if i==1 else w/2+35
        parts.append(_named(_panel(14,460,18,hx,18,1050,4),f'{prefix}:handle_{i}_chrome','chrome'))
    parts.append(_named(_panel(110,55,4,w*.72,4,1530,4),prefix+':control_screen','screen'))
    return parts


def _cupboard(w, d, prefix, model_id):
    parts=[_named(_box(8,25,80,w-8,d-8,850),prefix+':cabinet_wood','wood'),
           _named(_round(w,d,30,8,w/2,d/2,850),prefix+':counter_stone','counter')]
    for i in range(3):
        cx=w*(i+.5)/3
        parts.append(_named(_panel(w/3-12,735,16,cx,25,100,5),f'{prefix}:front_{i+1}_wood','wood'))
        parts.append(_named(_panel(100,12,8,cx,10,780,3),f'{prefix}:handle_{i+1}_chrome','chrome'))
    mw,md,mh=500,350,350;mx=w/2;my=d/2
    body=_round(mw,md,mh,10,mx,my,900).cut(_box(mx-210,my-md/2-1,940,mx+150,my+80,1210))
    parts.append(_named(body,prefix+':microwave_body_steel','steel'))
    parts.append(_named(_panel(360,255,7,mx-28,my-md/2-2,937,7),prefix+':microwave_glass','glass',.55))
    parts.append(_named(_panel(42,100,5,mx+210,my-md/2-3,1030,4),prefix+':microwave_screen','screen'))
    return parts


def _facing_kitchen(w,d,prefix,model_id):
    parts=_kitchen(w,d,prefix,model_id)
    hx,hy=w*.79,d*.5
    hood_w,hood_d=850,600
    canopy=_box(hx-hood_w/2,hy-hood_d/2,1850,hx+hood_w/2,hy+hood_d/2,2000)
    cavity=_box(hx-hood_w/2+25,hy-hood_d/2+25,1849,hx+hood_w/2-25,hy+hood_d/2-25,1975)
    parts.append(_named(canopy.cut(cavity),prefix+':range_hood_steel','steel'))
    parts.append(_named(_box(hx-360,hy-230,1870,hx+360,hy+230,1878),prefix+':hood_filter_dark','dark'))
    parts.append(_named(_box(hx-170,hy-120,2000,hx+170,hy+120,2550),prefix+':hood_duct_cover_steel','steel'))
    parts.append(_named(_box(hx-250,hy-270,1878,hx+250,hy-255,1890),prefix+':hood_light_white','white'))
    axis=bd.Axis((w/2,d/2,0),(0,0,1))
    rotated=[]
    for leaf in parts:
        result=leaf.rotate(axis,180);result.label=leaf.label;result.color=leaf.color;rotated.append(result)
    return rotated


_BUILDERS = {'bath': _bath, 'vanity': _vanity, 'toilet': _toilet,
             'washer': _washer, 'kitchen': _kitchen, 'fridge':_fridge,'cupboard':_cupboard}


def fixture_group(floor, p, model_id='house'):
    if model_id=='house' and getattr(p,'mirror_layout',False):
        from .orientation import canonical, shape
        from .house_redesign_plan import floor_plan
        q=canonical(p)
        return shape(fixture_group(floor_plan(floor.number,q),q,'house'),p.width)
    """Return F#:fixtures with exact approved footprint bounds and floor datum.

    Storage and loose furniture are intentionally excluded. A type's base shape
    is built at local Z=0, then all leaves move together to the plan fixture and
    the finished-floor elevation. Children retain their descriptive CAD names.
    """
    children = []
    z = (floor.number-1)*p.storey_height
    for index, (name, bounds) in enumerate(floor.fixtures, 1):
        kind = FIXTURE_KINDS.get(name)
        if kind is None:
            continue
        x1, y1, x2, y2 = bounds
        prefix = f'F{floor.number}:fixture_{index:02d}_{kind}'
        builder=_facing_kitchen if name=='対面キッチン' else _BUILDERS[kind]
        leaves = builder(x2-x1, y2-y1, prefix, model_id)
        for leaf in leaves:
            leaf.move(bd.Location((x1, y1, z)))
        children.append(bd.Compound(children=leaves, label=prefix))
    return bd.Compound(children=children, label=f'F{floor.number}:fixtures')
