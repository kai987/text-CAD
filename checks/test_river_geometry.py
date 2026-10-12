"""Physical datum, source-parameter and independent solid checks for the demo."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from lib.river_geometry import (GROUPS,R,bridge_dimensions,center_x,geometry_manifest,
                                lamp_positions,river_assembly,section_offsets,
                                stairs_positions,tree_positions,validate_parameters)


class RiverParametersTests(unittest.TestCase):
    def test_invalid_bank_or_elevation_is_rejected(self):
        for parameters in (replace(R,width=30000),replace(R,water_z=R.bed_z),
                           replace(R,bridge_y=R.length),replace(R,sample_count=2)):
            with self.assertRaises(ValueError):
                validate_parameters(parameters)

    def test_edited_width_updates_bridge_and_bank_positions(self):
        parameters=replace(R,water_width=22000)
        validate_parameters(parameters)
        self.assertEqual(bridge_dimensions(parameters)["span"],42000)
        self.assertEqual(section_offsets(parameters)["water_edge"],11000)
        self.assertAlmostEqual(bridge_dimensions(parameters)["start_x"],
                               center_x(parameters.bridge_y,parameters)-21000)

    def test_access_and_landscape_are_outside_clear_crest_paths(self):
        for stair in stairs_positions():
            self.assertEqual(stair["risers"],14)
            self.assertAlmostEqual(stair["riser"]*stair["risers"],R.crest_z-R.platform_z)
            self.assertEqual(stair["tread"],250)
        for tree in tree_positions():
            centre=abs(tree["x"]-center_x(tree["y"]))
            self.assertGreater(centre-tree["radius"],section_offsets()["path_outer"])
        for lamp in lamp_positions():
            self.assertGreater(abs(lamp["x"]-center_x(lamp["y"]))-180,
                               section_offsets()["path_outer"])


class RiverSolidTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assembly=river_assembly()
        cls.parts={part.label:part for part in cls.assembly.children}

    def test_named_groups_and_all_solids_are_valid(self):
        self.assertEqual(set(self.parts),set(GROUPS))
        labels=[]
        for group in self.parts.values():
            self.assertTrue(group.is_valid,group.label)
            self.assertGreater(len(group.solids()),0,group.label)
            labels.extend(child.label for child in group.children)
        self.assertEqual(len(labels),len(set(labels)))

    def test_water_and_bridge_have_real_separate_datums(self):
        water=self.parts["River:water"].bounding_box()
        bed=next(child for child in self.parts["River:bed"].children
                 if child.label=="River:bed:channel").bounding_box()
        deck=self.parts["Bridge:deck"].bounding_box()
        beams=self.parts["Bridge:beams"].bounding_box()
        self.assertAlmostEqual(water.max.Z,R.water_z,places=4)
        self.assertAlmostEqual(water.min.Z,bed.max.Z,places=4)
        self.assertAlmostEqual(self.parts["River:water"].volume,
                               R.length*(R.water_width-R.submerged_bank_run)*(R.water_z-R.bed_z),delta=1)
        self.assertAlmostEqual(deck.max.Z,R.bridge_top_z,places=4)
        self.assertGreater(beams.min.Z,water.max.Z)
        self.assertAlmostEqual(deck.size.X,bridge_dimensions()["span"],places=4)

    def test_saved_manifest_has_bounds_and_no_engineering_claim(self):
        manifest=geometry_manifest(assembly=self.assembly)
        self.assertAlmostEqual(manifest["bbox"]["min"][0],-R.width/2,places=4)
        self.assertAlmostEqual(manifest["bbox"]["max"][1],R.length/2,places=4)
        self.assertTrue(all(value is None for value in manifest["engineering"].values()))
        self.assertEqual(manifest["revision"],"RIVER-R01")


if __name__=="__main__":
    unittest.main()
