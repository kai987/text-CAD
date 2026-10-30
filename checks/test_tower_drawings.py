"""Independent saved-file checks for the editable landmark drawings."""
from __future__ import annotations

import hashlib
import json
import sys
from math import sqrt
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import ezdxf
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    'tokyo_tower': {'height':333000, 'decks':[125000,223550],
                    'base_dimension':80000, 'name':'東京タワー', 'elevation_scale':1500,
                    'revision':'LANDMARK-R04'},
    'tokyo_skytree': {'height':634000, 'decks':[350000,450000],
                      'base_dimension':68000, 'name':'東京スカイツリー', 'elevation_scale':3000,
                      'revision':'LANDMARK-R02'},
}


class TowerSavedDrawingTests(unittest.TestCase):
    def test_elevation_native_dimensions_preserve_official_mm_values(self):
        for stem, values in EXPECTED.items():
            with self.subTest(tower=stem):
                doc=ezdxf.readfile(ROOT/f'DXF/{stem}_elevation.dxf')
                self.assertEqual(doc.dxfversion,'AC1032')
                self.assertEqual(doc.units,ezdxf.units.MM)
                self.assertEqual(doc.header['$DIMASSOC'],2)
                dimensions=list(doc.modelspace().query('DIMENSION'))
                self.assertEqual(len(dimensions),3)
                self.assertEqual([round(float(d.get_measurement())) for d in dimensions],
                                 [values['height'],*values['decks']])
                self.assertTrue(all(d.dxf.geometry for d in dimensions))

    def test_plan_dimensions_measure_support_spacing_not_render_scale(self):
        for stem, values in EXPECTED.items():
            with self.subTest(tower=stem):
                doc=ezdxf.readfile(ROOT/f'DXF/{stem}_plan.dxf')
                dimensions=[float(d.get_measurement()) for d in doc.modelspace().query('DIMENSION')]
                self.assertTrue(dimensions)
                for measure in dimensions:self.assertAlmostEqual(measure,values['base_dimension'],places=6)
                if stem=='tokyo_skytree':
                    # 68m is a base-triangle side, not its circumcircle diameter.
                    self.assertNotAlmostEqual(dimensions[0],68000*2/sqrt(3),places=1)

    def test_all_native_labels_are_editable_and_follow_light_dark_layer_color(self):
        for stem in EXPECTED:
            for view in ('plan','elevation'):
                with self.subTest(tower=stem,view=view):
                    doc=ezdxf.readfile(ROOT/f'DXF/{stem}_{view}.dxf')
                    self.assertFalse(doc.audit().has_errors)
                    self.assertTrue(list(doc.modelspace().query('TEXT')))
                    self.assertEqual(doc.styles.get('TOWER_UNICODE').dxf.font,'Arial Unicode.ttf')
                    for entity in doc.modelspace():
                        self.assertIn(entity.dxf.color,(7,256))
                        self.assertFalse(entity.dxf.hasattr('true_color'))
                    for layer in doc.layers:
                        if layer.dxf.name.startswith('D-'):self.assertEqual(layer.dxf.color,7)

    def test_a3_layout_scale_is_applied_only_in_locked_viewport(self):
        for stem, values in EXPECTED.items():
            for view in ('plan','elevation'):
                scale=500 if view=='plan' else values['elevation_scale']
                with self.subTest(tower=stem,view=view):
                    doc=ezdxf.readfile(ROOT/f'DXF/{stem}_{view}.dxf')
                    layout=doc.layouts.get(f'LANDMARK_A3_1_{scale}')
                    viewports=[v for v in layout.query('VIEWPORT') if v.dxf.id>1]
                    extra=[300] if stem=='tokyo_tower' else [500,500]
                    expected_scales=[scale,*extra] if view=='elevation' else [scale]
                    self.assertEqual(len(viewports),len(expected_scales))
                    self.assertEqual(sorted(round(v.dxf.view_height/v.dxf.height) for v in viewports),sorted(expected_scales))
                    self.assertTrue(all(viewport.dxf.flags & 16384 for viewport in viewports))

    def test_svg_labels_native_measurements_and_source_binding_are_complete(self):
        for stem,values in EXPECTED.items():
            with self.subTest(tower=stem):
                metadata=json.loads((ROOT/f'output/review/{stem}_drawings.json').read_text())
                self.assertEqual(metadata['revision'],values['revision'])
                self.assertEqual(metadata['source_geometry_revision'],values['revision'])
                self.assertEqual(metadata['status'],'reference_concept_only')
                self.assertEqual(metadata['units'],'mm')
                self.assertEqual(len(metadata['drawings']),3 if stem=='tokyo_tower' else 2)
                detail_source='tokyo_tower_detail' if stem=='tokyo_tower' else 'skytree_detail'
                expected_sources={
                    'src/lib/tower_geometry.py',f'src/lib/{detail_source}.py',
                    'src/generate_tower_plans.py'}
                if stem=='tokyo_tower':expected_sources.add('src/lib/tokyo_tower_steel.py')
                self.assertEqual(set(metadata['source_sha256']),expected_sources)
                for section in ('source_sha256','artifacts'):
                    for rel,expected in metadata[section].items():
                        data=(ROOT/rel).read_bytes()
                        digest=expected if section=='source_sha256' else expected['sha256']
                        self.assertEqual(hashlib.sha256(data).hexdigest(),digest,rel)
                        if section=='artifacts':self.assertEqual(len(data),expected['bytes'])
                for drawing in metadata['drawings']:
                    svg=ET.fromstring((ROOT/drawing['svg']).read_text())
                    self.assertEqual(svg.attrib['data-units'],'mm')
                    self.assertEqual(svg.attrib['data-revision'],values['revision'])
                    doc=ezdxf.readfile(ROOT/drawing['dxf'])
                    self.assertEqual(doc.ezdxf_metadata()['REVISION'],values['revision'])
                    text=' '.join(svg.itertext())
                    for label in drawing['required_labels']:self.assertIn(label,text)
                    dimensions=[e for e in svg.iter() if 'data-dimension-mm' in e.attrib]
                    self.assertEqual(len(dimensions),len(drawing['dimensions_mm']))
                    for entity,expected in zip(dimensions,drawing['dimensions_mm']):
                        self.assertAlmostEqual(float(entity.attrib['data-dimension-mm']),expected,places=3)
                        self.assertAlmostEqual(float(entity.text.replace(',','')),expected,delta=.01)

    def test_print_pdf_contains_expected_a3_pages_and_readable_japanese_reference_values(self):
        for stem,values in EXPECTED.items():
            with self.subTest(tower=stem):
                path=ROOT/f'output/pdf/{stem}_sheets.pdf'
                self.assertTrue(path.read_bytes().startswith(b'%PDF-'))
                reader=PdfReader(path)
                self.assertEqual(len(reader.pages),3 if stem=='tokyo_tower' else 2)
                self.assertIn(values['revision'],reader.metadata.title)
                for page in reader.pages:
                    self.assertAlmostEqual(float(page.mediabox.width)*25.4/72,420,places=2)
                    self.assertAlmostEqual(float(page.mediabox.height)*25.4/72,297,places=2)
                    text=page.extract_text()
                    self.assertIn(values['name'],text)
                    self.assertIn('外観模式図',text)
                    self.assertIn('仮定',text)
                    self.assertIn('単位 mm',text)
                    self.assertIn(f"{values['height']:,}",text)
                elevation=reader.pages[1].extract_text()
                for level in values['decks']:self.assertIn(f'{level:,}',elevation)

    def test_tokyo_deck_detail_reuses_locked_native_projection_without_duplicate_dimensions(self):
        stem='tokyo_tower'
        metadata=json.loads((ROOT/f'output/review/{stem}_drawings.json').read_text())
        row=next(row for row in metadata['drawings'] if row['id']=='elevation')
        self.assertEqual(len(row['details']),1)
        detail=row['details'][0]
        self.assertEqual(detail['id'],'main_deck')
        self.assertEqual(detail['scale'],300)
        self.assertEqual(detail['view_center_mm'],[0,125000])
        self.assertEqual(detail['source_geometry_revision'],'LANDMARK-R04')
        self.assertTrue(any(part.startswith('decks:main_') for part in detail['source_parts']))
        self.assertEqual(len(set(detail['source_parts'])),len(detail['source_parts']))
        doc=ezdxf.readfile(ROOT/row['dxf'])
        self.assertEqual(len(list(doc.modelspace().query('DIMENSION'))),3)
        layout=doc.layouts.get('LANDMARK_A3_1_1500')
        viewport=next(viewport for viewport in layout.query('VIEWPORT')
                      if viewport.dxf.id>1 and round(viewport.dxf.view_height/viewport.dxf.height)==300)
        self.assertEqual(set(viewport.frozen_layers),set(detail['frozen_layers']))
        self.assertEqual(set(viewport.frozen_layers),{'D-STR-DIM','D-STR-TXT','D-BMK-AXIS'})
        self.assertAlmostEqual(viewport.dxf.view_center_point.x,0)
        self.assertAlmostEqual(viewport.dxf.view_center_point.y,125000)
        svg=ET.fromstring((ROOT/row['svg']).read_text())
        inset=next(element for element in svg.iter() if element.attrib.get('data-detail-id')=='main_deck')
        self.assertIn('clip-path',inset.attrib)
        self.assertGreater(len(list(inset)),5)
        text=PdfReader(ROOT/f'output/pdf/{stem}_sheets.pdf').pages[1].extract_text()
        self.assertIn('1:300',text)
        self.assertIn('メインデッキ付近',text)
        self.assertIn('LANDMARK-R04',text)
        for label in ('公式案内: メイン150 m / トップ250 m','施工GL',
                      '公式案内値との換算・完成面実測ではない。','床との対応'):
            self.assertIn(label,text)

    def test_skytree_deck_and_sloping_galleria_details_keep_actual_geometry_and_editable_levels(self):
        metadata=json.loads((ROOT/'output/review/tokyo_skytree_drawings.json').read_text())
        row=next(row for row in metadata['drawings'] if row['id']=='elevation')
        self.assertEqual({detail['id'] for detail in row['details']},{'tembo_deck','tembo_galleria'})
        doc=ezdxf.readfile(ROOT/row['dxf'])
        self.assertEqual(len(list(doc.modelspace().query('DIMENSION'))),3)
        layout=doc.layouts.get('LANDMARK_A3_1_3000')
        detail_viewports=[v for v in layout.query('VIEWPORT')
                          if v.dxf.id>1 and round(v.dxf.view_height/v.dxf.height)==500]
        self.assertEqual(len(detail_viewports),2)
        for detail in row['details']:
            prefix=f'decks:{detail["id"]}_'
            self.assertEqual(detail['source_part_prefix'],prefix)
            self.assertTrue(any(name.startswith(prefix) for name in detail['source_parts']))
            self.assertTrue(all(name.startswith(prefix) or name.startswith(('structure:','core:'))
                                for name in detail['source_parts']))
            self.assertEqual(detail['levels_mm'],[340000,345000,350000]
                             if detail['id']=='tembo_deck' else [445000,450000])
            viewport=next(v for v in detail_viewports
                          if abs(v.dxf.view_center_point.y-detail['view_center_mm'][1])<1e-6)
            self.assertEqual(set(viewport.frozen_layers),{'D-STR-DIM','D-STR-TXT','D-BMK-AXIS'})
        paper_text=' '.join(entity.dxf.text for entity in layout.query('TEXT'))
        for label in ('340,000','345,000','350,000','445,000','450,000','上昇する回廊'):
            self.assertIn(label,paper_text)
        svg=ET.fromstring((ROOT/row['svg']).read_text())
        insets={node.attrib['data-detail-id']:node for node in svg.iter() if 'data-detail-id' in node.attrib}
        self.assertEqual(set(insets),{'tembo_deck','tembo_galleria'})
        self.assertTrue(all('clip-path' in node.attrib and len(node)>5 for node in insets.values()))
        sys.path.insert(0,str(ROOT/'src'))
        from lib.tower_geometry import component_specs
        ramps=[part for part in component_specs('tokyo-skytree')
               if part['kind']=='loft3d' and part['name'].startswith('decks:tembo_galleria_')
               and part.get('role')=='galleria_ramp']
        self.assertTrue(ramps,'The saved detail must include the actual inclined CAD ramp.')
        ramp=ramps[len(ramps)//2]
        expected={(round(point[0],6),round(point[2],6))
                  for section in ramp['sections'] for point in section}
        self.assertGreater(len({point[1] for point in expected}),2)
        saved=[]
        for entity in doc.modelspace().query('LWPOLYLINE'):
            if entity.has_xdata('TOWER_PART') and entity.get_xdata('TOWER_PART')[0].value==ramp['name']:
                saved.extend(entity.get_points('xy'))
        actual={(round(x,6),round(y,6)) for x,y in saved}
        self.assertEqual(actual,expected,'DXF must project actual 3D vertices, not a levelled substitute.')

    def test_tokyo_steel_nodes_are_catalogued_actual_local_projections_with_native_dimensions(self):
        sys.path.insert(0,str(ROOT/'src'))
        from lib.tower_geometry import component_specs,geometry_manifest
        nodes=geometry_manifest('tokyo-tower')['steel_nodes']
        by_id={node['id']:node for node in nodes}
        parts={part['name']:part for part in component_specs('tokyo-tower')}
        metadata=json.loads((ROOT/'output/review/tokyo_tower_drawings.json').read_text())
        row=next(row for row in metadata['drawings'] if row['id']=='steel-nodes')
        self.assertEqual(row['dxf'],'DXF/tokyo_tower_steel_nodes.dxf')
        self.assertEqual(len(row['sections']),20)
        self.assertEqual({node['id'] for node in row['node_index']},set(by_id))
        self.assertEqual({detail['id'] for detail in row['details']},{'TT-N01','TT-N05','TT-N13','TT-N17'})
        doc=ezdxf.readfile(ROOT/row['dxf'])
        self.assertFalse(doc.audit().has_errors)
        dimensions=list(doc.modelspace().query('DIMENSION'))
        expected_count=sum(len(by_id[detail['id']]['feature_dimensions']) for detail in row['details'])
        self.assertEqual(len(dimensions),expected_count)
        self.assertEqual(len(row['dimensions_mm']),expected_count)
        for actual,expected in zip(dimensions,row['dimensions_mm']):
            self.assertAlmostEqual(actual.get_measurement(),expected,places=5)
        layout=doc.layouts.get(f'LANDMARK_A3_1_{row["scale"]}')
        viewports=[viewport for viewport in layout.query('VIEWPORT') if viewport.dxf.id>1]
        self.assertEqual(len(viewports),5)
        self.assertTrue(all(viewport.dxf.flags & 16384 for viewport in viewports))
        self.assertEqual(sorted(round(v.dxf.view_height/v.dxf.height) for v in viewports),
                         sorted([row['scale'],*[detail['scale'] for detail in row['details']]]))
        paper_text=' '.join(entity.dxf.text for entity in layout.query('TEXT'))
        for ident in by_id:self.assertIn(ident,paper_text)
        self.assertIn('全て仮定',paper_text)
        for detail in row['details']:
            node=by_id[detail['id']];frame=node['local_frame'];translation=detail['native_translation_mm']
            self.assertEqual(detail['node_part_names'],node['part_names'])
            self.assertEqual(detail['plate_thickness_mm'],node['parameters']['plate_thickness_mm'])
            self.assertFalse(detail['small_parts_omitted'])
            self.assertTrue(all(name in detail['source_parts'] for name in node['part_names']))
            plate=next(parts[name] for name in node['part_names'] if parts[name]['steel_detail_kind']=='plate')
            expected=set()
            for section in plate['sections']:
                for point in section:
                    delta=[point[i]-frame['origin_mm'][i] for i in range(3)]
                    expected.add(tuple(round(sum(delta[i]*frame[axis][i] for i in range(3))+translation[j],5)
                                       for j,axis in enumerate(('u','v'))))
            saved=set();saved_names=set()
            for entity in doc.modelspace().query('LWPOLYLINE'):
                if not entity.has_xdata('STEEL_NODE') or entity.get_xdata('STEEL_NODE')[0].value!=node['id']:continue
                name=entity.get_xdata('TOWER_PART')[0].value;saved_names.add(name)
                if name==plate['name']:saved.update((round(x,5),round(y,5)) for x,y in entity.get_points('xy'))
                if name in detail['context_part_names']:
                    x1,y1,x2,y2=detail['bounds_mm']
                    for x,y in entity.get_points('xy'):
                        self.assertTrue(x1-1e-5<=x<=x2+1e-5 and y1-1e-5<=y<=y2+1e-5)
            self.assertEqual(saved,expected,'The tilted source plate must be projected without changing its real dimensions.')
            self.assertTrue(set(node['part_names'])<=saved_names)
            for feature in detail['feature_dimensions']:
                points=feature['points_mm']
                expected_length=sqrt(sum((points[1][i]-points[0][i])**2 for i in range(3)))
                self.assertAlmostEqual(feature['measurement_mm'],expected_length,places=6)
                parameter='dimensioned_plate_width_mm' if feature['kind']=='plate_width' else 'rivet_pitch_mm'
                self.assertAlmostEqual(expected_length,node['parameters'][parameter],places=5)
        svg=ET.fromstring((ROOT/row['svg']).read_text())
        ids={element.attrib['data-detail-id'] for element in svg.iter() if 'data-detail-id' in element.attrib}
        self.assertEqual(ids,{'node-index','TT-N01','TT-N05','TT-N13','TT-N17'})
        pdf_text=PdfReader(ROOT/'output/pdf/tokyo_tower_sheets.pdf').pages[2].extract_text()
        for label in ('鋼接合部・節点詳細','解釈配置','完成面未測量','未測量・未計算'):
            self.assertIn(label,pdf_text)
        for detail in row['details']:
            self.assertIn(f'板厚 t={detail["plate_thickness_mm"]:g}',pdf_text)
            for feature in detail['feature_dimensions']:
                self.assertIn(f'{feature["measurement_mm"]:,.1f}',pdf_text)


class TowerProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'src'))
        import generate_tower_plans
        cls.module=generate_tower_plans

    def test_sloped_loft3d_projection_preserves_every_real_vertex(self):
        part={'group':'decks','name':'decks:tembo_galleria_projection_fixture','kind':'loft3d',
              'color':'#778899','sections':[
                  [[0,0,10],[200,0,12],[200,20,13],[0,20,11]],
                  [[0,0,30],[200,0,32],[200,20,33],[0,20,31]] ]}
        for view,axis in [('plan',1),('elevation',2)]:
            drawing=self.module._DetailProjection('tokyo-skytree',1,(0,0));drawing.view=view
            self.module.draw_components(drawing,[part])
            points={tuple(point) for operation in drawing.operations for point in operation['points']}
            self.assertEqual(points,{(point[0],point[axis]) for section in part['sections'] for point in section})
        self.assertEqual(self.module._projected_bounds(part),(0,10,200,33))

    def test_main_deck_filter_does_not_match_maintenance_names(self):
        level=self.module.TOWERS['tokyo-tower']['deck_levels_mm'][0]
        candidates=[{'group':'decks','name':name,'kind':'box','bounds':[-100,-100,level-100,100,100,level+100],
                     'color':'#778899'} for name in ['decks:main_test','decks:maintenance_test']]
        drawing=self.module.TowerDrawing('tokyo-tower','elevation',1500,(130,28))
        with patch.object(self.module,'_drawing_parts',return_value=candidates):
            self.module.add_main_deck_detail(drawing)
        self.assertEqual(drawing.details[0]['source_parts'],['decks:main_test'])

    def test_tokyo_notes_keep_official_guidance_separate_from_interpreted_model_positions(self):
        for view in ('plan','elevation'):
            drawing=self.module.TowerDrawing('tokyo-tower',view,1500,(130,28))
            text=' '.join(operation['text'] for operation in drawing.operations if operation['kind']=='text')
            self.assertIn('150 m',text)
            self.assertIn('250 m',text)
            self.assertIn('施工GL',text)
            self.assertIn('125,000',text)
            self.assertIn('223,550',text)
            self.assertIn('床',text)
            self.assertIn('仮定',text)
            self.assertIn('公式案内値との換算・完成面実測ではない。',text)

    def test_local_node_projection_is_orthographic_and_context_clipping_preserves_real_points(self):
        frame={'origin_mm':[10,20,30],'u':[.6,.8,0],'v':[0,0,1]}
        self.assertEqual(self.module._local_projection([16,28,35],frame),(10,5))
        polygon=[(-20,-10),(20,-10),(20,10),(-20,10)]
        result=self.module._clip_polygon(polygon,[-5,-3,7,4])
        self.assertEqual(set(result),{(-5,-3),(7,-3),(7,4),(-5,4)})


if __name__=='__main__':
    unittest.main()
