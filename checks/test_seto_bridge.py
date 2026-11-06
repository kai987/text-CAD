"""Independent physical relationships for the photo-informed Bisan bridge pair."""
import math
import hashlib
import json
from pathlib import Path
from copy import deepcopy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lib.seto_bridge_geometry import (GROUPS, bridges, cable_z, component_specs, geometry_manifest, parameters,
    stations, tower_portal_profile, cad_shape, tower_column_outline)
from lib.seto_bridge_activity import activity_manifest
from checks.seto_r01_baseline import (COUNT as BASELINE_COUNT, NAMES as BASELINE_NAMES, SPECS_SHA256,
    CLEARANCE_NAMES, CLEARANCE_ORIGINAL_SPECS, UNCHANGED_CLEARANCE_EXCLUDED_SHA256)
from checks import seto_r02_baseline as r02
from checks import seto_r03_baseline as r03
from checks import seto_r04_baseline as r04
from checks.seto_bridge_clearance import physical_clearance_checks, prism_vertices, shared_anchorage_profile_checks


def r04_specs():
    records={part['name']:part for part in component_specs()
             if not part['name'].startswith('foundations:BB4A_shared:detail:')}
    records.update(deepcopy(r04.ORIGINAL_SHARED_SPECS))
    return records


def historical_specs():
    records=r04_specs()
    records.update(deepcopy(r03.ORIGINAL_TOWER_SPECS))
    return records


def portable_fingerprint(rows):
    def normalize(value):
        if isinstance(value,float): return round(value,6) or 0.
        if isinstance(value,list): return [normalize(v) for v in value]
        if isinstance(value,dict): return {k:normalize(v) for k,v in value.items()}
        return value
    return hashlib.sha256(json.dumps(normalize(sorted(rows,key=lambda p:p['name'])),sort_keys=True,
        ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


class SetoBridgeTests(unittest.TestCase):
    def test_published_span_chains_and_shared_anchor_spacing(self):
        p=parameters();n,s=bridges(p)
        self.assertEqual(n['end']-n['start'],1538000)
        self.assertEqual(s['end']-s['start'],1648000)
        self.assertEqual(n['tower_b']-n['tower_a'],990000)
        self.assertEqual(s['tower_b']-s['tower_a'],1100000)
        self.assertEqual(s['start']-n['end'],49000)
        self.assertEqual(p['overall_length_mm'],3333800)
        for b in (n,s):
            self.assertEqual(b['tower_a']-b['start'],274000)
            self.assertEqual(b['end']-b['tower_b'],274000)

    def test_cable_saddles_and_hanger_clearance(self):
        p=parameters()
        for b in bridges(p):
            self.assertAlmostEqual(cable_z(b['tower_a'],b),b['tower_top']-2500)
            self.assertAlmostEqual(cable_z(b['tower_b'],b),b['tower_top']-2500)
            self.assertAlmostEqual(cable_z((b['tower_a']+b['tower_b'])/2,b),91500)
            for x in stations(b)[1:-1]:
                # Hangers are only placed where the cable clears the road.
                local_road=p['road_deck_z_mm']-.01*abs(x)
                if b['tower_a'] <= x <= b['tower_b']:
                    self.assertGreater(cable_z(x,b),local_road)

    def test_named_groups_and_box_member_hierarchy(self):
        specs=component_specs();names=[s['name'] for s in specs]
        self.assertEqual(len(names),len(set(names)))
        self.assertEqual({s['group'] for s in specs},set(GROUPS))
        self.assertTrue(all(s['name'].startswith(s['group']+':') for s in specs))
        self.assertTrue(all(s['profile']=='member' for s in specs if s['group']=='truss' and s['kind']=='beam'))
        anchor=[s for s in specs if s['name']=='foundations:BB4A_shared:V_notched_body']
        self.assertEqual(len(anchor),1)
        self.assertEqual(anchor[0]['width_mm'],58000)

    def test_r02_preserves_2962_specs_and_only_raises_four_explicit_road_beams(self):
        old_names=set(BASELINE_NAMES)
        retained=sorted((s for s in historical_specs().values() if s['name'] in old_names),key=lambda s:s['name'])
        self.assertEqual(len(retained),BASELINE_COUNT)
        # Restore only the independently captured R03 anchor/floorbeam
        # exceptions before replaying the stricter original R01 audit.
        retained=[deepcopy(r02.ALLOWED_ORIGINAL[s['name']])
                  if s['name'] in (*r02.ANCHOR_NAMES,*r02.FLOORBEAM_NAMES) else s for s in retained]
        encode=lambda rows:json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
        unchanged=[s for s in retained if s['name'] not in CLEARANCE_NAMES]
        self.assertEqual(len(unchanged),2962)
        self.assertEqual(hashlib.sha256(encode(unchanged)).hexdigest(),UNCHANGED_CLEARANCE_EXCLUDED_SHA256)
        by_name={s['name']:s for s in retained}
        for name in CLEARANCE_NAMES:
            expected=deepcopy(CLEARANCE_ORIGINAL_SPECS[name])
            expected['start'][2]+=3000
            expected['end'][2]+=3000
            self.assertEqual(by_name[name],expected)
        # The untouched records and four separately captured originals must
        # reconstruct the original complete R01 fingerprint as well.
        reconstructed=sorted([*unchanged,*deepcopy(list(CLEARANCE_ORIGINAL_SPECS.values()))],key=lambda s:s['name'])
        self.assertEqual(hashlib.sha256(encode(reconstructed)).hexdigest(),SPECS_SHA256)

    def test_r03_preserves_3583_r02_specs_with_exact_physical_exceptions(self):
        by_name=historical_specs()
        self.assertTrue(set(r02.NAMES)<=set(by_name))
        encode=lambda rows:json.dumps(rows,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
        retained=[by_name[name] for name in r02.NAMES]
        unchanged=[s for s in retained if s['name'] not in r02.ALLOWED_ORIGINAL]
        self.assertEqual(len(unchanged),3583)
        self.assertEqual(hashlib.sha256(encode(unchanged)).hexdigest(),r02.UNCHANGED_SHA256)
        for name in r02.FLOORBEAM_NAMES:
            expected=deepcopy(r02.ALLOWED_ORIGINAL[name])
            expected['start'][2]-=1200;expected['end'][2]-=1200
            actual=deepcopy(by_name[name])
            for end in ('start','end'):
                self.assertAlmostEqual(actual[end][2],expected[end][2],places=6)
                actual[end][2]=expected[end][2]
            self.assertEqual(actual,expected)
        for name in r02.ANCHOR_NAMES:
            part=deepcopy(by_name[name]);cuts=part.pop('clearance_cuts')
            self.assertEqual(len(cuts),1)
            self.assertEqual(cuts[0]['purpose'],'road_rail_transport_envelope_demo')
            expected=deepcopy(r02.ALLOWED_ORIGINAL[name])
            if 'BB4A_shared' in name:
                self.assertEqual(expected['outline_xz'][6],[0,72000])
                expected['outline_xz'][6]=[0,52500]
            self.assertEqual(part,expected)
        actors={a['id']:a for a in activity_manifest(parameters())['actors']}
        def local(v,pose,vector=False):
            x,y,z=v if vector else [v[i]-pose['origin_mm'][i] for i in range(3)]
            yaw=pose['heading_rad']
            return (math.cos(yaw)*x+math.sin(yaw)*y,-math.sin(yaw)*x+math.cos(yaw)*y,z)
        for name in r02.BOAT_NAMES:
            part,old=by_name[name],r02.ALLOWED_ORIGINAL[name]
            self.assertEqual({k:v for k,v in part.items() if k not in ('outline','extrusion')},
                             {k:v for k,v in old.items() if k not in ('outline','extrusion')})
            self.assertEqual(len(part['outline']),len(old['outline']))
            for point,prior in zip(part['outline'],old['outline']):
                for a,b in zip(local(point,actors[part['actor_id']]),local(prior,r02.BOAT_POSES[old['actor_id']])):
                    self.assertAlmostEqual(a,b,places=6)
            for a,b in zip(local(part['extrusion'],actors[part['actor_id']],True),
                           local(old['extrusion'],r02.BOAT_POSES[old['actor_id']],True)):
                self.assertAlmostEqual(a,b,places=6)
        reconstructed=sorted([*unchanged,*deepcopy(list(r02.ALLOWED_ORIGINAL.values()))],key=lambda s:s['name'])
        self.assertEqual(len(reconstructed),r02.COUNT)
        self.assertEqual(hashlib.sha256(encode(reconstructed)).hexdigest(),r02.SPECS_SHA256)

    def test_native_anchor_and_floorbeam_sweeps_fix_real_original_collisions(self):
        rows=physical_clearance_checks(component_specs(),parameters(),activity_manifest(parameters()))
        failed=[row for row in rows if not row['pass']]
        self.assertEqual(failed,[],json.dumps(failed,ensure_ascii=False))

    def test_every_vehicle_route_has_real_clearance_under_all_four_tower_beams(self):
        # The unsupported above-road bar was removed to match the photo.
        # Both complete road and rail swept-solid checks cover the portal.
        specs=component_specs()
        self.assertFalse(any(part['name'] in CLEARANCE_NAMES for part in specs))
        rows=physical_clearance_checks(specs,parameters(),activity_manifest(parameters()))
        road=next(row for row in rows if row['check']=='road:all_tower_full_route_sweeps')
        self.assertTrue(road['pass'],road)
        self.assertEqual(road['actual']['lanes'],4)

    def test_r04_changes_only_68_frozen_tower_and_pier_specs(self):
        specs=list(r04_specs().values())
        new_names={f'towers:{bridge}:tower_{number}:{suffix}' for bridge in ('north','south')
            for number in (1,2) for suffix in ('base_plate_-1','base_plate_1','lower_chevron_L',
                'lower_chevron_R','joint:upper_3','joint:upper_4','joint:lower')}
        unchanged=[s for s in specs if s['name'] not in r03.ORIGINAL_TOWER_SPECS and s['name'] not in new_names]
        self.assertEqual(len(unchanged),r03.UNCHANGED_COUNT)
        self.assertEqual(portable_fingerprint(unchanged),r03.UNCHANGED_SHA256)
        self.assertEqual(portable_fingerprint([*unchanged,*r03.ORIGINAL_TOWER_SPECS.values()]),r03.FULL_SHA256)
        removed={f'towers:{b}:tower_{n}:crossbeam_{j}' for b in ('north','south') for n in (1,2) for j in (0,2,3,4)}
        actual={s['name'] for s in specs}
        self.assertFalse(actual & removed)
        self.assertTrue(new_names<=actual)
        self.assertEqual(len(specs),r03.COUNT-len(removed)+len(new_names))

    def test_r05_changes_only_two_frozen_shared_anchorage_specs(self):
        specs=component_specs();names={s['name'] for s in specs}
        additions={name for name in names if name.startswith('foundations:BB4A_shared:detail:')}
        retained=[s for s in specs if s['name'] not in r04.ORIGINAL_SHARED_SPECS and s['name'] not in additions]
        self.assertEqual(len(retained),r04.UNCHANGED_COUNT)
        self.assertEqual(portable_fingerprint(retained),r04.UNCHANGED_SHA256)
        self.assertEqual(portable_fingerprint([*retained,*r04.ORIGINAL_SHARED_SPECS.values()]),r04.FULL_SHA256)
        self.assertTrue(set(r04.ORIGINAL_SHARED_SPECS)<=names)
        self.assertEqual(len(specs),r04.COUNT+len(additions))

    def test_shared_anchorage_native_silhouette_matches_reference_shoulders_and_v(self):
        rows=shared_anchorage_profile_checks(component_specs())
        failed=[row for row in rows if not row['pass']]
        self.assertEqual(failed,[],json.dumps(failed,ensure_ascii=False))
        # The old block must fail the same actual-solid probes; relabeling
        # metadata as R05 without changing the concrete cannot satisfy them.
        old={part['name']:part for part in component_specs()}
        old.update(deepcopy(r04.ORIGINAL_SHARED_SPECS))
        rejected={row['check'] for row in shared_anchorage_profile_checks(list(old.values())) if not row['pass']}
        self.assertTrue({'shared_anchor:solid_probe:'+name for name in
            ('lower_narrow_face','upper_batter','blind_recess','upper_v_return','base_footprint')}<=rejected)

    def test_tower_brace_ends_contact_real_column_and_support_solids(self):
        import build123d as bd
        by_name={p['name']:p for p in component_specs()}
        for b in bridges():
            for number in (1,2):
                prefix=f"towers:{b['id']}:tower_{number}:"
                columns={sign:cad_shape(by_name[prefix+f'leg_{sign}'],bd) for sign in (-1,1)}
                support=cad_shape(by_name[prefix+'crossbeam_1'],bd)
                for part in by_name.values():
                    if not part['name'].startswith(prefix) or not ('X_' in part['name'] or 'lower_chevron_' in part['name']):continue
                    shape=cad_shape(part,bd)
                    self.assertTrue(shape.is_valid)
                    for point in (part['start'],part['end']):
                        host=support if abs(point[1])<.001 else columns[1 if point[1]>0 else -1]
                        common=shape.intersect(host)
                        volume=sum(abs(s.volume) for s in common) if common else 0
                        self.assertGreater(volume,1,part['name'])

    def test_traffic_uses_four_left_hand_lanes_and_complete_named_vehicles(self):
        p=parameters();actors=activity_manifest(p)['actors'];cars=[a for a in actors if a['group']=='traffic']
        self.assertEqual(len(cars),24)
        self.assertEqual({a['kind'] for a in cars},{'sedan','van','bus'})
        self.assertEqual({a['route']['fixed_mm'] for a in cars},{-8500,-3500,3500,8500})
        by_name={s['name']:s for s in component_specs()}
        for actor in cars:
            route=actor['route'];x,y,z=actor['origin_mm']
            self.assertEqual(actor['direction'],1 if y>0 else -1)
            self.assertAlmostEqual(actor['heading_rad'],0 if y>0 else math.pi)
            self.assertAlmostEqual(z,93000-.01*max(abs(x),24500))
            self.assertGreaterEqual(x-actor['length_mm']/2,p['north_outer_end_mm'])
            self.assertLessEqual(x+actor['length_mm']/2,p['south_outer_end_mm'])
            self.assertGreater(abs(y)-actor['width_mm']/2,325)
            self.assertLess(abs(y)+actor['width_mm']/2,12625)
            self.assertTrue(0 < actor['speed_mps'] <= 35)
            self.assertGreaterEqual(len(actor['part_names']),8)
            self.assertTrue(all(name in by_name and by_name[name]['actor_id']==actor['id'] for name in actor['part_names']))
            self.assertEqual(len([name for name in actor['part_names'] if ':tyre_' in name]),4)
            self.assertTrue(any('window' in name or 'glass' in name for name in actor['part_names']))
            self.assertEqual(len([name for name in actor['part_names'] if name.endswith(':painted_body')]),1)
            self.assertEqual(len([name for name in actor['part_names'] if ':headlamp_' in name]),2)
            self.assertEqual(len([name for name in actor['part_names'] if ':taillamp_' in name]),2)
            self.assertEqual(route['axis'],'x')
            self.assertTrue(route['min_mm'] <= x <= route['max_mm'])

    def test_boat_routes_keep_their_full_hulls_on_water_and_outside_islands(self):
        p=parameters();actors=activity_manifest(p)['actors'];boats=[a for a in actors if a['group']=='vessels']
        self.assertEqual(len(boats),4)
        self.assertEqual(len({a['id'] for a in actors}),len(actors))
        specs=component_specs();islands=[s for s in specs if s['kind']=='island'];by_name={s['name']:s for s in specs}
        for actor in boats:
            route=actor['route'];x,y,z=actor['origin_mm'];half_width=actor['width_mm']/2
            self.assertEqual(z,0)
            self.assertGreaterEqual(actor['length_mm'],15000)
            self.assertLess(actor['length_mm'],70000)
            self.assertTrue(0 < actor['speed_mps'] <= 15)
            self.assertEqual(route['axis'],'y')
            self.assertEqual(route['fixed_mm'],x)
            self.assertEqual((route['min_mm'],route['max_mm']),(-300000,300000))
            self.assertTrue(route['min_mm'] <= y <= route['max_mm'])
            self.assertAlmostEqual(actor['heading_rad'],actor['direction']*math.pi/2)
            self.assertLess(max(abs(route['min_mm']),abs(route['max_mm']))+actor['length_mm']/2,p['context_width_mm']/2)
            for island in islands:
                # The complete perpendicular crossing lies outside every
                # island's longitudinal envelope at every marine-route Y.
                self.assertGreater(abs(x-island['centre'][0])-half_width,island['radii'][0]+5000)
            b=next(b for b in bridges(p) if b['tower_a'] < x < b['tower_b'])
            self.assertGreater(x-half_width,b['tower_a']+20000)
            self.assertLess(x+half_width,b['tower_b']-20000)
            # Actual hull polygons are rotated across the bridge, not just
            # labeled differently; no caisson or body occupies their sweep.
            max_top=max(v[2] for name in actor['part_names'] for v in prism_vertices(by_name[name]))
            deck=p['rail_deck_z_mm']-.01*abs(x)-1750
            self.assertGreater(deck-max_top,50000)
            self.assertTrue(any('hull' in name for name in actor['part_names']))
            self.assertTrue(any('cabin' in name for name in actor['part_names']))
            self.assertTrue(all(name in by_name and by_name[name]['actor_id']==actor['id'] for name in actor['part_names']))
            hull=[by_name[name] for name in actor['part_names'] if name.endswith(':flared_hull')]
            self.assertEqual(len(hull),1)
            self.assertGreaterEqual(len(hull[0]['outline']),5)

    def test_electric_trains_are_two_complete_consists_with_rail_contact_and_pantographs(self):
        p=parameters();activity=activity_manifest(p);actors=activity['actors']
        self.assertEqual(activity['schema_version'],2)
        self.assertEqual(len(actors),36)
        self.assertEqual(activity['rail_crest_z_mm'],80420)
        trains=[a for a in actors if a['group']=='trains']
        self.assertEqual(len(trains),8)
        self.assertEqual({a['route']['fixed_mm'] for a in trains},{-10500,-5500})
        by_name={s['name']:s for s in component_specs()}
        crest=lambda x:80420-.01*max(abs(x),24500)
        for ident in {a['train_id'] for a in trains}:
            cars=sorted([a for a in trains if a['train_id']==ident],key=lambda a:a['carriage_index'])
            self.assertEqual([a['carriage_index'] for a in cars],[0,1,2,3])
            self.assertEqual([a['consist_offset_mm'] for a in cars],[0,-20500,-41000,-61500])
            lead=cars[0]
            self.assertTrue(all(a['route']==lead['route'] and a['speed_mps']==lead['speed_mps'] and
                a['direction']==lead['direction'] and a['lead_position_mm']==lead['lead_position_mm'] for a in cars))
            # Times before/after either route wrap retain exact 20.5m
            # spacing. The same leader wraps once for the whole consist.
            length=lead['route']['max_mm']-lead['route']['min_mm']
            for time in (0,1,100,length/(lead['speed_mps']*1000)-.001,length/(lead['speed_mps']*1000)+.001):
                position=lead['route']['min_mm']+(lead['lead_position_mm']-lead['route']['min_mm']+
                    lead['direction']*lead['speed_mps']*1000*time)%length
                positions=[position+a['direction']*a['consist_offset_mm'] for a in cars]
                self.assertTrue(all(abs(abs(a-b)-20500)<1e-6 for a,b in zip(positions,positions[1:])))
            for actor in cars:
                x,y,z=actor['origin_mm'];half=actor['bogie_spacing_mm']/2
                rear,front=crest(x-half),crest(x+half)
                self.assertAlmostEqual(z,(rear+front)/2)
                self.assertAlmostEqual(actor['pitch_rad'],-math.atan(actor['direction']*(front-rear)/(2*half)))
                self.assertAlmostEqual(x,lead['lead_position_mm']+actor['direction']*actor['consist_offset_mm'])
                parts=[by_name[name] for name in actor['part_names']]
                self.assertEqual(sum(':wheel_' in part['name'] and ':wheel_hub_' not in part['name'] for part in parts),8)
                self.assertTrue(any(part['name'].endswith(':pantograph_contact_bar') for part in parts))
                self.assertTrue(any('sliding_door' in part['name'] for part in parts))
                self.assertTrue(all(part['actor_id']==actor['id'] and part['group']=='trains' for part in parts))

    def test_local_road_grade_and_hanger_attachments(self):
        p=parameters();specs=component_specs()
        hangers=[s for s in specs if s['group']=='hangers']
        self.assertGreater(len(hangers),350)
        for part in hangers:
            x,y,z=part['start']
            self.assertAlmostEqual(z,p['road_deck_z_mm']-.01*abs(x))
            self.assertEqual(abs(y),17500)
            self.assertGreater(part['end'][2],z)
        for part in specs:
            if part['group']=='truss' and ':chord:' in part['name']:
                nominal=p['rail_deck_z_mm'] if ':lower:' in part['name'] else p['road_deck_z_mm']
                for x,y,z in (part['start'],part['end']):
                    self.assertAlmostEqual(z,nominal-.01*abs(x))

    def test_four_portal_towers_have_two_upper_x_levels(self):
        specs=component_specs();legs=[s for s in specs if s['group']=='towers' and ':leg_' in s['name']]
        self.assertEqual(len(legs),8)
        self.assertEqual(sorted({s['base_centre_mm'][0] for s in legs}),parameters()['tower_stations_mm'])
        self.assertEqual(sorted({s['top_centre_mm'][2] for s in legs}),[179500,189500])
        for leg in legs:
            self.assertEqual(leg['kind'],'tower_column')
            self.assertEqual(len(tower_column_outline(leg)),12)
            self.assertEqual(leg['width_mm'],4800)
            self.assertEqual((leg['base_depth_mm'],leg['top_depth_mm']),(10700,7100))
        for bridge in ('north','south'):
            for tower in ('tower_1','tower_2'):
                cross=[s for s in specs if s['name'].startswith(f'towers:{bridge}:{tower}:X_') and min(s['start'][2],s['end'][2])>100000]
                self.assertEqual(len(cross),4) # Two diagonals per X, two levels.
                prefix=f'towers:{bridge}:{tower}:'
                own=[s for s in specs if s['name'].startswith(prefix)]
                self.assertEqual(sum('lower_chevron_' in s['name'] for s in own),2)
                self.assertEqual({s['name'].split(':')[-1] for s in own if 'crossbeam_' in s['name']},
                    {'crossbeam_1','crossbeam_5'})

    def test_references_and_assumptions_keep_datums_distinct(self):
        m=geometry_manifest()
        self.assertEqual(m['status'],'reference_concept_only')
        self.assertEqual(m['official_dimensions']['north_tower_top_mm']['datum'],'T.P.')
        self.assertGreaterEqual(len(m['references']),7)
        self.assertTrue(all(set(a)=={'zh','ja','en'} and all(a.values()) for a in m['assumptions']))
        self.assertIn('high-water',m['assumptions'][1]['en'])
        copy=parameters();copy['north_length_mm']=1
        self.assertEqual(parameters()['north_length_mm'],1538000)


if __name__=='__main__': unittest.main()
