"""Tokyo Skytree appearance parameters, millimetres and Z-up.

Each call creates independent dictionaries and lists. There is no shared mutable
default object; callers can safely copy or adjust a returned parameter set.
"""


def parameters():
    """Return an independent copy of the recorded parameter values."""
    return {
        'file_stem': 'tokyo_skytree',
        'revision': 'LANDMARK-R05',
        'names': {'zh': '东京晴空塔', 'ja': '東京スカイツリー', 'en': 'Tokyo Skytree'},
        'height_mm': 634000,
        'deck_levels_mm': [350000, 450000],
        'base_width_mm': 68000,
        'base_triangle_side_mm': 68000,
        'transition_height_mm': 315000,
        'transition_diameter_mm': 32000,
        'ring_divisions': 24,
        'detail': {'frame': {'connection_height_mm': 50000.0,
                             'ring_spacing_mm': 12500.0,
                             'radial_spacing_mm': 25000.0,
                             'body_top_mm': 497000.0,
                             'ring_bays': 12,
                             'group_width_mm': 4000.0,
                             'group_depth_mm': 8000.0,
                             'ring_tiers_mm': [[0.0, 12500.0],
                                               [150000.0, 10000.0],
                                               [250000.0, 7500.0],
                                               [315000.0, 5000.0]],
                             'ring_tier_scope': '12.5/10/7.5 m lower pitches; 150/250 m switches are illustrative, '
                                                'not disclosed construction levels; 5 m above 315 m.',
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
                             'outer_horizontal_diameter_mm': 406.4,
                             'outer_horizontal_wall_mm': 16.0,
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
                   'base_wings': {'enabled': True,
                                  'root_attachment_height_mm': 750.0,
                                  'top_attachment_inset_mm': 100.0,
                                  'panel_levels_mm': [12500.0, 25000.0, 37500.0],
                                  'fan_curve_factor': 0.35,
                                  'chord_diameter_mm': 1016.0,
                                  'chord_wall_mm': 40.0,
                                  'horizontal_diameter_mm': 406.4,
                                  'horizontal_wall_mm': 16.0,
                                  'brace_diameter_mm': 508.0,
                                  'brace_wall_mm': 25.0,
                                  'tie_axis_inset_mm': 300.0,
                                  'scope': 'Broad steel wings on three faces grow from the existing four-column '
                                           'kanae feet and leave central pointed-arch pedestrian openings. Fan '
                                           'axes, 12.5 m modelling panels, wall attachments and section sizes are '
                                           'CG/photo-guided appearance assumptions, not recovered as-built joints '
                                           'or structural design.'},
                   'gain': {'interface_mm': 497000.0,
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
                            'equipment_banks_mm': [[506000.0, 527000.0, 3500.0],
                                                   [537000.0, 556000.0, 3500.0],
                                                   [579000.0, 587500.0, 3400.0],
                                                   [589000.0, 597500.0, 3400.0],
                                                   [599000.0, 607500.0, 3400.0],
                                                   [609000.0, 617500.0, 3400.0]],
                            'equipment_faces': 20,
                            'equipment_rows': 4,
                            'equipment_belt_stride': 2,
                            'equipment_skin_mm': 80.0,
                            'maintenance_levels_mm': [527000.0,
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
                            'equipment_scope': 'Bank bounds, panel subdivision, platforms and TMD section sizes are '
                                               'photo-guided appearance estimates; no internal vibration mechanism '
                                               'is simulated.'},
                   'tembo_floors_mm': [340000, 345000, 350000],
                   'shinbashira_height_mm': 375000,
                   'shinbashira_diameter_mm': 8000,
                   'shinbashira_wall_lower_mm': 400,
                   'shinbashira_wall_upper_mm': 600,
                   'scope': 'Published rounded controls are separate from model-fitted principal arcs, intermediate '
                            'outline interpolation, lower pitch switch heights, local steel sections, three-face '
                            'lower wing/arch topology and fitted joints, skin/crown station sizes, route placement, '
                            'equipment and lights. Round ordinary outer horizontals are distinct from rectangular '
                            'inner ring/radial trusses. Original appearance study; not survey, member schedules, '
                            'structural or damping analysis.',
                   'outline': {'cone_reference_height_mm': 495000.0,
                               'cone_reference_diameter_mm': 18000.0,
                               'method': 'principal circular arcs tangent to the upper cone; affine 24-point '
                                         'section blend',
                               'published_sori_radius_mm': 4520000.0,
                               'published_mukuri_max_radius_mm': 5950000.0,
                               'scope': 'Rounded reference controls; intermediate guide curves are appearance '
                                        'interpolation, not recovered original coordinates.'},
                   'tembo_deck': {'facade_angle_deg': 71.0,
                                  'radius_at350_mm': 23500.0,
                                  'facade_bottom_mm': 335000.0,
                                  'facade_top_mm': 355000.0,
                                  'facade_glass_zones_mm': [[335000.0, 337200.0],
                                                            [340000.0, 342400.0],
                                                            [345000.0, 347400.0],
                                                            [350000.0, 355000.0]],
                                  'opaque_stations_mm': [[355000.0, 25222.0],
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
                                  'appearance_scope': '71 degree outward glazing and approximate 47 m diameter at '
                                                      'H350 follow designer controls; the designer describes the '
                                                      'upper mouth as approximately 60 m. Opaque-band/crown '
                                                      'sections remain image-based estimates, with published '
                                                      'rooftop H375. The low service glazing strip is not a fourth '
                                                      'public floor.'},
                   'galleria': {'start_mm': 445000.0,
                                'end_mm': 450000.0,
                                'sorakara_level_mm': 451200.0,
                                'path_length_mm': 114000.0,
                                'segments': 44,
                                'clear_width_mm': 2400.0,
                                'body_radius_controls_mm': [[438000.0, 11800.0],
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
                                               'width. Radius profile, azimuth and sectional tube are photo-guided '
                                               'approximations, not a surveyed as-built route.'},
                   'lights': {'body_levels_mm': [90000.0, 180000.0, 270000.0, 495000.0],
                              'deck_roof_levels_mm': [371000.0, 375000.0],
                              'galleria_roof_level_mm': 455000.0,
                              'gain_platform_levels_mm': [530000.0, 570000.0, 610000.0],
                              'tmd_roof_level_mm': 632500.0,
                              'lens_half_mm': 150.0,
                              'post_height_mm': 300.0,
                              'scope': 'Eleven controller lenses retained at illustrative exposed supports; not an '
                                       'obstruction-lighting compliance layout.'},
                   'deck_appearance': {'glass_alpha': 0.58}},
        'profile': [[0, 39259.81830489456], [315000, 16000.0], [495000, 9000.0], [497000, 8922.222222222223]],
        'profile_kind': 'triangle_circle_tangent_arcs',
        'deck_specs': [{'id': 'tembo_deck',
                        'level_mm': 350000,
                        'bottom_mm': 333000.0,
                        'glass_bottom_mm': 335000.0,
                        'top_mm': 375000,
                        'radius_mm': 23500,
                        'radius_scope': 'Approximate H350 reference, not maximum equipment-envelope radius.'},
                       {'id': 'tembo_galleria',
                        'level_mm': 450000,
                        'bottom_mm': 438000,
                        'glass_bottom_mm': 445000,
                        'top_mm': 460000.0,
                        'radius_mm': 20000,
                        'radius_scope': 'Approximate outer passage/envelope control; not constant ramp radius.'}],
        'antenna_start_mm': 497000,
        'base_slab_thickness_mm': 2500,
        'source_references': [{'title': '日建設計 NIKKEN JOURNAL 12 / 2012 Autumn pp10-17',
                               'url': 'https://www.nikken.co.jp/ja/insights/publication/journal_archive/p4iusj0000001hyd-att/Journal-2012_Autumn.pdf',
                               'confirmed_rounded_controls_mm': {'H315_diameter': 32000,
                                                                 'H495_diameter': 18000,
                                                                 'sori_radius': 4520000,
                                                                 'mukuri_max_radius': 5950000,
                                                                 'gallery_route_length': 114000,
                                                                 'gain_external_diameter': 6000},
                               'confirmed_facade_angle_degrees': 71,
                               'reference_notes': 'Original designer account: lower principal circular guides '
                                                  'tangent to an upper cone; triangle/circle correspondences each24 '
                                                  'equal perimeter intervals. Rounded dimensions define fitted '
                                                  'principal arcs here, not an exact recovery of all original3D '
                                                  'guides. Published arc radii are reference records, not extra '
                                                  'exact constraints. Gallery azimuth and detailed section stations '
                                                  'remain appearance assumptions.'},
                              {'title': '土屋哲夫 東京スカイツリーのデザイン / 電気設備学会誌32(10) pp721-724',
                               'url': 'https://www.jstage.jst.go.jp/article/ieiej/32/10/32_721/_pdf/-char/en',
                               'confirmed_rounded_controls_mm': {'tembo_deck_reference_diameter': 47000,
                                                                 'upper_horizontal_member_pitch': 5000},
                               'confirmed_facade_angle_degrees': 71,
                               'reference_notes': 'Author is a project designer. Circular observation floor and '
                                                  'outward-sloping facades; horizontal member pitches12.5/10/7.5m '
                                                  'and5m above315m. The150/250m model switch heights for lower '
                                                  'pitches are not published construction levels.'},
                              {'title': '東京スカイツリー 天望デッキ屋上 特別企画 2024-10-15',
                               'url': 'https://www.tokyo-skytree.jp/pdf/pressreleases/02fc6924e036215dc33870cb108fdea823153520240310.pdf',
                               'confirmed_values_mm': {'tembo_deck_rooftop': 375000},
                               'reference_notes': 'Operator identifies the rooftop at375m. This is an '
                                                  'equipment/rooftop reference, not a fourth public observation '
                                                  'floor. Intermediate opaque-envelope radii and band elevations '
                                                  'remain photo-guided approximations.'},
                              {'title': '宮越工芸 東京スカイツリー 空中回廊外装パネル',
                               'url': 'https://www.miyakoshikogei.co.jp/works/81/',
                               'published_approximate_values_mm': {'galleria_diameter': 40000,
                                                                   'galleria_path_length': 110000,
                                                                   'galleria_clear_width': 2400},
                               'reference_notes': 'Fabricator describes approximately40m diameter,110m length,2.4m '
                                                  'passage width; designer Journal quotes114m. These rounded source '
                                                  'accounts are retained separately; the model does not assert an '
                                                  'exact surveyed route.'},
                              {'title': '大林組 制振装置のあるゲイン塔頂部をつくる',
                               'url': 'https://www.obayashi.co.jp/solution_technology/detail/skytree23.html',
                               'confirmed_values_mm': {'body_top': 497000, 'tip': 634000},
                               'published_approximate_values_mm': {'gain_external_diameter': 6000},
                               'reference_notes': 'Upper gain tower has a wider two-storey TMD machine room and a '
                                                  'roof lightning rod reaching634m. Antenna panels, platform '
                                                  'stations and TMD dimensions are photo-guided approximations; '
                                                  'internal dynamics are not simulated.'},
                              {'title': '大林組 ゲイン塔のリフトアップ',
                               'url': 'https://www.obayashi.co.jp/solution_technology/detail/skytree22.html',
                               'reference_notes': 'Six-column hexagonal gain assembly and lift-up construction; no '
                                                  'surveyed antenna/equipment schedule is inferred.'},
                              {'title': '日建設計による解説 ほぼ日 東京スカイツリーうんちく50 2010-09-28',
                               'url': 'https://www.1101.com/skytree/2010-09-28.html',
                               'published_design_stage_approximate_values_mm': {'maximum_tembo_deck_upper_diameter': 60000},
                               'reference_notes': 'Design-team commentary published during construction describes '
                                                  'an upper maximum of approximately60m. The model equipment '
                                                  'envelope near58m is an appearance estimate consistent with this '
                                                  'design-stage scale, not an as-built dimension schedule.'},
                              {'title': '東京スカイツリー 構造設計（日建設計供図）',
                               'url': 'https://www.tokyo-skytree.jp/about/spec/structure/',
                               'confirmed_values_mm': {'ring_vertical_interval': 12500,
                                                       'horizontal_link_interval': 25000,
                                                       'maximum_base_pipe_diameter': 2300,
                                                       'maximum_base_pipe_wall': 100},
                               'reference_notes': 'Three vertex groups of four columns make the kanae trusses. '
                                                  'Circular tubes branch directly by welding rather than large '
                                                  'gusset plates. Ring and radial-link hierarchy informs '
                                                  'appearance. Member-specific diameters/walls, group widths and '
                                                  'every branch position are modelling assumptions, not a recovered '
                                                  'member schedule.'},
                              {'title': '東京スカイツリー 各部紹介',
                               'url': 'https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/parts.php',
                               'confirmed_values_mm': {'lower_legs_connect_height': 50000,
                                                       'base_triangle_side': 68000,
                                                       'circular_transition_height': 315000},
                               'reference_notes': 'The three support groups meet the body at approximately50m; this '
                                                  'does not state the complete vertical extent of the kanae '
                                                  'assembly.'},
                              {'title': '巴コーポレーション 鉄骨製作の概要',
                               'url': 'https://www.tomoe-corporation.co.jp/steel-tower/works/skytree/outline.html',
                               'published_member_ranges_mm': {'kanae_column_diameter': [711.2, 2300],
                                                              'kanae_wall': [28, 100],
                                                              'outer_column_diameter': [1016, 1100],
                                                              'outer_brace_diameter': [508, 1000],
                                                              'horizontal_diameter': [267.4, 609.6],
                                                              'ring_rhs_size': [300, 500],
                                                              'gain_column_diameter': [900, 1200],
                                                              'gain_column_wall': [25, 80]},
                               'reference_notes': 'Ordinary exterior/kanae horizontals use round pipe; horizontal '
                                                  'link and ring trusses also include actual rectangular BX '
                                                  'sections. These families must not be conflated. Manufacturer '
                                                  'ranges cover the fabricated steel families, not diameters at '
                                                  'every model node. The model assigns approximate dimensions '
                                                  'within these ranges. Direct pipe-branch welding guides joint '
                                                  'appearance; no joint capacity or welding specification is '
                                                  'inferred.'},
                              {'title': '大林組 3本脚を地上50mで一体化',
                               'url': 'https://www.obayashi.co.jp/solution_technology/detail/skytree07.html',
                               'confirmed_values_mm': {'lower_legs_connect_height': 50000},
                               'reference_notes': 'Completed-rendering and structural-analysis diagrams show broad '
                                                  'lower steel wings on all three sides, with central pointed-arch '
                                                  'pedestrian openings. Model wing paths, member sizes and fitted '
                                                  'connections are appearance assumptions. The temporary bent '
                                                  'supports at 20/36/50m in construction diagrams are not a '
                                                  'permanent member-level schedule.'},
                              {'title': '日建設計 東京スカイツリー構造と心柱',
                               'url': 'https://www.nikken.co.jp/ja/about/projects_history/corporate_history/12_03.html',
                               'reference_notes': 'Separates the steel body/shaft from the hollow '
                                                  'reinforced-concrete shinbashira. Upper movable core is not '
                                                  'rigidly connected to the added steel radial frame in this '
                                                  'appearance model; no damping response is simulated.'},
                              {'title': '東京スカイツリー アウトライン',
                               'url': 'https://www.tokyo-skytree.jp/about/outline/',
                               'confirmed_values_mm': {'height': 634000,
                                                       'tembo_deck': 350000,
                                                       'tembo_galleria': 450000}},
                              {'title': '東京スカイツリー フロアガイド',
                               'url': 'https://www.tokyo-skytree.jp/floor/',
                               'confirmed_values_mm': {'galleria_start': 445000, 'galleria_end': 450000},
                               'reference_notes': 'Published floor levels340/345/350 and445/450 remain distinct '
                                                  'from the375m equipment rooftop.'},
                              {'title': '東京都 地域資源 東京スカイツリー',
                               'url': 'https://www.chiikishigen.metro.tokyo.lg.jp/introduction/details/introduction_26.html',
                               'confirmed_values_mm': {'approximate_base_triangle_side': 68000,
                                                       'circular_transition_height': 315000}},
                              {'title': '東京スカイツリー 天望デッキ / 天望回廊',
                               'url': 'https://www.tokyo-skytree.jp/floor/',
                               'confirmed_values_mm': {'tembo_floor_340': 340000,
                                                       'tembo_floor_345': 345000,
                                                       'tembo_floor_350': 350000},
                               'reference_notes': 'Floor levels are public references; model radii, glazing '
                                                  'divisions, floor/roof thickness and roof heights are '
                                                  'assumptions.'},
                              {'title': '東京スカイツリー 天望回廊',
                               'url': 'https://www.tokyo-skytree.jp/floor/tembogalleria/',
                               'confirmed_values_mm': {'galleria_start': 445000,
                                                       'galleria_end': 450000,
                                                       'sorakara_point': 451200},
                               'reference_notes': 'The glass tube gallery slopes upward from Floor445 to Floor450. '
                                                  'Model radius, turns, ramp width and entrance/exit positions are '
                                                  'original assumptions.'},
                              {'title': '東京スカイツリー 塔体のしくみ',
                               'url': 'https://www.tokyo-skytree.jp/group/pre-learning/skytree/construction/body.php',
                               'confirmed_values_mm': {'shinbashira_height': 375000,
                                                       'shinbashira_diameter': 8000,
                                                       'lower_wall_thickness': 400,
                                                       'upper_wall_thickness': 600},
                               'reference_notes': 'Published concrete cylinder dimensions inform the visible core. '
                                                  'Model joints, guide frames and spatial representation are '
                                                  'schematic; no damping behaviour or structural capacity is '
                                                  'simulated.'}]
    }
