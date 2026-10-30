"""Geometry regressions for source-guided R05 Skytree appearance primitives."""
from __future__ import annotations
from collections import Counter
from math import atan2, cos, dist, hypot, isfinite, pi, sin, sqrt
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lib.tower_geometry import TOWERS,GROUPS,component_specs,geometry_manifest,ring_points,profile_radius
from lib.skytree_detail import (_frame_config,_base_wing_config,_gain_config,_deck_config,_galleria_config,
                               _frame_point,_frame_stations,_gain_column_radius,_chord_section)


def numbers(value):
    if isinstance(value,dict):
        for item in value.values():yield from numbers(item)
    elif isinstance(value,(list,tuple)):
        for item in value:yield from numbers(item)
    elif type(value) in (int,float):yield value


def points(part):
    if part['kind']=='box':
        b=part['bounds'];return [[b[i],b[j],b[k]] for i in (0,3) for j in (1,4) for k in (2,5)]
    if part['kind'] in ('tube','rhs','beam'):return [part['start'],part['end']]
    if part['kind']=='tube_loft':return [[*s['center'],s['z']] for s in part['sections']]
    if part['kind']=='loft3d':return [v for s in part['sections'] for v in s]
    return [[x,y,s['z']] for s in part['sections'] for x,y in s['points']]


def max_z(part):
    if part['kind']=='tube':
        dz=(part['end'][2]-part['start'][2])/dist(part['start'],part['end'])
        return max(part['start'][2],part['end'][2])+part['radius']*sqrt(max(0,1-dz*dz))
    if part['kind']=='rhs':return max(part['start'][2],part['end'][2])+hypot(part['width_mm'],part['depth_mm'])/2
    if part['kind']=='beam':return max(part['start'][2],part['end'][2])+part['radius']
    return max(v[2] for v in points(part))


def polygon_area3(vertices):
    """Newell area works for the vertical radial sections of a sloping ramp."""
    normal=[0.,0.,0.]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        normal[0]+=(a[1]-b[1])*(a[2]+b[2])
        normal[1]+=(a[2]-b[2])*(a[0]+b[0])
        normal[2]+=(a[0]-b[0])*(a[1]+b[1])
    return sqrt(sum(v*v for v in normal))/2


def inside_polygon(point,vertices):
    """Convex roof sectors; accept a point on a sector's radial boundary."""
    crosses=[]
    for a,b in zip(vertices,vertices[1:]+vertices[:1]):
        crosses.append((b[0]-a[0])*(point[1]-a[1])-(b[1]-a[1])*(point[0]-a[0]))
    return all(v>=-1e-5 for v in crosses) or all(v<=1e-5 for v in crosses)


class SkytreeDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=TOWERS['tokyo-skytree'];cls.c=_frame_config(cls.p);cls.g=_gain_config(cls.p)
        cls.deck=_deck_config(cls.p);cls.hall=_galleria_config(cls.p)
        cls.parts=component_specs('tokyo-skytree');cls.by={p['name']:p for p in cls.parts}
        cls.ring=staticmethod(lambda z:ring_points('tokyo-skytree',z))

    def test_catalog_budget_names_groups_and_exact_634m_limit(self):
        self.assertEqual(len(self.parts),len(self.by));self.assertLessEqual(len(self.parts),8500)
        self.assertGreater(len(self.parts),6000);self.assertEqual({p['group'] for p in self.parts},set(GROUPS))
        self.assertTrue(all(p['name'].startswith(p['group']+':') for p in self.parts))
        self.assertEqual(max(max_z(p) for p in self.parts),634000)
        self.assertEqual(min(v[2] for p in self.parts for v in points(p)),-2500)
        self.assertEqual(self.p['deck_levels_mm'],[350000,450000])
        self.assertTrue(all(v is None for v in geometry_manifest('tokyo-skytree')['engineering'].values()))

    def test_primitives_are_finite_hollow_nondegenerate_and_have_real_sections(self):
        for p in self.parts:
            self.assertTrue(all(isfinite(v) for v in numbers(p)),p['name'])
            if p['kind']=='tube':
                self.assertGreater(dist(p['start'],p['end']),0,p['name'])
                self.assertTrue(0<p['wall_thickness_mm']<p['radius'],p['name'])
            elif p['kind']=='tube_loft':
                self.assertGreater(len(p['sections']),1)
                self.assertTrue(all(b['z']>a['z'] for a,b in zip(p['sections'],p['sections'][1:])),p['name'])
                self.assertTrue(all(len(s['center'])==2 and 0<s['wall_thickness_mm']<s['radius'] for s in p['sections']))
                self.assertIn('Horizontal',p['section_scope'])
            elif p['kind']=='rhs':
                self.assertGreater(dist(p['start'],p['end']),0)
                self.assertTrue(0<2*p['wall_thickness_mm']<min(p['width_mm'],p['depth_mm']))
            elif p['kind']=='loft':
                self.assertTrue(all(b['z']>a['z'] for a,b in zip(p['sections'],p['sections'][1:])),p['name'])
                for section in p['sections']:
                    self.assertGreater(polygon_area3([[x,y,section['z']] for x,y in section['points']]),1.,p['name'])
            elif p['kind']=='loft3d':
                for section in p['sections']:self.assertGreater(polygon_area3(section),1.,p['name'])
        self.assertGreater(sum(p['kind']=='tube' for p in self.parts),1500)

    def test_three_kanae_groups_have_four_real_columns_and_enclosed_feet(self):
        ground=[p for p in self.parts if p.get('role')=='kanae_chord' and p['sections'][0]['z']==0]
        self.assertEqual(len(ground),12)
        self.assertEqual({(p['kanae_group'],p['kanae_chord']) for p in ground},{(g,c) for g in range(3) for c in range(4)})
        self.assertFalse(any('lower_arch' in p['name'] or p.get('role')=='primary_leg' for p in self.parts))
        for group in range(3):
            horizontal=[p for p in self.parts if p.get('role')=='kanae_horizontal' and p['kanae_group']==group]
            self.assertEqual(Counter(p['level_mm'] for p in horizontal),Counter({z:4 for z in (0,12500,25000,37500,50000)}))
            footing=self.by[f'base:footing_{group+1}']['bounds']
            for p in ground:
                if p['kanae_group']!=group:continue
                section=p['sections'][0]
                for k in range(2):
                    self.assertGreaterEqual(section['center'][k]-section['radius'],footing[k])
                    self.assertLessEqual(section['center'][k]+section['radius'],footing[k+3])
            self.assertEqual(footing[2],-1500)

    def test_all_24_outer_axes_follow_real_contour_without_odd_node_shrink(self):
        for z in (315000,400000,495000,497000):
            target=self.ring(z)
            for node in range(24):
                actual=_frame_point(self.p,self.ring,node,z)
                self.assertLess(dist(actual,[*target[node],z]),1e-7,(node,z))
        for z in (315000,400000,495000):
            ring=[p for p in self.parts if p.get('role')=='outer_horizontal' and p['level_mm']==z and p['ring_layer']=='outer']
            self.assertEqual({p['body_node'] for p in ring},set(range(24)))
            for p in ring:
                node=p['body_node']
                self.assertEqual(p['start'],_frame_point(self.p,self.ring,node,z))
                self.assertEqual(p['end'],_frame_point(self.p,self.ring,(node+1)%24,z))

    def test_frame_tiers_and_inner_ring_reduction_preserve_upper_5m_pitch(self):
        levels=_frame_stations(self.p)
        self.assertEqual([z for z in levels if 315000<=z<=495000],list(range(315000,495001,5000)))
        self.assertEqual(levels[-1],497000)
        for lower,upper,pitch in ((50000,150000,12500),(150000,250000,10000),(250000,310000,7500)):
            actual=[z for z in levels if lower<=z<=upper]
            self.assertEqual([b-a for a,b in zip(actual,actual[1:])],[pitch]*(len(actual)-1))
        self.assertIn('illustrative',self.c['ring_tier_scope'])
        rings=[p for p in self.parts if p.get('role') in ('ring_truss','outer_horizontal')]
        for z in {p['level_mm'] for p in rings}:
            counts=Counter(p['ring_layer'] for p in rings if p['level_mm']==z)
            self.assertEqual(counts['outer'],24);self.assertEqual(counts['inner'],12)
            self.assertGreaterEqual(counts['web'],3);self.assertLessEqual(counts['web'],6)
        self.assertTrue(all(p['kind']=='tube' for p in rings if p['ring_layer']=='outer'))
        self.assertTrue(all(p['kind']=='rhs' and p['role']=='ring_truss' for p in rings if p['ring_layer']!='outer'))
        self.assertTrue(all(p['kind']=='rhs' for p in self.parts if p.get('role')=='horizontal_link'))
        outer=self.by['structure:ring_truss_00_00_outer'];inner=self.by['structure:ring_truss_00_00_inner']
        self.assertGreater(hypot(*outer['start'][:2])-hypot(*inner['start'][:2]),2000)
        links=[p for p in self.parts if p.get('role')=='horizontal_link']
        self.assertEqual(sorted({p['level_mm'] for p in links}),list(range(50000,475001,25000)))

    def test_base_wings_cover_three_faces_from_actual_feet_without_new_ground_axes(self):
        c=_base_wing_config(self.p)
        wings=[p for p in self.parts if p.get('role','').startswith('base_wing_')]
        self.assertTrue(wings)
        self.assertEqual({p['wing_face'] for p in wings},{0,1,2})
        self.assertEqual({p['wing_side'] for p in wings},{'left','right'})
        self.assertEqual({p['wing_root_group'] for p in wings},{0,1,2})
        self.assertEqual({p['wing_root_node'] for p in wings},{1,7,9,15,17,23})
        self.assertEqual({p['role'] for p in wings},{'base_wing_chord','base_wing_horizontal','base_wing_brace'})
        self.assertTrue(all(p['kind']=='tube' and p['kanae_group']==p['wing_root_group'] for p in wings))
        self.assertTrue(all('appearance' in p['scope'] for p in wings))
        roots=[p for p in wings if p.get('wing_segment')==0]
        self.assertEqual(len(roots),18)
        for part in roots:
            self.assertEqual(part['start'][2],c['root_attachment_height_mm'])
            self.assertGreater(part['start'][2],part['radius'])
            root=self.by[part['root_support_name']]
            self.assertEqual((root['role'],root['kanae_group']),('kanae_chord',part['wing_root_group']))
            self.assertEqual(root['sections'][0]['z'],0)
            self.assertEqual(root['body_node'],part['wing_root_node'])
            diameter,wall=_chord_section(self.p,root['body_node'],part['start'][2])
            self.assertAlmostEqual(dist(part['start'],part['root_axis_mm']),(diameter-wall)/2)
        tips=[p for p in wings if p.get('wing_segment')==len(c['panel_levels_mm'])]
        self.assertEqual({p['body_node'] for p in tips},{2,3,4,5,6,10,11,12,13,14,18,19,20,21,22})
        for part in tips:
            top=self.by[part['top_support_name']]
            self.assertEqual(top['role'],'outer_chord');self.assertEqual(top['body_node'],part['body_node'])
            self.assertEqual(part['end'][2],self.c['connection_height_mm']+c['top_attachment_inset_mm'])
            self.assertGreater(dist(part['end'],part['top_axis_mm']),500)
        # Only the original twelve kanae lofts reach ground; fan roots branch
        # from their walls rather than inventing 24 new ground columns.
        self.assertTrue(all(min(p['start'][2],p['end'][2])>0 for p in wings))

    def test_base_wings_are_threefold_symmetric_and_leave_central_pedestrian_portals(self):
        wings=[p for p in self.parts if p.get('role','').startswith('base_wing_')]
        angle=2*pi/3
        for part in wings:
            if part['wing_face']!=0:continue
            other=self.by[part['name'].replace('_f0_','_f1_')]
            for key in ('start','end'):
                x,y,z=part[key];rotated=[x*cos(angle)-y*sin(angle),x*sin(angle)+y*cos(angle),z]
                self.assertLess(dist(rotated,other[key]),1e-6,(part['name'],key))
        def axis(part,z):
            t=(z-part['start'][2])/(part['end'][2]-part['start'][2])
            return [part['start'][k]*(1-t)+part['end'][k]*t for k in range(3)]
        def segment_distance(point,part):
            a,b=part['start'],part['end'];d=[b[k]-a[k] for k in range(3)]
            t=max(0,min(1,sum((point[k]-a[k])*d[k] for k in range(3))/sum(v*v for v in d)))
            return dist(point,[a[k]+t*d[k] for k in range(3)])
        for face in range(3):
            for z in (2500,10000,25000,37500):
                boundaries=[]
                for side in ('left','right'):
                    part=next(p for p in wings if p['wing_face']==face and p['wing_side']==side and p.get('wing_lane')==3
                              and p['role']=='base_wing_chord' and p['start'][2]<=z<=p['end'][2])
                    boundaries.append(axis(part,z))
                # The arch boundary narrows as it rises, with no crossing
                # tie or low lintel blocking the central opening.
                self.assertGreater(dist(*boundaries),10000)
                middle=[sum(v[k] for v in boundaries)/2 for k in range(3)]
                self.assertTrue(all(segment_distance(middle,p)>p['radius']+2000 for p in wings if p['wing_face']==face))

    def test_pipe_role_ranges_and_actual_attachment_interpolation(self):
        columns=[p for p in self.parts if p.get('role') in ('kanae_chord','outer_chord')]
        self.assertLessEqual(max(2*s['radius'] for p in columns for s in p['sections']),2300)
        outer=[p for p in columns if p['role']=='outer_chord']
        self.assertTrue(all(1016-1e-6<=2*s['radius']<=1100+1e-6 for p in outer for s in p['sections']))
        self.assertTrue(all(508<=2*p['radius']<=1000 for p in self.parts if p.get('role')=='body_brace'))
        for node,z in ((0,333100),(2,333100),(18,444875),(3,450000)):
            point=_frame_point(self.p,self.ring,node,z)
            part=next(p for p in columns if p.get('body_node')==node and p['sections'][0]['z']<=z<=p['sections'][-1]['z'])
            for a,b in zip(part['sections'],part['sections'][1:]):
                if a['z']<=z<=b['z']:
                    t=(z-a['z'])/(b['z']-a['z'])
                    self.assertLess(dist(point[:2],[a['center'][k]*(1-t)+b['center'][k]*t for k in range(2)]),1e-7)
                    break
        connector=self.by['decks:tembo_deck_apron_connector_00']
        self.assertGreater(dist(connector['start'],connector['frame_axis_mm']),500)

    def test_steel_middle_tower_keeps_rc_core_isolation_gap(self):
        clearance=self.c['middle_radius_mm']*cos(pi/6)-self.c['horizontal_diameter_mm']/2-4000
        self.assertGreaterEqual(clearance,1000)
        self.assertTrue(any(p.get('role')=='middle_tower' for p in self.parts))
        self.assertFalse(any(p.get('role') in ('rivet_head','steel_connection_plate') for p in self.parts))
        walls=[p for p in self.parts if p.get('role')=='shinbashira_wall'];self.assertEqual(len(walls),48)
        self.assertEqual(max(s['z'] for p in walls for s in p['sections']),375000)

    def test_main_deck_glass_leans_outward_71_degrees_and_has_47m_350_floor(self):
        glass=[p for p in self.parts if p['name'].startswith('decks:tembo_deck_glazing_')]
        self.assertTrue(glass)
        for p in glass:
            a,b=p['sections'][0],p['sections'][-1]
            ra,rb=hypot(*a['points'][1]),hypot(*b['points'][1])
            self.assertGreater(rb,ra)
            self.assertAlmostEqual(atan2(b['z']-a['z'],rb-ra)*180/pi,71.,places=7)
            self.assertLessEqual(b['z'],355000)
        floors=[p for p in self.parts if p['name'].startswith('decks:tembo_deck_floor_')]
        self.assertEqual({p['floor_level_mm'] for p in floors},{340000,345000,350000})
        floor350=[p for p in floors if p['floor_level_mm']==350000]
        self.assertAlmostEqual(max(hypot(*v) for p in floor350 for s in p['sections'] for v in s['points'])*2,47000)
        self.assertTrue(any(p.get('facade_band')=='lower_service' for p in glass))
        self.assertNotIn(335000,{p['floor_level_mm'] for p in floors})

    def test_main_deck_opaque_roof_and_crown_have_separate_375m_mass(self):
        enclosures=[p for p in self.parts if p.get('role')=='deck_equipment_enclosure']
        self.assertTrue(enclosures)
        self.assertEqual(min(s['z'] for p in enclosures for s in p['sections']),355000)
        self.assertGreater(max(s['z'] for p in enclosures for s in p['sections']),365000)
        mouth=2*max(hypot(*v) for p in enclosures for s in p['sections'] for v in s['points'])
        self.assertGreaterEqual(mouth,56000);self.assertLessEqual(mouth,62000)
        crowns=[p for p in self.parts if p.get('role')=='deck_equipment_crown']
        self.assertEqual(max(s['z'] for p in crowns for s in p['sections']),375000)
        self.assertLess(max(hypot(*v) for p in crowns for s in p['sections'] for v in s['points']),mouth/2)

    def test_galleria_has_expanding_main_hall_and_about_40m_maximum_diameter(self):
        shell=[p for p in self.parts if p.get('gallery_surface')=='inverted_cone_hall']
        self.assertTrue(shell)
        for p in shell:
            a,b=p['sections'][0],p['sections'][-1]
            self.assertGreater(hypot(*b['points'][1]),hypot(*a['points'][1]))
        external=[p for p in self.parts if p['name'].startswith('decks:tembo_galleria_')]
        diameter=2*max(hypot(*v[:2]) for p in external for v in points(p))
        self.assertGreater(diameter,38000);self.assertLess(diameter,41000)
        self.assertTrue(any(p.get('role')=='galleria_apron' for p in external))
        self.assertTrue(any(p.get('role')=='galleria_equipment_crown' for p in external))

    def test_gallery_is_continuous_variable_radius_2_4m_ramp_and_reaches_451_2m(self):
        ramp=sorted((p for p in self.parts if p.get('role')=='galleria_ramp'),key=lambda p:p['segment'])
        self.assertEqual(len(ramp),self.hall['segments'])
        self.assertEqual(ramp[0]['route_start'][2],445000);self.assertEqual(ramp[-1]['route_end'][2],450000)
        for a,b in zip(ramp,ramp[1:]):self.assertEqual(a['sections'][-1],b['sections'][0])
        length=sum(dist(p['route_start'],p['route_end']) for p in ramp)
        self.assertGreater(length,110000);self.assertLess(length,115000)
        self.assertGreater(hypot(*ramp[-1]['route_end'][:2]),hypot(*ramp[0]['route_start'][:2]))
        for p in ramp:
            for section in p['sections']:
                self.assertAlmostEqual(dist(section[0],section[1]),2400.)
        upper=sorted((p for p in self.parts if p.get('role')=='galleria_upper_incline'),key=lambda p:p['segment'])
        for a,b in zip(upper,upper[1:]):self.assertEqual(a['sections'][-1],b['sections'][0])
        self.assertEqual(max(v[2] for p in upper for v in points(p)),451200)
        self.assertEqual(self.by['decks:tembo_galleria_sorakara_landing']['floor_level_mm'],451200)
        self.assertFalse(any(p.get('role')=='stair_tread' for p in self.parts))
        self.assertFalse(any('tembo_galleria_inner_glazing_' in p['name'] for p in self.parts))

    def test_gain_general_steel_is_six_near_6m_chords_ending_below_top_machine_room(self):
        chords=[p for p in self.parts if p.get('role')=='gain_chord'];self.assertEqual(len(chords),6)
        self.assertEqual({p['gain_node'] for p in chords},set(range(6)))
        for p in chords:
            self.assertEqual(p['sections'][0]['z'],497000)
            self.assertEqual(p['sections'][-1]['z'],self.g['tmd_bottom_mm'])
            self.assertLessEqual(len(p['sections']),4)
            for s in p['sections']:
                diameter=2*(hypot(*s['center'])+s['radius'])
                self.assertGreater(diameter,5900);self.assertLess(diameter,6100)
        transitions=[p for p in self.parts if p.get('role')=='gain_transition'];self.assertEqual(len(transitions),6)
        self.assertTrue(all(p['start'][2]<497000<p['end'][2] for p in transitions))
        self.assertEqual(self.c['body_top_mm'],497000)
        self.assertEqual(self.g['interface_mm'],497000)

    def test_gain_equipment_banks_leave_lattice_gaps_and_have_attached_platforms(self):
        panels=[p for p in self.parts if p.get('role')=='broadcast_antenna_panel']
        self.assertGreaterEqual(len({p['bank'] for p in panels}),5)
        ranges=sorted({(p['sections'][0]['z'],p['sections'][-1]['z']) for p in panels})
        self.assertTrue(any(b[0]-a[1]>=10000 for a,b in zip(ranges,ranges[1:])))
        self.assertTrue(all(p['kind']=='loft' and len(p['sections'])==2 for p in panels))
        platforms={p['level_mm'] for p in self.parts if p.get('role')=='gain_maintenance_platform'}
        self.assertTrue({530000,570000,610000}<=platforms)
        self.assertEqual(platforms,{p['level_mm'] for p in self.parts if p.get('role')=='gain_platform_support'})

    def test_two_storey_expanded_tmd_cap_and_short_lightning_rod_define_top(self):
        floors=[p for p in self.parts if p.get('role')=='tmd_machine_floor']
        self.assertEqual({p['level_mm'] for p in floors},{self.g['tmd_bottom_mm'],self.g['tmd_middle_mm'],self.g['tmd_roof_mm']})
        self.assertEqual({p['tmd_storeys'] for p in floors},{2})
        self.assertGreater(self.g['tmd_radius_mm'],3000)
        rod=self.by['antenna:gain_terminal_mast']
        self.assertEqual(rod['end'],[0,0,634000]);self.assertLess(rod['end'][2]-rod['start'][2],2000)
        self.assertTrue(all(max_z(p)<634000 for p in self.parts if p.get('role') in ('gain_chord','gain_ring','tmd_enclosure_frame')))

    def test_lenses_are_on_real_steel_or_exposed_roof_platforms_in_same_group(self):
        self.assertEqual(Counter(p.get('role') for p in self.parts)['light_lens'],6)
        lenses=[p for p in self.parts if p.get('role')=='obstruction_light_lens'];self.assertEqual(len(lenses),11)
        for lens in lenses:
            support=self.by[lens['support_name']]
            self.assertEqual(lens['group'],support['group'])
            self.assertEqual(lens['mount_surface'],support['mount_surface'])
            box=lens['bounds'];end=support['end']
            self.assertTrue(all(box[k]<=end[k]<=box[k+3] for k in range(3)))
            if lens['mount_surface']=='body_chord':
                self.assertEqual(lens['group'],'structure')
                self.assertEqual(support['start'],_frame_point(self.p,self.ring,0,lens['surface_level_mm']))
                continue
            z=lens['surface_level_mm'];anchor=support['start']
            candidates=[p for p in self.parts if p['group']==lens['group'] and p['kind']=='loft'
                        and p.get('role') in ('deck_roof','gain_maintenance_platform','tmd_machine_floor')
                        and p['sections'][0]['z']<anchor[2]<p['sections'][-1]['z']]
            self.assertTrue(any(inside_polygon(anchor[:2],p['sections'][-1]['points']) for p in candidates),lens['name'])
            self.assertGreater(box[2],z)
        self.assertFalse(any(p['group']=='antenna' and p['surface_level_mm']==495000 for p in lenses))
        self.assertFalse(any(p['surface_level_mm'] in (350000,450000) for p in lenses))

    def test_reference_contours_and_ground_triangle_remain_geometrically_controlled(self):
        ground=self.ring(0)[::8]
        for a,b in zip(ground,ground[1:]+ground[:1]):self.assertAlmostEqual(dist(a,b),68000)
        for v in self.ring(315000):self.assertAlmostEqual(hypot(*v),16000)
        for v in self.ring(495000):self.assertAlmostEqual(hypot(*v),9000)
        for z,r in self.p['profile']:self.assertAlmostEqual(profile_radius('tokyo-skytree',z),r)


class SkytreeNativeContactTests(unittest.TestCase):
    """Small B-rep samples protect actual mounts rather than just their axes."""
    @classmethod
    def setUpClass(cls):
        try:
            from cadgen import build123d as bd
        except ImportError:
            raise unittest.SkipTest('Native contact tests require the project CAD environment.')
        from lib.tower_geometry import _cad_shape
        cls.bd=bd;cls.make=staticmethod(_cad_shape)
        cls.parts=component_specs('tokyo-skytree');cls.by={p['name']:p for p in cls.parts};cls.shapes={}

    def shape(self,name):
        if name not in self.shapes:
            result=self.make(self.by[name],self.bd)
            self.assertTrue(result.is_valid,name)
            self.assertGreater(sum(abs(s.volume) for s in result.solids()),0,name)
            self.shapes[name]=result
        return self.shapes[name]

    def contact(self,a,b,overlap=True):
        aa,bb=self.shape(a),self.shape(b)
        self.assertLess(aa.distance_to(bb),.01,(a,b))
        if overlap:
            common=aa.intersect(bb)
            self.assertIsNotNone(common,(a,b))
            self.assertGreater(sum(abs(s.volume) for s in common.solids()),1.,(a,b))

    def test_base_fan_roots_tips_and_bent_chords_have_real_wall_connections(self):
        for side in ('left','right'):
            for lane in (1,2,3):
                root=f'structure:base_wing_f0_{side}_lane{lane}_chord_0'
                tip=f'structure:base_wing_f0_{side}_lane{lane}_chord_3'
                self.contact(root,self.by[root]['root_support_name'])
                self.contact(tip,self.by[tip]['top_support_name'])
            for segment in range(3):
                self.contact(f'structure:base_wing_f0_{side}_lane3_chord_{segment}',
                             f'structure:base_wing_f0_{side}_lane3_chord_{segment+1}')

    def test_wing_secondary_tubes_land_in_real_hollow_walls_not_empty_axes(self):
        for name in ('structure:base_wing_f0_left_horizontal_0_0',
                     'structure:base_wing_f0_left_horizontal_0_2',
                     'structure:base_wing_f0_right_brace_0_2',
                     'structure:base_wing_f0_left_brace_2_0'):
            part=self.by[name]
            self.contact(name,part['start_support_name'])
            self.contact(name,part['end_support_name'])

    def test_gain_stem_tmd_two_floors_roof_and_rod_have_solid_connections(self):
        for a,b in (
            ('antenna:gain_chord_00','antenna:tmd_machine_floor_0_03'),
            ('antenna:tmd_frame_post_0','antenna:tmd_machine_floor_0_03'),
            ('antenna:tmd_frame_post_0','antenna:tmd_machine_floor_2_03'),
            ('antenna:gain_top_link_00','antenna:gain_terminal_mast'),
        ):self.contact(a,b)

    def test_deck_crown_cone_ramp_and_equipment_supports_have_real_contact(self):
        for a,b in (
            ('decks:tembo_deck_equipment_apron_00','decks:tembo_deck_roof_00'),
            ('decks:tembo_deck_equipment_crown_00','decks:tembo_deck_crown_roof_00'),
            ('antenna:gain_equipment_bank_00_05','antenna:gain_equipment_support_00_0'),
            ('antenna:gain_equipment_bank_00_05','antenna:gain_equipment_belt_00_02_03'),
            ('antenna:gain_maintenance_platform_01_03','antenna:gain_maintenance_spoke_01_0'),
            ('decks:tembo_deck_apron_connector_00','decks:tembo_deck_apron_12'),
            ('decks:tembo_galleria_radial_support_00','decks:tembo_galleria_ramp_00'),
            ('decks:tembo_galleria_arch_glazing_00_3','decks:tembo_galleria_inner_hall_glazing_00_1'),
        ):self.contact(a,b)
        self.contact('decks:tembo_deck_equipment_crown_00','decks:tembo_deck_roof_00',overlap=False)
        body=next(p['name'] for p in self.parts if p.get('body_node')==0 and p.get('role')=='kanae_chord'
                  and p['sections'][0]['z']<=333100<=p['sections'][-1]['z'])
        self.contact('decks:tembo_deck_apron_connector_00',body)

    def test_every_roof_lamp_has_positive_overlap_with_its_actual_mount_and_lens(self):
        for lens in self.parts:
            if lens.get('role')!='obstruction_light_lens' or lens['mount_surface']=='body_chord':continue
            support=self.by[lens['support_name']];anchor=support['start']
            candidates=[p for p in self.parts if p['group']==lens['group'] and p['kind']=='loft'
                        and p.get('role') in ('deck_roof','gain_maintenance_platform','tmd_machine_floor')
                        and p['sections'][0]['z']<anchor[2]<p['sections'][-1]['z']
                        and inside_polygon(anchor[:2],p['sections'][-1]['points'])]
            self.assertTrue(candidates,lens['name'])
            self.contact(support['name'],candidates[0]['name'])
            self.contact(lens['name'],support['name'])


if __name__=='__main__':unittest.main()
