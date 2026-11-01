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
                    'revision':'LANDMARK-R07'},
    'tokyo_skytree': {'height':634000, 'decks':[350000,450000],
                      'roof_levels':[375000],
                      'base_dimension':68000, 'name':'東京スカイツリー', 'elevation_scale':3000,
                      'revision':'LANDMARK-R05'},
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
                self.assertEqual(len(dimensions),3+len(values.get('roof_levels',[])))
                self.assertEqual([round(float(d.get_measurement())) for d in dimensions],
                                 [values['height'],*values['decks'],*values.get('roof_levels',[])])
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
                    extra=[300,400,1250] if stem=='tokyo_tower' else [750,500]
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
                self.assertEqual(len(metadata['drawings']),3)
                detail_source='tokyo_tower_detail' if stem=='tokyo_tower' else 'skytree_detail'
                expected_sources={
                    'src/lib/tower_geometry.py',f'src/lib/{detail_source}.py',
                    'src/generate_tower_plans.py'}
                if stem=='tokyo_tower':expected_sources.add('src/lib/tokyo_tower_steel.py')
                else:expected_sources.add('src/lib/skytree_outline.py')
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
                self.assertEqual(len(reader.pages),3)
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
                for level in [*values['decks'],*values.get('roof_levels',[])]:self.assertIn(f'{level:,}',elevation)

    def test_skytree_equipment_roof_has_its_own_native_dimension_and_metadata(self):
        metadata=json.loads((ROOT/'output/review/tokyo_skytree_drawings.json').read_text())
        self.assertEqual(metadata['roof_levels_mm'],[375000])
        row=next(row for row in metadata['drawings'] if row['id']=='elevation')
        self.assertEqual(row['roof_levels_mm'],[375000])
        self.assertEqual(sorted(row['dimensions_mm']),[350000,375000,450000,634000])
        detail=next(detail for detail in row['details'] if detail['id']=='tembo_deck')
        self.assertEqual(detail['levels_mm'],[340000,345000,350000])
        self.assertEqual((detail['scale'],detail['view_center_mm'],detail['paper_bounds_mm']),
                         (750,[0,354000],[257,134,394,198]))
        self.assertEqual(detail['bounds_mm'],[-51375,330000,51375,378000])
        text=PdfReader(ROOT/'output/pdf/tokyo_skytree_sheets.pdf').pages[1].extract_text()
        for label in ('設備屋上','375,000','展望床ではない。','1:750'):
            self.assertIn(label,text)

    def test_tokyo_deck_detail_reuses_locked_native_projection_without_duplicate_dimensions(self):
        stem='tokyo_tower'
        metadata=json.loads((ROOT/f'output/review/{stem}_drawings.json').read_text())
        row=next(row for row in metadata['drawings'] if row['id']=='elevation')
        self.assertEqual({detail['id'] for detail in row['details']},{'main_deck','top_deck','antenna'})
        detail=next(detail for detail in row['details'] if detail['id']=='main_deck')
        self.assertEqual(detail['scale'],300)
        self.assertEqual(detail['view_center_mm'],[0,125000])
        self.assertEqual(detail['paper_bounds_mm'],[257,139,394,195])
        self.assertEqual(detail['source_part_prefix'],'decks:main_')
        self.assertEqual(detail['levels_mm'],[120000,125000])
        self.assertEqual(detail['source_geometry_revision'],'LANDMARK-R07')
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
        self.assertIn('LANDMARK-R07',text)
        for label in ('公式案内: メイン150 m / トップ250 m','施工GL',
                      '公式案内値との換算・完成面実測ではない。','独立平面',
                      'H11 27×27 / H12 28×28 m','ST支柱□450','1:400','1:1250'):
            self.assertIn(label,text)

    def test_tokyo_upper_details_retain_native_sources_and_the_complete_antenna_zone(self):
        sys.path.insert(0,str(ROOT/'src'))
        from generate_tower_plans import _projected_bounds
        from lib.tower_geometry import component_specs
        parts={part['name']:part for part in component_specs('tokyo-tower')}
        metadata=json.loads((ROOT/'output/review/tokyo_tower_drawings.json').read_text())
        row=next(row for row in metadata['drawings'] if row['id']=='elevation')
        details={detail['id']:detail for detail in row['details']}
        expected={
            'top_deck':(400,[0,227000],[257,65,326,120],'decks:top_'),
            'antenna':(1250,[0,285500],[334,40,394,120],'antenna:'),
        }
        doc=ezdxf.readfile(ROOT/row['dxf'])
        viewports=[v for v in doc.layouts.get('LANDMARK_A3_1_1500').query('VIEWPORT') if v.dxf.id>1]
        for ident,(scale,center,paper,prefix) in expected.items():
            with self.subTest(detail=ident):
                detail=details[ident]
                self.assertEqual((detail['scale'],detail['view_center_mm'],detail['paper_bounds_mm'],
                                  detail['source_part_prefix']),(scale,center,paper,prefix))
                viewport=next(v for v in viewports if round(v.dxf.view_height/v.dxf.height)==scale)
                self.assertEqual(set(viewport.frozen_layers),{'D-STR-DIM','D-STR-TXT','D-BMK-AXIS'})
                self.assertAlmostEqual(viewport.dxf.view_center_point.y,center[1])
                x1,z1,x2,z2=detail['bounds_mm']
                target=[parts[name] for name in detail['source_parts'] if name.startswith(prefix)
                        and parts[name].get('role') not in ('deck_bracket','deck_support_ring')]
                self.assertTrue(target)
                self.assertTrue(all(name.startswith((prefix,'structure:','core:')) for name in detail['source_parts']))
                for part in target:
                    a,b,c,d=_projected_bounds(part)
                    self.assertTrue(x1<=a<=c<=x2 and z1<=b<=d<=z2,part['name'])
        self.assertTrue(any(parts[name]['kind']=='rhs' for name in details['antenna']['source_parts']
                            if name.startswith('antenna:')),'The ST BOX must remain native hollow geometry.')

    def test_skytree_deck_and_sloping_galleria_details_keep_actual_geometry_and_editable_levels(self):
        metadata=json.loads((ROOT/'output/review/tokyo_skytree_drawings.json').read_text())
        row=next(row for row in metadata['drawings'] if row['id']=='elevation')
        self.assertEqual({detail['id'] for detail in row['details']},{'tembo_deck','tembo_galleria'})
        doc=ezdxf.readfile(ROOT/row['dxf'])
        self.assertEqual(len(list(doc.modelspace().query('DIMENSION'))),4)
        layout=doc.layouts.get('LANDMARK_A3_1_3000')
        detail_viewports=[v for v in layout.query('VIEWPORT')
                          if v.dxf.id>1 and round(v.dxf.view_height/v.dxf.height) in (500,750)]
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
        for label in ('340,000','345,000','350,000','445,000','450,000','最高451,200'):
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

    def test_skytree_structure_page_uses_actual_kanae_groups_and_native_model_intervals(self):
        sys.path.insert(0,str(ROOT/'src'))
        from lib.tower_geometry import component_specs
        parts={part['name']:part for part in component_specs('tokyo-skytree')}
        metadata=json.loads((ROOT/'output/review/tokyo_skytree_drawings.json').read_text())
        row=next(row for row in metadata['drawings'] if row['id']=='structure-zones')
        self.assertEqual(row['dxf'],'DXF/tokyo_skytree_structure_zones.dxf')
        self.assertEqual(row['dimensions_mm'],[50000,12500,25000])
        self.assertEqual(row['projection_sampling']['circular_segments'],24)
        self.assertEqual({section['id'] for section in row['sections']},{'kanae-base','kanae-module'})
        for section in row['sections']:
            self.assertTrue(section['source_parts'])
            self.assertTrue(all(name in parts for name in section['source_parts']))
        detail=row['details'][0]
        self.assertEqual(detail['id'],'kanae-module')
        self.assertEqual(detail['levels_mm'],[0,12500,25000])
        wing_roles={'base_wing_chord','base_wing_horizontal','base_wing_brace'}
        for section in row['sections']:
            self.assertEqual(set(section['scope_i18n']),{'zh','ja','en'})
        base=next(section for section in row['sections'] if section['id']=='kanae-base')
        wing_names={name for name,part in parts.items() if part.get('role') in wing_roles}
        self.assertTrue(wing_names,'The base page needs the real three-face wing members.')
        self.assertTrue(wing_names<=set(base['source_parts']))
        self.assertEqual({parts[name]['wing_face'] for name in wing_names},{0,1,2})
        selected=[parts[name] for name in detail['source_parts']]
        self.assertTrue(all((part.get('role') in wing_roles and part.get('wing_root_group')==0)
                            or (part.get('role') in {'kanae_chord','kanae_horizontal','kanae_brace'}
                                and part.get('kanae_group')==0) for part in selected))
        selected_wings=[part for part in selected if part.get('role') in wing_roles]
        self.assertTrue(selected_wings)
        self.assertEqual({part['wing_side'] for part in selected_wings},{'left','right'})
        horizontals=[parts[name] for name in detail['source_parts'] if parts[name].get('role')=='kanae_horizontal']
        levels={round(point[2]) for part in horizontals for point in (part['start'],part['end'])}
        self.assertTrue({0,12500,25000}<=levels,'Dimensioned levels must belong to real source members.')
        doc=ezdxf.readfile(ROOT/row['dxf'])
        self.assertFalse(doc.audit().has_errors)
        self.assertEqual([round(entity.get_measurement()) for entity in doc.modelspace().query('DIMENSION')],
                         [50000,12500,25000])
        layout=doc.layouts.get(f'LANDMARK_A3_1_{row["scale"]}')
        viewports=[viewport for viewport in layout.query('VIEWPORT') if viewport.dxf.id>1]
        self.assertEqual(len(viewports),2)
        self.assertTrue(all(viewport.dxf.flags & 16384 for viewport in viewports))
        self.assertEqual(sorted(round(v.dxf.view_height/v.dxf.height) for v in viewports),
                         sorted([detail['scale'],750]))
        saved_names={entity.get_xdata('TOWER_PART')[0].value for entity in doc.modelspace()
                     if entity.has_xdata('STRUCTURE_VIEW')}
        self.assertEqual(saved_names,set(detail['source_parts']))
        # A wing must be an exact CAD-owned circular member projection,
        # including both wall rims, rather than decorative sheet linework.
        from generate_tower_plans import _hollow_member_sections,_local_projection
        wing=next(part for part in selected_wings if part['kind']=='tube')
        outside,inside=_hollow_member_sections(wing)
        frame=detail['local_frame'];translation=detail['native_translation_mm']
        expected={tuple(round(value+translation[index],5)
                        for index,value in enumerate(_local_projection(point,frame)))
                  for section in [*outside,inside[0],inside[-1]] for point in section}
        actual={(round(x,5),round(y,5)) for entity in doc.modelspace().query('LWPOLYLINE')
                if entity.has_xdata('STRUCTURE_VIEW') and entity.has_xdata('TOWER_PART')
                and entity.get_xdata('TOWER_PART')[0].value==wing['name']
                for x,y in entity.get_points('xy')}
        self.assertEqual(actual,expected)
        text=PdfReader(ROOT/'output/pdf/tokyo_skytree_sheets.pdf').pages[2].extract_text()
        for label in ('50,000','12,500','25,000','鼎トラス全体の高さを示す寸法ではない。',
                      '方位・断面位置はモデル参照。','鋼管架構の構成','5,000 mm節間',
                      '150/250 m','モデル仮定','3面の翼架構','外周水平材は円管',
                      '中央の開口','付随する翼架構'):
            self.assertIn(label,text)


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
            self.assertIn('H13 29×24 m',text)
            self.assertIn('独立平面',text)
            self.assertNotIn('機械室層',text)
            self.assertIn('JAEE',text)

    def test_plan_notes_stay_inside_the_panel_above_the_separate_footer(self):
        for tower in ('tokyo-tower','tokyo-skytree'):
            drawing=self.module.TowerDrawing(tower,'plan',500,(130,28))
            notes=[op for op in drawing.operations if op['kind']=='text' and op['points'][0]==257]
            self.assertGreater(len(notes),20)
            for note in notes:
                y=note['points'][1];half=note['height']/2
                self.assertGreaterEqual(y-half,40,note['text'])
                self.assertLessEqual(y+half,251,note['text'])

    def test_skytree_inset_source_fixtures_keep_roof_and_obstruction_lens_inside_the_clip(self):
        def box(name,bounds,group='decks',role='deck_roof'):
            return {'group':group,'name':name,'kind':'box','bounds':bounds,'role':role,'color':'#778899'}
        candidates=[
            box('decks:tembo_deck_glazing_fixture',[-24000,-24000,335000,24000,24000,355000],role='glazing'),
            box('decks:tembo_deck_crown_roof_fixture',[-16000,-16000,374650,16000,16000,375000]),
            box('decks:tembo_deck_obstruction_light_lens_fixture',[-150,-150,375300,150,150,375600],role='obstruction_light_lens'),
            box('decks:tembo_galleria_envelope_fixture',[-21000,-21000,443000,21000,21000,460000]),
            box('decks:unrelated_maintenance',[-100,-100,355000,100,100,356000]),
            box('core:context',[-4000,-4000,0,4000,4000,452500],'core','elevator_guide'),
        ]
        drawing=self.module.TowerDrawing('tokyo-skytree','elevation',3000,(130,28))
        with patch.object(self.module,'_drawing_parts',return_value=candidates):
            self.module.add_skytree_details(drawing)
        expected={
            'tembo_deck':(750,[0,354000],[257,134,394,198],'decks:tembo_deck_',candidates[:3]),
            'tembo_galleria':(500,[0,449000],[257,59,394,115],'decks:tembo_galleria_',candidates[3:4]),
        }
        for detail in drawing.details:
            scale,center,paper,prefix,targets=expected[detail['id']]
            self.assertEqual((detail['scale'],detail['view_center_mm'],detail['paper_bounds_mm'],
                              detail['source_part_prefix']),(scale,center,paper,prefix))
            self.assertTrue({part['name'] for part in targets}<=set(detail['source_parts']))
            self.assertNotIn(candidates[4]['name'],detail['source_parts'])
            x1,z1,x2,z2=detail['bounds_mm']
            for part in targets:
                a,b,c,d=self.module._projected_bounds(part)
                self.assertTrue(x1<=a<=c<=x2 and z1<=b<=d<=z2,part['name'])
        for op in drawing.operations:
            if op['kind']!='text':continue
            x,y=op['points']
            for _,_,(x1,y1,x2,y2),_,_ in expected.values():
                self.assertFalse(x1<=x<=x2 and y1<=y<=y2,op['text'])

    def test_skytree_equipment_roof_source_fixture_does_not_become_an_observation_floor(self):
        with patch.object(self.module,'_drawing_parts',return_value=[]):
            drawing=self.module.build_elevation('tokyo-skytree')
        self.assertEqual(self.module.TOWERS['tokyo-skytree']['deck_levels_mm'],[350000,450000])
        self.assertEqual([round(d.get_measurement()) for d in drawing.msp.query('DIMENSION')],
                         [634000,350000,450000,375000])
        self.assertEqual(next(detail for detail in drawing.details if detail['id']=='tembo_deck')['levels_mm'],
                         [340000,345000,350000])
        text=' '.join(op['text'] for op in drawing.operations if op['kind']=='text')
        for value in ('設備屋上（参考）','375,000','展望床ではない。','315 m/D32','H495 m/D18','H497 m','TMD頂帽'):
            self.assertIn(value,text)
        for detail in drawing.details:
            x1,y1,x2,y2=detail['paper_bounds_mm']
            for op in drawing.operations:
                if op['kind']=='text':
                    x,y=op['points'];self.assertFalse(x1<=x<=x2 and y1<=y<=y2,op['text'])

    def test_skytree_two_insets_include_every_named_deck_and_gallery_exterior(self):
        drawing=self.module.build_elevation('tokyo-skytree')
        parts=self.module._drawing_parts('tokyo-skytree')
        for detail in drawing.details:
            targets=[part for part in parts if part['name'].startswith(detail['source_part_prefix'])]
            self.assertTrue(targets)
            self.assertTrue({part['name'] for part in targets}<=set(detail['source_parts']))
            x1,z1,x2,z2=detail['bounds_mm']
            for part in targets:
                a,b,c,d=self.module._projected_bounds(part)
                self.assertTrue(x1<=a<=c<=x2 and z1<=b<=d<=z2,part['name'])

    def test_skytree_structure_notes_keep_dense_upper_tiers_out_of_lower_native_dimensions(self):
        drawing=self.module.StructureZoneDrawing('tokyo-skytree','structure-zones',750,(0,0))
        text=' '.join(op['text'] for op in drawing.operations if op['kind']=='text')
        self.assertIn('315 m以高は5,000 mm節間',text)
        self.assertIn('150/250 mの密度切替位置もモデル仮定',text)
        self.assertEqual(drawing.dimensions,[])

    def test_skytree_group_detail_follows_wing_root_ownership_instead_of_name_prefix(self):
        def member(name,role,**data):
            return {'group':'structure','name':name,'kind':'tube','start':[0,0,0],
                    'end':[0,0,12500],'radius':200,'wall_thickness_mm':16,'role':role,**data}
        group=member('structure:kanae_01_fixture','kanae_chord',kanae_group=0)
        left=member('structure:base_wing_f0_left_fixture','base_wing_chord',wing_root_group=0)
        right=member('structure:base_wing_f2_right_fixture','base_wing_brace',wing_root_group=0)
        unrelated=member('structure:kanae_01_name_collision','base_wing_brace',wing_root_group=1,kanae_group=0)
        upper=member('structure:base_wing_upper_fixture','base_wing_horizontal',wing_root_group=0)
        upper['start'][2]=37500;upper['end'][2]=50000
        self.assertEqual(self.module._structure_module_parts([group,left,right,unrelated,upper]),
                         [group,left,right])

    def test_skytree_structure_insets_include_all_real_wings_without_hiding_their_spread(self):
        drawing=self.module.build_structure_zones()
        parts={part['name']:part for part in self.module._drawing_parts('tokyo-skytree')}
        detail=drawing.details[0]
        roles={'base_wing_chord','base_wing_horizontal','base_wing_brace'}
        all_wings={name for name,part in parts.items() if part.get('role') in roles}
        self.assertTrue(all_wings)
        self.assertTrue(all_wings<=set(drawing.index_viewport['source_parts']))
        own_wings={name for name in all_wings if parts[name]['wing_root_group']==0
                   and self.module._projected_bounds(parts[name])[1]<=25000}
        self.assertTrue(own_wings<=set(detail['source_parts']))
        # Visible source vertices retain their genuine local coordinates and
        # fit the inset horizontally even as wings widen the old group view.
        x1,_,x2,_=detail['bounds_mm'];frame=detail['local_frame']
        translation=detail['native_translation_mm']
        for name in detail['source_parts']:
            part=parts[name]
            outside,_=self.module._hollow_member_sections(part)
            for section in outside:
                for point in section:
                    if 0<=point[2]<=25000:
                        x=self.module._local_projection(point,frame)[0]+translation[0]
                        self.assertTrue(x1<=x<=x2,name)
        self.assertEqual(drawing.dimensions,[50000,12500,25000])
        self.assertEqual(len(drawing.details),1)
        for op in drawing.operations:
            if op['kind']!='text':continue
            x,y=op['points']
            for bounds in (drawing.index_viewport['paper_bounds_mm'],detail['paper_bounds_mm']):
                left,bottom,right,top=bounds
                self.assertFalse(left<=x<=right and bottom<=y<=top,op['text'])

    def test_skytree_exterior_ring_projection_preserves_circular_hollow_source_sections(self):
        parts=self.module._drawing_parts('tokyo-skytree')
        exterior=[part for part in parts if part.get('role')=='outer_horizontal'
                  and part.get('ring_layer')=='outer']
        self.assertTrue(exterior)
        self.assertEqual({part['kind'] for part in exterior},{'tube'})
        part=exterior[0]
        outside,inside=self.module._hollow_member_sections(part)
        drawing=self.module._DetailProjection('tokyo-skytree',1,(0,0))
        self.module.draw_components(drawing,[part])
        actual={tuple(point) for operation in drawing.operations for point in operation['points']}
        expected={(point[0],point[2]) for section in [*outside,inside[0],inside[-1]] for point in section}
        self.assertEqual(actual,expected)
        # Internal rings remain separately specified, rather than forcing
        # every rectangular hollow engineering primitive to become circular.
        self.assertTrue(any(part['kind']=='rhs' and part.get('ring_layer')=='inner' for part in parts))

    def test_tokyo_three_insets_keep_all_target_geometry_inside_their_viewports(self):
        drawing=self.module.build_elevation('tokyo-tower')
        parts=self.module._drawing_parts('tokyo-tower')
        expected={
            'main_deck':(300,[0,125000],[257,139,394,195],'decks:main_'),
            'top_deck':(400,[0,227000],[257,65,326,120],'decks:top_'),
            'antenna':(1250,[0,285500],[334,40,394,120],'antenna:'),
        }
        self.assertEqual(len(list(drawing.msp.query('DIMENSION'))),3)
        self.assertEqual({detail['id'] for detail in drawing.details},set(expected))
        for detail in drawing.details:
            with self.subTest(detail=detail['id']):
                scale,center,paper,prefix=expected[detail['id']]
                self.assertEqual((detail['scale'],detail['view_center_mm'],detail['paper_bounds_mm'],
                                  detail['source_part_prefix']),(scale,center,paper,prefix))
                # Supporting braces continue below the local deck window;
                # the complete enclosure, floors and equipment must fit.
                targets=[part for part in parts if part['name'].startswith(prefix)
                         and part.get('role') not in ('deck_bracket','deck_support_ring')]
                self.assertTrue(targets)
                self.assertTrue({part['name'] for part in targets}<=set(detail['source_parts']))
                x1,z1,x2,z2=detail['bounds_mm']
                for part in targets:
                    a,b,c,d=self.module._projected_bounds(part)
                    self.assertTrue(x1<=a<=c<=x2 and z1<=b<=d<=z2,part['name'])
                detail_op=next(op for op in drawing.operations
                               if op['kind']=='detail' and op['id']==detail['id'])
                self.assertEqual(detail_op['points'],paper)
                self.assertTrue(detail_op['operations'])
        # Clips constrain contextual members only; labels remain outside all
        # three windows, so future note changes cannot obscure their geometry.
        for op in drawing.operations:
            if op['kind']!='text':continue
            x,y=op['points']
            for _,_,(x1,y1,x2,y2),_ in expected.values():
                self.assertFalse(x1<=x<=x2 and y1<=y<=y2,op['text'])

    def test_tokyo_antenna_detail_prefix_includes_equipment_but_rejects_other_decks(self):
        fixture=lambda name,z,group:{'group':group,'name':name,'kind':'box',
                                     'bounds':[-100,-100,z-100,100,100,z+100],'color':'#778899'}
        candidates=[fixture('antenna:equipment_h25',238600,'antenna'),
                    fixture('antenna:sg_external_frame',280000,'antenna'),
                    fixture('antenna:st_tip',333000,'antenna'),
                    fixture('structure:upper_context',245000,'structure'),
                    fixture('decks:maintenance_outside_prefix',280000,'decks')]
        drawing=self.module.TowerDrawing('tokyo-tower','elevation',1500,(130,28))
        with patch.object(self.module,'_drawing_parts',return_value=candidates):
            self.module.add_tokyo_upper_details(drawing)
        detail=next(detail for detail in drawing.details if detail['id']=='antenna')
        self.assertEqual(detail['source_parts'],[part['name'] for part in candidates[:-1]])

    def test_local_node_projection_is_orthographic_and_context_clipping_preserves_real_points(self):
        frame={'origin_mm':[10,20,30],'u':[.6,.8,0],'v':[0,0,1]}
        self.assertEqual(self.module._local_projection([16,28,35],frame),(10,5))
        polygon=[(-20,-10),(20,-10),(20,10),(-20,10)]
        result=self.module._clip_polygon(polygon,[-5,-3,7,4])
        self.assertEqual(set(result),{(-5,-3),(7,-3),(7,4),(-5,4)})

    def test_circular_hollow_drawings_retain_wall_rims_and_real_loft_stations(self):
        tube={'group':'structure','name':'structure:tube_fixture','kind':'tube',
              'start':[0,0,0],'end':[0,0,1000],'radius':100,'wall_thickness_mm':10}
        drawing=self.module._DetailProjection('tokyo-skytree',1,(0,0));drawing.view='plan'
        self.module.draw_components(drawing,[tube])
        radii={round(sqrt(x*x+y*y),6) for operation in drawing.operations for x,y in operation['points']}
        self.assertEqual(radii,{90,100})
        self.assertEqual(self.module._projected_bounds(tube),(-100,0,100,1000))
        inclined={**tube,'start':[10,20,30],'end':[310,420,1230]}
        outside,inside=self.module._hollow_member_sections(inclined)
        axis=[inclined['end'][i]-inclined['start'][i] for i in range(3)]
        for rings,radius in ((outside,100),(inside,90)):
            for center,section in zip((inclined['start'],inclined['end']),rings):
                for point in section:
                    offset=[point[i]-center[i] for i in range(3)]
                    self.assertAlmostEqual(sum(offset[i]*axis[i] for i in range(3)),0,places=7)
                    self.assertAlmostEqual(sqrt(sum(value*value for value in offset)),radius,places=7)
        loft={'group':'structure','name':'structure:loft_fixture','kind':'tube_loft','sections':[
            {'z':0,'center':[0,0],'radius':100,'wall_thickness_mm':10},
            {'z':500,'center':[80,0],'radius':90,'wall_thickness_mm':10},
            {'z':1000,'center':[100,0],'radius':70,'wall_thickness_mm':8}]}
        outer,inner=self.module._hollow_member_sections(loft)
        self.assertEqual([len(section) for section in outer],[24,24,24])
        drawing=self.module._DetailProjection('tokyo-skytree',1,(0,0))
        self.module.draw_components(drawing,[loft])
        expected={(point[0],point[2]) for section in [*outer,inner[0],inner[-1]] for point in section}
        actual={tuple(point) for operation in drawing.operations for point in operation['points']}
        self.assertEqual(actual,expected)
        self.assertEqual(self.module._projected_bounds(loft),(-100,0,170,1000))

    def test_rectangular_hollow_drawing_uses_backend_basis_and_open_inner_rectangle(self):
        rhs={'group':'structure','name':'structure:rhs_fixture','kind':'rhs','start':[0,0,0],
             'end':[0,0,1000],'width_mm':400,'depth_mm':600,'wall_thickness_mm':20}
        outer,inner=self.module._hollow_member_sections(rhs)
        self.assertEqual(set(tuple(point[:2]) for point in outer[0]),{(-300,-200),(300,-200),(300,200),(-300,200)})
        self.assertEqual(set(tuple(point[:2]) for point in inner[0]),{(-280,-180),(280,-180),(280,180),(-280,180)})
        drawing=self.module._DetailProjection('tokyo-skytree',1,(0,0));drawing.view='plan'
        self.module.draw_components(drawing,[rhs])
        actual={tuple(point) for operation in drawing.operations for point in operation['points']}
        self.assertEqual(actual,{tuple(point[:2]) for section in [*outer,*inner] for point in section})
        self.assertEqual(self.module._projected_bounds(rhs),(-300,0,300,1000))


if __name__=='__main__':
    unittest.main()
