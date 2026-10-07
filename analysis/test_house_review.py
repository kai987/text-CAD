"""Engineering unit conversion, independent integration and source/area boundaries."""
import copy
import unittest

from analysis.house_review import (
    VALUES, assess_case, build_report, elastic_beam, input_template,
    circulation_review, load_sources, markdown, space_review,
)


def complete_case(support="simple", system="W"):
    return {"id": "test_only", "system": system, "support": support,
            "assumptions_reviewed": True,
            "load_and_material_reference": "Hypothetical test data, not selected house loads",
            "support_and_member_reference": "Ideal prismatic test beam, not a house member",
            "values": dict(zip(VALUES, [4000, 2, 3, 10000, 1e8, 1e6, None, None]))}


def numerical_deflection(case, steps=12000):
    """Independently integrate curvature M(x)/EI and enforce support conditions."""
    v = case["values"]
    L, w, P = v["span_mm"], v["uniform_load_kN_m"], v["point_load_kN"] * 1000
    dx, EI = L / steps, v["E_N_mm2"] * v["I_mm4"]
    curvature = []
    for i in range(steps + 1):
        x = i * dx
        if case["support"] == "simple":
            moment = (w * L + P) * x / 2 - w * x*x / 2 - P * max(0, x - L/2)
        else:
            moment = w * (L-x)**2 / 2 + P * (L-x)
        curvature.append(moment / EI)
    slope, y = [0.0], [0.0]
    for i in range(steps):
        slope.append(slope[-1] + (curvature[i] + curvature[i+1]) * dx/2)
        y.append(y[-1] + (slope[-2] + slope[-1]) * dx/2)
    if case["support"] == "simple":
        y = [v - y[-1] * i / steps for i, v in enumerate(y)]
    return max(abs(v) for v in y)


class BeamTests(unittest.TestCase):
    def test_unit_conversion_and_reactions(self):
        case = complete_case()
        r = elastic_beam(case["values"], "simple")
        self.assertAlmostEqual(r["max_moment_kN_m_magnitude"], 7)
        self.assertAlmostEqual(r["max_shear_kN_magnitude"], 5.5)
        self.assertAlmostEqual(r["elastic_bending_stress_N_mm2"], 7)
        self.assertAlmostEqual(sum(r["reactions"].values()), 11)
        self.assertIsNone(r["structural_capacity_result"])

    def test_numeric_curvature_integration_for_both_supports(self):
        for support in ["simple", "cantilever"]:
            for w, P in [(2, 0), (0, 3), (2, 3)]:
                with self.subTest(support=support, w=w, P=P):
                    case = complete_case(support)
                    case["values"].update(uniform_load_kN_m=w, point_load_kN=P)
                    r = elastic_beam(case["values"], support)
                    self.assertAlmostEqual(r["max_deflection_mm_magnitude"],
                                           numerical_deflection(case), delta=0.00001)

    def test_cantilever_equilibrium(self):
        r = elastic_beam(complete_case("cantilever")["values"], "cantilever")
        self.assertAlmostEqual(r["reactions"]["fixed_vertical_kN"], 11)
        self.assertAlmostEqual(r["reactions"]["fixed_moment_kN_m_magnitude"], 28)

    def test_invalid_and_unknown_loads_never_become_zero(self):
        for key in VALUES:
            for invalid in [True, "2", float("nan"), float("inf"), -1]:
                with self.subTest(key=key, invalid=invalid):
                    case = complete_case()
                    case["values"][key] = invalid
                    with self.assertRaises(ValueError):
                        assess_case(case)
        case = complete_case()
        case["values"]["point_load_kN"] = None
        result = assess_case(case)
        self.assertEqual(result["status"], "awaiting_inputs")
        self.assertIsNone(result["elastic_demand"])

    def test_explicit_review_and_references_required(self):
        for key, value in [("assumptions_reviewed", False), ("load_and_material_reference", ""),
                           ("support_and_member_reference", None)]:
            case = complete_case()
            case[key] = value
            self.assertEqual(assess_case(case)["status"], "awaiting_inputs")

    def test_user_limits_never_create_overall_pass(self):
        case = complete_case()
        case["values"].update(allowable_bending_N_mm2=7, deflection_limit_mm=1)
        r = assess_case(case)
        comparisons = r["elastic_demand"]["user_limit_comparisons"]
        self.assertFalse(comparisons["allowable_bending_N_mm2"]["exceeds_user_limit"])
        self.assertTrue(comparisons["deflection_limit_mm"]["exceeds_user_limit"])
        self.assertEqual(r["status"], "elastic_demand_only")
        self.assertIsNone(r["structural_capacity_result"])

    def test_RC_requires_dedicated_model(self):
        case = complete_case(system="RC")
        self.assertEqual(assess_case(case)["status"], "specialist_RC_model_required")
        self.assertIsNone(assess_case(case)["elastic_demand"])

    def test_overflowed_stiffness_rejected_instead_of_zero_deflection(self):
        case = complete_case()
        case["values"].update(E_N_mm2=1e300, I_mm4=1e300)
        with self.assertRaises(ValueError):
            elastic_beam(case["values"], "simple")


class ModelReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.binding = load_sources()

    def test_current_geometry_and_separate_attic_balcony(self):
        space = space_review(self.data[0], self.data[2])
        expected = 2 * self.data[0]["parameters"]["width"] * self.data[0]["parameters"]["depth"] / 1e6
        self.assertAlmostEqual(space["combined"]["outline_projection_m2"], expected)
        rooms = [r for f in self.data[0]["floors"] for r in f["rooms"] if r["id"] not in {"stairs", "balcony"}]
        self.assertAlmostEqual(space["combined"]["assigned_excluding_stairs_m2"], sum(r["area_m2"] for r in rooms))
        self.assertEqual(len(space["floors"][1]["external_rooms_excluded"]), 1)
        self.assertIsNone(space["statutory_floor_area_m2"])
        self.assertIsNone(space["walkable_unobstructed_area_m2"])

    def test_overlap_and_outside_are_rejected(self):
        for outside in [False, True]:
            plan = copy.deepcopy(self.data[0])
            room = plan["floors"][0]["rooms"][1]
            if outside:
                room["polygon_mm"] = [[-10, 0], [-10, 10], [10, 10], [10, 0]]
                room["area_m2"] = 0.0002
            else:
                other = plan["floors"][0]["rooms"][0]
                room["polygon_mm"] = other["polygon_mm"]
                room["area_m2"] = other["area_m2"]
            with self.assertRaises(ValueError):
                space_review(plan, self.data[2])

    def test_manifest_area_mismatch_rejected(self):
        plan = copy.deepcopy(self.data[0])
        plan["floors"][0]["rooms"][0]["area_m2"] += 1
        with self.assertRaises(ValueError):
            space_review(plan, self.data[2])

    def test_unknown_room_and_duplicate_floor_rejected(self):
        plan = copy.deepcopy(self.data[0])
        plan["floors"][0]["rooms"][0]["id"] = "unknown"
        with self.assertRaises(ValueError):
            space_review(plan, self.data[2])
        plan = copy.deepcopy(self.data[0])
        plan["floors"][1]["floor"] = 1
        with self.assertRaises(ValueError):
            space_review(plan, self.data[2])

    def test_stale_binding_refused(self):
        template = input_template(self.data[1], self.binding)
        template["source_binding"] = {**self.binding, "revision": "old"}
        with self.assertRaises(ValueError):
            build_report(self.data, self.binding, template)

    def test_default_review_keeps_all_capacities_pending(self):
        template = input_template(self.data[1], self.binding)
        report = build_report(self.data, self.binding, template)
        self.assertTrue(report["missing_engineering_inputs"])
        for case in report["member_cases"]:
            self.assertEqual(case["status"], "awaiting_inputs")
            self.assertIsNone(case["elastic_demand"])
        self.assertIsNone(report["structural_capacity_result"])
        self.assertIsNone(report["statutory_compliance_result"])
        self.assertEqual(report["source_binding"], self.binding)
        self.assertIsNone(report["circulation"]["statutory_egress_result"])
        self.assertIn("展开期间的同时通行", markdown(report))

    def test_incomplete_system_specific_schema_rejected(self):
        template = input_template(self.data[1], self.binding)
        del template["system_specific_inputs"]["S"]["local_and_global_buckling"]
        with self.assertRaises(ValueError):
            build_report(self.data, self.binding, template)


class CirculationReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data, _ = load_sources()
        cls.plan, cls.model = data[0], data[2]

    def test_current_saved_portals_and_reproducible_room_paths(self):
        result = circulation_review(self.plan, self.model)
        self.assertFalse(result["conflicts"])
        self.assertEqual(sum(len(f["doors"]) for f in result["floors"]), 14)
        self.assertTrue(all(d["full_width_room_adjacency"] for f in result["floors"] for d in f["doors"]))
        self.assertEqual(result["floors"][0]["room_paths"]["bath"],
                         ["outside", "foyer", "ldk", "wash", "bath"])
        self.assertEqual(result["floors"][1]["room_paths"]["master"], ["stairs", "hall", "master"])
        self.assertIsNone(result["statutory_egress_result"])

    def test_missing_door_is_not_replaced_by_declared_room_connectivity(self):
        plan = copy.deepcopy(self.plan)
        plan["floors"][0]["doors"] = [d for d in plan["floors"][0]["doors"] if d["id"] != "D04"]
        result = circulation_review(plan, self.model)
        self.assertEqual(result["floors"][0]["unreachable_rooms"], ["bath"])
        self.assertTrue(any(c["kind"] == "unreachable_room" for c in result["conflicts"]))

    def test_full_width_adjacency_detects_portal_that_only_has_valid_midpoint(self):
        plan = copy.deepcopy(self.plan)
        door = next(d for d in plan["floors"][1]["doors"] if d["id"] == "D21")
        door["start"] = 3800  # Midpoint 4175 is inside both rooms; endpoint 4550 is outside.
        result = circulation_review(plan, self.model)
        measured = next(d for d in result["floors"][1]["doors"] if d["id"] == "D21")
        self.assertFalse(measured["full_width_room_adjacency"])
        self.assertAlmostEqual(measured["sides"][0]["room_coverage_mm"]["hall"], 480)
        self.assertTrue(any(c["kind"] == "door_room_adjacency" for c in result["conflicts"]))

    def test_wrong_declared_rooms_do_not_create_spurious_graph_edge(self):
        plan = copy.deepcopy(self.plan)
        next(d for d in plan["floors"][0]["doors"] if d["id"] == "D04")["b"] = "wc"
        result = circulation_review(plan, self.model)
        self.assertEqual(result["floors"][0]["unreachable_rooms"], ["bath"])
        self.assertTrue(any(c["kind"] == "door_room_adjacency" for c in result["conflicts"]))

    def test_furniture_envelope_in_portal_is_reported_without_capacity_or_width_claim(self):
        model = copy.deepcopy(self.model)
        sofa = next(o for o in model["furnishings"][0]["objects"] if o["id"] == "sofa")
        door = next(d for d in self.plan["floors"][0]["doors"] if d["id"] == "D02")
        sofa["footprint_mm"] = [door["start"], door["at"]-40, door["start"]+300, door["at"]+40]
        result = circulation_review(self.plan, model)
        measured = next(d for d in result["floors"][0]["doors"] if d["id"] == "D02")
        self.assertEqual(measured["furniture_envelope_overlaps"][0]["envelope_overlap_mm2"], 24000)
        self.assertTrue(any(c["kind"] == "door_furniture_envelope_overlap" for c in result["conflicts"]))
        self.assertIsNone(result["statutory_egress_result"])

    def test_attic_access_containment_and_deployed_operation_restriction_measured(self):
        result = circulation_review(self.plan, self.model)
        access = result["attic_access"]
        self.assertTrue(all(v == 0 for k, v in access.items() if k.endswith("_mm2")))
        self.assertAlmostEqual(access["deployed_operation_occupied_hall_projection_m2"], .8430484945625423)
        scans = access["deployed_hall_vertical_cross_sections"]
        self.assertEqual(scans[-1]["remaining_span_lengths_mm"], [150, 150])
        self.assertEqual(scans[0]["remaining_span_lengths_mm"], [125, 1025])
        self.assertIsNone(access["simultaneous_hall_passage_result"])
        self.assertIsNone(access["headroom_and_ladder_product_safety_result"])

    def test_hatch_outside_hall_is_not_hidden_by_valid_deck_area(self):
        model = copy.deepcopy(self.model)
        bounds = model["attic"]["hatch_bounds_mm"]
        bounds[1] -= 1000
        bounds[4] -= 1000
        result = circulation_review(self.plan, model)
        self.assertEqual(result["attic_access"]["hatch_outside_F2_hall_mm2"], 780000)
        self.assertTrue(any(c["id"] == "attic/hatch_outside_F2_hall_mm2" for c in result["conflicts"]))

    def test_disconnected_ladder_landing_envelope_is_reported_without_crashing(self):
        model = copy.deepcopy(self.model)
        bounds = model["attic"]["ladder"]["bottom_landing_bounds_mm"]
        bounds[0] -= 2200
        bounds[2] -= 2200
        result = circulation_review(self.plan, model)
        self.assertGreater(result["attic_access"]["bottom_landing_outside_F2_hall_mm2"], 0)
        self.assertTrue(result["conflicts"])

    def test_vertical_room_shift_reports_projection_misalignment(self):
        plan = copy.deepcopy(self.plan)
        room = next(r for r in plan["floors"][1]["rooms"] if r["id"] == "wc")
        room["polygon_mm"] = [[x+20, y] for x, y in room["polygon_mm"]]
        result = circulation_review(plan, self.model)
        self.assertEqual(result["vertical_coordination"]["wc"]["lower_projection_outside_upper_mm2"], 36400)
        self.assertTrue(any(c["kind"] == "projection_misalignment" for c in result["conflicts"]))

    def test_invalid_saved_dimensions_and_door_identity_rejected(self):
        for invalid in (True, float("nan"), -1):
            plan = copy.deepcopy(self.plan)
            plan["floors"][0]["doors"][0]["width"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                circulation_review(plan, self.model)
        plan = copy.deepcopy(self.plan)
        plan["floors"][0]["doors"][1]["id"] = plan["floors"][0]["doors"][0]["id"]
        with self.assertRaises(ValueError):
            circulation_review(plan, self.model)
        model = copy.deepcopy(self.model)
        model["furnishings"][0]["objects"][0]["footprint_mm"][2] = float("inf")
        with self.assertRaises(ValueError):
            circulation_review(self.plan, model)
        model = copy.deepcopy(self.model)
        model["furnishings"].pop()
        with self.assertRaises(ValueError):
            circulation_review(self.plan, model)


if __name__ == "__main__":
    unittest.main()
