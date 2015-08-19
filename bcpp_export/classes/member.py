from copy import copy
from datetime import date

from apps.bcpp_household.choices import HOUSEHOLD_LOG_STATUS
from apps.bcpp_household.constants import ELIGIBLE_REPRESENTATIVE_PRESENT
from apps.bcpp_household.models import Plot
from apps.bcpp_household_member.classes import HouseholdMemberHelper
from apps.bcpp_household_member.constants import (BHS, UNDECIDED, ANNUAL, ABSENT, REFUSED,
                                                  HTC, NOT_ELIGIBLE, REFUSED_HTC)
from apps.bcpp_household_member.models import SubjectRefusal, SubjectAbsenteeEntry
from apps.bcpp_subject.models.subject_consent import SubjectConsent
from apps.bcpp_survey.models import Survey as SurveyModel

from .base import Base
from .household_member import HouseholdMember


class Member(Base):
    """
    For example::
        from apps.bcpp_export.helpers import Subject, Plot as PlotCls, Member
        data_errors = []
        members = []
        for household_member in HouseholdMember.objects.filter(
                is_consented=True, household_structure__household__plot__community='digawana').order_by('-created')[0:25]:
            print household_member.internal_identifier
            member = Member(household_member)
            if member.data_errors:
                data_errors.append(member.data_errors)
            members.append(member)

    See all for on type of message:
        [dct.get('consented') for dct in data_errors if 'consented' in dct]

    """

    def __init__(self, household_member, **kwargs):
        super(Member, self).__init__(**kwargs)
        self.errors = {}
        self.household_member = HouseholdMember(household_member, **kwargs)
        self.revision = self.household_member.revision
        self.internal_identifier = self.household_member.internal_identifier
        self.household = self.household_member.household
        self.registered_subject = self.household_member.registered_subject
        self.update_plot()
        self.update_survey()
        self.update_household()
        self.update_member()
        self.update_member_status()
        self.update_refusal()
        self.update_absentee()

    def __repr__(self):
        return 'Member({0.household_member!r})'.format(self)

    def __str__(self):
        return '{0.household_member!r}'.format(self)

    @property
    def unique_key(self):
        return self.internal_identifier

    def prepare_csv_data(self, delimiter=None):
        """Customizes attribute self.csv_data dictionary."""
        super(Member, self).prepare_csv_data(delimiter=delimiter)
        del self.csv_data['registered_subject']
        del self.csv_data['household_member']
        del self.csv_data['household']
        del self.csv_data['survey']
        del self.csv_data['plot_count_all']

    def update_survey(self):
        """Set attributes related to the surveys the member has been enumerated in."""
        self.surveys_enumerated = [
            hm.household_structure.survey.survey_abbrev.lower() for hm in self.household_member.membership.members]
        self.survey = self.household_member.survey
        for attr, value in self.survey.__dict__.iteritems():
            setattr(self, attr, value)

    def update_plot(self):
        """Sets the plot attributes for this instance using an instance of the Plot model."""
        # self.plot = Plot(household_member=self.household_member)
        plot = Plot.objects.defer(*Plot.encrypted_fields()).get(id=self.household.plot_id)
        attrs = [
            ('plot_identifier', 'plot_identifier'),
            ('location', 'location'),
            ('community', 'community')]
        for attr in attrs:
            setattr(self, attr[1], getattr(plot, attr[0]))

    def update_member(self):
        """Set attributes from the HouseholdMember instance."""
        attrs = [
            ('initials', 'initials'),
            ('age_in_years', 'age_in_years'),
            ('gender', 'gender'),
            ('study_resident', 'study_resident'),
            ('enumeration_first_date', 'enumeration_first_date'),
            ('enumeration_last_date', 'enumeration_last_date'),
            ('consented', 'consented')]
        for attr in attrs:
            setattr(self, attr[1], getattr(self.household_member.membership, attr[0]))
        attrs_to_denormalize = [
            ('created', 'enumeration_date'),
            ('visit_attempts', 'member_visit_attempts'),
            ('study_resident', 'study_resident'),
            ('relation', 'relation_to_hoh'),
            ('absent', 'absent'),
            ('eligible_member', 'eligible_member'),
            ('eligible_subject', 'eligible_subject'),
            ('enrollment_checklist_completed', 'enrollment_checklist_completed'),
            ('enrollment_loss_completed', 'enrollment_loss_completed'),
            ]
        for survey_abbrev in self.survey.survey_abbrevs:
            attr_suffix = survey_abbrev
            self.denormalize(
                attr_suffix, attrs_to_denormalize,
                instance=self.household_member.membership.by_survey.get(survey_abbrev))

    def check_member_status(self, household_member, survey_abbrev):
        try:
            member_status = household_member.member_status
        except AttributeError:
            member_status = None
        if survey_abbrev in self.surveys_enumerated:
            if member_status not in [ANNUAL, ABSENT, BHS, HTC, REFUSED, NOT_ELIGIBLE, REFUSED_HTC]:
                self.output_to_console(
                    'Warning: {initials} plot {plot} has member_status of {status} ({id}).\n'.format(
                        initials=self.initials, plot=self.plot_identifier, status=member_status,
                        id=self.internal_identifier))
            else:
                expected_member_status = HouseholdMemberHelper(household_member).member_status(member_status)
                if member_status != expected_member_status:
                    self.output_to_console('Warning! Expected member_status {} for {}. Got {}\n'.format(
                        expected_member_status, self.household_member, member_status))

    def update_member_status(self):
        """Sets attributes related to member status."""
        for survey_abbrev in self.survey.survey_abbrevs:
            household_member = self.household_member.membership.by_survey.get(survey_abbrev)
            self.check_member_status(household_member, survey_abbrev)
            attrs = [('member_status', 'member_status')]
            self.denormalize(survey_abbrev, attrs, household_member)

    def update_household(self):
        try:
            household = self.household_member.household_structure.household
            self.household_identifier = household.household_identifier
        except AttributeError:
            self.household_identifier = None

    def update_refusal(self):
        """Set attributes related to member refusal, if relevant."""
        fieldattrs = [
            ('refusal_date', 'refusal_date'),
            ('subject_refusal_status', 'refused')]
        fieldattrs_other = [('reason', 'reason_other', 'refusal_reason')]
        for survey_abbrev in self.survey.survey_abbrevs:
            attr_suffix = survey_abbrev
            subject_refusal = self.denormalize(
                attr_suffix, fieldattrs,
                lookup_model=SubjectRefusal,
                lookup_string='household_member',
                lookup_instance=self.household_member.membership.by_survey.get(survey_abbrev)
                )
            self.denormalize_other(
                attr_suffix, fieldattrs_other,
                instance=subject_refusal)

    def update_absentee(self):
        """Set attributes related to member absenteeism, if relevant."""
        fieldattrs = [('report_datetime', 'absent_log_date')]
        fieldattrs_other = [('reason', 'reason_other', 'absent_log_reason')]
        for survey in SurveyModel.objects.all():
            attr_suffix = survey.survey_abbrev
            subject_absentee_entry = self.denormalize(
                attr_suffix, fieldattrs,
                lookup_model=SubjectAbsenteeEntry,
                lookup_string='subject_absentee__household_member',
                lookup_instance=self.household_member.membership.by_survey.get(attr_suffix)
                )
            self.denormalize_other(
                attr_suffix, fieldattrs_other,
                instance=subject_absentee_entry)

    @property
    def data_errors(self):
        """Checks for known data error conditions and returns error messages as a dictionary."""
        data_errors = {'member_status': [], 'enumeration_date': [],
                       'household_status': [], 'consented': [],
                       'household_log': []}
        # 1. test if only uses current HOUSEHOLD_LOG_STATUS options
        condition = list(set(
            [item for item in self.household_log_status if item not in [tpl[0] for tpl in HOUSEHOLD_LOG_STATUS]]
            ))
        if condition:
            data_errors['household_status'].append(
                'Invalid household status options in {}. Got {}'.format(self.community, condition))
        # 2. confirm is_consented agrees with SubjectConsent
        consented = SubjectConsent.objects.filter(household_member=self.household_member).exists
        if self.consented != consented:
            data_errors['consented'].append(
                'household_member.is_consented should be \'{0!r}\' in {1!r}'.format(consented, self.community))
        if self.consented and self.member_status not in [BHS, ANNUAL]:
            data_errors['consented'].append(
                'member_status should be {0!r} for consented member in {1!r}.'.format(BHS, self.community))
        # 3.enumeration date must me in the log
        if self.enumeration_date not in self.household_log_date:
            data_errors['enumeration_date'].append(
                'enumeration date does not match a household log '
                'report date in {}, self.community'.format(self.community))
        # 4. member_status and consented
        if self.member_status == BHS and not self.consented:
            data_errors['member_status'].append(
                'not consented but member_status is {} in {}'.format(BHS, self.community))
        if self.member_status != BHS and self.consented:
            data_errors['member_status'].append(
                'consented but member_status is {} in {}'.format(BHS, self.community))
        # 5. member_status and survey date
        if self.member_status == UNDECIDED and self.member_survey.end_date < date.today():
            data_errors['member_status'].append(
                'member_status cannot be {} for completed {} survey in {}.'.format(
                    UNDECIDED, self.member_survey.name, self.community))
        # log status valid for enumeration
        if ELIGIBLE_REPRESENTATIVE_PRESENT not in self.household_log_status:
            data_errors['household_log'].append('Members enumerated but no valid log entry.')
        self._data_errors = copy(data_errors)
        for k, v in data_errors.iteritems():
            if not v:
                del self._data_errors[k]
        return self._data_errors

#     def update_htc(self):
#         attrs_to_denormalize = [
#             ('offered', 'htc_offered'),
#             ('accepted', 'htc_accepted'),
#             ('date', 'htc_date'),
#             ('refusal_reason', 'htc_refusal_reason'),
#             ('referred', 'htc_referred'),
#             ('referral_clinic', 'htc_referral_clinic'),
#             ('tracking_identifier', 'htc_tracking_identifier')]
#         for survey_abbrev in self.survey.survey_abbrevs:
#             attr_suffix = survey_abbrev
#             htc = Htc(self.household_member.membership.by_survey.get(attr_suffix))
#             self.denormalize(
#                 attr_suffix, attrs_to_denormalize,
#                 instance=htc)
# 
#     def update_htc_status(self):
#         """Sets a htc status attr according to HSPH logic."""
#         for attr_suffix in self.survey.survey_abbrevs:
#             status = None
#             offered = getattr(self, '{}_{}'.format('htc_offered', attr_suffix))
#             accepted = getattr(self, '{}_{}'.format('htc_accepted', attr_suffix))
#             refused = getattr(self, '{}_{}'.format('htc_refusal_reason', attr_suffix))
#             if offered and not accepted:
#                 status = 'offered'
#             elif offered and accepted:
#                 status = 'accepted'
#             elif offered and refused:
#                 status = 'refused'
#             else:
#                 status = None
#         setattr(self, 'htc_status', status)
#
#     def update_hm_status(self):
#         """Sets member status as defined by HSPH.
# 
#         Note: does not consider refused? is None when BHS,
#         if refused, will set to failed checklist even if checklist was not complete
#             .
# 
#         data status_2;
#         merge hh_members (keep=registered_subject_id  eligible_member eligible_subject member_status)
#             undecided (in=a keep=registered_subject_id)
#             refusal (in=b keep=registered_subject_id)
#             absentee (in=c keep=registered_subject_id)
#             consent (in=d keep=registered_subject_id subject_identifier);
#         by registered_subject_id; format status $30.;
# 
#         if eligible_member == '0':
#             status='age_residency_ineligible'
#         if eligible_member == '1' and c and  not b and not a and eligible_subject <>'1':
#             status='absent'
#         if eligible_member == '1' and eligible_subject == '0':
#                 status='failed_checklist';"""
# 
#         options = {
#             'age_residency_ineligible': [NOT_ELIGIBLE, HTC, REFUSED_HTC],
#             'absent': [ABSENT],
#             'failed_checklist': [NOT_ELIGIBLE, HTC, REFUSED_HTC, REFUSED]
#             }
#         for survey_abbrev in self.survey.survey_abbrevs:
#             status = None
#             eligible_member = getattr(self, '{}_{}'.format('eligible_member', survey_abbrev))
#             eligible_subject = getattr(self, '{}_{}'.format('eligible_subject', survey_abbrev))
#             absent = getattr(self, '{}_{}'.format('absent', survey_abbrev))
#             if not eligible_member:
#                 status = 'age_residency_ineligible'
#             elif eligible_member:
#                 if not eligible_subject and absent:
#                     status = 'absent'
#                 elif not eligible_subject:
#                     status = 'failed_checklist'
#             # only set attr if survey was conducted
#             setattr(self, '{}_{}'.format('hm_status', survey_abbrev), status if survey_abbrev in self.surveys_enumerated else None)
#             # get for this survey
#             member_status = getattr(self, '{}_{}'.format('member_status', survey_abbrev))
#             # warn if not equal and survey was conducted
#             if (survey_abbrev in self.surveys_enumerated) and (member_status not in options.get(status) if status else []) and self.verbose:
#                 print 'Warning! member_status <> hm_status. Got {} {}'.format(member_status, status)

