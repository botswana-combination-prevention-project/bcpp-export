import uuid
from mock import MagicMock

import factory
import numpy as np
import pandas as pd

from datetime import datetime, date, timedelta
from django.test.utils import override_settings

from django.test.testcases import TestCase, TransactionTestCase

from edc_constants.constants import MALE, YES, NOT_APPLICABLE

from bcpp_export.enumerated import enumerated
from bcpp_export.derived_variables import DerivedVariables
from bcpp_export.constants import (
    NEG, POS, UNK, YES, NAIVE, NO, DEFAULTER, edc_ART_PRESCRIPTION, ON_ART, SUBJECT_IDENTIFIER)

from bhp066.apps.bcpp_household.models import Plot
from bhp066.apps.bcpp_household_member.models import HouseholdMember
from bhp066.apps.bcpp_household_member.tests.factories import HouseholdMemberFactory
from bhp066.apps.bcpp_household.models.household import Household
from bhp066.apps.bcpp_household.models.household_structure import HouseholdStructure
from bhp066.apps.bcpp_survey.models.survey import Survey
from bhp066.apps.bcpp_household.models.representative_eligibility import RepresentativeEligibility
from edc.subject.registration.models.registered_subject import RegisteredSubject
from bhp066.apps.bcpp_household.models.household_refusal import HouseholdRefusal
from .bcpp_mixin import BcppMixin

Plot.allow_enrollment = MagicMock(return_value=True)


class TestEnumerated(TestCase, BcppMixin):

    def setUp(self):
        self.mixin_setup()
        self.row = {
            SUBJECT_IDENTIFIER: '111111111-1',
            'consent_date': date(2016, 1, 15),
            'dob': datetime(1992, 1, 15),
            'community': 'digawana',
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
            'identity': None,
            'household_identifier': '99999-9',
        }

    def test_is_enumerated(self):
        members = pd.DataFrame(
            [('99999-9',), ('99999-8', ), ('99997-9', ), ('99996-9', )],
            columns=['household_identifier'])
        self.assertEqual(enumerated(members, self.row), YES)
        members = pd.DataFrame()
        self.assertTrue(pd.isnull(enumerated(members, self.row)))

    def test_is_enrolled(self):
        members = pd.DataFrame(
            [('99999-9',), ('99999-8', ), ('99997-9', ), ('99996-9', )],
            columns=['household_identifier'])
        self.assertEqual(enumerated(members, self.row), YES)
        members = pd.DataFrame()
        self.assertTrue(pd.isnull(enumerated(members, self.row)))
