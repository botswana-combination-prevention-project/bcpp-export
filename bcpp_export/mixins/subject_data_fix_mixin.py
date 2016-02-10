from collections import namedtuple

from edc_constants.constants import YES, NO

from bhp066.apps.bcpp_household_member.constants import BHS, CLINIC_RBD, ANNUAL
from bhp066.apps.bcpp_household_member.classes import HouseholdMemberHelper
from bhp066.apps.bcpp_clinic.models import ClinicEligibility

from .console_mixin import ConsoleMixin


class SubjectDataFixMixin(ConsoleMixin):

    def fix_referred_yesno(self):
        """Fixes values that are incorrect due to a previous source code bug (Data Fix #1096)."""
        if str(self.referred_y1) == '1':
            self.referred_y1 = YES
        if str(self.referred_y1) == '2':
            self.referred_y1 = NO

    def fix_clinic_citizen(self, household_member):
        """Gets citizen from Eligibility until Consent is fixed (Bug #1094)."""
        if not self.citizen:
            try:
                clinic_eligibility = ClinicEligibility.objects.get(
                    household_member=household_member)
                self.citizen = clinic_eligibility.citizen
            except ClinicEligibility.DoesNotExist:
                pass

    def fix_clinic_member_status(self, clinic_consent):
        """Sets member_status to CLINIC_RDB until bug is fixed where signal flips to BHS_ELIGIBLE (Bug #1095)."""
        NamedTpl = namedtuple('Tpl', 'member_status')
        if self.location == 'clinic':
            fieldattrs = [('member_status', 'member_status')]
            for survey_abbrev in self.survey.survey_abbrevs:
                if (clinic_consent.household_member.household_structure.survey.survey_abbrev.lower() ==
                        survey_abbrev):
                    namedtpl = NamedTpl(member_status=CLINIC_RBD)
                else:
                    namedtpl = NamedTpl(member_status=None)
                self.denormalize(survey_abbrev, fieldattrs, namedtpl)

    def fix_subject_member_status(self, subject_consent):
        """Sets member_status to BHS until data is fixed (Data Fix #1097)."""
        NamedTpl = namedtuple('Tpl', 'member_status')
        if self.location == 'household':
            fieldattrs = [('member_status', 'member_status')]
            for survey_abbrev in self.survey.survey_abbrevs:
                if (subject_consent.household_member.household_structure.survey.survey_abbrev.lower() ==
                        survey_abbrev):
                    household_member_helper = HouseholdMemberHelper(subject_consent.household_member)
                    expected_member_status = household_member_helper.member_status(None)
                    if expected_member_status not in [BHS, ANNUAL]:
                        self.output_to_console(
                            'Warning! Member status does not match '
                            'for {}. Expected BHS. Got {}.\n'.format(subject_consent, expected_member_status)
                        )
                    if getattr(self, 'member_status_{}'.format(survey_abbrev)) not in [BHS, ANNUAL]:
                        namedtpl = NamedTpl(member_status=BHS)
                        self.denormalize(survey_abbrev, fieldattrs, namedtpl)
