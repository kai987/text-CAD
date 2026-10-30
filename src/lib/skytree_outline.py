"""Source-informed Skytree outline controls in millimetres, without CAD.

NIKKEN JOURNAL 12 (2012 Autumn), printed pages 16--17, identifies an
approximately 68 m triangular base, a 32 m circle at 315 m and an 18 m
circle at 495 m. The upper body is conical. The principal corner (sori)
and face-midpoint (mukuri) guides below 315 m are circular arcs tangent
to that cone. Rounded published dimensions determine the arcs here;
the separately published 4,520 m and maximum 5,950 m radii are records,
not extra exact constraints imposed on those approximate dimensions.

The triangle and circle each have 24 equally spaced perimeter points.
The original construction of the other guide curves is not published in
the cited account. Their affine section blend below is an explicit
appearance assumption: it preserves the two principal arcs and gives
every guide the upper cone's tangent at 315 m. These are guide axes,
not measured pipe surfaces or original architectural CAD coordinates.
"""
from __future__ import annotations

from functools import lru_cache
from math import cos, isfinite, pi, sin, sqrt


SKYTREE_OUTLINE_DEFAULTS = {
    'cone_reference_height_mm': 495000.0,
    'cone_reference_diameter_mm': 18000.0,
    'method': 'principal circular arcs tangent to the upper cone; affine 24-point section blend',
    'published_sori_radius_mm': 4520000.0,
    'published_mukuri_max_radius_mm': 5950000.0,
    'scope': 'Rounded reference controls; intermediate guide curves are appearance interpolation, not recovered original coordinates.',
}


def outline_config(p):
    """Return an independent outline settings dictionary with defaults applied."""
    return {**SKYTREE_OUTLINE_DEFAULTS, **p.get('detail', {}).get('outline', {})}


def _number(value, name):
    try:
        result = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f'Skytree {name} must be finite.') from error
    if not isfinite(result):
        raise ValueError(f'Skytree {name} must be finite.')
    return result


def _parameters(p):
    c = outline_config(p)
    side = _number(p['base_triangle_side_mm'], 'base triangle side')
    height = _number(p['transition_height_mm'], 'transition height')
    radius = _number(p['transition_diameter_mm'], 'transition diameter') / 2
    upper_height = _number(c['cone_reference_height_mm'], 'cone reference height')
    upper_radius = _number(c['cone_reference_diameter_mm'], 'cone reference diameter') / 2
    if min(side, height, radius, upper_radius) <= 0 or upper_height <= height:
        raise ValueError('Skytree outline controls require positive dimensions and an upper reference above the transition.')
    if upper_radius > radius:
        raise ValueError('Skytree upper cone must not widen above the transition.')
    if p.get('ring_divisions', 24) != 24:
        raise ValueError('Skytree outline uses the published 24-point perimeter correspondence.')
    return side / sqrt(3), height, radius, (upper_radius-radius) / (upper_height-height)


@lru_cache(maxsize=32)
def _arc_fit(ground_radius, height, radius, slope):
    """Return signed circular radius and centre height, or a straight tangent."""
    dx = ground_radius-radius
    normal_length = sqrt(1+slope*slope)
    normal_projection = (dx+height*slope) / normal_length
    # If the ground point lies on the cone's tangent, the unique limit is
    # a straight line, rather than a numerically enormous circle.
    if abs(normal_projection) <= 1e-12 * max(height, radius, ground_radius):
        return None
    signed_radius = (dx*dx+height*height) / (2*normal_projection)
    centre_z = height-signed_radius*slope/normal_length
    return signed_radius, centre_z


def _arc_radius_at(ground_radius, z, height, radius, slope):
    if z == 0:
        return ground_radius
    if z == height:
        return radius
    fit = _arc_fit(ground_radius, height, radius, slope)
    if fit is None:
        return radius+slope*(z-height)
    signed_radius, centre_z = fit
    # Rationalize the difference of square roots instead of subtracting
    # a roughly 4,500,000 mm centre from a similarly large square root.
    # The factored square also remains accurate immediately below 315 m.
    root_at_transition = abs(signed_radius) / sqrt(1+slope*slope)
    squared_difference = (z-height)*(z+height-2*centre_z)
    root_squared = root_at_transition*root_at_transition-squared_difference
    if root_squared < 0:
        raise ValueError('Skytree controls do not define a circular guide across the lower body.')
    root_at_z = sqrt(root_squared)
    sign = 1 if signed_radius > 0 else -1
    return radius+sign*squared_difference/(root_at_transition+root_at_z)


def _principal_radii(parameters, z):
    base_radius, height, radius, slope = parameters
    z = max(0.0, _number(z, 'outline height'))
    if z >= height:
        upper_radius = radius+slope*(z-height)
        if upper_radius <= 0:
            raise ValueError('Skytree outline height reaches beyond the upper cone apex.')
        return upper_radius, upper_radius
    return (_arc_radius_at(base_radius, z, height, radius, slope),
            _arc_radius_at(base_radius/2, z, height, radius, slope))


def principal_radii(p, z):
    """Return the corner and face-midpoint guide radii at height ``z``."""
    return _principal_radii(_parameters(p), z)


def profile_radius(p, z):
    """Return the principal corner radius, or the upper circular cone radius."""
    return principal_radii(p, z)[0]


def ring_points(p, z):
    """Return the 24 guide-axis XY points, starting at the +Y corner.

    Ground points divide each triangle edge into eight equal segments;
    upper circular points divide the circle into equal 15-degree angles.
    The two principal arcs determine the section blend, rather than a
    shared radial scale or a smoothstep transition.
    """
    parameters = _parameters(p)
    base_radius, _, transition_radius, _ = parameters
    corner, midpoint = _principal_radii(parameters, z)
    triangle_weight = 2*(corner-midpoint) / base_radius
    circle_weight = (2*midpoint-corner) / transition_radius
    vertices = [(base_radius*cos(pi/2+2*pi*i/3),
                 base_radius*sin(pi/2+2*pi*i/3)) for i in range(3)]
    result = []
    for index in range(24):
        side, offset = divmod(index, 8)
        amount = offset/8
        a, b = vertices[side], vertices[(side+1)%3]
        angle = pi/2+2*pi*index/24
        circular = (transition_radius*cos(angle), transition_radius*sin(angle))
        result.append([triangle_weight*((1-amount)*a[k]+amount*b[k])
                       +circle_weight*circular[k] for k in range(2)])
    return result
