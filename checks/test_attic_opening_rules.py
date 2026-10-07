import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from lib.attic_opening_rules import review_opening

class OpeningReferencesTests(unittest.TestCase):
    def test_tokyo_example_retains_or_and_strict_ratio_boundary(self):
        self.assertTrue(review_opening('tokyo',.6,10,'fixed_aluminium_louver')['area_reference_match'])
        self.assertTrue(review_opening('tokyo',.9,20,'fixed_aluminium_louver')['area_reference_match'])
        self.assertFalse(review_opening('tokyo',1,20,'fixed_aluminium_louver')['area_reference_match'])
        self.assertIsNone(review_opening('tokyo',.18,24.5384,'fixed_aluminium_louver')['actual_confirming_authority'])

    def test_osaka_checks_form_independently_of_area(self):
        glass=review_opening('osaka',.18,24.5384,'top_hung_glass')
        self.assertTrue(glass['area_reference_match']);self.assertFalse(glass['form_reference_match'])
        self.assertTrue(review_opening('osaka',.18,24.5384,'fixed_aluminium_louver')['form_reference_match'])
        self.assertFalse(review_opening('osaka',.21,24.5384,'fixed_aluminium_louver')['area_reference_match'])

    def test_silence_and_numeric_reference_never_become_permit_approval(self):
        for city in ('tokyo','osaka','kyoto','nagoya'):
            result=review_opening(city,.18,24.5384,'fixed_aluminium_louver')
            self.assertIsNone(result['statutory_compliance_result'])
            self.assertIsNone(result['effective_ventilation_area_m2'])
            if city in ('kyoto','nagoya'):self.assertIsNone(result['area_reference_match'])

    def test_multiple_openings_are_counted_without_assuming_permission(self):
        for city in ('tokyo','osaka','kyoto','nagoya'):
            r=review_opening(city,.18,24.5384,'fixed_aluminium_louver',2)
            self.assertEqual(r['opening_count'],2)
            if city!='tokyo':self.assertIsNone(r['quantity_reference_match'])
            self.assertIsNone(r['statutory_compliance_result'])
        for count in (0,3,True,1.5):
            with self.assertRaises(ValueError):review_opening('osaka',.18,24,'fixed_aluminium_louver',count)

    def test_invalid_values_rejected(self):
        for value in (0,-1,math.inf,math.nan):
            with self.assertRaises(ValueError):review_opening('osaka',value,24,'fixed_aluminium_louver')

if __name__=='__main__':unittest.main()
