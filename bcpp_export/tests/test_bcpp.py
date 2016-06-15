from mock import MagicMock

from django.test.testcases import TestCase
from django.test.utils import override_settings

from bhp066.apps.bcpp_household.models.household_structure import HouseholdStructure
from bhp066.apps.bcpp_survey.models import Survey
from bhp066.apps.bcpp_household.models.plot import Plot
from bhp066.apps.bcpp_household_member.models.household_member import HouseholdMember
from bhp066.apps.bcpp_household_member.constants import BHS_ELIGIBLE

from .bcpp_mixin import BcppMixin

Plot.allow_enrollment = MagicMock(return_value=True)


class TestBcpp(TestCase, BcppMixin):

    def setUp(self):
        self.mixin_setup()

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_household_refusal_mechanism(self):
        """Asserts the household refusal mechanism only updates household structure.refused_enumeration for
        the survey for which the refusal form is entered."""
        self.representative_eligibility(eligible=True)
        self.assertFalse(self.household_structure.refused_enumeration)
        self.household_refusal()
        self.assertTrue(HouseholdStructure.objects.get(
            survey=Survey.objects.get(survey_name=self.survey_data[0][0])).refused_enumeration)
        self.assertFalse(HouseholdStructure.objects.get(
            survey=Survey.objects.get(survey_name=self.survey_data[1][0])).refused_enumeration)
        self.assertFalse(HouseholdStructure.objects.get(
            survey=Survey.objects.get(survey_name=self.survey_data[2][0])).refused_enumeration)

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_household_refusal_does_not_block_enumeration(self):
        """Demonstrates that a household refusal INCORRECTLY! does NOT
        block enumeration."""
        self.representative_eligibility(eligible=True)
        self.household_refusal()
        self.create_members(5)

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_household_enumeration_does_not_block_refusal(self):
        """Demonstrates that a household enumerated correctly accepts a refusal."""
        self.representative_eligibility(eligible=True)
        self.create_members(5)
        self.household_refusal()

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_household_member_member_status_not_update(self):
        """Demonstrates that a household member member status is NOT correctly updated for an ELIGIBLE member."""
        self.representative_eligibility(eligible=True)
        self.create_members(5)
        for obj in HouseholdMember.objects.all():
            self.assertFalse(obj.member_status == BHS_ELIGIBLE)

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_households_enrolled_not_updated_on_consent(self):
        """Demonstrates that a household NOT correctly enrolled on consent of a member."""
        self.representative_eligibility(eligible=True)
        self.create_members(5)
        self.consent_members(1)
        self.assertFalse(self.household_structure.enrolled)
        self.assertFalse(self.household.enrolled)
        # self.assertTrue(self.plot.enrolled)

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_household_enrollment_blocks_refusal(self):
        """Demonstrates that a household enumerated correctly accepts a refusal."""
        self.representative_eligibility(eligible=True)
        self.create_members(5)
        self.consent_members(1)
        self.household_refusal()

    @override_settings(CURRENT_COMMUNITY='test_community', SUBJECT_TYPE=['subject'])
    def test_consent_does_not_block_refusal(self):
        """Demonstrates that a household enumerated and consented accepts a refusal, which it should not."""
        self.representative_eligibility(eligible=True)
        self.create_members(5)
        self.household_refusal()
        self.consent_members(1)
