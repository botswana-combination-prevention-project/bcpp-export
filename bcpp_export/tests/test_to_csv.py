import uuid
import random    
import pandas as pd

from django.test.testcases import TestCase

from bcpp_export.dataframes import Subjects, Members, Residences, CombinedDataFrames, CDCDataFrames
from django.test.utils import override_settings


class DummySubjects(Subjects):

    return_values = {}

    def _to_csv(self, df, **options):
        self.return_values.update({uuid.uuid4(): [df, options]})


class DummyCDCDataFrames(CDCDataFrames):
    def __init__(self, *args, **kwargs):
        super(CombinedDataFrames, self).__init__(**kwargs)


class TestToCsv(TestCase):

    def setUp(self):
        df = pd.DataFrame({
            'intervention': pd.Series([1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0]),
            'pair': pd.Series(range(1, 16)),
            'one': pd.Series(range(1, 16), ),
            'two': pd.Series(range(1, 16)),
            'three': pd.Series(range(1, 16)),
            'four': pd.Series(range(1, 16)),
            'five': pd.Series(range(1, 16)),
            'six': pd.Series(range(1, 16)),
        })
        self.intervention_pairs = df[df['intervention'] == 1]['pair']
        self.non_intervention_pairs = df[df['intervention'] == 0]['pair']
        self.all_pairs = df['pair']
        self.df = df

    def filtered_pairs(self, subjects):
        return tuple(sorted(list(subjects.filtered_export_dataframe(self.df).pair)))

    def test_subject_df_filter_pairs_defaults(self):
        subjects = DummySubjects('bcpp-year-1')
        subjects.return_values = {}
        subjects._results = self.df
        self.assertEqual(subjects.export_arms, (1, ))
        self.assertEqual(subjects.export_pairs, (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15))
        self.assertEqual(self.filtered_pairs(subjects), (1, 2, 3, 4, 7, 9, 10, 13, 14))

    def test_subject_df_filter_pairs1(self):
        subjects = DummySubjects('bcpp-year-1', export_arms=(0, 1), export_pairs=range(1, 4))
        subjects.return_values = {}
        subjects._results = self.df
        self.assertEqual(subjects.export_arms, (0, 1))
        self.assertEqual(subjects.export_pairs, (1, 2, 3))
        self.assertEqual(self.filtered_pairs(subjects), (1, 2, 3))

    def test_subject_df_filter_pairs2(self):
        subjects = DummySubjects('bcpp-year-1', export_arms=(1, ), export_pairs=range(1, 6))
        subjects.return_values = {}
        subjects._results = self.df
        self.assertEqual(subjects.export_arms, (1, ))
        self.assertEqual(subjects.export_pairs, (1, 2, 3, 4, 5))
        self.assertEqual(self.filtered_pairs(subjects), (1, 2, 3, 4))

    def test_subject_df_filter_pairs3(self):
        subjects = DummySubjects('bcpp-year-1', export_arms=(1, ), export_pairs=(3, 10))
        subjects.return_values = {}
        subjects._results = self.df
        self.assertEqual(subjects.export_arms, (1, ))
        self.assertEqual(subjects.export_pairs, (3, 10))
        self.assertEqual(self.filtered_pairs(subjects), (3, 10))

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_subject_df_export_columns(self):
        """Assert each object has a list of columns on the class."""
        dfs = DummyCDCDataFrames('bcpp-year-1')
        self.assertTrue(len(dfs.get_export_columns('plots').get('plots')) > 0)
        self.assertTrue(len(dfs.get_export_columns('households').get('households')) > 0)
        self.assertTrue(len(dfs.get_export_columns('members').get('members')) > 0)
        self.assertTrue(len(dfs.get_export_columns('subjects').get('subjects')) > 0)
