import uuid
from mock import MagicMock

from datetime import timedelta, date
from django.utils import timezone

from bcpp_export.constants import YES, NO

from bhp066.apps.bcpp_household.models import Plot
from bhp066.apps.bcpp_household_member.tests.factories import HouseholdMemberFactory
from bhp066.apps.bcpp_household.models.household import Household
from bhp066.apps.bcpp_household.models.household_structure import HouseholdStructure
from bhp066.apps.bcpp_survey.models.survey import Survey
from bhp066.apps.bcpp_household.models.representative_eligibility import RepresentativeEligibility
from edc.subject.registration.models.registered_subject import RegisteredSubject
from bhp066.apps.bcpp_household.models.household_refusal import HouseholdRefusal
from bhp066.apps.bcpp_household_member.models.household_member import HouseholdMember
from bhp066.apps.bcpp_subject.models.subject_consent import SubjectConsent
from dateutil.relativedelta import relativedelta
from bhp066.apps.bcpp_household_member.constants import BHS_ELIGIBLE
from edc_consent.models.consent_type import ConsentType

Plot.allow_enrollment = MagicMock(return_value=True)
SubjectConsent.matches_enrollment_checklist = MagicMock(return_value=True)
SubjectConsent.prepare_appointments = MagicMock(return_value=True)


class BcppMixin(object):

    counter = 0
    survey_data = [('bcpp-year-1', -1, 364), ('bcpp-year-2', 364 + 1, 364), ('bcpp-year-3', (364 * 2) + 1, 364)]

    def mixin_setup(self):
        self.counter = 0
        ConsentType.objects.create(
            app_label='bcpp_subject',
            model_name='subjectconsent',
            start_datetime=timezone.now() + timedelta(days=-1),
            end_datetime=timezone.now() + relativedelta(years=4),
            version='1'
        )
        self.plot = Plot.objects.create(community='test_community', household_count=1)
        for data in self.survey_data:
            self.survey = Survey.objects.create(
                survey_name=data[0],
                datetime_start=timezone.now() + timedelta(days=data[1]),
                datetime_end=timezone.now() + timedelta(days=data[2]),
            )
        self.household = Household.objects.get(plot=self.plot)
        for survey in Survey.objects.all():
            HouseholdStructure.objects.create(
                household=self.household, survey=survey)
        self.household_structure = HouseholdStructure.objects.get(survey=Survey.objects.get(survey_name='bcpp-year-1'))

    @property
    def subject_identifier(self):
        self.counter += 1
        yield '066-10000-{}'.format(self.counter + 1)

    @property
    def registered_subject(self):
        yield RegisteredSubject.objects.create(
            subject_type='subject',
            subject_identifier=next(self.subject_identifier),
            registration_identifier=uuid.uuid4())

    def representative_eligibility(self, eligible=None, **kwargs):
        options = dict(
            household_structure=self.household_structure,
            report_datetime=timezone.now(),
            aged_over_18=YES if eligible else NO,
            household_residency=YES,
            verbal_script=YES,
        )
        options.update(**kwargs)
        return RepresentativeEligibility.objects.create(
            **options)

    def household_refusal(self):
        return HouseholdRefusal.objects.create(
            household_structure=self.household_structure,
            report_datetime=timezone.now())

    def create_members(self, count):
        for i in range(0, count - 1):
            rs = next(self.registered_subject)
            HouseholdMemberFactory(
                household_structure=self.household_structure,
                registered_subject=rs,
                internal_identifier=rs.registration_identifier,
            )

    def consent_members(self, count):
        for household_member in HouseholdMember.objects.filter(household_structure=self.household_structure):
            count -= 1
            household_member.member_status = BHS_ELIGIBLE
            SubjectConsent.objects.create(
                household_member=household_member,
                consent_datetime=timezone.now(),
                gender='M',
                identity='99919999{}'.format(count),
                confirm_identity='99919999{}'.format(count),
                dob=date.today() - relativedelta(years=25),
                is_literate=YES)
            if not count:
                break
