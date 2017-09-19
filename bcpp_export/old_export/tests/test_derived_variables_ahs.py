from datetime import datetime, date

import numpy as np
import pandas as pd

from django.test.testcases import TestCase

from bcpp_export.derived_variables import DerivedVariables
from bcpp_export.constants import (
    NEG, POS, UNK, YES, IND, NAIVE, NO, DEFAULTER, edc_ART_PRESCRIPTION, ON_ART, SUBJECT_IDENTIFIER)
from dateutil.relativedelta import relativedelta

from bcpp_export.dataframes.longitudinal_subjects import LongitudinalSubjects


class TestDerivedVariablesAhs(TestCase):

    def setUp(self):
        row1 = {
            'subject_identifier': '111111111-1',
            'consent_date': date(2015, 1, 15),
            'visit_date': date(2015, 1, 15),
            'dob': datetime(1992, 1, 15),
            'community': 'digawana',
            'arv_evidence': np.nan,
            'elisa_hiv_result': np.nan,
            'elisa_hiv_result_date': np.nan,
            'ever_taken_arv': np.nan,
            'has_tested': np.nan,
            'on_arv': np.nan,
            'other_record': np.nan,
            'recorded_hiv_result': np.nan,
            'recorded_hiv_result_date': np.nan,
            'result_recorded': np.nan,
            'result_recorded_date': np.nan,
            'result_recorded_document': np.nan,
            'self_reported_result': np.nan,
            'today_hiv_result': np.nan,
            'today_hiv_result_date': np.nan,
            'identity': np.nan,
            'household_identifier': '99999-9',
            'final_hiv_result': np.nan,
            'final_hiv_result_date': np.nan,
            'prev_result': np.nan,
            'prev_result_date': np.nan,
            'prev_result_known': np.nan,
        }

        row2 = {
            'subject_identifier': '111111111-1',
            'consent_date': date(2016, 1, 15),
            'visit_date': date(2016, 1, 15),
            'dob': datetime(1992, 1, 15),
            'community': 'digawana',
            'arv_evidence': np.nan,
            'elisa_hiv_result': np.nan,
            'elisa_hiv_result_date': np.nan,
            'ever_taken_arv': np.nan,
            'has_tested': np.nan,
            'on_arv': np.nan,
            'other_record': np.nan,
            'recorded_hiv_result': np.nan,
            'recorded_hiv_result_date': np.nan,
            'result_recorded': np.nan,
            'result_recorded_date': np.nan,
            'result_recorded_document': np.nan,
            'self_reported_result': np.nan,
            'today_hiv_result': np.nan,
            'today_hiv_result_date': np.nan,
            'identity': np.nan,
            'household_identifier': '99999-9',
            'final_hiv_result': np.nan,
            'final_hiv_result_date': np.nan,
            'prev_result': np.nan,
            'prev_result_date': np.nan,
            'prev_result_known': np.nan,
        }
        df_y1 = pd.DataFrame()
        for n in range(1, 15):
            d = {}
            row1['subject_identifier'] = '11111111-{}'.format(n)
            for key in row1:
                d.update({key: [row1[key]]})
            tmp = pd.DataFrame(d)
            df_y1 = df_y1.append(tmp, ignore_index=True)

        df_y2 = pd.DataFrame()
        for n in range(1, 15):
            d = {}
            row2['subject_identifier'] = '11111111-{}'.format(n)
            for key in row2:
                d.update({key: [row2[key]]})
            tmp = pd.DataFrame(d)
            df_y2 = df_y2.append(tmp, ignore_index=True)
        self.df = pd.merge(df_y1, df_y2, how='left', on='subject_identifier', suffixes=['', '_y1'])

    def test1(self):
        subject_identifier = '11111'
        last_year = datetime.today() - relativedelta(years=1)
        self.df.loc[0, 'subject_identifier'] = subject_identifier
        self.df.loc[0, 'final_hiv_result'] = 1
        self.df.loc[0, 'final_hiv_result_date'] = last_year

        subjects = LongitudinalSubjects(self.df)
        df_y2 = subjects.dataframe

        self.assertEqual(
            df_y2[df_y2['subject_identifier'] == subject_identifier]['final_hiv_result'].item(), 1)
        self.assertEqual(
            df_y2[df_y2['subject_identifier'] == subject_identifier]['final_hiv_result_date'].astype(date).item(), last_year)

    def test2(self):
        """Assert if tests NEG in both years uses y2 test date."""
        y1_date = datetime.today() - relativedelta(years=1)
        y2_date = datetime.today()

        hiv_results_y1 = [NEG, NEG, NEG, NEG, np.nan, np.nan, NEG, np.nan]
        hiv_results_y2 = [NEG, POS, IND, UNK, NEG, POS, np.nan, np.nan]
        hiv_results_ex = [NEG, POS, IND, UNK, NEG, POS, np.nan, np.nan]  # expected
        hiv_result_dates_ex = [y2_date, y2_date, y2_date, y2_date, y2_date, y2_date, np.nan, np.nan]  # expected

        self.assertTrue(len(hiv_results_y1) == len(hiv_results_y2) == len(hiv_results_ex) == len(hiv_result_dates_ex))

        for index, final_hiv_result in enumerate(hiv_results_y2):
            self.df.loc[index, 'final_hiv_result'] = final_hiv_result
            if not pd.isnull(final_hiv_result):
                self.df.loc[index, 'final_hiv_result_date'] = y2_date

        for index, final_hiv_result in enumerate(hiv_results_y1):
            self.df.loc[index, 'final_hiv_result_y1'] = final_hiv_result
            if not pd.isnull(final_hiv_result):
                self.df.loc[index, 'final_hiv_result_date_y1'] = y1_date

        subjects = LongitudinalSubjects(self.df)
        df_y2 = subjects.dataframe

        self.assertTrue(
            df_y2['final_hiv_result'][0:len(hiv_results_ex)].equals(pd.Series(hiv_results_ex, dtype=float)))

        self.assertTrue(
            df_y2['final_hiv_result_date'][0:len(hiv_results_ex)].equals(pd.Series(hiv_result_dates_ex)))

    def test3(self):
        """Assert if tests POS in both years uses y1 test date."""
        y1_date = datetime.today() - relativedelta(years=1)
        y2_date = datetime.today()

        hiv_results_y1 = [POS, POS, NEG]
        hiv_results_y2 = [POS, np.nan, POS]
        hiv_results_ex = [POS, POS, POS]  # expected
        hiv_result_dates_ex = [y1_date, y1_date, y2_date]  # expected

        self.assertTrue(len(hiv_results_y1) == len(hiv_results_y2) == len(hiv_results_ex) == len(hiv_result_dates_ex))

        for index, final_hiv_result in enumerate(hiv_results_y2):
            self.df.loc[index, 'final_hiv_result'] = final_hiv_result
            if not pd.isnull(final_hiv_result):
                self.df.loc[index, 'final_hiv_result_date'] = y2_date

        for index, final_hiv_result in enumerate(hiv_results_y1):
            self.df.loc[index, 'final_hiv_result_y1'] = final_hiv_result
            if not pd.isnull(final_hiv_result):
                self.df.loc[index, 'final_hiv_result_date_y1'] = y1_date

        subjects = LongitudinalSubjects(self.df)
        df_y2 = subjects.dataframe

        self.assertTrue(
            df_y2['final_hiv_result'][0:len(hiv_results_ex)].equals(pd.Series(hiv_results_ex, dtype=float)))

        self.assertTrue(
            df_y2['final_hiv_result_date'][0:len(hiv_results_ex)].equals(pd.Series(hiv_result_dates_ex)))

    def test4(self):
        """Assert if tests UNK or IND takes current."""
        y1_date = datetime.today() - relativedelta(years=1)
        y2_date = datetime.today()

        hiv_results_y1 = [UNK, UNK, UNK, IND, IND, IND]
        hiv_results_y2 = [NEG, POS, np.nan, np.nan, NEG, POS]
        hiv_results_ex = [NEG, POS, np.nan, np.nan, NEG, POS]  # expected
        hiv_result_dates_ex = [y2_date, y2_date, np.nan, np.nan, y2_date, y2_date]  # expected

        self.assertTrue(len(hiv_results_y1) == len(hiv_results_y2) == len(hiv_results_ex) == len(hiv_result_dates_ex))

        for index, final_hiv_result in enumerate(hiv_results_y2):
            self.df.loc[index, 'final_hiv_result'] = final_hiv_result
            if not pd.isnull(final_hiv_result):
                self.df.loc[index, 'final_hiv_result_date'] = y2_date

        for index, final_hiv_result in enumerate(hiv_results_y1):
            self.df.loc[index, 'final_hiv_result_y1'] = final_hiv_result
            if not pd.isnull(final_hiv_result):
                self.df.loc[index, 'final_hiv_result_date_y1'] = y1_date

        subjects = LongitudinalSubjects(self.df)
        df_y2 = subjects.dataframe

        self.assertTrue(
            df_y2['final_hiv_result'][0:len(hiv_results_ex)].equals(pd.Series(hiv_results_ex, dtype=float)))

        self.assertTrue(
            df_y2['final_hiv_result_date'][0:len(hiv_results_ex)].equals(pd.Series(hiv_result_dates_ex)))
