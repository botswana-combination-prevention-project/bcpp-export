import re

from edc_constants.constants import NOT_APPLICABLE, POS

from bhp066.apps.bcpp_clinic.models import ClinicConsent, Questionnaire, ClinicVlResult
from bhp066.apps.bcpp_household_member.constants import CLINIC_RBD
from bhp066.apps.bcpp_household.models import Plot
from bhp066.apps.bcpp_lab.models.subject_requisition import SubjectRequisition
from bhp066.apps.bcpp_subject.models import (
    SubjectConsent, SubjectReferral, HivTestingHistory,
    HivCareAdherence, Pregnancy, HivUntested, HivTestReview,
    HivTested, SubjectLocator, Pima)

from .base import Base
from .member import Member
from ..mixins import SubjectDataFixMixin
from .specimen import Specimen
from .survey import Survey


class Subject(Base, SubjectDataFixMixin):

    def __init__(self, household_member, **kwargs):
        super(Subject, self).__init__(**kwargs)
        self.member = Member(household_member, **kwargs)
        self.revision = self.member.revision
        self.household_member = self.member.household_member
        self.household = self.household_member.household_structure.household
        self.registered_subject = self.member.registered_subject
        self.internal_identifier = self.member.internal_identifier
        self.community = self.member.community
        self.survey = Survey(self.community, **kwargs)
        for survey_abbrev in self.survey.survey_abbrevs:
            fieldattrs = [('member_status', 'member_status')]
            self.denormalize(survey_abbrev, fieldattrs, self.member.household_member.membership.by_survey.get(survey_abbrev))
        self.update_plot(**kwargs)
        self.update_household(**kwargs)
        self.update_subject_consent()
        self.update_subject_referral()
        self.update_subject_locator()
        self.update_hiv_and_art()
        self.update_pregnancy()
        self.update_pima()
        self.update_viral_load(**kwargs)
        self.update_from_clinic_forms()  # RBD clinic
        self.apply_data_fixes()

    def __repr__(self):
        return '{0}({1.household_member!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.household_member!s}'.format(self)

    @property
    def unique_key(self):
        return self.internal_identifier

    def prepare_csv_data(self):
        super(Subject, self).prepare_csv_data()
        self.csv_data['revision'] = self.revision
        del self.csv_data['household_member']
        del self.csv_data['registered_subject']
        del self.csv_data['member']
        del self.csv_data['household']
        del self.csv_data['subject_consent']
        del self.csv_data['survey']

    def apply_data_fixes(self):
        """Applies data_fixes defined in individual methods."""
        self.fix_referred_yesno()
        self.fix_clinic_citizen(self.household_member.household_member)
        self.fix_clinic_member_status(self.subject_consent)
        self.fix_subject_member_status(self.subject_consent)

    def update_plot(self, **kwargs):
        """Sets the plot attributes for this instance using an instance of the Plot model."""
        plot = Plot.objects.defer(*Plot.encrypted_fields()).get(id=self.household.plot_id)
        attrs = [
            ('plot_identifier', 'plot_identifier'),
            ('location', 'location'),
            ('community', 'community')]
        for attr in attrs:
            setattr(self, attr[1], getattr(plot, attr[0]))

    def update_household(self, **kwargs):
        if self.location == 'clinic':
            self.household_identifier = None
        else:
            self.household_identifier = self.household.household_identifier

    def update_subject_consent(self):
        try:
            if self.location == 'clinic':
                self.subject_consent = ClinicConsent.objects.defer(*ClinicConsent.encrypted_fields()).get(
                    registered_subject=self.registered_subject)
            else:
                self.subject_consent = SubjectConsent.objects.defer(*SubjectConsent.encrypted_fields()).get(
                    registered_subject=self.registered_subject)
            # self.consenting_household_member = self.subject_consent.household_member
            self.age_in_years = self.subject_consent.age
            self.citizen = self.subject_consent.citizen
            self.consent_datetime = self.subject_consent.consent_datetime
            self.date_of_birth = self.subject_consent.dob
            # self.first_name = self.subject_consent.first_name
            self.gender = self.subject_consent.gender
            self.identity = self.subject_consent.identity
            self.identity_type = self.subject_consent.identity_type
            # self.last_name = self.subject_consent.last_name
            self.spouse_of_citizen = None if NOT_APPLICABLE else self.subject_consent.legal_marriage
            self.subject_identifier = self.subject_consent.subject_identifier
            self.survey_consented = self.subject_consent.household_member.survey.survey_abbrev
        except (SubjectConsent.DoesNotExist, ClinicConsent.DoesNotExist):
            self.age_in_years = self.household_member.age_in_years
            self.citizen = None
            self.consent_datetime = None
            # self.consenting_household_member = None
            self.date_of_birth = None
            # self.first_name = self.household_member.first_name
            self.gender = self.household_member.gender
            self.identity = None
            self.identity_type = None
            # self.last_name = None
            self.spouse_of_citizen = None
            self.subject_consent = None
            self.subject_identifier = None
            self.survey_consented = None

    def update_from_clinic_forms(self):
        """Updates hiv status, arv clinic, etc for Clinic consented subjects.

        Clinic consented subjects do not have a subject referral."""
        class ClinicAssumptions(object):
            """Simple class for values not in any form to be passed as an instance to denormalize()."""
            def __init__(self, subject_consent, community, survey_abbrev):
                self.hiv_result = None
                self.arv_clinic = None
                self.member_status = None
                if subject_consent.household_member.household_structure.survey.survey_abbrev.lower() == survey_abbrev:
                    self.hiv_result = POS
                    self.arv_clinic = community
                    self.member_status = CLINIC_RBD

        self.htc_identifier = None
        self.pims_identifier = None
        if self.location == 'clinic':
            fieldattrs = [('hiv_result', 'hiv_result'),
                          ('arv_clinic', 'arv_clinic'),
                          ('member_status', 'member_status')]
            for survey_abbrev in self.survey.survey_abbrevs:
                clinic_assumptions = ClinicAssumptions(self.subject_consent, self.community, survey_abbrev)
                self.denormalize(survey_abbrev, fieldattrs, clinic_assumptions)

            fieldattrs = [('on_arv', 'on_art'),
                          ('cd4_count', 'cd4_value')]
            for survey_abbrev in self.survey.survey_abbrevs:
                self.denormalize(
                    survey_abbrev, fieldattrs,
                    lookup_model=Questionnaire,
                    lookup_string='clinic_visit__household_member',
                    lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))

            fieldattrs = [('result_value', 'vl_result'),
                          ('collection_datetime', 'vl_drawn_datetime'),
                          ('assay_date', 'vl_assay_datetime')]
            for survey_abbrev in self.survey.survey_abbrevs:
                self.denormalize(
                    survey_abbrev, fieldattrs,
                    lookup_model=ClinicVlResult,
                    lookup_string='clinic_visit__household_member',
                    lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))
            # fill in other identifiers used (only applied to clinic
            pattern = re.compile(r'^[0-9]{2}\-[0-9]{2}\-[0-9]{3}\-[0-9]{2}$')
            if re.search(pattern, self.subject_consent.htc_identifier or ''):
                self.htc_identifier = self.subject_consent.htc_identifier
            self.pims_identifier = self.subject_consent.pims_identifier

    def update_subject_referral(self):
        if self.subject_consent and self.location == 'household':
            if not SubjectReferral.objects.filter(
                    subject_visit__household_member__id=self.household_member.household_member.id).exists():
                self.output_to_console(
                    'Warning! SubjectReferral not found for consented subject. '
                    'See {}\n'.format(self.subject_identifier))
        fieldattrs = [('subject_referred', 'referred'),
                      ('referral_appt_date', 'referral_appt_date'),
                      ('referral_clinic', 'referral_clinic'),
                      ('referral_code', 'referral_code'),
                      ('hiv_result', 'hiv_result'),
                      ('hiv_result_datetime', 'hiv_result_date'),
                      ('new_pos', 'new_pos'),
                      ('on_art', 'on_art'),
                      ('pregnant', 'pregnant'),
                      ('circumcised', 'circumcised'),
                      ('permanent_resident', 'permanent_resident'),
                      ('part_time_resident', 'part_time_resident'),
                      ('arv_clinic', 'arv_clinic'),
                      ('arv_documentation', 'arv_documentation'),
                      ('direct_hiv_documentation', 'direct_hiv_documentation'),
                      ('indirect_hiv_documentation', 'indirect_hiv_documentation'),
                      ('verbal_hiv_result', 'verbal_hiv_result'),
                      ('todays_hiv_result', 'todays_hiv_result'),
                      ('last_hiv_result', 'last_hiv_result'),
                      ('last_hiv_result_date', 'last_hiv_result_date'),
                      ]
        for survey_abbrev in self.survey.survey_abbrevs:
            self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=SubjectReferral,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))

    def update_hiv_and_art(self):
        for survey_abbrev in self.survey.survey_abbrevs:
            # HivTestingHistory
            fieldattrs = [('has_tested', 'has_tested')]
            self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=HivTestingHistory,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))
            # HivTestReview
            fieldattrs = [('recorded_hiv_result', 'recorded_hiv_result')]
            self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=HivTestReview,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))
            # HivTested
            fieldattrs = [('where_hiv_test', 'where_hiv_test')]
            fieldattrs_other = [('where_hiv_test', 'where_hiv_test_other', 'where_hiv_test')]
            hiv_tested = self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=HivTested,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))
            self.denormalize_other(
                survey_abbrev, fieldattrs_other,
                instance=hiv_tested)
            # HivCareAdherence
            fieldattrs = [('ever_taken_arv', 'ever_taken_arv')]
            self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=HivCareAdherence,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))
            # HivUntested
            fieldattrs = [('why_no_hiv_test', 'why_no_hiv_test')]
            self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=HivUntested,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))

    def update_pregnancy(self):
        for survey_abbrev in self.survey.survey_abbrevs:
            fieldattrs = [('anc_reg', 'anc_reg')]
            self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=Pregnancy,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))

    def update_subject_locator(self):
        try:
            subject_locator = SubjectLocator.objects.defer(*SubjectLocator.encrypted_fields()).get(
                registered_subject=self.registered_subject)
            self.home_visit_permission = subject_locator.home_visit_permission
            self.may_follow_up = subject_locator.may_follow_up
        except SubjectLocator.DoesNotExist:
            self.home_visit_permission = None
            self.may_follow_up = None

    def update_pima(self):
        fieldattrs = [('pima_today', 'cd4_tested'),
                      ('cd4_datetime', 'cd4_date'),
                      ('cd4_value', 'cd4_value')]
        model_cls = Pima
        for survey_abbrev in self.survey.survey_abbrevs:
            pima = self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=model_cls,
                lookup_string='subject_visit__household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev)
            )
            try:
                setattr(self, '{}_{}'.format('cd4_not_tested_reason', survey_abbrev),
                        pima.pima_today_other if not pima.pima_today_other.upper() == 'OTHER' else pima.pima_today_other_other)
            except AttributeError:
                setattr(self, '{}_{}'.format('cd4_not_tested_reason', survey_abbrev), None)

    def update_viral_load(self, **kwargs):
        for survey_abbrev in self.survey.survey_abbrevs:
            try:
                subject_requisition = SubjectRequisition.objects.defer(
                    *SubjectRequisition.encrypted_fields()).get(
                    subject_visit__household_member=self.member.household_member.membership.by_survey.get(survey_abbrev),
                    panel__name='Viral Load')
                specimen = Specimen(
                    subject_requisition,
                    subject_identifier=self.subject_identifier,
                    survey_abbrev=survey_abbrev,
                    **kwargs)
                vl_result, vl_drawn_datetime, vl_assay_date = [], [], []
                for results in specimen.lis_results.itervalues():
                    for result in results:
                        vl_result.append('{}{}'.format(result.lis_result_quantifier, result.lis_result))
                        vl_drawn_datetime.append(result.drawn_datetime)
                        vl_assay_date.append(result.lis_assay_date)
                setattr(self, '{}_{}'.format('vl_result', survey_abbrev), vl_result)
                setattr(self, '{}_{}'.format('vl_drawn_datetime', survey_abbrev), vl_drawn_datetime)
                setattr(self, '{}_{}'.format('vl_assay_datetime', survey_abbrev), vl_assay_date)
            except SubjectRequisition.DoesNotExist:
                setattr(self, '{}_{}'.format('vl_result', survey_abbrev), None)
                setattr(self, '{}_{}'.format('vl_drawn_datetime', survey_abbrev), None)
                setattr(self, '{}_{}'.format('vl_assay_datetime', survey_abbrev), None)
