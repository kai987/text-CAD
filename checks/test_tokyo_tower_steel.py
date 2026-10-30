"""Pure invariants for the photo-informed R04 appearance families."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from math import dist,isfinite,sqrt
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from lib.tower_geometry import TOWERS,ring_points,_tower_paint
from lib.tokyo_tower_detail import component_specs as appearance_specs
from lib.tokyo_tower_steel import refine_steel,node_catalog


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def area(p):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1])))/2

def inside(point,polygon):
    x,y=point;result=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result

def numbers(value):
    if isinstance(value,dict):
        for x in value.values():yield from numbers(x)
    elif isinstance(value,(list,tuple)):
        for x in value:yield from numbers(x)
    elif type(value) in (int,float):yield value


class TokyoSteelDetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=TOWERS['tokyo-tower'];cls.base=appearance_specs(cls.p,lambda z:ring_points('tokyo-tower',z),_tower_paint)
        cls.parts=refine_steel(cls.p,cls.base);cls.catalog=node_catalog(cls.p,cls.base)
        cls.by={p['name']:p for p in cls.parts};cls.original={p['name']:p for p in cls.base}

    def test_twenty_nodes_and_budget_remain_bounded_despite_source_panel_changes(self):
        self.assertEqual([n['id'] for n in self.catalog],[f'TT-N{i:02d}' for i in range(1,21)])
        self.assertEqual(Counter(n['type'] for n in self.catalog),Counter(base=4,lower_truss=8,splice=4,deck_support=4))
        self.assertEqual(len(self.parts)-len(self.base),296);self.assertLessEqual(len(self.parts),6000)
        self.assertEqual(len(self.parts),len(self.by))
        self.assertEqual(len({name for n in self.catalog for name in n['part_names']}),296)

    def test_four_real_node_families_have_different_plates_ribs_and_edge_patterns(self):
        reps={n['type']:n for n in self.catalog};outlines={};patterns={}
        for kind,node in reps.items():
            f=node['local_frame'];o=f['origin_mm'];plate=self.by[node['part_names'][0]]
            outlines[kind]=tuple((round(dot(sub(q,o),f['u']),3),round(dot(sub(q,o),f['v']),3)) for q in plate['sections'][0])
            parts=[self.by[n] for n in node['part_names']]
            patterns[kind]=Counter(s['steel_detail_kind'] for s in parts)
        self.assertEqual(len(set(outlines.values())),4)
        self.assertEqual(patterns['base'],Counter(plate=1,stiffener=4,rivet=10))
        self.assertEqual(patterns['lower_truss'],Counter(plate=1,rivet=12))
        self.assertEqual(patterns['splice'],Counter(plate=2,rivet=16))
        self.assertEqual(patterns['deck_support'],Counter(plate=1,stiffener=2,rivet=12))

    def test_catalog_parts_members_and_dimensioned_geometry_are_traceable(self):
        for node in self.catalog:
            self.assertEqual(set(node['names']),{'zh','ja','en'})
            self.assertTrue(all(n in self.by for n in node['member_names']))
            self.assertEqual(node['dimensions_status'],'demonstration_assumption')
            for name in node['part_names']:
                p=self.by[name];self.assertEqual(p['steel_node_id'],node['id']);self.assertEqual(p['group'],'structure')
                self.assertIn(p['contact_with'],self.by)
            f=node['local_frame'];u,v,n=f['u'],f['v'],f['normal']
            for axis in (u,v,n):self.assertAlmostEqual(dot(axis,axis),1)
            for a,b in ((u,v),(u,n),(v,n)):self.assertAlmostEqual(dot(a,b),0)
            for feature in node['feature_dimensions']:
                a,b=feature['points_mm'];d=sub(b,a);self.assertAlmostEqual(dot(d,n),0,places=6)
                self.assertGreater(dist(a,b),0)
                self.assertAlmostEqual(sqrt(dot(d,u)**2+dot(d,v)**2),dist(a,b),places=6)

    def test_h_and_i_sections_preserve_axis_and_use_a_real_web_instead_of_uniform_l(self):
        chords=[p for p in self.parts if p.get('role')=='primary_chord']
        self.assertEqual(len(chords),sum(p.get('role')=='primary_chord' for p in self.base))
        self.assertEqual({p['profile_type'] for p in chords},{'H','I'})
        self.assertEqual({p['section_profile']['family'] for p in chords},{'lower','middle','upper'})
        for p in chords:
            centres=[]
            for s in (self.original[p['name']]['sections'][0],self.original[p['name']]['sections'][-1]):
                centres.append([sum(q[i] for q in s['points'])/len(s['points']) for i in range(2)]+[s['z']])
            self.assertEqual(p['axis_start'],centres[0]);self.assertEqual(p['axis_end'],centres[1])
            f=p['local_frame'];profile=p['section_profile']
            for section,o in zip(p['sections'],centres):
                local=[[dot(sub(q,o),f[k]) for k in ('u','v')] for q in section]
                self.assertEqual(len(local),12);self.assertTrue(inside([0,0],local))
                expected=2*profile['width_mm']*profile['flange_thickness_mm']+profile['web_thickness_mm']*(profile['depth_mm']-2*profile['flange_thickness_mm'])
                self.assertAlmostEqual(area(local),expected,delta=.001)
                self.assertTrue(all(abs(dot(sub(q,o),f['normal']))<1e-6 for q in section))
            self.assertEqual(profile['dimensions_status'],'demonstration_assumption')

    def test_legacy_arch_target_axes_stay_inside_member_web(self):
        anchors=[p for p in self.parts if p['name'].startswith('structure:lower_arch_anchor_')]
        self.assertTrue(anchors)
        for p in anchors:
            target=p['attachment_points'][1];chord=self.by[p['target_member']];a,b=chord['axis_start'],chord['axis_end']
            t=(target[2]-a[2])/(b[2]-a[2]);self.assertTrue(0<=t<=1)
            for i in range(3):self.assertAlmostEqual(target[i],a[i]+t*(b[i]-a[i]),places=6)

    def test_node_anchor_is_on_an_actual_selected_member_at_its_recorded_z(self):
        for node in self.catalog:
            member=self.by[node['member_names'][0]];a,b=member['axis_start'],member['axis_end'];z=node['anchor_mm'][2]
            t=(z-a[2])/(b[2]-a[2]);self.assertTrue(0<=t<=1)
            for i in range(3):self.assertAlmostEqual(node['anchor_mm'][i],a[i]+t*(b[i]-a[i]),places=6)
            if node['type']=='deck_support':self.assertEqual(z,self.p['detail'].get('steel_main_support_z_mm',115000))

    def test_nonbase_plate_back_has_one_mm_contact_and_heads_are_exposed(self):
        for node in self.catalog:
            if node['type']=='base':continue
            f=node['local_frame'];o=f['origin_mm'];n=f['normal'];chord=self.by[node['member_names'][0]]
            half=chord['section_profile']['depth_mm']/2;thick=node['parameters']['plate_thickness_mm']
            self.assertAlmostEqual(dot(sub(o,node['anchor_mm']),n)-thick/2,half-1,places=6)
            for name in node['part_names']:
                head=self.by[name]
                if head.get('role')!='rivet_head':continue
                sign=head['face_sign']
                for section in head['sections']:
                    for point in section:self.assertGreater(sign*dot(sub(point,chord['axis_start']),n),half)

    def test_edge_heads_lie_inside_their_real_plate_outline_and_have_lod_metadata(self):
        rivets=[p for p in self.parts if p.get('role')=='rivet_head'];self.assertEqual(len(rivets),248)
        for node in self.catalog:
            f=node['local_frame'];o=f['origin_mm']
            for name in node['part_names']:
                p=self.by[name]
                if p.get('role')!='rivet_head':continue
                plate=self.by[p['contact_with']]
                polygon=[[dot(sub(q,o),f[k]) for k in ('u','v')] for q in plate['sections'][0]]
                centre=[dot(sub(p['rivet_centre_mm'],o),f[k]) for k in ('u','v')]
                self.assertTrue(inside(centre,polygon),name)
                self.assertEqual(p['detail_level'],'steel_micro')

    def test_new_primitives_are_finite_planar_and_not_duplicate_solids(self):
        signatures=[]
        for p in self.parts:
            if 'steel_node_id' not in p:continue
            self.assertTrue(all(isfinite(x) for x in numbers(p)));self.assertEqual(p['kind'],'loft3d')
            for s in p['sections']:
                a,b,c=s[:3];u,v=sub(b,a),sub(c,a);n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                length=sqrt(dot(n,n));self.assertGreater(length,0)
                self.assertTrue(all(abs(dot(sub(q,a),n))/length<1e-6 for q in s))
            signatures.append(tuple(tuple(tuple(round(x,6) for x in q) for q in s) for s in p['sections']))
        self.assertEqual(len(signatures),len(set(signatures)))

    def test_unrelated_source_parts_and_routes_are_not_changed_by_refinement(self):
        for p in self.base:
            if p.get('role')!='primary_chord':self.assertEqual(p,self.by[p['name']])
        self.assertEqual(sum(p.get('role')=='stair_tread' for p in self.parts),600)
        self.assertEqual(sum(p.get('role') in ('light_lens','obstruction_light_lens') for p in self.parts),17)
        self.assertFalse(any(p['name'].startswith('decks:steel_') for p in self.parts))

    def test_inputs_are_private_and_catalog_bounds_cover_all_real_geometry(self):
        before=deepcopy(self.base);refine_steel(self.p,self.base);node_catalog(self.p,self.base);self.assertEqual(before,self.base)
        for node in self.catalog:
            b=node['bounds_mm']
            for name in node['part_names']:
                for section in self.by[name]['sections']:
                    for point in section:self.assertTrue(all(b[i]-1e-6<=point[i]<=b[i+3]+1e-6 for i in range(3)))

if __name__=='__main__':unittest.main()
