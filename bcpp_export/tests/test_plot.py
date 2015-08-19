from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from edc.constants import NOT_APPLICABLE, YES, NO

from apps.bcpp_export.classes import Subject, Plot as PlotCls
from apps.bcpp_household_member.models import HouseholdMember
from apps.bcpp_household_member.tests import BaseTestMember
from apps.bcpp_household_member.tests.factories import HouseholdMemberFactory, EnrollmentChecklistFactory
from apps.bcpp_household_member.tests.factories import SubjectHtcFactory
from apps.bcpp_subject.tests.factories import SubjectConsentFactory
from apps.bcpp_household.tests.factories.plot_factory import PlotFactory


class TestPlot(BaseTestMember):

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
        """Assert handles plot"""
        plot = PlotFactory(community='test_community')
        self.assertTrue(PlotCls(plot))
