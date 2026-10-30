"""Parametric landmark appearance models, millimetres and Z-up.

Explicitly cited controls and historical reference dimensions are recorded
separately from assumed section assignments, interpolation, glazing, foundations
and all other unreferenced geometry. This is
original concept geometry, not surveyed or original architectural CAD.

The parameter and component-specification API is dependency-free. build123d
is imported only when ``tower_assembly`` actually creates CAD solids; drawings
and tests can read exactly the same specification without a CAD environment.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from math import cos, sin, pi, sqrt

REVISION = 'LANDMARK-R01'
CHECKED_ON = '2026-10-30'
GROUPS = ('base', 'structure', 'core', 'decks', 'antenna')
GROUP_NAMES = {
    'base': {'zh': '基座与地面', 'ja': '基壇・地盤', 'en': 'Base and ground'},
    'structure': {'zh': '塔身与桁架', 'ja': '塔体・トラス', 'en': 'Tower frame'},
    'core': {'zh': '中央核心与竖井', 'ja': '中央コア・シャフト', 'en': 'Central core and shafts'},
    'decks': {'zh': '展望台', 'ja': '展望施設', 'en': 'Observation decks'},
    'antenna': {'zh': '天线与塔尖', 'ja': 'アンテナ・塔頂', 'en': 'Antenna and spire'},
}
TOWERS = {
    'tokyo-tower': {   'file_stem': 'tokyo_tower',
            'revision': 'LANDMARK-R06',
            'names': {'zh': '东京塔', 'ja': '東京タワー', 'en': 'Tokyo Tower'},
            'height_mm': 333000,
            'deck_levels_mm': [125000, 223550],
            'nominal_deck_levels_mm': [150000, 250000],
            'geometry_datum': 'Historical construction-GL controls; H23 is treated as a roof band. Current '
                              'nominal150m/250m visitor names remain separate; present finished-floor conversion and '
                              'facade mapping are not surveyed.',
            'base_width_mm': 80000,
            'detail': {   'deck_appearance': {   'main_lower_half_width_mm': 13500.0,
                                                 'main_upper_half_width_mm': 14000.0,
                                                 'main_chamfer_factor': 0.18,
                                                 'main_glass_top_scale': 1.0,
                                                 'main_long_face_bays': 24,
                                                 'main_corner_face_bays': 4,
                                                 'main_mullion_radius_mm': 32.0,
                                                 'main_transom_height_mm': 65.0,
                                                 'main_glass_color': '#284C61',
                                                 'main_soffit_thickness_mm': 180.0,
                                                 'main_fascia_height_mm': 350.0,
                                                 'main_roof_fascia_height_mm': 180.0,
                                                 'main_cleaning_track_radius_mm': 48.0,
                                                 'top_facets': 48,
                                                 'top_glass_color': '#385C6C',
                                                 'top_lower_radius_factor': 0.86,
                                                 'top_glass_radius_factor': 1.0,
                                                 'top_roof_radius_factor': 1.04,
                                                 'top_mullion_radius_mm': 28.0,
                                                 'top_glass_top_offset_mm': 850.0,
                                                 'top_service_platform_mm': 231000.0,
                                                 'top_service_radius_mm': 6800.0,
                                                 'top_service_inner_radius_mm': 4500.0,
                                                 'top_service_rail_height_mm': 1100.0,
                                                 'glass_alpha': 0.72},
                          'antenna_appearance': {   'digital_panel_bottom_mm': 240550.0,
                                                    'digital_group_height_mm': 5300.0,
                                                    'digital_group_gap_mm': 500.0,
                                                    'digital_lower_diameter_mm': 13400.0,
                                                    'digital_upper_diameter_mm': 12876.0,
                                                    'digital_support_diameter_mm': 11800.0,
                                                    'digital_panel_columns': 30,
                                                    'digital_panel_rows': 5,
                                                    'digital_panel_depth_mm': 220.0,
                                                    'digital_panel_azimuth_gap_degrees': 0.25,
                                                    'digital_panel_gap_mm': 50.0,
                                                    'mx_panel_bottom_mm': 237600.0,
                                                    'mx_panel_height_mm': 650.0,
                                                    'mx_panel_row_pitch_mm': 950.0,
                                                    'mx_panel_radius_mm': 6200.0,
                                                    'sg_bay_height_mm': 4500.0,
                                                    'sg_inner_half_width_low_mm': 1500.0,
                                                    'sg_inner_half_width_high_mm': 500.0,
                                                    'sg_outer_offset_mm': 440.0,
                                                    'sg_inner_chord_radius_mm': 95.0,
                                                    'sg_outer_chord_radius_mm': 105.0,
                                                    'sg_inner_brace_radius_mm': 40.0,
                                                    'sg_outer_brace_radius_mm': 50.0,
                                                    'sg_link_radius_mm': 48.0,
                                                    'sg_link_layer_offset_mm': 160.0,
                                                    'st_width_mm': 450.0,
                                                    'st_depth_mm': 450.0,
                                                    'st_wall_mm': 16.0,
                                                    'st_equipment_levels_mm': [   315000.0,
                                                                                  318000.0,
                                                                                  321000.0,
                                                                                  324000.0,
                                                                                  327000.0,
                                                                                  330000.0],
                                                    'st_equipment_half_width_mm': 380.0},
                          'main_floor_half_widths_mm': [13500.0, 14000.0],
                          'historical_section_controls_mm': {   'H11': {'width': 27000, 'depth': 27000},
                                                                'H12': {'width': 28000, 'depth': 28000},
                                                                'H13': {   'width': 29000,
                                                                           'depth': 24000,
                                                                           'status': 'Historical H13 plan recorded '
                                                                                     'separately; its function and '
                                                                                     'mapping to the current facade '
                                                                                     'remain unverified'},
                                                                'H23': {   'diameter': 13000,
                                                                           'datum_scope': 'Historical structural roof '
                                                                                          'band; not a verified present '
                                                                                          'visitor finished-floor '
                                                                                          'elevation.'}},
                          'leg_stations_mm': [0, 9000, 18000, 28000, 40000, 52000, 65000, 80000],
                          'foot_town_roof_mm': 18300,
                          'arch_crown_mm': 40000,
                          'lower_belt_levels_mm': [40000, 53000, 66000, 80000],
                          'main_floor_levels_mm': [120000, 125000],
                          'steel_main_support_z_mm': 115000,
                          'external_stair_risers': 600,
                          'external_stair_flights': 24,
                          'external_stair_tread_mm': 260,
                          'external_stair_bounds_mm': [4700, -8000, 18300, 9300, 1500, 125000],
                          'main_deck_stair_opening_mm': [4700, -8000, 9300, 1800],
                          'glazing_thickness_mm': 90,
                          'member_profiles': 'graded built-up H/I appearance chords; four schematic connection families '
                                             'at twenty selected nodes',
                          'steel_node_count': 20,
                          'steel_profile_families': {   'lower': {   'type': 'H',
                                                                     'width_factor': 1.0,
                                                                     'depth_factor': 0.85,
                                                                     'web_thickness_mm': 24.0,
                                                                     'flange_thickness_mm': 30.0},
                                                        'middle': {   'type': 'H',
                                                                      'width_factor': 0.9,
                                                                      'depth_factor': 0.8,
                                                                      'web_thickness_mm': 18.0,
                                                                      'flange_thickness_mm': 24.0},
                                                        'upper': {   'type': 'I',
                                                                     'width_factor': 0.62,
                                                                     'depth_factor': 1.0,
                                                                     'web_thickness_mm': 14.0,
                                                                     'flange_thickness_mm': 18.0}},
                          'steel_node_families': {   'base': {   'width_mm': 1200.0,
                                                                 'height_mm': 1000.0,
                                                                 'plate_thickness_mm': 30.0,
                                                                 'stiffener_thickness_mm': 16.0,
                                                                 'stiffener_depth_mm': 160.0,
                                                                 'rivet_radius_mm': 18.0,
                                                                 'rivet_projection_mm': 12.0},
                                                     'lower_truss': {   'width_mm': 1100.0,
                                                                        'height_mm': 1200.0,
                                                                        'plate_thickness_mm': 20.0,
                                                                        'stiffener_thickness_mm': 16.0,
                                                                        'stiffener_depth_mm': 140.0,
                                                                        'rivet_radius_mm': 18.0,
                                                                        'rivet_projection_mm': 12.0},
                                                     'splice': {   'width_mm': 620.0,
                                                                   'height_mm': 1050.0,
                                                                   'plate_thickness_mm': 16.0,
                                                                   'stiffener_thickness_mm': 14.0,
                                                                   'stiffener_depth_mm': 100.0,
                                                                   'rivet_radius_mm': 18.0,
                                                                   'rivet_projection_mm': 12.0},
                                                     'deck_support': {   'width_mm': 1100.0,
                                                                         'height_mm': 1000.0,
                                                                         'plate_thickness_mm': 24.0,
                                                                         'stiffener_thickness_mm': 16.0,
                                                                         'stiffener_depth_mm': 180.0,
                                                                         'rivet_radius_mm': 18.0,
                                                                         'rivet_projection_mm': 12.0}},
                          'scope': 'Original appearance detail; route, risers, sections, connections, glass and light '
                                   'positions are schematic assumptions.'},
            'profile': [   [0, 40000],
                           [25000, 30500],
                           [40000, 25000],
                           [53000, 21000],
                           [66000, 18000],
                           [80000, 15500],
                           [100000, 13000],
                           [120000, 10800],
                           [130000, 9900],
                           [150000, 8800],
                           [170000, 7900],
                           [190000, 7000],
                           [210000, 6000],
                           [223550, 3950],
                           [238000, 3600],
                           [252650, 3100]],
            'profile_kind': 'square_half_width',
            'deck_specs': [   {   'id': 'main',
                                  'level_mm': 125000,
                                  'bottom_mm': 119500,
                                  'glass_bottom_mm': 120300,
                                  'top_mm': 130000,
                                  'half_width_mm': 14000,
                                  'support_mm': 115000},
                              {   'id': 'top',
                                  'level_mm': 220550,
                                  'bottom_mm': 219050,
                                  'glass_bottom_mm': 220550,
                                  'top_mm': 223550,
                                  'half_width_mm': 6500,
                                  'support_mm': 216550,
                                  'datum_scope': 'H23 roof GL223550; the internal floor GL220550 and the current facade '
                                                 'correspondence are appearance interpretations, separate from the '
                                                 'operator nominal250m.'}],
            'antenna_start_mm': 252650,
            'antenna_lattice_top_mm': 312600,
            'base_slab_thickness_mm': 2000,
            'source_references': [   {   'title': '山森一之（古河C&B技術部）親局用アンテナ，中継局用送受信アンテナ 2012 p979 Fig5',
                                         'url': 'https://www.jstage.jst.go.jp/article/itej/66/12/66_977/_pdf',
                                         'confirmed_historical_values_mm': {   'upper_array_diameter': 12876,
                                                                               'lower_array_diameter': 13400,
                                                                               'support_diameter': 11800,
                                                                               'each_group_height': 5300,
                                                                               'intergroup_gap': 500},
                                         'confirmed_historical_array_counts': {   'panels_per_row': 30,
                                                                                  'rows_per_group': 5,
                                                                                  'groups': 2},
                                         'reference_notes': 'Manufacturer-authored historical array drawing. Diameters '
                                                            'and group heights are separate from model-fitted absolute '
                                                            'GL, seam widths, thickness, support members and lower '
                                                            'short-array sizes. Historical station/channel assignments '
                                                            'are not current operating-use claims.'},
                                     {   'title': '川上春夫 RFワールド No1 pp42-43 東京タワーの地デジ送信用アンテナ',
                                         'url': 'https://www.rf-world.jp/bn/RFW01/samples/p042-043a.pdf',
                                         'reference_notes': 'Original technical explanation confirms30 panels per row, '
                                                            'five rows and upper/lower groups, with the same dimensioned '
                                                            'geometry. Historic channel text is not reused as current '
                                                            'equipment-use metadata.'},
                                     {   'title': '日本地震工学会掲載 風間了 実在建物の振動性状 p96-97 / 内藤ほか1962 Fig3',
                                         'url': 'https://www.jaee.gr.jp/jp/wp-content/uploads/2015/04/vibration_characteristics.pdf',
                                         'confirmed_historical_values_mm': {   'H11_plan': [27000, 27000],
                                                                               'H12_plan': [28000, 28000],
                                                                               'H13_plan': [29000, 24000],
                                                                               'H23_diameter': 13000},
                                         'reference_notes': 'Historical 1962 paper figure reproduced in the JAEE-hosted '
                                                            'volume (PDF pages105-106, printed96-97). H13 is an '
                                                            'independently recorded historical plan; its function and '
                                                            'mapping to the current facade remain unverified. Original '
                                                            'observations at120m/223m support separating '
                                                            'historical/construction GL from current nominal150m/250m '
                                                            'guidance; no verified conversion is asserted.'},
                                     {   'title': 'LIXIL 東京タワー 2019カーテンウォール改修',
                                         'url': 'https://www.biz-lixil.com/case/curtainwall/B190037/',
                                         'reference_notes': 'Primary supplier exterior photographs inform narrow vertical '
                                                            'mullions, fine transoms, light soffits and exterior '
                                                            'gondola-cleaning tracks. Model bay counts, exact slopes, '
                                                            'frame widths and glass thickness remain appearance '
                                                            'assumptions.'},
                                     {   'title': 'LIXILリニューアル 東京タワー改修前後',
                                         'url': 'https://www.lixil-renewal.co.jp/business/case/archives/15',
                                         'reference_notes': '2019 after-renovation exterior and interior photographs '
                                                            'guide current facade character; no supplier photograph is '
                                                            'redistributed with the model.'},
                                     {   'title': '宮地技報 No18 東京タワー塔体補強報告 p86 図1',
                                         'url': 'https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf',
                                         'confirmed_values_mm': {   'leg_axis_spacing': 80000,
                                                                    'H3_GL': 40000,
                                                                    'H11_GL': 120000,
                                                                    'H23_GL': 223550,
                                                                    'H27_GL': 252650,
                                                                    'tip_GL': 333000},
                                         'reference_notes': 'The model interprets observation-shell positions from '
                                                            'H11/H23 structural bands at GL120000/223550, with an assumed '
                                                            '5000mm main-floor interval. These are not independently '
                                                            'verified visitor finished-floor levels; unlabelled H belts, '
                                                            'widths and arch curvature are traced approximations. '
                                                            'Historical retrofit figure, not a current surveyed as-built '
                                                            'model.'},
                                     {   'title': '宮地技報 No28 東京タワー耐震改修報告 p65 図1',
                                         'url': 'https://www.miyaji-eng.co.jp/technology/newsletter/media/28/no28-p064-070.pdf',
                                         'confirmed_values_mm': {   'support_tower_top_GL': 312600,
                                                                    'replacement_ST_BOX_width': 450},
                                         'reference_notes': 'Later retrofit drawing confirms H27 GL252650 and upper SG/ST '
                                                            'zones. Page66 Fig2 and page69 photograph10 show the external '
                                                            'SG strengthening frame; page66 specifies replacement ST as '
                                                            'a450mm BOX section. Wall thickness, intermediate '
                                                            'bay/equipment positions and joints remain unverified. Its '
                                                            'H23 label reads223500, versus223550 in No18; this model '
                                                            'consistently uses the earlier223550 control, not both.'},
                                     {   'title': 'IHI 東京タワー施工写真',
                                         'url': 'https://www.ihi.co.jp/technology/techinfo/contents_no/1200541_13491.html',
                                         'reference_notes': 'Tokyo Tower construction photograph shows built-up wide '
                                                            'plate chords, lacing and a hierarchy of bracing. Nearby '
                                                            'angle-steel prose refers to Tsutenkaku, not a section '
                                                            'schedule for Tokyo Tower. Exact H/I member sections below '
                                                            'remain appearance assumptions.'},
                                     {   'title': '東京タワー 施設案内',
                                         'url': 'https://www.tokyotower.co.jp/guidance/',
                                         'confirmed_nominal_values_mm': {   'height': 333000,
                                                                            'main_deck': 150000,
                                                                            'top_deck': 250000}},
                                     {   'title': '東京タワー タワペディア',
                                         'url': 'https://www.tokyotower.co.jp/plan/towerpedia/',
                                         'reference_notes': 'Official 270m painting limit excludes the top antenna; this '
                                                            'is not the construction H27 support-tower start. '
                                                            'International Orange and white, with seven schematic bands '
                                                            'above the main deck.'},
                                     {   'title': '東京タワー メインデッキ',
                                         'url': 'https://www.tokyotower.co.jp/maindeck/',
                                         'reference_notes': 'Main Deck has 1F and 2F; the model intermediate floor and '
                                                            'all plan dimensions are schematic.'},
                                     {   'title': '東京タワー オープンエア外階段ウォーク',
                                         'url': 'https://www.tokyotower.co.jp/plan/open_air_stair/',
                                         'reference_notes': 'Outdoor stairs connect Foot Town roof to the Main Deck '
                                                            '(official published guidance150m) with approximately 600 '
                                                            'steps. The model route and flight configuration are original '
                                                            'assumptions.'},
                                     {   'title': '東京タワー フットタウン',
                                         'url': 'https://www.tokyotower.co.jp/foottown/',
                                         'reference_notes': 'Public entrance and rooftop outdoor-stair access inform the '
                                                            'schematic base building; no original floor plan is '
                                                            'reproduced.'},
                                     {   'title': '日本溶接協会 東京スカイツリー製作現場見学雑感（東京タワーとの比較）',
                                         'url': 'https://www-it.jwes.or.jp/we-com/bn/vol_1/sec_2/2-1.pdf',
                                         'reference_notes': 'Page2 describes the original Tokyo Tower as rivet-assembled '
                                                            'SS41 steelwork. This establishes historical connection '
                                                            'character only; model section sizes, twenty selected nodes, '
                                                            'rivet counts, pitch, plate/stiffener sizes and local '
                                                            'coordinates are assumptions, not original drawings or '
                                                            'retrofit design.'},
                                     {   'title': '竹中工務店 東京タワー改修',
                                         'url': 'https://www.takenaka.co.jp/solution/asset/project/07/',
                                         'reference_notes': 'The tower has undergone maintenance and strengthening. This '
                                                            'appearance study does not reconstruct every original or '
                                                            'later connection or certify present-day structural '
                                                            'capacity.'}]},
    'tokyo-skytree': {   'file_stem': 'tokyo_skytree',
            'revision': 'LANDMARK-R04',
            'names': {'zh': '东京晴空塔', 'ja': '東京スカイツリー', 'en': 'Tokyo Skytree'},
            'height_mm': 634000,
            'deck_levels_mm': [350000, 450000],
            'base_width_mm': 68000,
            'base_triangle_side_mm': 68000,
            'transition_height_mm': 315000,
            'transition_diameter_mm': 32000,
            'ring_divisions': 24,
            'detail': {   'frame': {   'connection_height_mm': 50000.0,
                                       'ring_spacing_mm': 12500.0,
                                       'radial_spacing_mm': 25000.0,
                                       'body_top_mm': 497000.0,
                                       'ring_bays': 12,
                                       'group_width_mm': 4000.0,
                                       'group_depth_mm': 8000.0,
                                       'ring_tiers_mm': [   [0.0, 12500.0],
                                                            [150000.0, 10000.0],
                                                            [250000.0, 7500.0],
                                                            [315000.0, 5000.0]],
                                       'ring_tier_scope': '12.5/10/7.5 m lower pitches; 150/250 m switches are '
                                                          'illustrative, not disclosed construction levels; 5 m above 315 '
                                                          'm.',
                                       'ring_depth_low_mm': 2200.0,
                                       'ring_depth_high_mm': 1200.0,
                                       'chunk_intervals': 7,
                                       'ring_web_stride': 4,
                                       'group_diameter_ground_mm': 2300.0,
                                       'group_diameter_50m_mm': 1800.0,
                                       'group_diameter_315m_mm': 1100.0,
                                       'group_diameter_top_mm': 1016.0,
                                       'group_wall_ground_mm': 100.0,
                                       'group_wall_top_mm': 60.0,
                                       'outer_diameter_low_mm': 1100.0,
                                       'outer_diameter_high_mm': 1016.0,
                                       'outer_wall_low_mm': 25.0,
                                       'outer_wall_high_mm': 60.0,
                                       'brace_diameter_mm': 508.0,
                                       'brace_wall_mm': 25.0,
                                       'group_brace_diameter_mm': 600.0,
                                       'group_brace_wall_mm': 28.0,
                                       'horizontal_diameter_mm': 406.4,
                                       'horizontal_wall_mm': 16.0,
                                       'ring_rhs_width_mm': 400.0,
                                       'ring_rhs_depth_mm': 400.0,
                                       'ring_rhs_wall_mm': 12.0,
                                       'radial_rhs_width_mm': 500.0,
                                       'radial_rhs_depth_mm': 500.0,
                                       'radial_rhs_wall_mm': 12.0,
                                       'middle_radius_mm': 6200.0,
                                       'middle_top_radius_mm': 3200.0,
                                       'middle_diameter_mm': 355.6,
                                       'middle_wall_mm': 16.0},
                          'gain': {   'interface_mm': 497000.0,
                                      'lattice_start_mm': 497000.0,
                                      'top_mm': 634000.0,
                                      'top_tie_mm': 620000.0,
                                      'column_count': 6,
                                      'bay_height_mm': 10000.0,
                                      'column_diameter_low_mm': 1200.0,
                                      'column_diameter_high_mm': 900.0,
                                      'column_wall_low_mm': 80.0,
                                      'column_wall_high_mm': 50.0,
                                      'brace_diameter_mm': 300.0,
                                      'brace_wall_mm': 22.0,
                                      'ring_width_mm': 300.0,
                                      'ring_depth_mm': 300.0,
                                      'ring_wall_mm': 12.0,
                                      'bridge_start_mm': 493000.0,
                                      'bridge_end_mm': 500500.0,
                                      'bridge_diameter_mm': 900.0,
                                      'bridge_wall_mm': 35.0,
                                      'radius_controls_mm': [[497000.0, 2400.0], [507000.0, 2400.0], [620000.0, 2550.0]],
                                      'equipment_banks_mm': [   [506000.0, 527000.0, 3500.0],
                                                                [537000.0, 556000.0, 3500.0],
                                                                [579000.0, 587500.0, 3400.0],
                                                                [589000.0, 597500.0, 3400.0],
                                                                [599000.0, 607500.0, 3400.0],
                                                                [609000.0, 617500.0, 3400.0]],
                                      'equipment_faces': 20,
                                      'equipment_rows': 4,
                                      'equipment_belt_stride': 2,
                                      'equipment_skin_mm': 80.0,
                                      'maintenance_levels_mm': [   527000.0,
                                                                   530000.0,
                                                                   556000.0,
                                                                   570000.0,
                                                                   587500.0,
                                                                   597500.0,
                                                                   607500.0,
                                                                   610000.0,
                                                                   617500.0],
                                      'maintenance_radius_mm': 4100.0,
                                      'maintenance_thickness_mm': 140.0,
                                      'tmd_bottom_mm': 620000.0,
                                      'tmd_middle_mm': 626000.0,
                                      'tmd_roof_mm': 632500.0,
                                      'tmd_radius_mm': 4200.0,
                                      'tmd_inner_radius_mm': 3500.0,
                                      'tmd_flange_radius_mm': 4600.0,
                                      'lightning_rod_radius_mm': 130.0,
                                      'equipment_scope': 'Bank bounds, panel subdivision, platforms and TMD section sizes '
                                                         'are photo-guided appearance estimates; no internal vibration '
                                                         'mechanism is simulated.'},
                          'tembo_floors_mm': [340000, 345000, 350000],
                          'shinbashira_height_mm': 375000,
                          'shinbashira_diameter_mm': 8000,
                          'shinbashira_wall_lower_mm': 400,
                          'shinbashira_wall_upper_mm': 600,
                          'scope': 'Published rounded controls are separate from model-fitted principal arcs, '
                                   'intermediate outline interpolation, lower pitch switch heights, local steel sections, '
                                   'skin/crown station sizes, route placement, equipment and lights. Original appearance '
                                   'study; not survey, member schedules, structural or damping analysis.',
                          'outline': {   'cone_reference_height_mm': 495000.0,
                                         'cone_reference_diameter_mm': 18000.0,
                                         'method': 'principal circular arcs tangent to the upper cone; affine 24-point '
                                                   'section blend',
                                         'published_sori_radius_mm': 4520000.0,
                                         'published_mukuri_max_radius_mm': 5950000.0,
                                         'scope': 'Rounded reference controls; intermediate guide curves are appearance '
                                                  'interpolation, not recovered original coordinates.'},
                          'tembo_deck': {   'facade_angle_deg': 71.0,
                                            'radius_at350_mm': 23500.0,
                                            'facade_bottom_mm': 335000.0,
                                            'facade_top_mm': 355000.0,
                                            'facade_glass_zones_mm': [   [335000.0, 337200.0],
                                                                         [340000.0, 342400.0],
                                                                         [345000.0, 347400.0],
                                                                         [350000.0, 355000.0]],
                                            'opaque_stations_mm': [   [355000.0, 25222.0],
                                                                      [369000.0, 29000.0],
                                                                      [371000.0, 28900.0]],
                                            'roof_level_mm': 371000.0,
                                            'roof_radius_mm': 28900.0,
                                            'roof_thickness_mm': 350.0,
                                            'crown_bottom_mm': 371000.0,
                                            'crown_top_mm': 375000.0,
                                            'crown_radius_mm': 16000.0,
                                            'bottom_mm': 333000.0,
                                            'bottom_radius_mm': 16500.0,
                                            'skin_mm': 180.0,
                                            'glass_mm': 80.0,
                                            'panels': 48,
                                            'floor_inner_radius_mm': 6000.0,
                                            'appearance_scope': '71 degree outward glazing and approximate 47 m diameter '
                                                                'at H350 follow designer controls; the designer describes '
                                                                'the upper mouth as approximately 60 m. Opaque-band/crown '
                                                                'sections remain image-based estimates, with published '
                                                                'rooftop H375. The low service glazing strip is not a '
                                                                'fourth public floor.'},
                          'galleria': {   'start_mm': 445000.0,
                                          'end_mm': 450000.0,
                                          'sorakara_level_mm': 451200.0,
                                          'path_length_mm': 114000.0,
                                          'segments': 44,
                                          'clear_width_mm': 2400.0,
                                          'body_radius_controls_mm': [   [438000.0, 11800.0],
                                                                         [445000.0, 15600.0],
                                                                         [455000.0, 18800.0]],
                                          'facade_top_mm': 455000.0,
                                          'apron_top_mm': 445000.0,
                                          'roof_thickness_mm': 350.0,
                                          'crown_top_mm': 460000.0,
                                          'crown_radius_mm': 12000.0,
                                          'floor_inner_radius_mm': 5000.0,
                                          'floor_thickness_mm': 300.0,
                                          'glass_mm': 80.0,
                                          'skin_mm': 180.0,
                                          'tube_height_mm': 3100.0,
                                          'tube_bulge_mm': 320.0,
                                          'tube_arch_panels': 4,
                                          'upper_route_segments': 12,
                                          'upper_route_angle_rad': 2.199114857512855,
                                          'upper_route_centre_radius_mm': 15100.0,
                                          'route_scope': 'Designer route approximately 114 m; external-panel contractor '
                                                         'approximately 110 m and approximately 40 m diameter/2.4 m clear '
                                                         'width. Radius profile, azimuth and sectional tube are '
                                                         'photo-guided approximations, not a surveyed as-built route.'},
                          'lights': {   'body_levels_mm': [90000.0, 180000.0, 270000.0, 495000.0],
                                        'deck_roof_levels_mm': [371000.0, 375000.0],
                                        'galleria_roof_level_mm': 455000.0,
                                        'gain_platform_levels_mm': [530000.0, 570000.0, 610000.0],
                                        'tmd_roof_level_mm': 632500.0,
                                        'lens_half_mm': 150.0,
                                        'post_height_mm': 300.0,
                                        'scope': 'Eleven controller lenses retained at illustrative exposed supports; not '
                                                 'an obstruction-lighting compliance layout.'},
                          'deck_appearance': {'glass_alpha': 0.58}},
            'profile': [[0, 39259.81830489456], [315000, 16000.0], [495000, 9000.0], [497000, 8922.222222222223]],
            'profile_kind': 'triangle_circle_tangent_arcs',
            'deck_specs': [   {   'id': 'tembo_deck',
                                  'level_mm': 350000,
                                  'bottom_mm': 333000.0,
                                  'glass_bottom_mm': 335000.0,
                                  'top_mm': 375000,
                                  'radius_mm': 23500,
                                  'radius_scope': 'Approximate H350 reference, not maximum equipment-envelope radius.'},
                              {   'id': 'tembo_galleria',
                                  'level_mm': 450000,
                                  'bottom_mm': 438000,
                                  'glass_bottom_mm': 445000,
                                  'top_mm': 460000.0,
                                  'radius_mm': 20000,
                                  'radius_scope': 'Approximate outer passage/envelope control; not constant ramp '
                                                  'radius.'}],
            'antenna_start_mm': 497000,
            'base_slab_thickness_mm': 2500,
            'source_references': [   {   'title': '日建設計 NIKKEN JOURNAL 12 / 2012 Autumn pp10-17',
                                         'url': 'https://www.nikken.co.jp/ja/insights/publication/journal_archive/p4iusj0000001hyd-att/Journal-2012_Autumn.pdf',
                                         'confirmed_rounded_controls_mm': {   'H315_diameter': 32000,
                                                                              'H495_diameter': 18000,
                                                                              'sori_radius': 4520000,
                                                                              'mukuri_max_radius': 5950000,
                                                                              'gallery_route_length': 114000,
                                                                              'gain_external_diameter': 6000},
                                         'confirmed_facade_angle_degrees': 71,
                                         'reference_notes': 'Original designer account: lower principal circular guides '
                                                            'tangent to an upper cone; triangle/circle correspondences '
                                                            'each24 equal perimeter intervals. Rounded dimensions define '
                                                            'fitted principal arcs here, not an exact recovery of all '
                                                            'original3D guides. Published arc radii are reference '
                                                            'records, not extra exact constraints. Gallery azimuth and '
                                                            'detailed section stations remain appearance assumptions.'},
                                     {   'title': '土屋哲夫 東京スカイツリーのデザイン / 電気設備学会誌32(10) pp721-724',
                                         'url': 'https://www.jstage.jst.go.jp/article/ieiej/32/10/32_721/_pdf/-char/en',
                                         'confirmed_rounded_controls_mm': {   'tembo_deck_reference_diameter': 47000,
                                                                              'upper_horizontal_member_pitch': 5000},
                                         'confirmed_facade_angle_degrees': 71,
                                         'reference_notes': 'Author is a project designer. Circular observation floor and '
                                                            'outward-sloping facades; horizontal member '
                                                            'pitches12.5/10/7.5m and5m above315m. The150/250m model '
                                                            'switch heights for lower pitches are not published '
                                                            'construction levels.'},
                                     {   'title': '東京スカイツリー 天望デッキ屋上 特別企画 2024-10-15',
                                         'url': 'https://www.tokyo-skytree.jp/pdf/pressreleases/02fc6924e036215dc33870cb108fdea823153520240310.pdf',
                                         'confirmed_values_mm': {'tembo_deck_rooftop': 375000},
                                         'reference_notes': 'Operator identifies the rooftop at375m. This is an '
                                                            'equipment/rooftop reference, not a fourth public observation '
                                                            'floor. Intermediate opaque-envelope radii and band '
                                                            'elevations remain photo-guided approximations.'},
                                     {   'title': '宮越工芸 東京スカイツリー 空中回廊外装パネル',
                                         'url': 'https://www.miyakoshikogei.co.jp/works/81/',
                                         'published_approximate_values_mm': {   'galleria_diameter': 40000,
                                                                                'galleria_path_length': 110000,
                                                                                'galleria_clear_width': 2400},
                                         'reference_notes': 'Fabricator describes approximately40m diameter,110m '
                                                            'length,2.4m passage width; designer Journal quotes114m. '
                                                            'These rounded source accounts are retained separately; the '
                                                            'model does not assert an exact surveyed route.'},
                                     {   'title': '大林組 制振装置のあるゲイン塔頂部をつくる',
                                         'url': 'https://www.obayashi.co.jp/solution_technology/detail/skytree23.html',
                                         'confirmed_values_mm': {'body_top': 497000, 'tip': 634000},
                                         'published_approximate_values_mm': {'gain_external_diameter': 6000},
                                         'reference_notes': 'Upper gain tower has a wider two-storey TMD machine room and '
                                                            'a roof lightning rod reaching634m. Antenna panels, platform '
                                                            'stations and TMD dimensions are photo-guided approximations; '
                                                            'internal dynamics are not simulated.'},
                                     {   'title': '大林組 ゲイン塔のリフトアップ',
                                         'url': 'https://www.obayashi.co.jp/solution_technology/detail/skytree22.html',
                                         'reference_notes': 'Six-column hexagonal gain assembly and lift-up construction; '
                                                            'no surveyed antenna/equipment schedule is inferred.'},
                                     {   'title': '日建設計による解説 ほぼ日 東京スカイツリーうんちく50 2010-09-28',
                                         'url': 'https://www.1101.com/skytree/2010-09-28.html',
                                         'published_design_stage_approximate_values_mm': {   'maximum_tembo_deck_upper_diameter': 60000},
                                         'reference_notes': 'Design-team commentary published during construction '
                                                            'describes an upper maximum of approximately60m. The model '
                                                            'equipment envelope near58m is an appearance estimate '
                                                            'consistent with this design-stage scale, not an as-built '
                                                            'dimension schedule.'},
                                     {   'title': '東京スカイツリー 構造設計（日建設計供図）',
                                         'url': 'https://www.tokyo-skytree.jp/about/spec/structure/',
                                         'confirmed_values_mm': {   'ring_vertical_interval': 12500,
                                                                    'horizontal_link_interval': 25000,
                                                                    'maximum_base_pipe_diameter': 2300,
                                                                    'maximum_base_pipe_wall': 100},
                                         'reference_notes': 'Three vertex groups of four columns make the kanae trusses. '
                                                            'Circular tubes branch directly by welding rather than large '
                                                            'gusset plates. Ring and radial-link hierarchy informs '
                                                            'appearance. Member-specific diameters/walls, group widths '
                                                            'and every branch position are modelling assumptions, not a '
                                                            'recovered member schedule.'},
                                     {   'title': '東京スカイツリー 各部紹介',
                                         'url': 'https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/parts.php',
                                         'confirmed_values_mm': {   'lower_legs_connect_height': 50000,
                                                                    'base_triangle_side': 68000,
                                                                    'circular_transition_height': 315000},
                                         'reference_notes': 'The three support groups meet the body at approximately50m; '
                                                            'this does not state the complete vertical extent of the '
                                                            'kanae assembly.'},
                                     {   'title': '巴コーポレーション 鉄骨製作の概要',
                                         'url': 'https://www.tomoe-corporation.co.jp/steel-tower/works/skytree/outline.html',
                                         'published_member_ranges_mm': {   'kanae_column_diameter': [711.2, 2300],
                                                                           'kanae_wall': [28, 100],
                                                                           'outer_column_diameter': [1016, 1100],
                                                                           'outer_brace_diameter': [508, 1000],
                                                                           'horizontal_diameter': [267.4, 609.6],
                                                                           'ring_rhs_size': [300, 500],
                                                                           'gain_column_diameter': [900, 1200],
                                                                           'gain_column_wall': [25, 80]},
                                         'reference_notes': 'Manufacturer ranges cover the fabricated steel families, not '
                                                            'diameters at every model node. The model assigns approximate '
                                                            'dimensions within these ranges. Direct pipe-branch welding '
                                                            'guides joint appearance; no joint capacity or welding '
                                                            'specification is inferred.'},
                                     {   'title': '日建設計 東京スカイツリー構造と心柱',
                                         'url': 'https://www.nikken.co.jp/ja/about/projects_history/corporate_history/12_03.html',
                                         'reference_notes': 'Separates the steel body/shaft from the hollow '
                                                            'reinforced-concrete shinbashira. Upper movable core is not '
                                                            'rigidly connected to the added steel radial frame in this '
                                                            'appearance model; no damping response is simulated.'},
                                     {   'title': '東京スカイツリー アウトライン',
                                         'url': 'https://www.tokyo-skytree.jp/about/outline/',
                                         'confirmed_values_mm': {   'height': 634000,
                                                                    'tembo_deck': 350000,
                                                                    'tembo_galleria': 450000}},
                                     {   'title': '東京スカイツリー フロアガイド',
                                         'url': 'https://www.tokyo-skytree.jp/floor/',
                                         'confirmed_values_mm': {'galleria_start': 445000, 'galleria_end': 450000},
                                         'reference_notes': 'Published floor levels340/345/350 and445/450 remain distinct '
                                                            'from the375m equipment rooftop.'},
                                     {   'title': '東京都 地域資源 東京スカイツリー',
                                         'url': 'https://www.chiikishigen.metro.tokyo.lg.jp/introduction/details/introduction_26.html',
                                         'confirmed_values_mm': {   'approximate_base_triangle_side': 68000,
                                                                    'circular_transition_height': 315000}},
                                     {   'title': '東京スカイツリー 天望デッキ / 天望回廊',
                                         'url': 'https://www.tokyo-skytree.jp/floor/',
                                         'confirmed_values_mm': {   'tembo_floor_340': 340000,
                                                                    'tembo_floor_345': 345000,
                                                                    'tembo_floor_350': 350000},
                                         'reference_notes': 'Floor levels are public references; model radii, glazing '
                                                            'divisions, floor/roof thickness and roof heights are '
                                                            'assumptions.'},
                                     {   'title': '東京スカイツリー 天望回廊',
                                         'url': 'https://www.tokyo-skytree.jp/floor/tembogalleria/',
                                         'confirmed_values_mm': {   'galleria_start': 445000,
                                                                    'galleria_end': 450000,
                                                                    'sorakara_point': 451200},
                                         'reference_notes': 'The glass tube gallery slopes upward from Floor445 to '
                                                            'Floor450. Model radius, turns, ramp width and entrance/exit '
                                                            'positions are original assumptions.'},
                                     {   'title': '東京スカイツリー 塔体のしくみ',
                                         'url': 'https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/body.php',
                                         'confirmed_values_mm': {   'shinbashira_height': 375000,
                                                                    'shinbashira_diameter': 8000,
                                                                    'lower_wall_thickness': 400,
                                                                    'upper_wall_thickness': 600},
                                         'reference_notes': 'Published concrete cylinder dimensions inform the visible '
                                                            'core. Model joints, guide frames and spatial representation '
                                                            'are schematic; no damping behaviour or structural capacity '
                                                            'is simulated.'}]},
}


def _tower(tower_id):
    try:
        return TOWERS[tower_id]
    except KeyError as error:
        raise ValueError(f'Unknown landmark: {tower_id!r}') from error


def geometry_source_paths(tower_id):
    """Explicit per-model source dependency list for reproducible export binding."""
    _tower(tower_id)
    return ['src/lib/tower_geometry.py', *(['src/lib/tokyo_tower_detail.py', 'src/lib/tokyo_tower_steel.py'] if tower_id == 'tokyo-tower' else ['src/lib/skytree_detail.py','src/lib/skytree_outline.py'])]


def revision_for(tower_id):
    return _tower(tower_id).get('revision', REVISION)


def profile_radius(tower_id, z):
    """Interpolate the recorded control radius/half-width at height z (mm)."""
    profile = _tower(tower_id)['profile']
    if tower_id == 'tokyo-tower':
        from .tokyo_tower_detail import profile_radius as detailed_radius
        return detailed_radius(profile, z)
    from .skytree_outline import profile_radius as detailed_radius
    return detailed_radius(_tower(tower_id), z)


def circle_points(radius, divisions=24, angle=0):
    return [[radius * cos(angle + 2 * pi * i / divisions),
             radius * sin(angle + 2 * pi * i / divisions)] for i in range(divisions)]


def square_points(half_width):
    return [[-half_width, -half_width], [half_width, -half_width],
            [half_width, half_width], [-half_width, half_width]]


def ring_points(tower_id, z):
    """The actual frame-node positions used by both CAD and drawing exports."""
    p = _tower(tower_id)
    radius = profile_radius(tower_id, z)
    if p['profile_kind'] == 'square_half_width':
        return square_points(radius)
    from .skytree_outline import ring_points as outline_ring
    return outline_ring(p,z)


def profile_ring(tower_id, z):
    """Alias for clients projecting the common frame outline."""
    return ring_points(tower_id, z)


def base_vertices(tower_id):
    """Primary leg centres: four square or three equilateral vertices."""
    points = ring_points(tower_id, 0)
    return points if tower_id == 'tokyo-tower' else points[::8]


def _section(z, points):
    return {'z': z, 'points': points}


def _beam(group, name, a, b, radius, color):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'beam',
            'start': list(a), 'end': list(b), 'radius': radius, 'color': color}


def _loft(group, name, sections, color):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'loft',
            'sections': sections, 'color': color}


def _box(group, name, bounds, color):
    return {'group': group, 'name': f'{group}:{name}', 'kind': 'box',
            'bounds': list(bounds), 'color': color}


def _tower_paint(z):
    # Seven schematic bands above the model main deck, ending orange/red.
    if z < 125000:
        return '#E34C25'
    index = min(6, int((z - 125000) / ((333000 - 125000) / 7)))
    return '#E34C25' if index % 2 == 0 else '#F4F0E7'


def _tokyo_base_specs():
    from .tokyo_tower_detail import component_specs as detailed_specs
    return detailed_specs(TOWERS['tokyo-tower'],
                          lambda z: ring_points('tokyo-tower', z), _tower_paint)


def _tokyo_specs():
    from .tokyo_tower_steel import refine_steel
    return refine_steel(TOWERS['tokyo-tower'], _tokyo_base_specs())


def _skytree_specs():
    from .skytree_detail import component_specs as detailed_specs
    return detailed_specs(TOWERS['tokyo-skytree'],
                          lambda z: ring_points('tokyo-skytree', z))


@lru_cache(maxsize=2)
def _component_specs_cached(tower_id):
    _tower(tower_id)
    return _tokyo_specs() if tower_id=='tokyo-tower' else _skytree_specs()


def component_specs(tower_id):
    """Return a private copy of exact beam/box/loft input records, in mm."""
    return deepcopy(_component_specs_cached(tower_id))


def assembly_specs(tower_id):
    """Alias for drawing clients: this is also the exact 3D source geometry."""
    return component_specs(tower_id)


def geometry_manifest(tower_id):
    p=deepcopy(_tower(tower_id));stem=p['file_stem'];specs=component_specs(tower_id)
    references=p.pop('source_references')
    for reference in references:reference['checked_on']=CHECKED_ON
    assumed = {
        'zh':'除明确引用的总高、展望台高度及晴空塔三角形基脚/315m圆形控制截面外，底座、杆件截面、平面尺度、展望台外壳、色带位置及几何插值均为原创示意假设。不是测绘、原建筑CAD、结构计算或施工图。',
        'ja':'明示した総高さ・展望施設高さ・スカイツリー三角形基部と315m円形制御断面以外の、基壇・部材断面・平面寸法・展望施設外形・塗装境界・補間形状は独自の概念仮定です。測量図、原設計CAD、構造計算書、施工図ではありません。',
        'en':'Except for explicitly cited total/deck heights and Skytree triangular-base/315m circular controls, bases, member sizes, plan dimensions, deck shells, paint boundaries and geometric interpolation are original schematic assumptions. Not a survey, original-design CAD, structural calculation or construction drawing.',
    }
    assumptions = [assumed, {
        'zh':'地面基准为Z=0；演示地台位于负标高，总高从地面而非地台底部量取。杆件以八边形棱柱表达，不代表原塔选材或截面。',
        'ja':'地盤基準はZ=0です。概念基壇は負の高さに置き、総高さは基壇下面ではなく地盤から測ります。八角柱の部材表現は原塔の材料・断面仕様ではありません。',
        'en':'Ground datum is Z=0. The schematic base is below ground; landmark height is measured from ground, not the slab underside. Octagonal member prisms do not specify original tower materials or sections.',
    }]
    if tower_id == 'tokyo-tower':
        assumptions[0] = {
            'zh':'总高333m、脚基准轴距80m及施工图H3/H11/H23/H27标高有公开依据。未标注的宽度、H中间分节、拱曲线及截面仍是图面解释和建模近似；双层GL125000是从GL120000加5m层距的解释。官方150m/250m案内值与几何GL解释分列；H11外壳对应与H23屋顶的解释均未实测核定；R06内部GL220550楼板为假设。不是测绘或原设计复原。',
            'ja':'全高333m・脚基準軸間80mと施工図H3/H11/H23/H27は公表値。無記入の幅・中間H節間・アーチ曲線・断面は図面解釈と近似です。GL125000はGL120000から5mの層間を解釈。公式案内150m/250mとモデルGLを分離し、床位置との対応もモデル上の解釈で、実測・原設計復元ではありません。',
            'en':'Published controls cover333m overall height,80m leg-axis spacing and construction H3/H11/H23/H27 GL. Unlabelled widths, belts, arch curve and sections remain interpreted approximations; GL125000 interprets a5m upper-floor interval aboveGL120000. Official150m/250m guidance values are separate from geometricGL. H23 is treated as a historical roof band; the R06 internalGL220550 floor is an appearance assumption, not a surveyed present-day finished-floor conversion.',
        }
        assumptions[1] = {
            'zh':'地面GL=0、屋面Z=18300；主展望层GL120000/125000、上部H23屋顶GL223550（假设内部楼板220550），官方150m/250m案内值另列。24梯跑600踢面为约600阶公开描述的示意布置，路径、踢面、260mm踏面和平台尺寸均非原建筑实测。R04按宽面组合柱形态表达H/I主材，细部截面未核实。',
            'ja':'地盤GL=0、屋上Z=18300、モデルの主展望外殻・仮定床GL120000/125000・H23屋根GL223550（内部床220550は仮定）。公式案内150m/250mは別記。24折返し・600段は公表の約600段をもとにした独自配置です。経路、蹴上げ、踏面260mm、踊場寸法、H/I組立主材・八角副材は実測仕様ではありません。',
            'en':'Ground GL=0, roof Z=18300; interpreted model shell/floor GL120000/125000 and H23 roofGL223550 (assumed inner floorGL220550) are separate from official150m/250m visitor names. The 24-flight/600-rise staircase is an original schematic arrangement informed by the published approximate 600 steps; route, rises, 260 mm treads and landings are not measured specifications. R04 uses graded built-up H/I appearance chords with unverified sections; braces retain octagonal prisms.',
        }
        assumptions.append({
            'zh':'R05主展望台两层外轮廓分别参考历史H11的27m方形、H12的28m方形；H13的29×24m历史平面独立记录（功能未核定），不作为当前外幕墙边界。R06将H23的13m圆形细分为48面，H23作为屋顶控制；上部H24环形平台、上下白色钢架和小型抛物面设备参照照片拟合。2019改修窄窗、浅色底缘与清扫轨道参照供应商实景；分格、倾角、板厚、现况对应及H23附近塔身轴线收分仍为近似。',
            'ja':'R05は歴史的なH11の27m角・H12の28m角を各階の外形参考とし、H13の29×24m歴史平面（用途未確認）は現在の外装境界に流用せず別記します。R06はH23の直径13m円を48面で近似し、H23を屋根制御とします。H24の環状保守床・上下の白い架構・小型反射鏡は写真近似です。2019年改修の細い窓枠・明色の下面・清掃軌道は製作者写真を参照し、割付・勾配・板厚・現況との対応・H23付近の塔体軸線はモデル仮定です。',
            'en':'R05 uses historical H11 27m-square and H12 28m-square controls for separate deck levels. The H13 29x24m historical plan (function unverified) is recorded independently, not used as the current facade boundary. R06 samples the H23 13m circle with48 facets and treats H23 as a roof control. Its separate H24 ring platform, white framing and small reflectors are photo-guided fits. Supplier photographs guide2019 narrow glazing frames, pale soffits and cleaning tracks; divisions, slopes, thicknesses, current-state mapping and nearby tower-axis taper remain approximations.',
        })
        assumptions.append({
            'zh':'R05补充H25-H27数字天线分组与SG内外两层格构。宫地No28记载ST更换为450mm BOX角柱；模型墙厚、设备尺寸、节距、SG杆径、连接及H27承接均为假设，不含临时吊运平台，也不进行制振或结构计算。',
            'ja':'R05はH25-H27のデジタルアンテナ群とSGの内外架構を追加します。STは宮地No28の更新記録に基づく450mm BOX角柱です。壁厚・機器寸法・節間・SG部材径・接合・H27取合いは仮定で、仮設荷揚げ足場や制振・構造解析は含みません。',
            'en':'R05 adds H25-H27 digital antenna banks and separate inner/outer SG frames. The ST is a450mm BOX post following the Miyaji No28 replacement record; its wall, equipment dimensions, bay pitch, SG sections, joints and H27 interface remain assumptions. Temporary hoisting stages, damping response and structural capacity are not modelled.',
        })
    if tower_id == 'tokyo-skytree':
        assumptions[0] = {
            'zh':'R04采用公开的634m总高、约68m地面正三角形、315m处约32m直径和495m处约18m直径。上段为直锥，下段分别拟合与其相切的角部反り及面中むくり圆弧；为满足这些圆整控制值，拟合半径并不等于发表的4520m/最大5950m。24点截面之间的引导线、局部截面及连接为外观近似，不是原设计坐标、测绘CAD或施工图。',
            'ja':'R04は公表された全高634m・地上の約68m正三角形・315mで約32m径・495mで約18m径を用います。上部を直円錐、下部の反りとむくりをそれに接する別々の円弧で近似します。丸めた制御値を満たすため、近似半径は公表の4520m・最大5950mとは一致しません。24点断面間のガイド・部材断面・接合は外観近似で、原設計座標や測量CAD・施工図ではありません。',
            'en':'R04 uses published rounded controls:634m height,68m ground triangle,32m diameter at315m and18m at495m. Separate principal sori/mukuri arcs are fitted tangent to the upper cone. Satisfying these rounded controls gives fitted radii different from the published4520m/maximum5950m. Intermediate24-point guides, local sections and joints remain appearance approximations, not recovered original coordinates, survey CAD or construction drawings.',
        }
        assumptions[1] = {
            'zh':'地面GL=0，演示地台位于负标高，总高由地面量取。保留真实中空圆管、方管和独立钢筋混凝土心柱；长主弦采用水平圆环站点放样，未复原原塔逐杆法向截面及相贯端切。不模拟心柱制振或结构承载。',
            'ja':'地盤GL=0、概念基壇は負の高さに置き、全高は地盤から測ります。実際に中空の円管・角管と独立したRC心柱を保持します。長い主弦は水平円環ロフト近似で、原塔の各部材の法線断面や相貫端切を復元せず、心柱制振や構造耐力も解析しません。',
            'en':'Ground GL=0; the schematic base is below ground. Actual hollow circular/rectangular tubes and the separate RC core are retained. Long chords use horizontal annular loft stations without recovering member-normal sections or saddle cuts. Core damping and structural capacity are not simulated.',
        }
        assumptions.append({
            'zh':'主台保留340/345/350m三个公共楼层，335m服务带不另算公共层。71度外倾幕墙及350m处约47m直径有设计者资料；375m屋顶有运营方公开依据。上口约58m等设备壳体截面为参考施工阶段约60m描述与实景的拟合。回廊445→450m、451.2m最高点有官方依据；设计者114m与制造商约110m/宽2.4m的记述分别保留。模型采用114m变径路径，方位、上部衔接、玻璃分片及设备冠部尺寸仍为近似。',
            'ja':'主展望施設は340/345/350mの公共3階を保ち、335mのサービス帯を公共階には数えません。71度の外傾ガラスと350mで約47m径は設計者資料、375m屋上は運営者資料に基づきます。約58m径の設備外殻等は工事段階の上端約60mという説明と写真に基づく近似。回廊445→450m・最高451.2mは公式値、設計者の114mと製作者の約110m・幅2.4mは別々に記録します。114mの変径経路を採用し、方位・上部接続・ガラス割付・設備冠部寸法はモデル仮定です。',
            'en':'The main deck retains three public floors340/345/350m; the335m service band is not another public floor. Designer sources give71-degree outward glazing and about47m diameter at350m; the operator gives a375m rooftop. Equipment-envelope stations such as58m upper diameter are photo-guided fits informed by a construction-stage approximately60m upper diameter. Operator gallery levels445/450/451.2m are retained. Designer114m and fabricator approximately110m/2.4m width are recorded separately. The model uses a114m variable-radius route; azimuth, upper connection, glazing divisions and equipment-crown sections remain approximations.',
        })
        assumptions.append({
            'zh':'三组各四柱鼎桁架在50m连接。公开水平杆节距12.5/10/7.5m及315m以上5m用于24轴外圈；150m/250m切换高度、内12边环和稀疏腹杆属建模假设，不能当作真实逐杆布置。497m起六柱增益塔保持约6m外径，补充分段天线、维护平台和外扩双层TMD机房，避雷杆达到634m；天线高度分段、机房尺寸、支座及灯位均参考实景拟合。',
            'ja':'三組各四柱の鼎トラスは50mで接合。公表の水平材ピッチ12.5/10/7.5m・315m以上5mを24軸外周に用います。150/250mの切替高さ、内側12角リングと省略腹材はモデル仮定で、実際の全材配置ではありません。497mからの六柱ゲイン塔は外径約6mを保ち、分節アンテナ・保守床・外側へ広がる二層TMD機械室・634mの避雷針を表現。アンテナ区間、機械室寸法、支持具、灯具位置は写真に基づく近似です。',
            'en':'Three four-column kanae groups join at50m. Published horizontal pitches12.5/10/7.5m and5m above315m inform the24-axis outer frame. The150/250m switches, inner12-sided rings and sparse webs are modelling assumptions, not an original member schedule. The six-column gain tower above497m keeps approximately6m external diameter, with separate antenna banks, maintenance decks, a wider two-storey TMD head and a lightning rod reaching634m. Antenna stations, head dimensions, supports and light positions are photo-guided approximations.',
        })
    if tower_id == 'tokyo-tower':
        assumptions.append({
            'zh':'R06按2012年天线供应商Fig5表达上下两组环形阵列：每组30片/行、5行，高5300mm，间隔500mm，外径上12876mm、下13400mm，内支撑圈11800mm。总300片取代四方板片。绝对GL240550起点、板厚、缝隙、支撑、下方两行短阵列与设备平台为图像拟合。旧频道标签不表示当前运营用途；2014后SG补强与BOX450 ST保留。',
            'ja':'R06は2012年の製作者Fig5に基づく上下二組の環状配列です。各組30枚/段・5段・高さ5300mm、間隔500mm、上径12876mm・下径13400mm、支持円11800mmの計300枚で四方の板列を置換。絶対GL240550、板厚・目地・支持材・下部二段短配列・保守床は画像近似です。旧チャンネル表記を現用用途とは扱わず、2014年後のSG補強とBOX450 STは保持します。',
            'en':'R06 follows the supplier2012 Fig5: two circular arrays, each30 panels per row and5 rows,5300mm high,500mm apart, upper diameter12876mm, lower13400mm and support circle11800mm,300 panels total. Absolute startingGL240550, shell thickness, seams, supports, lower short arrays and service platform are image fits. Historical channels do not identify current use; post2014 SG reinforcement and BOX450 ST remain.',
        })
    steel_nodes = []
    if tower_id == 'tokyo-tower':
        from .tokyo_tower_steel import node_catalog
        steel_nodes = node_catalog(TOWERS[tower_id], _tokyo_base_specs())
        assumptions.append({
            'zh':'R04的20个钢结构节点、H/I外观截面、板厚、加劲肋、铆钉头数量/尺寸/间距与布置均为演示假设。铆接特征参考历史资料，未复原原设计或历次加固节点，也未验算节点/锚固承载力。',
            'ja':'R04の20箇所の鋼接合部、H/I外観断面、板厚、補剛材、リベット頭の数・寸法・間隔・配置はモデル仮定です。歴史資料を参考にした外観表現であり、原設計・改修接合部の復元や接合・定着の耐力照査ではありません。',
            'en':'The twenty R04 steel nodes, H/I appearance sections, plate/stiffener thicknesses and rivet-head counts, sizes, pitch and placement are demonstration assumptions. Historical riveting character informs appearance; original/retrofit connections and connection/anchorage capacities have not been reconstructed or calculated.',
        })
    return {'schema_version':1,'id':tower_id,'revision':revision_for(tower_id),'units':'mm','names':p['names'],
            **({'steel_nodes':steel_nodes} if steel_nodes else {}),
            'status':'reference_concept_only',
            'height_mm':p['height_mm'],'parameters':p,
            'groups':[{'id':group,'node_name':group,'names':GROUP_NAMES[group],
                       'component_count':sum(s['group']==group for s in specs)} for group in GROUPS],
            'component_count':len(specs),'assumptions':assumptions, 'source_references':references,
            'coordinates':{'CAD':'millimetres; Z-up; ground datum Z=0',
                           'GLB':'metres; Y-up; (X,Z,-Y)/1000; identity grouping transforms'},
            'engineering':{'structural_capacity':None,'member_design':None,'foundation_design':None,
                           'earthquake_or_wind':None,'statutory_compliance':None},
            'files':{'step':f'STEP/{stem}.step','glb':f'GLB/{stem}.glb',
                     'plan_dxf':f'DXF/{stem}_plan.dxf','elevation_dxf':f'DXF/{stem}_elevation.dxf',
                     'plan_svg':f'output/svg/{stem}_plan.svg','elevation_svg':f'output/svg/{stem}_elevation.svg',
                     'pdf':f'output/pdf/{stem}_sheets.pdf',
                     **({'steel_nodes_dxf':f'DXF/{stem}_steel_nodes.dxf',
                         'steel_nodes_svg':f'output/svg/{stem}_steel_nodes.svg'} if tower_id == 'tokyo-tower' else
                        {'structure_zones_dxf':f'DXF/{stem}_structure_zones.dxf',
                         'structure_zones_svg':f'output/svg/{stem}_structure_zones.svg'})}}


def _cad_shape(spec, bd):
    if spec['kind']=='box':
        x1,y1,z1,x2,y2,z2=spec['bounds']
        return bd.Box(x2-x1,y2-y1,z2-z1,align=(bd.Align.MIN,)*3).moved(bd.Location((x1,y1,z1)))
    if spec['kind']=='loft':
        wires=[bd.Wire.make_polygon([(x,y,section['z']) for x,y in section['points']],close=True)
               for section in spec['sections']]
        return bd.Solid.make_loft(wires,ruled=True)
    if spec['kind']=='loft3d':
        # Planar end sections permit genuinely sloping gallery floors/glass.
        # Every end wire is retained as explicit CAD-space XYZ coordinates.
        wires=[bd.Wire.make_polygon(section,close=True) for section in spec['sections']]
        return bd.Solid.make_loft(wires,ruled=True)
    if spec['kind']=='tube':
        # Analytic circular hollow steel, with a section normal to its axis.
        a,b=spec['start'],spec['end'];d=[b[i]-a[i] for i in range(3)]
        length=sqrt(sum(x*x for x in d));r=spec['radius'];wall=spec['wall_thickness_mm']
        if length<=0 or not 0<wall<r:raise ValueError('Invalid circular tube')
        plane=bd.Plane(origin=tuple(a),z_dir=tuple(d))
        outer=bd.Solid.make_cylinder(r,length,plane=plane)
        inner=bd.Solid.make_cylinder(r-wall,length,plane=plane)
        return outer.cut(inner)
    if spec['kind']=='tube_loft':
        # Circular annuli at the recorded Z stations, not octagonal solid bars.
        # The ruled envelope follows the original straight frame intervals.
        outer=[];inner=[]
        for section in spec['sections']:
            r=section['radius'];wall=section['wall_thickness_mm']
            if not 0<wall<r:raise ValueError('Invalid tubular loft wall')
            plane=bd.Plane(origin=(*section['center'],section['z']))
            outer.append(bd.Wire.make_circle(r,plane=plane))
            inner.append(bd.Wire.make_circle(r-wall,plane=plane))
        return bd.Solid.make_loft(outer,ruled=True).cut(bd.Solid.make_loft(inner,ruled=True))
    if spec['kind']=='rhs':
        a,b=spec['start'],spec['end'];d=[b[i]-a[i] for i in range(3)]
        length=sqrt(sum(x*x for x in d));w,h,t=spec['width_mm'],spec['depth_mm'],spec['wall_thickness_mm']
        if length<=0 or not 0<2*t<min(w,h):raise ValueError('Invalid rectangular hollow section')
        z=[v/length for v in d];ref=[0.,0.,1.] if abs(z[2])<.95 else [1.,0.,0.]
        cross=lambda u,v:[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        u=cross(z,ref);norm=sqrt(sum(v*v for v in u));u=[v/norm for v in u];v=cross(z,u)
        def shell(width,height):
            rings=[]
            for c in (a,b):
                points=[[c[k]+u[k]*x+v[k]*y for k in range(3)] for x,y in
                        [(-width/2,-height/2),(width/2,-height/2),(width/2,height/2),(-width/2,height/2)]]
                rings.append(bd.Wire.make_polygon(points,close=True))
            return bd.Solid.make_loft(rings,ruled=True)
        return shell(w,h).cut(shell(w-2*t,h-2*t))
    if spec['kind']=='beam':
        # A genuine octagonal prism: explicit faceting controls draw cost and
        # avoids claiming that the assumed member profile is a selected tube.
        a,b=spec['start'],spec['end'];d=[b[i]-a[i] for i in range(3)]
        length=sqrt(sum(v*v for v in d));direction=[v/length for v in d]
        reference=[0.,0.,1.] if abs(direction[2])<.95 else [1.,0.,0.]
        cross=lambda u,v:[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        u=cross(direction,reference);norm=sqrt(sum(v*v for v in u));u=[v/norm for v in u]
        v=cross(direction,u);r=spec['radius'];rings=[]
        for centre in (a,b):
            points=[[centre[k]+r*(u[k]*cos(2*pi*i/8)+v[k]*sin(2*pi*i/8)) for k in range(3)] for i in range(8)]
            rings.append(bd.Wire.make_polygon(points,close=True))
        return bd.Solid.make_loft(rings,ruled=True)
    raise ValueError(f"Unknown primitive: {spec['kind']}")


def tower_assembly(tower_id):
    from cadgen import build123d as bd,srgb
    specs=component_specs(tower_id);groups=[]
    for group in GROUPS:
        children=[]
        for spec in specs:
            if spec['group']!=group:continue
            shape=_cad_shape(spec,bd);shape.label=spec['name'];shape.color=srgb(spec['color'])
            children.append(shape)
        groups.append(bd.Compound(children=children,label=group))
    return bd.Compound(children=groups,label='TokyoTower' if tower_id=='tokyo-tower' else 'TokyoSkytree')
