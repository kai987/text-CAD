"""Validate the original detailed fixtures without changing exported artifacts.

Run: .venv/bin/python checks/validate_fixtures.py
Checks both house floors and the apartment, closed solids, named hierarchy,
original plan footprints, finished-floor elevation and genuinely open basins.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from lib.fixture_geometry import FIXTURE_KINDS, fixture_group
from lib.house_plan import P as HOUSE, floor_plan
from lib.apartment_plan import P as APARTMENT, apartment_plan


def validate():
    results = []
    def check(name, condition, actual=None):
        results.append({'check': name, 'pass': bool(condition), 'actual': actual})

    for model, p, floors in [('house', HOUSE, [floor_plan(1), floor_plan(2)]),
                              ('apartment', APARTMENT, [apartment_plan()[0]])]:
        for floor in floors:
            group = fixture_group(floor, p, model)
            tag = f'{model}:F{floor.number}'
            planned = [(i, name, bounds) for i, (name, bounds) in enumerate(floor.fixtures, 1)
                       if name in FIXTURE_KINDS]
            check(f'{tag}:group_name', group.label == f'F{floor.number}:fixtures')
            check(f'{tag}:every_plan_fixture', len(group.children) == len(planned))
            labels = set()
            for fixture, (index, name, bounds) in zip(group.children, planned):
                kind = FIXTURE_KINDS[name]
                prefix = f'F{floor.number}:fixture_{index:02d}_{kind}'
                x1, y1, x2, y2 = bounds
                z = (floor.number-1)*p.storey_height
                bb = fixture.bounding_box()
                tol = .001
                check(f'{tag}:{kind}:hierarchy', fixture.label == prefix and len(fixture.children) >= 7)
                check(f'{tag}:{kind}:within_original_footprint',
                      bb.min.X >= x1-tol and bb.max.X <= x2+tol and
                      bb.min.Y >= y1-tol and bb.max.Y <= y2+tol,
                      [round(v, 3) for v in [bb.min.X, bb.min.Y, bb.max.X, bb.max.Y]])
                check(f'{tag}:{kind}:floor_datum', bb.min.Z >= z and bb.max.Z < z+(2600 if name=='対面キッチン' else 2000))
                for leaf in fixture.children:
                    solids = leaf.solids()
                    check(f'{tag}:{leaf.label}:one_valid_closed_solid',
                          len(solids) == 1 and solids[0].is_valid and solids[0].volume > 0)
                    check(f'{tag}:{leaf.label}:unique_descriptive_name',
                          leaf.label.startswith(prefix+':') and leaf.label not in labels)
                    labels.add(leaf.label)
                    check(f'{tag}:{leaf.label}:surface_color', leaf.color is not None)
                parts = {leaf.label.split(':')[-1]: leaf for leaf in fixture.children}
                cx, cy = (x1+x2)/2, (y1+y2)/2
                if kind == 'bath':
                    shell = parts['tub_shell_ceramic'].solids()[0]
                    check(f'{tag}:bath:deep_open_cavity', not shell.is_inside((cx, cy, z+300)))
                    check(f'{tag}:bath:sealed_tub_floor', shell.is_inside((cx, cy, z+80)))
                    check(f'{tag}:bath:recognizable_details',
                          {'tub_rim_ceramic', 'drain_chrome', 'shower_head_chrome', 'faucet_chrome'} <= parts.keys())
                elif kind == 'vanity':
                    basin = parts['basin_ceramic'].solids()[0]
                    bowl_y = y1+(y2-y1)*.46
                    check(f'{tag}:vanity:hollow_basin', not basin.is_inside((cx, bowl_y, z+750)))
                    check(f'{tag}:vanity:sealed_basin_floor', basin.is_inside((cx, bowl_y, z+660)))
                    check(f'{tag}:vanity:mirror_below_high_window', parts['mirror'].bounding_box().max.Z < z+1500)
                elif kind == 'toilet':
                    bowl_y = y1+(y2-y1)*.405
                    check(f'{tag}:toilet:open_bowl', not parts['bowl_ceramic'].solids()[0].is_inside((cx, bowl_y, z+340)))
                    check(f'{tag}:toilet:open_seat_ring', not parts['seat_ceramic'].solids()[0].is_inside((cx, bowl_y, z+400)))
                    check(f'{tag}:toilet:cistern_and_lid', {'cistern_ceramic', 'open_lid_ceramic'} <= parts.keys())
                elif kind == 'washer':
                    check(f'{tag}:washer:recessed_porthole',
                          not parts['body_white'].solids()[0].is_inside((cx, y1+90, z+438)))
                    check(f'{tag}:washer:recognizable_details',
                          {'porthole_chrome', 'washer_glass', 'drum_steel', 'dial_chrome', 'control_screen'} <= parts.keys())
                elif kind == 'kitchen':
                    sx, sy = x1+(x2-x1)*.285, y1+(y2-y1)*(.535 if name=='対面キッチン' else .465)
                    check(f'{tag}:kitchen:real_inset_sink', not parts['sink_steel'].solids()[0].is_inside((sx, sy, z+770)))
                    check(f'{tag}:kitchen:counter_sink_opening', not parts['counter_stone'].solids()[0].is_inside((sx, sy, z+835)))
                    check(f'{tag}:kitchen:three_hob_rings', all(f'hob_ring_{i}_steel' in parts for i in (1, 2, 3)))
    return results


if __name__ == '__main__':
    results = validate()
    failed = [item for item in results if not item['pass']]
    print(json.dumps({'checks': len(results), 'passed': len(results)-len(failed), 'failed': failed},
                     ensure_ascii=False, indent=2))
    raise SystemExit(1 if failed else 0)
