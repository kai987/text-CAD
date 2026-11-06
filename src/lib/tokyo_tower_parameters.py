"""Tokyo Tower appearance parameters, millimetres and Z-up.

Each call creates independent dictionaries and lists. There is no shared mutable
default object; callers can safely copy or adjust a returned parameter set.
"""


def parameters():
    """Return an independent copy of the recorded parameter values."""
    return {
        'file_stem': 'tokyo_tower',
        'revision': 'LANDMARK-R11',
        'names': {'zh': '东京塔', 'ja': '東京タワー', 'en': 'Tokyo Tower'},
        'height_mm': 333000,
        'deck_levels_mm': [125000, 223550],
        'nominal_deck_levels_mm': [150000, 250000],
        'geometry_datum': 'Historical construction-GL controls; H23 is treated as a roof band. Current '
                          'nominal150m/250m visitor names remain separate; present finished-floor conversion and '
                          'facade mapping are not surveyed.',
        'base_width_mm': 80000,
        'detail': {'base_appearance': {'leg_cage_transition_start_mm': 80000.0,
                                       'leg_cage_top_mm': 125000.0,
                                       'leg_cage_top_half_width_mm': 450.0,
                                       'leg_continuation_levels_mm': [88000.0,
                                                                      98000.0,
                                                                      106000.0,
                                                                      114000.0,
                                                                      120000.0,
                                                                      125000.0],
                                       'leg_continuation_chord_half_width_mm': 262.5,
                                       'leg_primary_section_scale': 0.7,
                                       'slenderness_scope': 'R08 multiplies retained nominal primary sizes by0.70 '
                                                            '(720-to-504mm at ground, 525-to-367.5mm continuation); '
                                                            'lacing and arch plate sizes are separate photo fits. '
                                                            'Axes and gross cage remain unchanged. Not a measured '
                                                            'section schedule.',
                                       'leg_web_radius_mm': 95.0,
                                       'leg_tie_radius_mm': 110.0,
                                       'leg_continuation_overlap_mm': 40.0,
                                       'leg_transition_link_radius_mm': 100.0,
                                       'leg_attachment_inset_mm': 150.0,
                                       'leg_continuation_scope': 'The four-member gross leg assemblies continue '
                                                                 'smoothly from ground through the former 80m '
                                                                 'modelling boundary to the Main Deck. Continuation '
                                                                 'stations, cage taper, constant 525mm H appearance '
                                                                 'sections, short branch links and fitted end laps '
                                                                 'are visual assumptions, not recovered original '
                                                                 'member or connection designs.',
                                       'arch_rib_depth_mm': 1800.0,
                                       'arch_plane_half_depth_mm': 650.0,
                                       'arch_panel_count': 16,
                                       'arch_profile_width_mm': 320.0,
                                       'arch_profile_depth_mm': 420.0,
                                       'arch_web_thickness_mm': 16.0,
                                       'arch_flange_thickness_mm': 20.0,
                                       'arch_joint_overlap_mm': 40.0,
                                       'arch_web_radius_mm': 60.0,
                                       'arch_cross_tie_radius_mm': 55.0,
                                       'arch_spandrel_tie_radius_mm': 90.0,
                                       'arch_spandrel_diagonal_radius_mm': 75.0,
                                       'foot_town_width_mm': 48000.0,
                                       'foot_town_depth_mm': 44000.0,
                                       'foot_town_floor_levels_mm': [0.0, 3600.0, 7200.0, 10800.0, 14400.0, 18300.0],
                                       'foot_town_glazed_bands': 2,
                                       'foot_town_bays_per_face': 8,
                                       'foot_town_wall_thickness_mm': 350.0,
                                       'foot_town_roof_overhang_mm': 900.0,
                                       'foot_town_upper_color': '#76584B',
                                       'foot_town_canopy_width_mm': 14000.0,
                                       'foot_town_canopy_projection_mm': 2800.0,
                                       'foot_town_door_height_mm': 3000.0,
                                       'foot_town_roof_housing_bounds_mm': [-4200.0,
                                                                            8000.0,
                                                                            18300.0,
                                                                            4200.0,
                                                                            13000.0,
                                                                            21000.0],
                                       'scope': 'H3 GL40m and 80m foot-axis spacing are published structural '
                                                'controls. Arch depth, profile and web sizes, panel layout, '
                                                'FootTown 48x44m plan, facade bands, cladding and rooftop equipment '
                                                'are photograph/drawing-guided appearance assumptions, not surveyed '
                                                'dimensions or structural design.'},
                   'lower_grid_continuity': {'enabled': True,
                                             'band_levels_mm': [80000.0, 93000.0, 106000.0, 120000.0],
                                             'columns': 4,
                                             'primary_brace_radius_mm': 160.0,
                                             'secondary_brace_radius_mm': 105.0,
                                             'vertical_radius_mm': 110.0,
                                             'belt_radius_mm': 200.0,
                                             'corner_clip_radius_mm': 90.0,
                                             'corner_clip_source_overlap_mm': 20.0,
                                             'support_link_radius_mm': 110.0,
                                             'support_height_mm': 114000.0},
                   'integrated_lower': {'enabled': True,
                                        'cover_thickness_mm': 20.0,
                                        'web_thickness_mm': 16.0,
                                        'border_width_mm': 180.0,
                                        'batten_width_mm': 180.0,
                                        'pitch_depth_ratio': 1.35,
                                        'min_cells': 2,
                                        'max_cells': 8,
                                        'diaphragm_length_mm': 60.0,
                                        'diaphragm_edge_clearance_mm': 1.0,
                                        'end_overlap_mm': 40.0,
                                        'seam_width_mm': 120.0,
                                        'max_pieces_per_assembly': 24},
                   'lower_built_up': {'enabled': True,
                                      'cover_thickness_mm': 20.0,
                                      'web_thickness_mm': 16.0,
                                      'border_width_mm': 40.0,
                                      'batten_width_mm': 55.0,
                                      'lacing_width_mm': 45.0,
                                      'pitch_depth_ratio': 2.0,
                                      'min_cells': 4,
                                      'max_cells': 12,
                                      'diaphragm_length_mm': 100.0,
                                      'max_pieces_per_member': 24},
                   'upper_equipment': {'enabled': True,
                                       'tiers_mm': [158000.0, 166000.0, 174000.0, 182000.0],
                                       'projections_mm': [2600.0, 3000.0, 3200.0, 2800.0],
                                       'projection_definition': 'Additional X and Y half-width at corner tips, not '
                                                                'a surveyed radial projection.',
                                       'arm_radius_mm': 110.0,
                                       'stay_radius_mm': 80.0,
                                       'stay_drop_mm': 1800.0,
                                       'mount_overlap_mm': 180.0,
                                       'platform_width_mm': 1200.0,
                                       'platform_length_mm': 1000.0,
                                       'platform_thickness_mm': 120.0,
                                       'tip_mast_height_mm': 1100.0,
                                       'crossbar_half_width_mm': 650.0,
                                       'gallery_height_mm': 182000.0,
                                       'gallery_projection_mm': 650.0,
                                       'gallery_guard_height_mm': 1000.0,
                                       'gallery_slab_thickness_mm': 120.0,
                                       'radome_facets': 16,
                                       'radome_depth_mm': 450.0,
                                       'radomes': [{'height_mm': 146000.0,
                                                    'face': 0,
                                                    'corner': -1,
                                                    'diameter_mm': 1600.0,
                                                    'projection_mm': 1500.0},
                                                   {'height_mm': 200000.0,
                                                    'face': 1,
                                                    'corner': 1,
                                                    'diameter_mm': 1700.0,
                                                    'projection_mm': 1700.0},
                                                   {'height_mm': 209000.0,
                                                    'face': 3,
                                                    'corner': 1,
                                                    'diameter_mm': 1400.0,
                                                    'projection_mm': 1600.0}],
                                       'dimensions_status': 'photo_guided_appearance_assumption',
                                       'equipment_inventory_status': 'operator_photo_reference_date_and_current_inventory_unverified',
                                       'source_reference': 'https://www.tokyotower.co.jp/plan/towerpedia/',
                                       'source_photo': 'https://www.tokyotower.co.jp/plan/towerpedia/img/img_006.jpg',
                                       'scope': 'Photo-guided outboard appearance from the operator photograph. '
                                                'Heights, projections, directions, bracket sections, service floors '
                                                'and circular covers are model fits, not measured installation '
                                                'coordinates or an original equipment schedule. Current inventory '
                                                'and photo date are unverified; no broadcaster or radio-system '
                                                'assignment is asserted.'},
                   'upper_shaft_outline': {'enabled': True,
                                           'start_mm': 130000.0,
                                           'end_mm': 223550.0,
                                           'start_half_width_mm': 9900.0,
                                           'end_half_width_mm': 3950.0,
                                           'start_slope_mm_per_mm': -0.06827586206896552,
                                           'end_slope_mm_per_mm': -0.041757602211552454,
                                           'method': 'convex integrated power tangent blend',
                                           'scope': 'Photo-guided appearance fit of the shaft between the Main Deck '
                                                    'roof and historical H23 roof control. End radii and tangents '
                                                    'match the retained reference profile; intermediate half-widths '
                                                    'are fitted, not original surveyed coordinates or a structural '
                                                    'member schedule.'},
                   'deck_appearance': {'main_lower_half_width_mm': 13500.0,
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
                   'antenna_appearance': {'digital_panel_bottom_mm': 240550.0,
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
                                          'st_equipment_levels_mm': [315000.0,
                                                                     318000.0,
                                                                     321000.0,
                                                                     324000.0,
                                                                     327000.0,
                                                                     330000.0],
                                          'st_equipment_half_width_mm': 380.0},
                   'main_floor_half_widths_mm': [13500.0, 14000.0],
                   'historical_section_controls_mm': {'H11': {'width': 27000, 'depth': 27000},
                                                      'H12': {'width': 28000, 'depth': 28000},
                                                      'H13': {'width': 29000,
                                                              'depth': 24000,
                                                              'status': 'Historical H13 plan recorded separately; '
                                                                        'its function and mapping to the current '
                                                                        'facade remain unverified'},
                                                      'H23': {'diameter': 13000,
                                                              'datum_scope': 'Historical structural roof band; not '
                                                                             'a verified present visitor '
                                                                             'finished-floor elevation.'}},
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
                   'member_profiles': 'graded built-up H/I appearance chords; four schematic connection families at '
                                      'twenty selected nodes',
                   'steel_node_count': 20,
                   'steel_profile_families': {'lower': {'type': 'H',
                                                        'width_factor': 1.0,
                                                        'depth_factor': 0.85,
                                                        'web_thickness_mm': 24.0,
                                                        'flange_thickness_mm': 30.0},
                                              'middle': {'type': 'H',
                                                         'width_factor': 0.9,
                                                         'depth_factor': 0.8,
                                                         'web_thickness_mm': 18.0,
                                                         'flange_thickness_mm': 24.0},
                                              'upper': {'type': 'I',
                                                        'width_factor': 0.62,
                                                        'depth_factor': 1.0,
                                                        'web_thickness_mm': 14.0,
                                                        'flange_thickness_mm': 18.0}},
                   'steel_node_families': {'base': {'width_mm': 1200.0,
                                                    'height_mm': 1000.0,
                                                    'plate_thickness_mm': 30.0,
                                                    'stiffener_thickness_mm': 16.0,
                                                    'stiffener_depth_mm': 160.0,
                                                    'rivet_radius_mm': 18.0,
                                                    'rivet_projection_mm': 12.0},
                                           'lower_truss': {'width_mm': 1100.0,
                                                           'height_mm': 1200.0,
                                                           'plate_thickness_mm': 20.0,
                                                           'stiffener_thickness_mm': 16.0,
                                                           'stiffener_depth_mm': 140.0,
                                                           'rivet_radius_mm': 18.0,
                                                           'rivet_projection_mm': 12.0},
                                           'splice': {'width_mm': 620.0,
                                                      'height_mm': 1050.0,
                                                      'plate_thickness_mm': 16.0,
                                                      'stiffener_thickness_mm': 14.0,
                                                      'stiffener_depth_mm': 100.0,
                                                      'rivet_radius_mm': 18.0,
                                                      'rivet_projection_mm': 12.0},
                                           'deck_support': {'width_mm': 1100.0,
                                                            'height_mm': 1000.0,
                                                            'plate_thickness_mm': 24.0,
                                                            'stiffener_thickness_mm': 16.0,
                                                            'stiffener_depth_mm': 180.0,
                                                            'rivet_radius_mm': 18.0,
                                                            'rivet_projection_mm': 12.0}},
                   'scope': 'R07 distinguishes the in-plane deep arch truss, continuous tapered primary legs below '
                            'the Main Deck and a photo-guided FootTown envelope. The shaft beneath the Top Deck '
                            'uses a local smooth fitted taper; deck shells, core, stairs and upper antenna remain. '
                            'Original appearance detail; route, risers, sections, connections, glass, building '
                            'dimensions and light positions are schematic assumptions.'},
        'profile': [[0, 40000],
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
        'deck_specs': [{'id': 'main',
                        'level_mm': 125000,
                        'bottom_mm': 119500,
                        'glass_bottom_mm': 120300,
                        'top_mm': 130000,
                        'half_width_mm': 14000,
                        'support_mm': 115000},
                       {'id': 'top',
                        'level_mm': 220550,
                        'bottom_mm': 219050,
                        'glass_bottom_mm': 220550,
                        'top_mm': 223550,
                        'half_width_mm': 6500,
                        'support_mm': 216550,
                        'datum_scope': 'H23 roof GL223550; the internal floor GL220550 and the current facade '
                                       'correspondence are appearance interpretations, separate from the operator '
                                       'nominal250m.'}],
        'antenna_start_mm': 252650,
        'antenna_lattice_top_mm': 312600,
        'base_slab_thickness_mm': 2000,
        'source_references': [{'title': 'IHI公開写真：東京タワー建設時の塔脚・アーチ',
                               'url': 'https://www.ihi.co.jp/technology/techinfo/contents_no/__icsFiles/afieldfile/2024/01/25/10.PNG',
                               'checked_on': '2026-11-01',
                               'reference_notes': 'Historical construction photograph shows wide built-up leg '
                                                  'members and triangulated arch framing. It guides the in-plane '
                                                  'depth and member hierarchy, not surveyed sections or present-day '
                                                  'retrofit connections.'},
                              {'title': '竹中工務店 東京タワー改修・外観写真',
                               'url': 'https://www.takenaka.co.jp/solution/asset/project/07/',
                               'checked_on': '2026-11-01',
                               'reference_notes': 'Photographs guide the lower building wall/glazing contrast and '
                                                  'broad low envelope. The R07 FootTown plan, facade levels and '
                                                  'rooftop housing are model fits. Published renovation project '
                                                  'area is not treated as a FootTown footprint or a measured plan.'},
                              {'title': '山森一之（古河C&B技術部）親局用アンテナ，中継局用送受信アンテナ 2012 p979 Fig5',
                               'url': 'https://www.jstage.jst.go.jp/article/itej/66/12/66_977/_pdf',
                               'confirmed_historical_values_mm': {'upper_array_diameter': 12876,
                                                                  'lower_array_diameter': 13400,
                                                                  'support_diameter': 11800,
                                                                  'each_group_height': 5300,
                                                                  'intergroup_gap': 500},
                               'confirmed_historical_array_counts': {'panels_per_row': 30,
                                                                     'rows_per_group': 5,
                                                                     'groups': 2},
                               'reference_notes': 'Manufacturer-authored historical array drawing. Diameters and '
                                                  'group heights are separate from model-fitted absolute GL, seam '
                                                  'widths, thickness, support members and lower short-array sizes. '
                                                  'Historical station/channel assignments are not current '
                                                  'operating-use claims.'},
                              {'title': '川上春夫 RFワールド No1 pp42-43 東京タワーの地デジ送信用アンテナ',
                               'url': 'https://www.rf-world.jp/bn/RFW01/samples/p042-043a.pdf',
                               'reference_notes': 'Original technical explanation confirms30 panels per row, five '
                                                  'rows and upper/lower groups, with the same dimensioned geometry. '
                                                  'Historic channel text is not reused as current equipment-use '
                                                  'metadata.'},
                              {'title': '日本地震工学会掲載 風間了 実在建物の振動性状 p96-97 / 内藤ほか1962 Fig3',
                               'url': 'https://www.jaee.gr.jp/jp/wp-content/uploads/2015/04/vibration_characteristics.pdf',
                               'confirmed_historical_values_mm': {'H11_plan': [27000, 27000],
                                                                  'H12_plan': [28000, 28000],
                                                                  'H13_plan': [29000, 24000],
                                                                  'H23_diameter': 13000},
                               'reference_notes': 'Historical 1962 paper figure reproduced in the JAEE-hosted '
                                                  'volume (PDF pages105-106, printed96-97). H13 is an independently '
                                                  'recorded historical plan; its function and mapping to the '
                                                  'current facade remain unverified. Original observations '
                                                  'at120m/223m support separating historical/construction GL from '
                                                  'current nominal150m/250m guidance; no verified conversion is '
                                                  'asserted.'},
                              {'title': 'LIXIL 東京タワー 2019カーテンウォール改修',
                               'url': 'https://www.biz-lixil.com/case/curtainwall/B190037/',
                               'reference_notes': 'Primary supplier exterior photographs inform narrow vertical '
                                                  'mullions, fine transoms, light soffits and exterior '
                                                  'gondola-cleaning tracks. Model bay counts, exact slopes, frame '
                                                  'widths and glass thickness remain appearance assumptions.'},
                              {'title': 'LIXILリニューアル 東京タワー改修前後',
                               'url': 'https://www.lixil-renewal.co.jp/business/case/archives/15',
                               'reference_notes': '2019 after-renovation exterior and interior photographs guide '
                                                  'current facade character; no supplier photograph is '
                                                  'redistributed with the model.'},
                              {'title': '宮地技報 No18 東京タワー塔体補強報告 p86 図1',
                               'url': 'https://www.miyaji-eng.co.jp/technology/newsletter/media/18/no18-p085-091.pdf',
                               'confirmed_values_mm': {'leg_axis_spacing': 80000,
                                                       'H3_GL': 40000,
                                                       'H11_GL': 120000,
                                                       'H23_GL': 223550,
                                                       'H27_GL': 252650,
                                                       'tip_GL': 333000},
                               'reference_notes': 'The model interprets observation-shell positions from H11/H23 '
                                                  'structural bands at GL120000/223550, with an assumed 5000mm '
                                                  'main-floor interval. These are not independently verified '
                                                  'visitor finished-floor levels; unlabelled H belts, widths and '
                                                  'arch curvature are traced approximations. Historical retrofit '
                                                  'figure, not a current surveyed as-built model.'},
                              {'title': '宮地技報 No28 東京タワー耐震改修報告 p65 図1',
                               'url': 'https://www.miyaji-eng.co.jp/technology/newsletter/media/28/no28-p064-070.pdf',
                               'confirmed_values_mm': {'support_tower_top_GL': 312600,
                                                       'replacement_ST_BOX_width': 450},
                               'reference_notes': 'Later retrofit drawing confirms H27 GL252650 and upper SG/ST '
                                                  'zones. Page66 Fig2 and page69 photograph10 show the external SG '
                                                  'strengthening frame; page66 specifies replacement ST as a450mm '
                                                  'BOX section. Wall thickness, intermediate bay/equipment '
                                                  'positions and joints remain unverified. Its H23 label '
                                                  'reads223500, versus223550 in No18; this model consistently uses '
                                                  'the earlier223550 control, not both.'},
                              {'title': 'IHI 東京タワー施工写真',
                               'url': 'https://www.ihi.co.jp/technology/techinfo/contents_no/1200541_13491.html',
                               'reference_notes': 'Tokyo Tower construction photograph shows built-up wide plate '
                                                  'chords, lacing and a hierarchy of bracing. Nearby angle-steel '
                                                  'prose refers to Tsutenkaku, not a section schedule for Tokyo '
                                                  'Tower. Exact H/I member sections below remain appearance '
                                                  'assumptions.'},
                              {'title': '東京タワー 施設案内',
                               'url': 'https://www.tokyotower.co.jp/guidance/',
                               'confirmed_nominal_values_mm': {'height': 333000,
                                                               'main_deck': 150000,
                                                               'top_deck': 250000}},
                              {'title': '東京タワー タワペディア',
                               'url': 'https://www.tokyotower.co.jp/plan/towerpedia/',
                               'reference_notes': 'Official 270m painting limit excludes the top antenna; this is '
                                                  'not the construction H27 support-tower start. International '
                                                  'Orange and white, with seven schematic bands above the main '
                                                  'deck.'},
                              {'title': '東京タワー メインデッキ',
                               'url': 'https://www.tokyotower.co.jp/maindeck/',
                               'reference_notes': 'Main Deck has 1F and 2F; the model intermediate floor and all '
                                                  'plan dimensions are schematic.'},
                              {'title': '東京タワー オープンエア外階段ウォーク',
                               'url': 'https://www.tokyotower.co.jp/plan/open_air_stair/',
                               'reference_notes': 'Outdoor stairs connect Foot Town roof to the Main Deck (official '
                                                  'published guidance150m) with approximately 600 steps. The model '
                                                  'route and flight configuration are original assumptions.'},
                              {'title': '東京タワー フットタウン',
                               'url': 'https://www.tokyotower.co.jp/foottown/',
                               'reference_notes': 'Public entrance and rooftop outdoor-stair access inform the '
                                                  'schematic base building; no original floor plan is reproduced.'},
                              {'title': '日本溶接協会 東京スカイツリー製作現場見学雑感（東京タワーとの比較）',
                               'url': 'https://www-it.jwes.or.jp/we-com/bn/vol_1/sec_2/2-1.pdf',
                               'reference_notes': 'Page2 describes the original Tokyo Tower as rivet-assembled SS41 '
                                                  'steelwork. This establishes historical connection character '
                                                  'only; model section sizes, twenty selected nodes, rivet counts, '
                                                  'pitch, plate/stiffener sizes and local coordinates are '
                                                  'assumptions, not original drawings or retrofit design.'},
                              {'title': '竹中工務店 東京タワー改修',
                               'url': 'https://www.takenaka.co.jp/solution/asset/project/07/',
                               'reference_notes': 'The tower has undergone maintenance and strengthening. This '
                                                  'appearance study does not reconstruct every original or later '
                                                  'connection or certify present-day structural capacity.'}]
    }
