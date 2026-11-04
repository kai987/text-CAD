"""Photo-guided outboard fittings below Tokyo Tower's Top Deck, in mm.

The operator's Towerpedia photographs show projecting brackets, small platforms
and circular antenna covers between the two decks. They do not publish a dated
equipment inventory, orientations, member sizes or installation elevations.
All controls here are appearance fits in this model's existing GL datum. No
broadcaster/channel, present operating function or surveyed dimensions are
inferred. The separately modelled above-Top-Deck antenna is not changed.
"""
from __future__ import annotations

from copy import deepcopy
from math import cos, isfinite, pi, sin, sqrt


SOURCE_REFERENCE = 'https://www.tokyotower.co.jp/plan/towerpedia/'
SOURCE_PHOTO = 'https://www.tokyotower.co.jp/plan/towerpedia/img/img_006.jpg'
WHITE = '#F4F0E7'
SCOPE = ('Photo-guided outboard appearance from the operator photograph. Heights, '
         'projections, directions, bracket sections, service floors and circular '
         'covers are model fits, not measured installation coordinates or an '
         'original equipment schedule. Current inventory and photo date are '
         'unverified; no broadcaster or radio-system assignment is asserted.')

UPPER_EQUIPMENT_DEFAULTS = {
    'enabled': True,
    'tiers_mm': [158000., 166000., 174000., 182000.],
    'projections_mm': [2600., 3000., 3200., 2800.],
    'projection_definition': 'Additional X and Y half-width at corner tips, not a surveyed radial projection.',
    'arm_radius_mm': 110., 'stay_radius_mm': 80.,
    'stay_drop_mm': 1800., 'mount_overlap_mm': 180.,
    'platform_width_mm': 1200., 'platform_length_mm': 1000.,
    'platform_thickness_mm': 120., 'tip_mast_height_mm': 1100.,
    'crossbar_half_width_mm': 650.,
    'gallery_height_mm': 182000., 'gallery_projection_mm': 650.,
    'gallery_guard_height_mm': 1000., 'gallery_slab_thickness_mm': 120.,
    'radome_facets': 16, 'radome_depth_mm': 450.,
    'radomes': [
        {'height_mm': 146000., 'face': 0, 'corner': -1, 'diameter_mm': 1600., 'projection_mm': 1500.},
        {'height_mm': 200000., 'face': 1, 'corner': 1, 'diameter_mm': 1700., 'projection_mm': 1700.},
        {'height_mm': 209000., 'face': 3, 'corner': 1, 'diameter_mm': 1400., 'projection_mm': 1600.},
    ],
    'dimensions_status': 'photo_guided_appearance_assumption',
    'equipment_inventory_status': 'operator_photo_reference_date_and_current_inventory_unverified',
    'source_reference': SOURCE_REFERENCE, 'source_photo': SOURCE_PHOTO,
    'scope': SCOPE,
}


def _config(p):
    supplied = p.get('detail', {}).get('upper_equipment')
    if supplied is None:
        return None
    if not isinstance(supplied, dict):
        raise ValueError('Upper equipment must use an explicit configuration object.')
    result = {**deepcopy(UPPER_EQUIPMENT_DEFAULTS), **supplied}
    if not isinstance(result['enabled'], bool):
        raise ValueError('Upper equipment enabled must be a boolean.')
    return result


def _point(r, corner, z):
    sx, sy = ((-1, -1), (1, -1), (1, 1), (-1, 1))[corner]
    return [sx * r, sy * r, z]


def _beam(name, start, end, radius, role, **metadata):
    return {'group': 'structure', 'name': f'structure:upper_equipment_{name}',
            'kind': 'beam', 'start': list(start), 'end': list(end),
            'radius': radius, 'color': WHITE, 'role': role, **metadata}


def _box(name, bounds, role, **metadata):
    return {'group': 'structure', 'name': f'structure:upper_equipment_{name}',
            'kind': 'box', 'bounds': list(bounds), 'color': WHITE,
            'role': role, **metadata}


def _slab(name, centre, normal, tangent, radial_half, tangent_half, thickness, **metadata):
    points = [[centre[k] + normal[k] * a + tangent[k] * b for k in range(2)]
              for a, b in [(-radial_half, -tangent_half), (radial_half, -tangent_half),
                           (radial_half, tangent_half), (-radial_half, tangent_half)]]
    return {'group': 'structure', 'name': f'structure:upper_equipment_{name}',
            'kind': 'loft', 'color': WHITE, 'role': 'upper_equipment_service_floor',
            'sections': [{'z': z, 'points': deepcopy(points)}
                         for z in (centre[2] - thickness, centre[2])], **metadata}


def upper_equipment_specs(p, radius_fn, *, frame_levels=None):
    """Return separate fittings; ``radius_fn`` follows actual straight chords.

    The configuration is opt-in so archived R07 parameter records stay exact.
    Pass ``frame_levels=_upper_frame_levels()`` from the detailed frame module
    for explicit host names. Every primary mount records its actual chord axis
    and extends inward beyond that point to make positive native contact.
    """
    cfg = _config(p)
    if cfg is None or not cfg['enabled']:
        return []
    if frame_levels is None:
        # Lazy only: this module has no import-time dependency on the generator.
        from .tokyo_tower_detail import _upper_frame_levels
        frame_levels = _upper_frame_levels()
    levels = list(frame_levels)
    if len(levels) < 2 or not all(isfinite(v) for v in levels) or any(b <= a for a, b in zip(levels, levels[1:])):
        raise ValueError('Equipment hosts require finite increasing frame stations.')
    decks = {deck['id']: deck for deck in p['deck_specs']}
    lower, upper = decks['main']['top_mm'], decks['top']['bottom_mm']
    positive = ('arm_radius_mm', 'stay_radius_mm', 'stay_drop_mm', 'mount_overlap_mm',
                'platform_width_mm', 'platform_length_mm', 'platform_thickness_mm',
                'tip_mast_height_mm', 'crossbar_half_width_mm', 'gallery_projection_mm',
                'gallery_guard_height_mm', 'gallery_slab_thickness_mm', 'radome_depth_mm')
    if any(not isfinite(cfg[key]) or cfg[key] <= 0 for key in positive):
        raise ValueError('Equipment dimensions must be finite positive model controls.')
    if cfg['mount_overlap_mm'] > cfg['stay_drop_mm']:
        raise ValueError('Fitted mount lap must be shorter than the bracket drop.')
    tiers, projections = cfg['tiers_mm'], cfg['projections_mm']
    if not isinstance(tiers, list) or not 1 <= len(tiers) <= 6 or len(projections) != len(tiers):
        raise ValueError('Equipment tiers and projections must have the same bounded count.')
    if any(not isfinite(z) or not lower + cfg['stay_drop_mm'] < z < upper - cfg['tip_mast_height_mm']
           for z in tiers) or any(b <= a for a, b in zip(tiers, tiers[1:])):
        raise ValueError('Equipment tiers must rise strictly between the retained decks.')
    if any(not isfinite(v) or not 0 < v <= 5000 for v in projections):
        raise ValueError('Equipment projection must be a finite restrained fit.')
    gallery_z = cfg['gallery_height_mm']
    if not isfinite(gallery_z) or not lower + cfg['stay_drop_mm'] < gallery_z < upper - cfg['gallery_guard_height_mm']:
        raise ValueError('Equipment gallery must stay between the retained decks.')
    radomes = cfg['radomes']
    facets = cfg['radome_facets']
    if not isinstance(radomes, list) or len(radomes) > 6 or not isinstance(facets, int) or not 12 <= facets <= 32:
        raise ValueError('Circular equipment covers require bounded counts and facets.')
    for dish in radomes:
        if not isinstance(dish, dict) or dish.get('face') not in range(4) or dish.get('corner') not in (-1, 1):
            raise ValueError('A circular cover requires a declared face and corner.')
        z, diameter, projection = dish.get('height_mm'), dish.get('diameter_mm'), dish.get('projection_mm')
        if not all(isinstance(v, (int, float)) and isfinite(v) for v in (z, diameter, projection)):
            raise ValueError('Circular cover dimensions must be finite.')
        if not 0 < diameter <= 3000 or not 0 < projection <= 4000 or not lower + diameter < z < upper - diameter:
            raise ValueError('Circular cover must remain a small fitting between the decks.')

    common = {key: cfg[key] for key in ('dimensions_status', 'equipment_inventory_status',
                                       'source_reference', 'source_photo', 'scope')}
    parts = []
    lap = cfg['mount_overlap_mm']

    def radius(z):
        value = radius_fn(z)
        if not isfinite(value) or value <= 0:
            raise ValueError('Equipment host radius must follow a finite positive chord.')
        return value

    def attachment(corner, z):
        index = next((i + 1 for i, (a, b) in enumerate(zip(levels, levels[1:])) if a <= z <= b), None)
        if index is None:
            raise ValueError('Equipment attachment is outside the retained upper chord intervals.')
        point = _point(radius(z), corner, z)
        return point, {'host_members': [f'structure:upper_chord_{corner}_{index}'],
                       'attachment_points': [point], 'mount_overlap_mm': lap}

    def inward(point, direction):
        return [point[k] - direction[k] * lap for k in range(3)]

    for tier, (z, projection) in enumerate(zip(tiers, projections)):
        for corner, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            normal = [sx / sqrt(2), sy / sqrt(2), 0.]
            tangent = [-normal[1], normal[0], 0.]
            root, mount = attachment(corner, z)
            tip = [root[0] + sx * projection, root[1] + sy * projection, z]
            equipment = f'outrigger_{tier:02d}_{corner}'
            parts.append(_beam(equipment, inward(root, normal), tip, cfg['arm_radius_mm'],
                               'upper_equipment_outrigger', equipment_id=equipment, **mount))
            low, stay_mount = attachment(corner, z - cfg['stay_drop_mm'])
            parts.append(_beam(f'stay_{tier:02d}_{corner}', inward(low, normal), tip,
                               cfg['stay_radius_mm'], 'upper_equipment_stay',
                               equipment_id=equipment, **stay_mount))
            parts.append(_slab(f'platform_{tier:02d}_{corner}', tip, normal, tangent,
                               cfg['platform_length_mm'] / 2, cfg['platform_width_mm'] / 2,
                               cfg['platform_thickness_mm'], equipment_id=equipment,
                               support_members=[parts[-2]['name'], parts[-1]['name']]))
            mast_top = [tip[0], tip[1], z + cfg['tip_mast_height_mm']]
            parts.append(_beam(f'tip_mast_{tier:02d}_{corner}', [tip[0], tip[1], z - 60],
                               mast_top, 60., 'upper_equipment_mount', equipment_id=equipment))
            half = cfg['crossbar_half_width_mm']
            ends = [[mast_top[k] + tangent[k] * sign * half for k in range(3)] for sign in (-1, 1)]
            parts.append(_beam(f'crossbar_{tier:02d}_{corner}', *ends, 55.,
                               'upper_equipment_crossbar', equipment_id=equipment))

    # Partition the four floor strips so their coplanar tops do not overlap.
    r = radius(gallery_z); outer = r + cfg['gallery_projection_mm']
    slab_bottom = gallery_z - cfg['gallery_slab_thickness_mm']
    floors = [(-outer, -outer, slab_bottom, outer, -r, gallery_z),
              (r, -r, slab_bottom, outer, r, gallery_z),
              (-outer, r, slab_bottom, outer, outer, gallery_z),
              (-outer, -r, slab_bottom, -r, r, gallery_z)]
    guard_z = gallery_z + cfg['gallery_guard_height_mm']
    outer_ring = [_point(outer, i, gallery_z) for i in range(4)]
    for side, bounds in enumerate(floors):
        parts.append(_box(f'gallery_floor_{side}', bounds, 'upper_equipment_service_floor', equipment_id='gallery'))
        a, b = outer_ring[side], outer_ring[(side + 1) % 4]
        parts.append(_beam(f'gallery_guard_{side}', [a[0], a[1], guard_z], [b[0], b[1], guard_z],
                           45., 'upper_equipment_guard', equipment_id='gallery'))
    for corner, tip in enumerate(outer_ring):
        normal = [tip[0] / abs(tip[0]) / sqrt(2), tip[1] / abs(tip[1]) / sqrt(2), 0.]
        low, mount = attachment(corner, gallery_z - cfg['stay_drop_mm'])
        parts.append(_beam(f'gallery_stay_{corner}', inward(low, normal),
                           [tip[0], tip[1], gallery_z - 60], cfg['stay_radius_mm'],
                           'upper_equipment_stay', equipment_id='gallery', **mount))
        parts.append(_beam(f'gallery_post_{corner}', [tip[0], tip[1], gallery_z - 60],
                           [tip[0], tip[1], guard_z], 45., 'upper_equipment_guard', equipment_id='gallery'))

    normals = [(0., -1., 0.), (1., 0., 0.), (0., 1., 0.), (-1., 0., 0.)]
    for index, dish in enumerate(radomes):
        z, face = dish['height_mm'], dish['face']; normal = list(normals[face])
        # The selected end of each face is a real corner-chord centreline.
        corner = ((0, 1), (1, 2), (2, 3), (3, 0))[face][0 if dish['corner'] == -1 else 1]
        root, mount = attachment(corner, z)
        tip = [root[k] + normal[k] * dish['projection_mm'] for k in range(3)]
        equipment = f'radome_{index:02d}'
        parts.append(_beam(f'{equipment}_arm', inward(root, normal), tip, 95.,
                           'upper_equipment_outrigger', equipment_id=equipment, **mount))
        low, stay_mount = attachment(corner, z - cfg['stay_drop_mm'])
        parts.append(_beam(f'{equipment}_stay', inward(low, normal), tip, 70.,
                           'upper_equipment_stay', equipment_id=equipment, **stay_mount))
        parts.append(_beam(f'{equipment}_post', [tip[0], tip[1], z - 350], [tip[0], tip[1], z + 350],
                           85., 'upper_equipment_mount', equipment_id=equipment))
        tangent = [-normal[1], normal[0], 0.]
        radius_mm = dish['diameter_mm'] / 2
        # Closed circular covers have a shallow tapered back. This intentionally
        # does not claim a measured parabola, focal length or internal reflector.
        centres = [[tip[k] - normal[k] * cfg['radome_depth_mm'] * .35 for k in range(3)],
                   [tip[k] + normal[k] * cfg['radome_depth_mm'] * .65 for k in range(3)]]
        sections = []
        for centre, scale in zip(centres, (.48, 1.)):
            sections.append([[centre[k] + tangent[k] * cos(2*pi*i/facets) * radius_mm * scale
                              + (sin(2*pi*i/facets) * radius_mm * scale if k == 2 else 0.)
                              for k in range(3)] for i in range(facets)])
        parts.append({'group': 'structure', 'name': f'structure:upper_equipment_{equipment}_cover',
                      'kind': 'loft3d', 'sections': sections, 'color': WHITE,
                      'role': 'upper_equipment_radome', 'equipment_id': equipment,
                      'diameter_mm': dish['diameter_mm'], 'cover_scope': 'Shallow circular closed appearance cover, not a measured parabolic reflector.'})
        # A short central mount connects the closed cover to its bracket/post.
        parts.append(_beam(f'{equipment}_feed', tip, centres[1], 65.,
                           'upper_equipment_feed', equipment_id=equipment))
    for part in parts:
        part.update(common)
    return parts
