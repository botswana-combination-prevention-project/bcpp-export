from datetime import date

import numpy as np
import pandas as pd

from django.test.testcases import TestCase

from bcpp_export.derived_vars import DerivedVariables
from bcpp_export.constants import NEG, POS, UNK, YES, NAIVE


class TestSubject(TestCase):

    def test(self):
        row = {
            'subject_identifier': '111111111-1',
            'arv_evidence': None,
            'ever_taken_arv': None,
            'has_tested': YES,
            'result_recorded_document': None,
            'on_arv': None,
            'other_record': UNK,
            'recorded_hiv_result': NEG,
            'recorded_hiv_result_date': date(2013, 5, 7),
            'result_recorded': None,
            'result_recorded_date': None,
            'self_reported_result': NEG,
            'today_hiv_result': POS,
            'today_hiv_result_date': date(2016, 1, 7),
            'elisa_hiv_result': None,
            'elisa_hiv_result_date': None,
        }

        obj = DerivedVariables(row)
        self.assertEqual(obj.final_hiv_status, POS)
        self.assertEqual(obj.final_arv_status, NAIVE)
        self.assertEqual(obj.prev_result_known, YES)
        self.assertEqual(obj.prev_result, NEG)

#     def test(self):
#         row = {
#             'subject_identifier': '111111111-1',
#             'self_reported_result': NEG,
#             'arv_evidence': None,
#             'ever_taken_arv': None,
#             'has_tested': YES,
#             'result_recorded_document': None,
#             'on_arv': None,
#             'other_record': UNK,
# 
#             'recorded_hiv_result': NEG,
#             'recorded_hiv_result_date': date(2013, 5, 7),
#             'result_recorded': None,
#             'result_recorded_date': None,
#             'today_hiv_result': POS,
#             'elisa_hiv_result': None,
#         }
# 
#         obj = DerivedVariables(row)
#         self.assertEqual(obj.final_hiv_status, POS)
#         self.assertEqual(obj.final_arv_status, NAIVE)
#         self.assertEqual(obj.prev_result_known, YES)
#         self.assertEqual(obj.prev_result, NEG)
