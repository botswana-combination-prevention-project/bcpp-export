from datetime import datetime, date

import numpy as np
import pandas as pd

from django.test.testcases import TestCase

from bcpp_export.derived_vars import DerivedVariables
from bcpp_export.constants import (
    NEG, POS, UNK, YES, NAIVE, NO, DEFAULTER, edc_ART_PRESCRIPTION, ON_ART, SUBJECT_IDENTIFIER)


class TestSubject(TestCase):

    def setUp(self):
        self.row = {
            SUBJECT_IDENTIFIER: '111111111-1',
            'consent_datetime': datetime(2016, 1, 15),
            'dob': datetime(1992, 1, 15),
            'arv_evidence': None,
            'elisa_hiv_result': None,
            'elisa_hiv_result_date': None,
            'ever_taken_arv': None,
            'has_tested': None,
            'on_arv': None,
            'other_record': None,
            'recorded_hiv_result': None,
            'recorded_hiv_result_date': None,
            'result_recorded': None,
            'result_recorded_date': None,
            'result_recorded_document': None,
            'self_reported_result': None,
            'today_hiv_result': None,
            'today_hiv_result_date': None,
        }

    def test(self):
        self.row.update(
            other_record=UNK,
            recorded_hiv_result=NEG,
            recorded_hiv_result_date=date(2013, 5, 7),
            self_reported_result=NEG,
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status, POS)
        self.assertEqual(obj.final_arv_status, NAIVE)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, NEG)

    def test_final_hiv_status_date(self):
        """Assert date is today's hiv result date."""
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status, POS)
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))
        self.assertTrue(pd.isnull(obj.prev_result))
        self.assertTrue(pd.isnull(obj.prev_result_date))
        self.assertTrue(pd.isnull(obj.prev_result_known))

    def test_prev_result1(self):
        """Assert prev_result is empty when there are no previous results recorded."""
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertTrue(pd.isnull(obj.prev_result))
        self.assertTrue(pd.isnull(obj.prev_result_date))
        self.assertTrue(pd.isnull(obj.prev_result_known))

    def test_prev_result_pos(self):
        """Assert prev_result POS taken from recorded_hiv_result/recorded_hiv_result_date."""
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            recorded_hiv_result=POS,
            recorded_hiv_result_date=date(2015, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.prev_result, POS)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 7))
        self.assertEqual(obj.prev_result_known, YES)

    def test_first_pos_date(self):
        """Assert uses recorded_hiv_result_date as final date since this is the date first POS."""
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            recorded_hiv_result=POS,
            recorded_hiv_result_date=date(2015, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status_date, date(2015, 1, 7))

    def test_prev_result_neg(self):
        """Assert prev_result NEG from recorded_hiv_result."""
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            recorded_hiv_result=NEG,
            recorded_hiv_result_date=date(2015, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, NEG)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 7))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))

    def test_prev_result_neg2(self):
        """Assert prev_result NEG from recorded_hiv_result, ignores result_recorded."""
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            recorded_hiv_result=NEG,
            recorded_hiv_result_date=date(2015, 1, 7),
            result_recorded=POS,
            result_recorded_date=date(2014, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, NEG)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))

    def test_prev_result_none_if_absurd1(self):
        self.row.update(
            today_hiv_result=NEG,
            today_hiv_result_date=date(2016, 1, 7),
            recorded_hiv_result=POS,
            recorded_hiv_result_date=date(2015, 1, 6),
        )
        obj = DerivedVariables(self.row)
        self.assertTrue(pd.isnull(obj.prev_result_known))
        self.assertTrue(pd.isnull(obj.prev_result))
        self.assertTrue(pd.isnull(obj.prev_result_date))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))

    def test_prev_result_none_if_absurd2(self):
        self.row.update(
            today_hiv_result=NEG,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=POS,
            result_recorded_date=date(2015, 1, 6),
        )
        obj = DerivedVariables(self.row)
        self.assertTrue(pd.isnull(obj.prev_result_known))
        self.assertTrue(pd.isnull(obj.prev_result))
        self.assertTrue(pd.isnull(obj.prev_result_date))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))

    def test_prev_result_neg_ignores_absurd_result_recorded(self):
        """Assert prev_result NEG from recorded_hiv_result, ignores result_recorded eventhough it is absurd."""
        self.row.update(
            today_hiv_result=NEG,
            today_hiv_result_date=date(2016, 1, 7),
            recorded_hiv_result=NEG,
            recorded_hiv_result_date=date(2015, 1, 7),
            result_recorded=POS,
            result_recorded_date=date(2014, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status, NEG)
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))
        self.assertEqual(obj.prev_result, NEG)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 7))

    def test_prev_result_pos2(self):
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=POS,
            result_recorded_date=date(2015, 1, 7)
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, POS)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 7))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2015, 1, 7))

    def test_prev_result_neg3(self):
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=NEG,
            result_recorded_date=date(2015, 1, 6),
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, NEG)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 6))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))

    def test_prev_result_missing(self):
        self.row.update(
            today_hiv_result=NEG,
            today_hiv_result_date=date(2016, 1, 7),
        )
        obj = DerivedVariables(self.row)
        self.assertTrue(pd.isnull(obj.prev_result_known))
        self.assertTrue(pd.isnull(obj.prev_result))
        self.assertTrue(pd.isnull(obj.prev_result_date))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status, NEG)
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))

    def test_prev_result_pos3(self):
        """Assert takes recorded_hiv_result over result_recorded."""
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            recorded_hiv_result=POS,
            recorded_hiv_result_date=date(2015, 1, 7),
            result_recorded=NEG,
            result_recorded_date=date(2015, 1, 6),
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, POS)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 7))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2015, 1, 7))

    def test_prev_result_neg4(self):
        """Assert takes recorded_hiv_result over result_recorded."""
        self.row.update(
            today_hiv_result=NEG,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=NEG,
            result_recorded_date=date(2015, 1, 6),
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, NEG)
        self.assertEqual(obj.prev_result_date, date(2015, 1, 6))
        self.assertEqual(obj.final_hiv_date, date(2016, 1, 7))
        self.assertEqual(obj.final_hiv_status_date, date(2016, 1, 7))

    def test_arv_status(self):
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=NEG,
            result_recorded_date=date(2015, 1, 6),
            ever_taken_arv=NO,
            on_arv=NO,
            result_recorded_document=edc_ART_PRESCRIPTION,
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status, POS)
        self.assertEqual(obj.arv_evidence, YES)
        self.assertEqual(obj.final_arv_status, DEFAULTER)

    def test_arv_status_naive(self):
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=NEG,
            result_recorded_date=date(2015, 1, 6),
            ever_taken_arv=NO,
            on_arv=NO,
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status, POS)
        self.assertTrue(pd.isnull(obj.arv_evidence))
        self.assertEqual(obj.final_arv_status, NAIVE)

    def test_arv_status_with_evidence(self):
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=NEG,
            result_recorded_date=date(2015, 1, 6),
            ever_taken_arv=NO,
            on_arv=NO,
            arv_evidence=YES
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status, POS)
        self.assertEqual(obj.arv_evidence, YES)
        self.assertEqual(obj.final_arv_status, DEFAULTER)

    def test_arv_status_on_art(self):
        self.row.update(
            today_hiv_result=POS,
            today_hiv_result_date=date(2016, 1, 7),
            result_recorded=NEG,
            result_recorded_date=date(2015, 1, 6),
            ever_taken_arv=YES,
            on_arv=YES,
            arv_evidence=YES
        )
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.final_hiv_status, POS)
        self.assertEqual(obj.arv_evidence, YES)
        self.assertEqual(obj.final_arv_status, ON_ART)

    def test_age_in_years(self):
        self.row.update(dob=datetime(1992, 1, 15))
        obj = DerivedVariables(self.row)
        self.assertEqual(obj.age_in_years, 24)
