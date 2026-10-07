"""Join verified jurisdiction references with uncalculated structural concepts.

Cities select regulatory review profiles, not invented member capacities.
Every saved case records missing project inputs and leaves engineering and
permit results unfilled. Run after generate_structural_variants.py.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lib.attic_opening_rules import CHECKED_AT, RULES, SOURCES, review_opening

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "output/review"
SYSTEM_CHECKS = {
    "W": [
        "Actual building weight and current required wall quantity/column-size rules",
        "Wall distribution, torsion, diaphragm stiffness and storey drift",
        "Beam/joist bending, shear, deflection and column stability",
        "Sheathing specification, hold-down forces and certified joint capacities",
        "Attic storage and concentrated loads; hatch headers and low-clearance access",
    ],
    "S": [
        "Select an approved lightweight steel system, steel grade and section specification",
        "Thin-wall local/distortional buckling, global stability and bracing effectiveness",
        "Brace tension/compression behaviour and load reversal; no assumed brace resistance",
        "Gusset, bolt/screw/weld, base-plate and anchor capacity",
        "Diaphragm specification, drift, corrosion protection and fire-resistance assemblies",
    ],
    "RC": [
        "Concrete and reinforcement grades; actual self-weight and mass model",
        "Column/beam axial-bending interaction, shear, joint forces and ductility",
        "Slab/hatch reinforcement, deflection, cracking and diaphragm transfer",
        "Shear-wall arrangement, torsion, drift and applicable structural calculation route",
        "Rebar layout, anchorage, splices, cover, durability and construction joints",
        "Architectural coordination of thick members with rooms, openings and attic clearance",
    ],
}
COMMON_INPUTS = (
    "street_address_and_confirming_authority", "surveyed_site_and_road_access",
    "use_zoning_floor_area_ratio_building_coverage_height_and_setbacks",
    "fire_and_quasi_fire_district_and_local_designation",
    "ground_investigation_and_liquefaction", "soil_bearing_settlement_and_foundation_level",
    "site_elevation_snow_zone_terrain_and_wind_exposure",
    "actual_dead_live_snow_wind_and_earthquake_loads",
    "attic_use_area_access_and_authority_interpretation",
    "material_grades_design_strengths_and_connections",
    "selected_structural_calculation_route_and_designer",
)


def generate():
    regulations = json.loads((REVIEW / "regulatory_profiles_R07.json").read_text())
    structural = json.loads((REVIEW / "structural_variants_R07.json").read_text())
    variants = structural["variants"]
    profiles = regulations["profiles"]
    house=json.loads((REVIEW / "house_3d_assumptions_R01.json").read_text())
    attic=house['attic']; opening=attic['north_vent_opening']
    regulations['attic_opening_checked_at']=CHECKED_AT
    regulations['attic_opening_revision']='R20'
    regulations['demonstration_geometry']['outline_mm']=[house['plan_parameters']['width'],house['plan_parameters']['depth']]
    existing={item['id'] for item in regulations['sources']}
    regulations['sources'].extend(item for item in SOURCES if item['id'] not in existing)
    for profile in profiles:
        profile['attic_opening_rule']=RULES[profile['id']]
        profile['attic_opening_review']=review_opening(profile['id'],opening['gross_area_m2'],attic['storage_projection_area_m2'],opening['form'],opening['count'])
        profile['attic_opening_review'].update({'width_mm':opening['width_mm'],'height_mm':opening['height_mm']})
    (REVIEW / "regulatory_profiles_R07.json").write_text(json.dumps(regulations,ensure_ascii=False,indent=2)+'\n')
    assert {p["id"] for p in profiles} == {"tokyo", "osaka", "kyoto", "nagoya"}
    assert set(variants) == {"W", "S", "RC"}
    destination = REVIEW / "cases"
    destination.mkdir(parents=True, exist_ok=True)
    cases = []
    for profile in profiles:
        for system in ("W", "S", "RC"):
            variant = variants[system]
            model_paths = {"glb": variant["glb_path"], "step": variant["step_path"]}
            case = {
                "revision": "R07", "case_id": f"{profile['id']}_{system}",
                "city_id": profile["id"], "city_name": profile["name"], "system": system,
                "status": "conditional_demonstration_not_engineered",
                "purpose": "Compare candidate load paths and jurisdiction review inputs",
                "model_paths": model_paths,
                "model_hashes_sha256": {kind: hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
                                        for kind, path in model_paths.items()},
                "regulatory_reference": "output/review/regulatory_profiles_R07.json",
                "structural_reference": "output/review/structural_variants_R07.json",
                "regulatory_profile": profile,
                "national_regulatory_requirements": regulations["national_requirements"],
                "structural_scheme": variant,
                "project_inputs": {key: None for key in COMMON_INPUTS},
                "required_system_checks": SYSTEM_CHECKS[system],
                "required_foundation_checks": [
                    "Recalculate gravity, lateral and uplift reactions for the selected system",
                    "Bearing, differential settlement, sliding, overturning and liquefaction",
                    "Foundation bending/shear, punching, reinforcement and anchor development",
                    "Drainage, waterproofing, frost/site conditions and adjacent foundations",
                ],
                "city_driven_member_sizing": False,
                "shared_geometry_explanation": (
                    "The same uncalculated material-system geometry is shared across cities. "
                    "Official regional reference parameters are not site-specific design loads. "
                    "Sizing must be recalculated after the actual site and load conditions are known."),
                "architectural_geometry_baseline": "R20-3D; current coordinated layout and fixed aluminium north attic louver",
                "attic_opening_review": profile["attic_opening_review"],
                "architectural_coordination_result": None,
                "capacity_results": None, "statutory_compliance_result": None,
                "building_confirmation_result": None,
            }
            path = f"output/review/cases/{case['case_id']}_R07.json"
            (ROOT/path).write_text(json.dumps(case, ensure_ascii=False, indent=2)+"\n")
            cases.append({"id": case["case_id"], "city_id": profile["id"], "system": system,
                          "path": path, "model_paths": model_paths, "status": case["status"]})
    manifest = {"revision": "R07", "case_count": len(cases), "cases": cases,
                "status": "conditional_demonstration_not_engineered",
                "capacity_results": None, "statutory_compliance_result": None}
    (REVIEW/"structural_cases_R07.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    print(f"Prepared {len(cases)} jurisdiction/material cases; calculation and approval results remain unfilled.")
    return manifest


if __name__ == "__main__":
    generate()
