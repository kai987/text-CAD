"""Independent control/route checks for the original Tokyo appearance detail."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
from math import dist, inf, isfinite, nextafter
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lib.tower_geometry import (TOWERS, GROUPS, component_specs, geometry_manifest,
                                geometry_source_paths, profile_radius, revision_for)


def polygon_area(points):
    return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1]))) / 2


def horizontal_bounds(spec):
    if spec['kind'] == 'box':
        return spec['bounds'][:2] + spec['bounds'][3:5]
    if spec['kind'] == 'beam':
        return [min(spec['start'][i],spec['end'][i])-spec['radius'] for i in range(2)] + [
            max(spec['start'][i],spec['end'][i])+spec['radius'] for i in range(2)]
    if spec['kind'] == 'rhs':
        half=max(spec['width_mm'],spec['depth_mm'])/2
        return [min(spec['start'][i],spec['end'][i])-half for i in range(2)]+[
            max(spec['start'][i],spec['end'][i])+half for i in range(2)]
    points=[point for section in spec['sections'] for point in (section if spec['kind']=='loft3d' else section['points'])]
    return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]


def maximum_z(spec):
    if spec['kind']=='box':return spec['bounds'][5]
    if spec['kind']=='beam':return max(spec['start'][2],spec['end'][2])+spec['radius']
    if spec['kind']=='rhs':return max(spec['start'][2],spec['end'][2])
    if spec['kind']=='loft3d':return max(p[2] for section in spec['sections'] for p in section)
    return max(section['z'] for section in spec['sections'])


def geometry_fingerprint(value):
    """Hash unchanged specifications on a 0.00001mm grid across libm platforms.

    Names, ordering, colours and metadata stay exact. Round coordinate tails
    and normalise signed zero before JSON encoding; raw float repr is not a
    portable geometry contract.
    """
    def canonical(item):
        if isinstance(item,float):
            if not isfinite(item):raise ValueError('Nonfinite geometry cannot be fingerprinted.')
            return round(item,5) or 0.0
        if isinstance(item,dict):return {key:canonical(v) for key,v in item.items()}
        if isinstance(item,(list,tuple)):return [canonical(v) for v in item]
        return item
    return hashlib.sha256(json.dumps(canonical(value),sort_keys=True,separators=(',',':')).encode()).hexdigest()


def upper_shaft_refitted_part(part):
    """Exactly the upper-frame bays and twelve moving deck connections."""
    match=re.fullmatch(r'structure:upper_(chord|diagonal|return|secondary|secondary_return|ring)_[0-3]_(\d+)',part['name'])
    if match:
        return 8<=int(match[2])<=(16 if match[1]=='ring' else 17)
    return bool(re.fullmatch(r'decks:top_support_ring_[0-3]|decks:top_underside_bracket_[0-7]',part['name']))


def r06_preserved_parts(specs):
    """Keep every R06 part outside the explicitly requested appearance edits.

    Besides arches/legs and Foot Town, only the shaft below the special
    deck and its twelve connected supports move. Deck shells, twenty steel
    nodes, core, stairs and the antenna remain immutable references.
    """
    result=[]
    for part in specs:
        if part['group']=='base':
            if part['name']=='base:ground_slab' or part['name'].startswith(('base:footing_','base:foot_uplight_')):
                result.append(part)
            continue
        lower=part['group']=='structure' and part['name'].startswith(
            ('structure:lower_arch_','structure:arch_spandrel_','structure:leg_'))
        if not lower and not upper_shaft_refitted_part(part):result.append(part)
    return result


def member_axis(part):
    return (part['axis_start'],part['axis_end']) if 'axis_start' in part else (part['start'],part['end'])


class TokyoTowerDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parameters=TOWERS['tokyo-tower']
        cls.specs=component_specs('tokyo-tower')

    def test_catalog_is_named_bounded_and_separate_from_skytree(self):
        names=[part['name'] for part in self.specs]
        self.assertEqual(len(set(names)),len(names))
        self.assertGreater(len(names),1000)
        self.assertLessEqual(len(names),6500)
        self.assertEqual(set(part['group'] for part in self.specs),set(GROUPS))
        self.assertTrue(all(name.startswith(part['group']+':') for name,part in zip(names,self.specs)))
        self.assertEqual(revision_for('tokyo-tower'),'LANDMARK-R07')
        self.assertEqual(revision_for('tokyo-skytree'),'LANDMARK-R05')
        self.assertNotEqual(component_specs('tokyo-skytree'), self.specs)
        self.assertEqual(geometry_source_paths('tokyo-skytree'),['src/lib/tower_geometry.py','src/lib/skytree_detail.py','src/lib/skytree_outline.py'])
        self.assertIn('src/lib/tokyo_tower_detail.py',geometry_source_paths('tokyo-tower'))

    def test_all_primitives_are_finite_and_have_nonzero_sections(self):
        def numbers(value):
            if isinstance(value,dict):
                for item in value.values():yield from numbers(item)
            elif isinstance(value,(list,tuple)):
                for item in value:yield from numbers(item)
            elif type(value) in (int,float):yield value
        for part in self.specs:
            with self.subTest(part=part['name']):
                self.assertTrue(all(isfinite(number) for number in numbers(part)))
                if part['kind']=='box':
                    self.assertTrue(all(part['bounds'][i+3]>part['bounds'][i] for i in range(3)))
                elif part['kind']=='beam':
                    self.assertGreater(part['radius'],0)
                    self.assertGreater(dist(part['start'],part['end']),0)
                elif part['kind']=='rhs':
                    self.assertGreater(dist(part['start'],part['end']),0)
                    self.assertGreater(part['wall_thickness_mm'],0)
                    self.assertLess(2*part['wall_thickness_mm'],min(part['width_mm'],part['depth_mm']))
                elif part['kind']=='loft3d':
                    self.assertGreater(len(part['sections']),1)
                    for section in part['sections']:
                        area=[sum(a[(i+1)%3]*b[(i+2)%3]-a[(i+2)%3]*b[(i+1)%3]
                                  for a,b in zip(section,section[1:]+section[:1])) for i in range(3)]
                        self.assertGreater(sum(v*v for v in area),0)
                else:
                    self.assertEqual(part['kind'],'loft')
                    self.assertGreater(len(part['sections']),1)
                    self.assertTrue(all(b['z']>a['z'] for a,b in zip(part['sections'],part['sections'][1:])))
                    self.assertTrue(all(polygon_area(section['points'])>0 for section in part['sections']))

    def test_smoother_leg_controls_are_monotone_and_keep_reference_heights(self):
        radii=[profile_radius('tokyo-tower',z) for z in range(0,252651,1000)]
        self.assertTrue(all(a>=b>0 for a,b in zip(radii,radii[1:])))
        fitted=self.parameters['detail']['upper_shaft_outline']
        from lib.tokyo_tower_detail import profile_radius as reference_radius
        for z,radius in self.parameters['profile']:
            self.assertAlmostEqual(reference_radius(self.parameters['profile'],z),radius,places=8)
            if not fitted['start_mm']<z<fitted['end_mm']:
                self.assertAlmostEqual(profile_radius('tokyo-tower',z),radius,places=8)
        self.assertEqual(self.parameters['height_mm'],333000)
        self.assertEqual(self.parameters['deck_levels_mm'],[125000,223550])
        self.assertAlmostEqual(max(maximum_z(part) for part in self.specs),333000)

    def test_lower_frame_keeps_the_base_building_approach_open(self):
        lower=[part for part in self.specs if part['group']=='structure' and maximum_z(part)<=20000]
        self.assertGreater(len(lower),12)
        for part in lower:
            x1,y1,x2,y2=horizontal_bounds(part)
            self.assertTrue(x2 < -18500 or x1 > 18500 or y2 < -18500 or y1 > 18500,part['name'])
        self.assertTrue(any(part.get('role')=='open_cross_frame' for part in self.specs))
        self.assertFalse(any(part['name'].startswith('structure:cross_a_') for part in lower))

    def test_six_hundred_rises_and_landings_connect_roof_to_main_deck(self):
        treads=sorted((p for p in self.specs if p.get('role')=='stair_tread'),key=lambda p:p['riser_index'])
        landings=sorted((p for p in self.specs if p.get('role')=='stair_landing'),key=lambda p:p['flight'])
        self.assertEqual(len(treads),600)
        self.assertEqual([part['riser_index'] for part in treads],list(range(1,601)))
        self.assertEqual(Counter(part['flight'] for part in treads),Counter({flight:25 for flight in range(1,25)}))
        self.assertEqual(len(landings),24)
        start=self.parameters['detail']['foot_town_roof_mm'];rise=(125000-start)/600
        self.assertAlmostEqual(rise,106700/600)
        self.assertAlmostEqual(treads[0]['bounds'][5]-rise,start)
        self.assertAlmostEqual(treads[-1]['bounds'][5],125000)
        for number,tread in enumerate(treads,1):
            self.assertAlmostEqual(tread['bounds'][5],start+number*rise)
            self.assertAlmostEqual(tread['bounds'][4]-tread['bounds'][1],260)
            # The entire route stays east of the guide-frame core and within
            # the tightest model frame below the main observation deck.
            self.assertGreaterEqual(tread['bounds'][0],5000)
            self.assertLessEqual(tread['bounds'][3],8750)
            self.assertGreaterEqual(tread['bounds'][1],-6500)
            self.assertLessEqual(tread['bounds'][4],0)
        for flight,landing in enumerate(landings,1):
            final=treads[flight*25-1]
            self.assertAlmostEqual(landing['bounds'][5],final['bounds'][5])
            if flight%2:self.assertAlmostEqual(final['bounds'][4],landing['bounds'][1])
            else:self.assertAlmostEqual(final['bounds'][1],landing['bounds'][4])
            if flight<24:self.assertAlmostEqual(treads[flight*25]['bounds'][5]-landing['bounds'][5],rise)
        self.assertEqual(landings[-1]['bounds'][:2],[4700,-8000])
        self.assertEqual(landings[-1]['bounds'][3:5],[9300,-6500])

    def test_main_deck_has_two_floor_levels_with_real_stair_openings(self):
        floors=[p for p in self.specs if p.get('role')=='deck_floor' and ':main_' in p['name']]
        self.assertEqual(len(floors),12)
        self.assertEqual(sorted({maximum_z(part) for part in floors}),[120000,125000])
        for level,half in zip((120000,125000),self.parameters['detail']['main_floor_half_widths_mm']):
            half*=.985;chamfer=half*.18
            expected=4*half*half-2*chamfer*chamfer-(9300-4700)*(1800+8000)
            area=0
            for part in floors:
                if maximum_z(part)!=level:continue
                if part['kind']=='box':
                    x1,y1,_,x2,y2,_=part['bounds'];area+=(x2-x1)*(y2-y1)
                else:area+=polygon_area(part['sections'][-1]['points'])
            self.assertAlmostEqual(area,expected,places=3)

    def test_glazing_is_split_into_thin_panels_instead_of_full_deck_volumes(self):
        panels=[p for p in self.specs if p.get('role')=='glazing']
        self.assertGreater(len(panels),100)
        self.assertTrue(all('glazing' in p['name'] and p.get('finish')=='glass' for p in panels))
        for panel in panels:
            x1,y1,x2,y2=horizontal_bounds(panel)
            if panel['kind']=='loft':
                self.assertEqual(len(panel['sections'][0]['points']),4)
                self.assertLess(polygon_area(panel['sections'][0]['points']),2e6)
        self.assertGreater(len([p for p in panels if ':main_glazing_' in p['name']]),16)

    def test_named_light_lenses_have_separate_roles_and_remain_below_tip(self):
        warm=[p for p in self.specs if p.get('role')=='light_lens']
        warning=[p for p in self.specs if p.get('role')=='obstruction_light_lens']
        self.assertEqual(len(warm),6)
        self.assertEqual(len(warning),11)
        for part in warm+warning:
            self.assertIn(part['role'],part['name'])
            self.assertEqual(part['detail_level'],'micro')
            self.assertLess(maximum_z(part),333000)
        manifest=geometry_manifest('tokyo-tower')
        self.assertTrue(all(value is None for value in manifest['engineering'].values()))
        self.assertGreaterEqual(len(manifest['assumptions']),2)

    def test_all_eight_deck_beacons_are_installed_on_the_real_roof_with_lenses_on_housings(self):
        by={p['name']:p for p in self.specs}
        housings=[p for p in self.specs if p['group']=='decks' and p.get('role')=='light_housing']
        self.assertEqual(len(housings),8)
        for housing in housings:
            ident=housing['name'].split(':',1)[1].split('_',1)[0]
            roof=by[f'decks:{ident}_roof_cover']['sections'][-1]
            x1,y1,z1,x2,y2,z2=housing['bounds']
            self.assertEqual(z1,roof['z'],'Beacon mounting base must contact the roof.')
            polygon=roof['points']
            for x,y in ((x1,y1),(x2,y1),(x2,y2),(x1,y2)):
                for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                    self.assertGreaterEqual((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]),0,
                                            'Every housing corner must fit inside the actual roof polygon.')
            lens=by[housing['name'].replace('_housing_','_lens_')]
            lx1,ly1,lz1,lx2,ly2,lz2=lens['bounds']
            self.assertEqual(lz1,z2,'The lens must contact the housing top.')
            self.assertTrue(x1<=lx1<lx2<=x2 and y1<=ly1<ly2<=y2)
            self.assertGreater(lz2,lz1)

    def test_reference_controls_are_separate_from_visitor_deck_names(self):
        p=self.parameters
        self.assertEqual(p['nominal_deck_levels_mm'],[150000,250000])
        self.assertEqual(p['detail']['arch_crown_mm'],40000)
        self.assertEqual(p['antenna_start_mm'],252650)
        self.assertEqual(p['antenna_lattice_top_mm'],312600)
        arches=[part for part in self.specs if part['name'].startswith('structure:lower_arch_') and part.get('role')=='open_cross_frame']
        self.assertAlmostEqual(max(max(point[2] for point in member_axis(part)) for part in arches),40000)
        self.assertLess(min(min(point[2] for point in member_axis(part)) for part in arches),2000)
        panels=[p for p in self.specs if p.get('role')=='lower_panel_brace']
        self.assertGreaterEqual(len(panels),96)
        self.assertTrue(all(40000<=p['start'][2]<=80000 and 40000<=p['end'][2]<=80000 for p in panels))
        self.assertGreater(len([p for p in self.specs if p.get('role')=='antenna_support_lacing']),40)

    def test_arch_end_plates_bridge_actual_chords_and_deck_supports_meet_aprons(self):
        by_name={part['name']:part for part in self.specs}
        connectors=[p for p in self.specs if p['name'].startswith('structure:lower_arch_anchor_')]
        self.assertEqual(len(connectors),16)
        for connector in connectors:
            source=by_name[connector['source_member']]
            target=by_name[connector['target_member']]
            a,b=connector['attachment_points']
            self.assertIn(a,member_axis(source))
            if target['kind']=='loft3d':
                centre_a,centre_b=target['axis_start'],target['axis_end']
            else:
                section_a,section_b=target['sections']
                centre_a=[sum(p[k] for p in section_a['points'])/4 for k in range(2)]+[section_a['z']]
                centre_b=[sum(p[k] for p in section_b['points'])/4 for k in range(2)]+[section_b['z']]
            t=(b[2]-centre_a[2])/(centre_b[2]-centre_a[2])
            self.assertTrue(0<=t<=1)
            for axis in range(2):
                self.assertAlmostEqual(b[axis],centre_a[axis]*(1-t)+centre_b[axis]*t)
            self.assertLess(connector['sections'][0]['z'],a[2])
            self.assertGreater(connector['sections'][1]['z'],a[2])
        brackets=[p for p in self.specs if p.get('role')=='deck_bracket']
        self.assertEqual(len(brackets),16)
        for bracket in brackets:
            apron=by_name[bracket['target_member']]
            edge=apron['sections'][0]
            expected=[(edge['points'][0][axis]+edge['points'][1][axis])/2 for axis in range(2)]+[edge['z']]
            self.assertEqual(bracket['end'],expected)
            level=115000 if ':main_' in bracket['name'] else 216550
            self.assertEqual(bracket['start'][2],level)
        self.assertEqual(len([p for p in self.specs if p.get('role')=='deck_support_ring']),4)

    def test_r07_preserves_r06_geometry_outside_requested_appearance(self):
        # Independently derive this fixed reference from immutable commit6bbcb73,
        # not from the modified model. The R07 exclusion is confined to the
        # requested arches/primary legs, Foot Town and upper shaft; the legacy leg geometry
        # below80m has a separate fixed reference in test_tokyo_tower_base.
        # Float normalisation
        # continues to protect the Linux/macOS preservation contract. The
        # expanded upper-frame subset has32 values within8ULP of1nm rounding
        # boundaries; the independently checked10nm grid has none. This is
        # still100 times smaller than the0.001mm mutation rejection check.
        unchanged=r06_preserved_parts(self.specs)
        self.assertEqual(len(unchanged),4415)
        self.assertEqual(geometry_fingerprint(unchanged),'66fb767e8037c8355514f931858a5c158204b424c2512fb4b28e523d99b78232')

    def test_upper_outline_preserves_the_completed_r07_base_and_all_other_parts(self):
        # Frozen before the subsequent upper-outline request, not derived
        # from the modified upper-shaft implementation.
        unchanged=[part for part in self.specs if not upper_shaft_refitted_part(part)]
        self.assertEqual(len(unchanged),6126)
        self.assertEqual(geometry_fingerprint(unchanged),'b4632bcc9e8c1e869040c7bcb90451521f4d57bbc56bade341bd0b44e9327f09')

    def test_preservation_fingerprint_tolerates_machine_tails_and_signed_zero(self):
        unchanged=r06_preserved_parts(self.specs)
        def perturb(item,direction):
            if isinstance(item,float):
                for _ in range(8):item=nextafter(item,direction)
                return item
            if isinstance(item,dict):return {k:perturb(v,direction) for k,v in item.items()}
            if isinstance(item,(list,tuple)):return [perturb(v,direction) for v in item]
            return item
        expected=geometry_fingerprint(unchanged)
        for direction in (inf,-inf):
            self.assertEqual(geometry_fingerprint(perturb(unchanged,direction)),expected)
        self.assertEqual(geometry_fingerprint([0.0]),geometry_fingerprint([-0.0]))

    def test_preservation_fingerprint_rejects_coordinate_and_metadata_changes(self):
        original={'name':'structure:reference','point':[1000.123456,0.0,180000.0],'color':'#E34C25'}
        expected=geometry_fingerprint(original)
        for modified in ({**original,'point':[1000.124456,0.0,180000.0]},
                         {**original,'name':'structure:changed'},
                         {**original,'color':'#F4F0E7'}):
            self.assertNotEqual(geometry_fingerprint(modified),expected)
        with self.assertRaises(ValueError):geometry_fingerprint([inf])

    def test_main_deck_has_two_independent_upright_narrow_window_levels(self):
        glass=[p for p in self.specs if p['name'].startswith('decks:main_glazing_')]
        self.assertEqual(len(glass),2*(4*24+4*4))
        widths={0:set(),1:set()}
        for panel in glass:
            low,high=panel['sections'];zone=int(panel['name'].rsplit('_',1)[1])
            self.assertEqual(low['points'],high['points'],'Each storey must retain its upright curtain-wall face.')
            self.assertLess(dist(low['points'][0],low['points'][1]),1300)
            widths[zone].add(round(max(abs(v) for point in low['points'][:2] for v in point),6))
            self.assertEqual(panel['color'],'#284C61')
        self.assertEqual(max(widths[0]),13500.)
        self.assertEqual(max(widths[1]),14000.)
        aprons=[p for p in self.specs if p['name'].startswith('decks:main_apron_')]
        self.assertTrue(all(p['color']=='#F4F0E7' for p in aprons))
        self.assertTrue(all(maximum_z(p)-min(s['z'] for s in p['sections'])<=800 for p in aprons))
        self.assertEqual(sum(p.get('role')=='deck_soffit' for p in self.specs),8)
        self.assertGreaterEqual(sum(p.get('role')=='soffit_rib' for p in self.specs),40)
        self.assertEqual(sum(p.get('role')=='cleaning_track' for p in self.specs),8)
        roof_edges=[p for p in self.specs if p['name'].startswith('decks:main_roof_edge_')]
        self.assertTrue(all(maximum_z(p)-min(s['z'] for s in p['sections'])<=200 for p in roof_edges))

    def test_top_deck_uses_a_separate_d13m_faceted_crown_without_window_cross_braces(self):
        panels=[p for p in self.specs if p['name'].startswith('decks:top_glazing_')]
        self.assertEqual(len(panels),48)
        for panel in panels:
            for point in panel['sections'][0]['points'][:2]:
                self.assertAlmostEqual(sum(v*v for v in point)**.5,6500.)
        self.assertEqual(sum(p.get('role')=='deck_crown' for p in self.specs),48)
        self.assertEqual(sum(p.get('role')=='deck_equipment_ring' for p in self.specs),96)
        glass_low=min(p['sections'][0]['z'] for p in panels)
        glass_top=max(p['sections'][-1]['z'] for p in panels)
        for member in self.specs:
            if member.get('role')=='deck_crown_connector':
                self.assertGreater(min(member['start'][2],member['end'][2]),glass_top)
            if member.get('role')=='deck_lower_ring_connector':
                self.assertLess(max(member['start'][2],member['end'][2]),glass_low)

    def test_real_h_profile_corners_stay_inside_top_deck_glass_not_only_their_axes(self):
        panels=[p for p in self.specs if p['name'].startswith('decks:top_glazing_')]
        bottom=min(p['sections'][0]['z'] for p in panels)
        top=max(p['sections'][-1]['z'] for p in panels)
        points=[]
        for part in self.specs:
            if not part['name'].startswith('structure:upper_chord_'):continue
            a,b=part['sections'];edges=list(zip(a,b))
            for section in (a,b):edges+=list(zip(section,section[1:]+section[:1]))
            for start,end in edges:
                points.extend(q for q in (start,end) if bottom<=q[2]<=top)
                if start[2]==end[2]:continue
                for z in (bottom,top):
                    t=(z-start[2])/(end[2]-start[2])
                    if 0<=t<=1:points.append([start[k]+t*(end[k]-start[k]) for k in range(3)])
        self.assertTrue(points)
        for point in points:
            scale=1+.015*(point[2]-bottom)/(top-bottom)
            for panel in panels:
                a,b=[[v*scale for v in p] for p in panel['sections'][0]['points'][:2]]
                dx,dy=b[0]-a[0],b[1]-a[1];length=(dx*dx+dy*dy)**.5
                # The 70mm inward glass strip must remain outside every
                # clipped native H/I section corner throughout the storey.
                self.assertGreaterEqual((dx*(point[1]-a[1])-dy*(point[0]-a[0]))/length,70*scale-1e-5)

    def test_digital_antenna_two_round_groups_follow_supplier_dimensions_and_leave_central_void(self):
        panels=[p for p in self.specs if p.get('role')=='digital_antenna_panel']
        self.assertEqual(len(panels),300)
        self.assertEqual(Counter(p['panel_bank'] for p in panels),Counter({0:150,1:150}))
        self.assertEqual(Counter(p['panel_row'] for p in panels),Counter({i:60 for i in range(5)}))
        for panel in panels:
            radius=6700 if panel['panel_bank']==0 else 6438
            for section in panel['sections']:
                values=[dist((0,0),point) for point in section['points']]
                self.assertAlmostEqual(max(values),radius)
                self.assertGreaterEqual(min(values),radius-220-1e-7)
            self.assertEqual(panel['published_group_height_mm'],5300)
            self.assertEqual(panel['color'],'#F4F0E7' if panel['panel_bank']==0 else '#E34C25')
        rails=[p for p in self.specs if p.get('role')=='digital_antenna_rail']
        self.assertEqual(len(rails),360)
        self.assertEqual(min(p['sections'][0]['z'] for p in rails),240505)
        self.assertEqual(max(p['sections'][-1]['z'] for p in rails),251695)
        by={p['name']:p for p in self.specs}
        for bracket in (p for p in self.specs if p.get('role')=='digital_antenna_bracket'):
            target=by[bracket['target_member']]
            self.assertLess(target['sections'][0]['z'],bracket['end'][2])
            self.assertGreater(target['sections'][-1]['z'],bracket['end'][2])
            self.assertTrue(5810<dist((0,0),bracket['end'][:2])<6670)
        self.assertEqual(sum(p.get('role')=='short_antenna_panel' for p in self.specs),60)

    def test_h23_roof_is_separate_from_fitted_floor_and_h24_open_service_platform(self):
        deck=self.parameters['deck_specs'][1]
        self.assertEqual(deck['top_mm'],223550)
        self.assertEqual(deck['level_mm'],220550)
        self.assertEqual(self.parameters['deck_levels_mm'][1],223550)
        platform=[p for p in self.specs if p.get('role')=='service_platform']
        self.assertEqual(len(platform),48)
        self.assertTrue(all(min(dist((0,0),q) for q in p['sections'][0]['points'])>=4499.9 for p in platform))
        self.assertEqual(max(maximum_z(p) for p in platform),231000)
        self.assertEqual(sum(p.get('role')=='service_dish' for p in self.specs),48)

    def test_sg_reinforcement_is_a_distinct_outer_frame_with_two_layers_of_radial_links(self):
        by={p['name']:p for p in self.specs}
        inner=[p for p in self.specs if p.get('role')=='antenna_support_chord']
        outer=[p for p in self.specs if p.get('role')=='antenna_reinforcement_chord']
        self.assertEqual(len(inner),56);self.assertEqual(len(outer),56)
        self.assertEqual(sum(p.get('role')=='antenna_reinforcement_brace' for p in self.specs),112)
        links=[p for p in self.specs if p.get('role')=='antenna_radial_link']
        self.assertEqual(len(links),120)
        for link in links:
            self.assertGreater(dist([0,0],link['end'][:2]),dist([0,0],link['start'][:2]))
            for point,name in zip((link['start'],link['end']),link['linked_chords']):
                member=by[name];a,b=member['start'],member['end'];t=(point[2]-a[2])/(b[2]-a[2])
                self.assertTrue(0<t<1)
                for axis in range(3):self.assertAlmostEqual(point[axis],a[axis]+t*(b[axis]-a[axis]),places=6)
        self.assertEqual(len({tuple(p['start']+p['end']) for p in links}),len(links))
        transfers=[p for p in self.specs if p.get('role')=='antenna_h27_transfer_link']
        self.assertEqual(len(transfers),4)
        body_tops=[p['axis_end'] for p in self.specs if p.get('role')=='primary_chord'
                   and p.get('axis_end',[0,0,0])[2]==252650]
        for transfer in transfers:
            self.assertIn(transfer['start'],body_tops)
            self.assertEqual(transfer['end'],by[transfer['target_member']]['start'])

    def test_replacement_st_is_a_real_box450_hollow_section_and_all_equipment_stays_below_tip(self):
        mast=[p for p in self.specs if p.get('role')=='antenna_mast']
        self.assertTrue(mast)
        for part in mast:
            self.assertEqual(part['kind'],'rhs')
            self.assertEqual((part['width_mm'],part['depth_mm']),(450.,450.))
            self.assertGreater(part['wall_thickness_mm'],0)
            self.assertEqual(part['wall_dimensions_status'],'demonstration_assumption')
        self.assertEqual(min(p['start'][2] for p in mast),312600)
        self.assertEqual(max(p['end'][2] for p in mast),333000)
        self.assertEqual(sum(p.get('role')=='antenna_insulator_collar' for p in self.specs),6)
        for collar in (p for p in self.specs if p.get('role')=='antenna_insulator_collar'):
            self.assertEqual(collar['kind'],'rhs')
            self.assertGreaterEqual(collar['width_mm']-2*collar['wall_thickness_mm'],450)
        self.assertTrue(all(maximum_z(p)<333000 for p in self.specs
                            if p.get('role') in ('antenna_equipment_arm','antenna_equipment_element','antenna_insulator_collar')))


class TokyoUpperNativeContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from cadgen import build123d as bd
        except ImportError:
            raise unittest.SkipTest('Native contacts require the project CAD environment.')
        from lib.tower_geometry import _cad_shape
        cls.bd=bd;cls.make=staticmethod(_cad_shape)
        cls.by={p['name']:p for p in component_specs('tokyo-tower')};cls.shapes={}

    def shape(self,name):
        if name not in self.shapes:
            result=self.make(self.by[name],self.bd)
            self.assertTrue(result.is_valid,name)
            self.assertGreater(sum(s.volume for s in result.solids()),0,name)
            self.shapes[name]=result
        return self.shapes[name]

    def contact(self,a,b):
        aa,bb=self.shape(a),self.shape(b)
        self.assertLess(aa.distance_to(bb),.01,(a,b))
        common=aa.intersect(bb)
        self.assertIsNotNone(common,(a,b))
        self.assertGreater(sum(s.volume for s in common.solids()),1.,(a,b))

    def test_circular_array_brackets_reach_real_annular_rails(self):
        for part in self.by.values():
            if part.get('role')=='digital_antenna_bracket':
                self.contact(part['name'],part['target_member'])

    def test_open_service_platform_and_reflector_have_native_support(self):
        self.contact('decks:top_service_spoke_0','decks:top_service_platform_05')
        self.contact('decks:top_service_dish_mount_0','decks:top_service_dish_0_0')
        self.shape('decks:top_service_dish_0_5')

    def test_refitted_top_deck_supports_keep_native_contact_at_both_ends(self):
        for side in range(4):
            ring=f'decks:top_support_ring_{side}'
            self.contact(ring,f'structure:upper_chord_{side}_16')
            self.contact(ring,f'structure:upper_chord_{(side+1)%4}_16')
        for index in range(8):
            bracket=f'decks:top_underside_bracket_{index}'
            part=self.by[bracket]
            # Its inner end lands on a face ring, rather than directly on
            # a corner column. Test the actual solid connection.
            # The apron endpoint is a bearing surface. Face contact is valid
            # here; the assembly does not assert a penetrating welded joint.
            self.assertLess(self.shape(bracket).distance_to(self.shape(part['target_member'])),.01)
            distances=[self.shape(bracket).distance_to(self.shape(f'decks:top_support_ring_{side}'))
                       for side in range(4)]
            self.contact(bracket,f'decks:top_support_ring_{distances.index(min(distances))}')


if __name__=='__main__':unittest.main()
