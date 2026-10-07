"""Validate provenance and publication boundaries of twelve R07 cases.

This check verifies saved inputs and model hashes, not structural capacity.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "output/review"
results = []


def check(name, condition):
    results.append({"check": name, "pass": bool(condition)})


profiles = json.loads((REVIEW/"regulatory_profiles_R07.json").read_text())
house=json.loads((REVIEW/'house_3d_assumptions_R01.json').read_text())
opening=house['attic']['north_vent_opening']
check('opening_gross_area_from_parameters',opening['gross_area_m2']==opening['count']*opening['width_mm']*opening['height_mm']/1e6)
check('current_outline_not_stale',profiles['demonstration_geometry']['outline_mm']==[house['plan_parameters']['width'],house['plan_parameters']['depth']])
for profile in profiles['profiles']:
    review=profile['attic_opening_review']
    check(profile['id']+':opening_matches_geometry',review['opening_area_m2']==opening['gross_area_m2'] and review['opening_form']==opening['form'] and review['opening_count']==opening['count'])
    check(profile['id']+':opening_not_approved',review['statutory_compliance_result'] is None and review['effective_ventilation_area_m2'] is None)
    if profile['id'] in ('kyoto','nagoya'):check(profile['id']+':no_invented_numeric_limit',review['area_reference_match'] is None)
variants = json.loads((REVIEW/"structural_variants_R07.json").read_text())["variants"]
index = json.loads((REVIEW/"structural_cases_R07.json").read_text())
expected = {f"{city}_{system}" for city in ("tokyo", "osaka", "kyoto", "nagoya")
            for system in ("W", "S", "RC")}
check("all_12_cases_exactly_once", len(index["cases"]) == 12 and {c["id"] for c in index["cases"]} == expected)
check("four_jurisdictions", {p["id"] for p in profiles["profiles"]} == {"tokyo", "osaka", "kyoto", "nagoya"})
check("source_verification_date_recorded", bool(profiles["checked_at"]))
sources = profiles["sources"]
if isinstance(sources, dict):
    sources = [{"id": key, **source} for key, source in sources.items()]
source_ids = {s["id"] for s in sources}
check("unique_official_source_ids", len(source_ids) == len(sources))
for source in sources:
    host = urlparse(source["url"]).hostname or ""
    check(f"official_source:{source['id']}", host.endswith(".go.jp") or host.endswith(".lg.jp")
          or host in {"faq.city.nagoya.jp", "www.city.nagoya.jp", "www.city.edogawa.tokyo.jp", "www.pref.aichi.jp"})
for entry in index["cases"]:
    record = json.loads((ROOT/entry["path"]).read_text())
    prefix = entry["id"]
    check(prefix+":opening_review_parity",record["attic_opening_review"]==record["regulatory_profile"]["attic_opening_review"])
    check(f"{prefix}:saved_id", record["case_id"] == prefix)
    check(f"{prefix}:review_profile", record["regulatory_profile"] == next(p for p in profiles["profiles"] if p["id"] == record["city_id"]))
    check(f"{prefix}:national_design_basis", record["national_regulatory_requirements"] == profiles["national_requirements"])
    check(f"{prefix}:structural_scheme", record["structural_scheme"] == variants[record["system"]])
    check(f"{prefix}:unknown_project_inputs", all(v is None for v in record["project_inputs"].values()))
    check(f"{prefix}:not_calculated_or_approved", all(record[key] is None for key in (
        "capacity_results", "statutory_compliance_result", "building_confirmation_result", "architectural_coordination_result")))
    check(f"{prefix}:no_arbitrary_city_sizing", record["city_driven_member_sizing"] is False)
    check(f"{prefix}:system_specific_design_tasks", len(record["required_system_checks"]) >= 5)
    check(f"{prefix}:foundation_design_tasks", len(record["required_foundation_checks"]) >= 3)
    for kind, path in record["model_paths"].items():
        check(f"{prefix}:{kind}_hash", hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == record["model_hashes_sha256"][kind])
    # Resolve every referenced source nested in the selected city profile.
    def resolve(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "source_ids":
                    check(f"{prefix}:source_references", set(item).issubset(source_ids))
                else: resolve(item)
        elif isinstance(value, list):
            for item in value: resolve(item)
    resolve(record["regulatory_profile"])
    resolve(record["national_regulatory_requirements"])

report = {"scope": "saved case integrity and official-source provenance; no engineering verification",
          "checks": len(results), "passed": sum(r["pass"] for r in results), "results": results}
(REVIEW/"structural_cases_validation_R07.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
print(f"Case integrity: {report['passed']}/{report['checks']} passed")
failures = [r["check"] for r in results if not r["pass"]]
if failures:
    raise SystemExit("Failed: "+", ".join(failures))
