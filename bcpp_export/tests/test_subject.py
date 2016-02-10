from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from edc_constants.constants import NOT_APPLICABLE, YES, NO

from bhp066.apps.bcpp_export.classes import Subject
from bhp066.apps.bcpp_household_member.models import HouseholdMember
from bhp066.apps.bcpp_household_member.tests import BaseTestMember
from bhp066.apps.bcpp_household_member.tests.factories import HouseholdMemberFactory, EnrollmentChecklistFactory
from bhp066.apps.bcpp_household_member.tests.factories import SubjectHtcFactory
from bhp066.apps.bcpp_subject.tests.factories import SubjectConsentFactory


class TestSubject(BaseTestMember):

    def enrollment_checklist(self, household_member, guardian=None):
        return EnrollmentChecklistFactory(
            household_member=household_member,
            report_datetime=datetime.today(),
            gender=household_member.gender,
            dob=date.today() - relativedelta(years=household_member.age_in_years),
            guardian=NO or guardian,
            initials=household_member.initials,
            part_time_resident=household_member.study_resident)

    def test1(self):
        """Assert handles a member not consented"""
        household_member = HouseholdMemberFactory(
            inability_to_participate=NOT_APPLICABLE,
            first_name='ERIK', initials='EW', age_in_years=64,
            study_resident='Yes', household_structure=self.household_structure)
        subject = Subject(household_member)
        self.assertEquals(subject.age_in_years, 64)

    def test2(self):
        """Assert handles a member consented"""
        household_member = HouseholdMemberFactory(
            inability_to_participate=NOT_APPLICABLE,
            first_name='ERIK', initials='EW', age_in_years=64,
            study_resident='Yes', household_structure=self.household_structure)
        self.enrollment_checklist(household_member)
#        household_member.member_status = BHS_ELIGIBLE
        subject_consent = SubjectConsentFactory(
            household_member=household_member, initials=household_member.initials,
            last_name='WWW', dob=date.today() - relativedelta(years=64),
            identity='123456789', identity_type='OMANG')
        subject = Subject(household_member)
        self.assertEqual(subject.subject_consent, subject_consent)

    def test3(self):
        """Assert handles a member not consented and accepted HTC"""
        household_member = HouseholdMemberFactory(
            inability_to_participate=NOT_APPLICABLE,
            first_name='ERIK', initials='EW', age_in_years=64,
            study_resident='Yes', household_structure=self.household_structure)
        subject_htc = SubjectHtcFactory(household_member=household_member, offered=YES, accepted=YES)
        household_member = HouseholdMember.objects.get(household_structure=self.household_structure)
        subject = Subject(household_member)
        self.assertEqual(subject.subject_htc, subject_htc)
        self.assertEqual(subject.subject_identifier, subject_htc.tracking_identifier)

    def test4(self):
        """Assert handles a member not consented and offered but did not accept HTC"""
        household_member = HouseholdMemberFactory(
            inability_to_participate=NOT_APPLICABLE,
            first_name='ERIK', initials='EW', age_in_years=64,
            study_resident='Yes', household_structure=self.household_structure)
        subject_htc = SubjectHtcFactory(household_member=household_member, offered=YES, accepted=NO)
        subject = Subject(household_member)
        self.assertEqual(subject.subject_htc, subject_htc)
        self.assertisNone(subject.subject_identifier)

    def test5(self):
        """Assert subject identifier is None if not consented"""
        household_member = HouseholdMemberFactory(
            inability_to_participate=NOT_APPLICABLE,
            first_name='ERIK', initials='EW', age_in_years=64,
            study_resident='Yes', household_structure=self.household_structure)
        subject = Subject(household_member)
        self.assertisNone(subject.subject_identifier)
