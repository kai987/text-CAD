"""Unfilled engineering brief, separate from geometry acceptance results."""
from __future__ import annotations


def engineering_inputs(p, g):
    return {
        "revision": "R18", "units": "mm; forces kN; distributed loads kN/m2",
        "status": "demonstration only; no structural calculations or permit determination",
        "confirmed_intent": {"main_storeys": 2, "attic_use": "storage only",
                             "candidate_system": "timber post-and-beam"},
        "demonstration_geometry": {"outline_mm": [p.width, p.depth],
                                   "storey_height_mm": p.storey_height,
                                   "roof_pitch_degrees": g.roof_pitch_degrees},
        "site_inputs": {key: None for key in (
            "municipality", "survey_and_road_information", "zoning_and_fire_district",
            "ground_investigation", "allowable_ground_bearing_kN_m2", "settlement",
            "snow_depth_mm", "basic_wind_speed_m_s", "seismic_site_conditions")},
        "material_inputs": {key: None for key in (
            "timber_species_and_grade", "moisture_and_design_strengths",
            "sheathing_specification", "wall_resistance_specification",
            "connection_products_and_capacities", "concrete_grade", "rebar_grade")},
        "load_inputs": {key: None for key in (
            "roof_dead_load_kN_m2", "wall_and_floor_dead_load_kN_m2",
            "residential_live_load_kN_m2", "attic_storage_live_load_kN_m2",
            "shelf_and_box_concentrated_loads_kN", "future_roof_equipment")},
        "required_calculations": [
            "gravity, wind, snow and earthquake load cases and combinations",
            "wall quantity, distribution, torsion and storey drift",
            "floor and roof diaphragm and hatch opening reinforcement",
            "beam/joist bending, shear, deflection and vibration; column stability",
            "joint, hold-down, anchor and uplift capacity",
            "foundation reactions, bearing, settlement and reinforcement",
        ],
        "local_attic_review": {
            "determination": "pending; no building locality selected",
            "example_only": "Nerima treatment is a reference, not the selected jurisdiction",
            "questions": ["maximum finished internal height and actual ceiling treatment",
                          "acceptance of a fixed false ceiling and remaining roof void above it",
                          "statutory projection area, stairs/hatch and corresponding floor area",
                          "storage-only use, openings, equipment and access ladder acceptance"],
            "reference": "https://www.city.nerima.tokyo.jp/kurashi/sumai/takuchi/kentiku-toriatukai.files/all.pdf",
        },
        "unresolved_detail_design": ["insulation, roof ventilation and condensation",
                                     "ceiling suspension/support and roof-void maintenance access",
                                     "fire protection, escape and energy performance",
                                     "ladder product, low-clearance access and fall protection",
                                     "drainage and foundation waterproofing"],
        "capacity_results": None, "statutory_compliance_result": None,
        "designer_and_supervisor": None,
    }
