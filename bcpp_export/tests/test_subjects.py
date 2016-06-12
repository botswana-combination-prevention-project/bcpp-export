from django.test.testcases import TestCase

from bcpp_export.dataframes.subjects import Subjects
from bcpp_export.tests.bcpp_mixin import BcppMixin


class TestSubjects(TestCase, BcppMixin):

    def setUp(self):
        self.mixin_setup()

    def test_subject_df(self):
        subjects = Subjects('bcpp-year-1')
        columns = subjects.results.columns
