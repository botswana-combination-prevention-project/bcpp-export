import os

import pandas as pd

from bcpp_export import urls  # DO NOT DELETE

from bhp066.apps.bcpp_subject.models import (
    SubjectReferral, SubjectConsent, Circumcision, ElisaHivResult, HivCareAdherence, HivResult,
    HivResultDocumentation, HivTestReview, HivTestingHistory, Pima, ReproductiveHealth,
    ResidencyMobility, SubjectVisit)

from ..constants import gender, hiv_options, tf, yes_no, SUBJECT_IDENTIFIER, HOUSEHOLD_MEMBER, PLOT_IDENTIFIER
from ..datetime_to_date import datetime_to_date
from ..derived_variables import DerivedVariables

from .csv_export_mixin import CsvExportMixin


class Subjects(CsvExportMixin):

    """A class to generate a dataset of bcpp subject data for a given survey year.

        from bcpp_export.dataframes.subjects import Subjects
        s = Subjects('bcpp-year-1')
        s.results

        from bcpp_export.dataframes.subjects import Subjects
        s = Subjects('bcpp-year-1')
        s.to_csv()

    """

    def __init__(self, survey_name, merge_on=None, add_identity256=None, **kwargs):
        super(Subjects, self).__init__(**kwargs)
        self.merge_on = merge_on or HOUSEHOLD_MEMBER
        self.add_identity256 = True if add_identity256 is True else False
        if self.merge_on not in (SUBJECT_IDENTIFIER, HOUSEHOLD_MEMBER):
            raise TypeError(
                'Invalid merge_on column. Expected one of {}.'.format((SUBJECT_IDENTIFIER, HOUSEHOLD_MEMBER)))
        self._circumcised = pd.DataFrame()
        self._hiv_care_adherence = pd.DataFrame()
        self._hiv_result_documentation = pd.DataFrame()
        self._hiv_test_review = pd.DataFrame()
        self._hiv_testing_history = pd.DataFrame()
        self._reproductive_health = pd.DataFrame()
        self._residency_mobility = pd.DataFrame()
        self._results = pd.DataFrame()
        self._subject_consents = pd.DataFrame()
        self._subject_visits = pd.DataFrame()
        self._subject_households = pd.DataFrame()
        self._subject_pimas = pd.DataFrame()
        self._subject_referrals = pd.DataFrame()
        self._today_hiv_result = pd.DataFrame()
        self._elisa_hiv_result = pd.DataFrame()
        self.survey_name = survey_name

    @property
    def results(self):
        if self._results.empty:
            self.merge_dataframes()
            self.map_edc_responses_to_numerics()
            self.add_derived_columns()
        return self._results

    def merge_dataframes(self):
        """Left Merge all dataframes starting with subject_consent into
        a single dataframe on subject_identifier or household_member.

        All methods that return dataframes are prefixed with 'df_'."""
        drop_column = SUBJECT_IDENTIFIER if self.merge_on == HOUSEHOLD_MEMBER else HOUSEHOLD_MEMBER
        self.df_subject_households.drop(drop_column, axis=1, inplace=True)
        self._results = pd.merge(
            self.df_subject_consents, self.df_subject_households, how='left', on=self.merge_on)
        for attrname in dir(self):
            if attrname.startswith('df_') and attrname not in ('df_subject_consents', 'df_subject_households'):
                suffix = '_' + ''.join([s[0] for s in attrname.split('_')])
                df = getattr(self, attrname)
                df.drop(drop_column, axis=1, inplace=True)
                self._results = pd.merge(
                    self._results, df, how='left', on=self.merge_on, suffixes=['', suffix])

    def map_edc_responses_to_numerics(self):
        """Map responses from edc raw data, mostly strings, to numerics."""
        self._results['arv_evidence'] = self._results['arv_evidence'].map(yes_no.get)
        self._results['cd4_tested'] = self._results['cd4_tested'].map(yes_no.get)
        self._results['circumcised'] = self._results['circumcised'].map(yes_no.get)
        self._results['citizen'] = self._results['citizen'].map(yes_no.get)
        self._results['ever_taken_arv'] = self._results['ever_taken_arv'].map(yes_no.get)
        self._results['has_tested'] = self._results['has_tested'].map(yes_no.get)
        self._results['on_arv'] = self._results['on_arv'].map(yes_no.get)
        self._results['other_record'] = self._results['other_record'].map(yes_no.get)
        self._results['permanent_resident'] = self._results['permanent_resident'].map(yes_no.get)
        self._results['pregnant'] = self._results['pregnant'].map(yes_no.get)
        self._results['referred'] = self._results['referred'].map(yes_no.get)
        self._results['spouse_of_citizen'] = self._results['spouse_of_citizen'].map(yes_no.get)
        self._results['gender'] = self._results['gender'].map(gender.get)
        self._results['part_time_resident'] = self._results['part_time_resident'].map(tf.get)
        self._results['recorded_hiv_result'] = self._results['recorded_hiv_result'].map(hiv_options.get)
        self._results['result_recorded'] = self._results['result_recorded'].map(hiv_options.get)
        self._results['self_reported_result'] = self._results['self_reported_result'].map(hiv_options.get)
        self._results['today_hiv_result'] = self._results['today_hiv_result'].map(hiv_options.get)
        self._results['elisa_hiv_result'] = self._results['elisa_hiv_result'].map(hiv_options.get)

    def add_derived_columns(self):
        attrnames = [
            'timestamp',
            'age_in_years',
            'arv_evidence',
            'final_arv_status',
            'final_hiv_status',
            'final_hiv_status_date',
            'prev_result',
            'prev_result_date',
            'prev_result_known',
            'pair',
            'intervention',
        ]
        if self.add_identity256:
            attrnames.append('identity256')
        for attrname in attrnames:
            self._results[attrname] = self._results.apply(
                lambda row: getattr(DerivedVariables(row), attrname), axis=1)

    @property
    def df_subject_consents(self):
        """Return a dataframe of a selection of the subject's consent values."""
        if self._subject_consents.empty:
            columns = [SUBJECT_IDENTIFIER, 'id', 'citizen', 'dob', 'gender', 'consent_datetime',
                       'identity', 'identity_type', 'household_member_id', 'registered_subject_id',
                       'community', 'legal_marriage']
            qs = SubjectConsent.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._subject_consents = df.rename(columns={
                'household_member_id': HOUSEHOLD_MEMBER,
                'id': 'consent',
                'legal_marriage': 'spouse_of_citizen',
                'registered_subject_id': 'registered_subject',
                'consent_datetime': 'consent_date',
            })
            self._subject_consents['consent_date'] = self._subject_consents.apply(
                lambda row: datetime_to_date(row['consent_date']), axis=1)
        return self._subject_consents

    @property
    def df_subject_households(self):
        """Return a dataframe of the subject's household and plot identifier."""
        if self._subject_households.empty:
            columns = [
                SUBJECT_IDENTIFIER, HOUSEHOLD_MEMBER,
                'household_member__household_structure',
                'household_member__household_structure__household__household_identifier',
                'household_member__household_structure__household__plot__plot_identifier',
                'household_member__household_structure__survey__survey_slug']
            qs = SubjectConsent.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name).exclude(
                household_member__household_structure__household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_member__household_structure': 'household_structure',
                'household_member__household_structure__household__household_identifier': 'household_identifier',
                'household_member__household_structure__household__plot__plot_identifier': PLOT_IDENTIFIER,
                'household_member__household_structure__survey__survey_slug': 'survey'})
            self._subject_households = df
        return self._subject_households

    @property
    def df_subject_visits(self):
        """Return a dataframe of a selection of the subject's visit values."""
        if self._subject_visits.empty:
            columns = [
                'household_member',
                'report_datetime',
                'appointment__visit_definition__code',
                'household_member__registered_subject',
                'household_member__registered_subject__subject_identifier',
            ]
            qs = SubjectVisit.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._subject_visits = df.rename(columns={
                'report_datetime': 'visit_date',
                'household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'household_member': HOUSEHOLD_MEMBER,
                'appointment__visit_definition__visit_code': 'visit_code',
            })
            self._subject_visits['visit_date'] = self._subject_visits.apply(
                lambda row: datetime_to_date(row['visit_date']), axis=1)
        return self._subject_visits

    @property
    def df_subject_referrals(self):
        """Return a dataframe of a selection of the subject's referral values."""
        if self._subject_referrals.empty:
            columns = [
                'subject_visit__household_member__registered_subject__subject_identifier',
                'subject_visit__household_member',
                'arv_clinic', 'export_uuid', 'referral_clinic', 'referral_code', 'subject_referred',
                'part_time_resident', 'vl_sample_drawn_datetime']
            qs = SubjectReferral.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._subject_referrals = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'subject_referred': 'referred',
                'vl_sample_drawn_datetime': 'vl_drawn_date',
            })
            self._subject_referrals['vl_drawn_date'] = self._subject_referrals.apply(
                lambda row: datetime_to_date(row['vl_drawn_date']), axis=1)
        return self._subject_referrals

    @property
    def df_today_hiv_result(self):
        """Return a dataframe of a selection of values from today's hiv test result, if performed."""
        if self._today_hiv_result.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'hiv_result', 'hiv_result_datetime', 'why_not_tested']
            qs = HivResult.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._today_hiv_result = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'hiv_result': 'today_hiv_result',
                'hiv_result_datetime': 'today_hiv_result_date',
                'why_not_tested': 'reason_not_tested_today'})
            self._today_hiv_result['today_hiv_result_date'] = self._today_hiv_result.apply(
                lambda row: datetime_to_date(row['today_hiv_result_date']), axis=1)
        return self._today_hiv_result

    @property
    def df_elisa_hiv_result(self):
        """Return a dataframe of a selection of values from today's hiv test result, if performed."""
        if self._elisa_hiv_result.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'hiv_result', 'hiv_result_datetime']
            qs = ElisaHivResult.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._elisa_hiv_result = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'hiv_result': 'elisa_hiv_result',
                'hiv_result_datetime': 'elisa_hiv_result_date'})
            if not self._elisa_hiv_result.empty:
                self._elisa_hiv_result['elisa_hiv_result_date'] = self._elisa_hiv_result.apply(
                    lambda row: datetime_to_date(row['elisa_hiv_result_date']), axis=1)
        return self._elisa_hiv_result

    @property
    def df_hiv_testing_history(self):
        if self._hiv_testing_history.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'has_tested', 'other_record', 'verbal_hiv_result']
            qs = HivTestingHistory.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_testing_history = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'verbal_hiv_result': 'self_reported_result',
            })
        return self._hiv_testing_history

    @property
    def df_hiv_test_review(self):
        if self._hiv_test_review.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'recorded_hiv_result', 'hiv_test_date']
            qs = HivTestReview.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_test_review = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'hiv_test_date': 'recorded_hiv_result_date'})
        return self._hiv_test_review

    @property
    def df_hiv_result_documentation(self):
        if self._hiv_result_documentation.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'result_recorded', 'result_date', 'result_doc_type']
            qs = HivResultDocumentation.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_result_documentation = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'result_date': 'result_recorded_date',
                'result_doc_type': 'result_recorded_document'})
        return self._hiv_result_documentation

    @property
    def df_hiv_care_adherence(self):
        if self._hiv_care_adherence.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'ever_taken_arv', 'on_arv', 'arv_evidence',
                       'clinic_receiving_from']
            qs = HivCareAdherence.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_care_adherence = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER})
        return self._hiv_care_adherence

    @property
    def df_circumcised(self):
        if self._circumcised.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'circumcised']
            qs = Circumcision.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._circumcised = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER})
        return self._circumcised

    @property
    def df_reproductive_health(self):
        if self._reproductive_health.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'currently_pregnant']
            qs = ReproductiveHealth.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._reproductive_health = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'currently_pregnant': 'pregnant'})
        return self._reproductive_health

    @property
    def df_residency_mobility(self):
        if self._residency_mobility.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'permanent_resident']
            qs = ResidencyMobility.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._residency_mobility = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER})
        return self._residency_mobility

    @property
    def df_subject_pimas(self):
        """Return a dataframe of a selection of the subject's pima/cd4 values."""
        if self._subject_pimas.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'pima_today', 'pima_today_other', 'cd4_datetime', 'cd4_value']
            qs = Pima.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._subject_pimas = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'pima_today': 'cd4_tested',
                'pima_today_other': 'cd4_not_tested_reason',
                'cd4_datetime': 'cd4_date'})
            self._subject_pimas['cd4_date'] = self._subject_pimas.apply(
                lambda row: datetime_to_date(row['cd4_date']), axis=1)
        return self._subject_pimas
