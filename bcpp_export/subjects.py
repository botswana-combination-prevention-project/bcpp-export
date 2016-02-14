import pandas as pd
import numpy as np
import os

from dateutil.relativedelta import relativedelta

from django.utils import timezone

from bcpp_export import urls

from bhp066.apps.bcpp_subject.models import SubjectReferral, SubjectConsent
from bhp066.apps.bcpp_subject.models.hiv_result import HivResult
from bhp066.apps.bcpp_subject.models.hiv_test_review import HivTestReview
from bhp066.apps.bcpp_subject.models.hiv_testing_history import HivTestingHistory
from bhp066.apps.bcpp_subject.models.pima import Pima

from bhp066.apps.bcpp_subject.models.hiv_result_documentation import HivResultDocumentation
from bhp066.apps.bcpp_subject.models.hiv_care_adherence import HivCareAdherence
from bhp066.apps.bcpp_subject.models.circumcision import Circumcision
from bhp066.apps.bcpp_subject.models.reproductive_health import ReproductiveHealth
from bhp066.apps.bcpp_subject.models.residency_mobility import ResidencyMobility

SUBJECT_IDENTIFIER = 'subject_identifier'
DEFAULTER = 2
ON_ART = 3
NAIVE = 1
DWTA = 'DWTA'
POS = 1
NEG = 0
YES = 1
NO = 0


class DerivedVariables(object):

    def __init__(self, row):
        self.arv_evidence = row['arv_evidence']
        self.ever_taken_arv = row['ever_taken_arv']
        self.has_tested = row['has_tested']
        self.on_arv = row['on_arv']
        self.other_record = row['other_record']
        self.recorded_hiv_result = row['recorded_hiv_result']
        self.recorded_hiv_result_date = row['recorded_hiv_result_date']
        self.result_recorded = row['result_recorded']
        self.result_recorded_date = row['result_recorded_date']
        self.self_reported_result = row['self_reported_result']
        self.today_hiv_result = row['today_hiv_result']

    @property
    def prev_result_known(self):
        prev_result_known = np.nan
        if self.recorded_hiv_result in (POS, NEG) or self.final_arv_status in (DEFAULTER, ON_ART):
            prev_result_known = YES
        elif self.result_recorded == POS and self.final_hiv_status == NEG:
            prev_result_known = NO
        elif self.result_recorded in (NEG, POS):
            prev_result_known = YES
        return prev_result_known

    @property
    def prev_result(self):
        prev_result = np.nan
        if pd.isnull(self.prev_result_known):
            if self.final_hiv_status == NEG:
                prev_result = NEG
            elif (self.recorded_hiv_result == POS or self.result_recorded == POS or
                  self.final_arv_status in (DEFAULTER, ON_ART)):
                prev_result = POS
            else:
                prev_result = NEG
        return prev_result

    @property
    def prev_result_date(self):
        prev_result_date = np.nan
        if self.prev_result_known == YES:
            prev_result_date = self.recorded_hiv_result_date
        if pd.isnull(self.recorded_hiv_result_date):
            prev_result_date = self.result_recorded_date
        return prev_result_date

    @property
    def final_hiv_status(self):
        # HIV status: 1 = infected, 0 = uninfected *;
        final_hiv_status = np.nan
        if self.today_hiv_result in (POS, NEG):
            final_hiv_status = self.today_hiv_result
        else:
            if pd.notnull(self.documented_pos):
                final_hiv_status = POS
        return final_hiv_status

    @property
    def final_arv_status(self):
        """1: art naive, 2: art defaulter,  3: on art ;"""
        final_arv_status = np.nan
        if self.final_hiv_status == POS:
            if self.ever_taken_arv in (NO, DWTA, np.nan):
                final_arv_status = NAIVE
            elif self.ever_taken_arv == YES and self.on_arv == NO:
                final_arv_status = DEFAULTER
            elif self.arv_evidence == YES and self.on_arv == NO:
                final_arv_status = DEFAULTER
            elif self.arv_evidence == YES and self.on_arv == YES:
                final_arv_status = ON_ART
            elif self.ever_taken_arv == YES and self.on_arv == YES:
                final_arv_status = ON_ART
            elif self.arv_evidence == YES and self.on_arv is None and self.ever_taken_arv is None:
                final_arv_status = ON_ART
        return final_arv_status

    @property
    def documented_pos(self):
        documented_pos = np.nan
        if (self.recorded_hiv_result == POS or (self.other_record == YES and self.result_recorded == POS) or
                self.arv_evidence == YES):
            documented_pos = YES
        elif (self.recorded_hiv_result not in (POS, NEG) and
                not (self.other_record == YES and self.result_recorded == POS)):
            documented_pos = np.nan
        else:
            documented_pos = NO
        return documented_pos


class Subjects(object):

    """A class to generate a dataset of bcpp subject data for a given survey year.

        from bcpp_export.subjects import Subjects
        s = Subjects('bcpp-year-1')
        s.to_csv()

    """

    def __init__(self, survey_name):
        self._circumcised = pd.DataFrame()
        self._hiv_care_adherence = pd.DataFrame()
        self._hiv_result_documentation = pd.DataFrame()
        self._hiv_test_review = pd.DataFrame()
        self._hiv_testing_history = pd.DataFrame()
        self._reproductive_health = pd.DataFrame()
        self._residency_mobility = pd.DataFrame()
        self._results = pd.DataFrame()
        self._subject_consents = pd.DataFrame()
        self._subject_households = pd.DataFrame()
        self._subject_pimas = pd.DataFrame()
        self._subject_referrals = pd.DataFrame()
        self._today_hiv_test = pd.DataFrame()
        self.survey_name = survey_name

    def to_csv(self, path=None, columns=None):
        self.results.to_csv(
            path_or_buf=os.path.expanduser(path or '~/bcpp_export.csv'),
            na_rep='',
            encoding='utf8',
            date_format='%Y-%m-%d %H:%M',
            cols=columns or self.export_columns)

    @property
    def results(self):
        if self._results.empty:
            self.merge_dataframes()
            self.rename_columns()
            self.map_responses()
            self.add_derived_columns()
            self._results = self._results.fillna(value=np.nan)
        return self._results

    def merge_dataframes(self):
        """Left Merge all dataframes starting with subject_consent into
        a single dataframe on subject_identifier."""
        self._results = pd.merge(
            self.df_subject_consents, self.df_subject_households, how='left', on=SUBJECT_IDENTIFIER)
        for attrname in dir(self):
            if attrname.startswith('df_') and attrname not in ('df_subject_consents', 'df_subject_households'):
                self._results = pd.merge(self._results, getattr(self, attrname), how='left', on=SUBJECT_IDENTIFIER)

    def rename_columns(self):
        """Rename columns acccording to final dataset spec."""
        self._results = self._results.rename(columns={
            'cd4_datetime': 'cd4_date',
            'cd4_value': 'cd4_value',
            'legal_marriage': 'spouse_of_citizen',
            'hiv_result_datetime': 'hiv_result_date',
            'household_member_id': 'household_member',
            'id': 'unique_key',
            'internal_identifier': '',
            'pima_today': 'cd4_tested',
            'pima_today_other': 'cd4_not_tested_reason',
            'registered_subject_id': 'registered_subject',
            'subject_referred': 'referred',
            'vl_sample_drawn_datetime': 'vl_drawn_datetime',
            'verbal_hiv_result': 'self_reported_result',
            'currently_pregnant': 'pregnant'})

    def map_responses(self):
        gender = {'M': 1, 'F': 2}
        hiv_options = {'POS': 1, 'NEG': 0, 'IND': 2, 'UNK': 3, 'not_answering': 4, None: np.nan}
        tf = {True: 1, False: 2, None: np.nan}
        yes_no = {'Yes': 1, 'No': 2, 'N/A': 3, None: np.nan, 'DWTA': 4, 'Not Sure': 5}
        yes_no_str = {'Yes': 1, 'No': 2, '1': 1, '2': 2, None: np.nan}
        self._results['gender'] = self._results['gender'].map(gender.get)
        self._results['citizen'] = self._results['citizen'].map(yes_no.get)
        self._results['circumcised'] = self._results['circumcised'].map(yes_no.get)
        self._results['ever_taken_arv'] = self._results['ever_taken_arv'].map(yes_no.get)
        self._results['arv_evidence'] = self._results['arv_evidence'].map(yes_no.get)
        self._results['on_arv'] = self._results['on_arv'].map(yes_no.get)
        self._results['spouse_of_citizen'] = self._results['spouse_of_citizen'].map(yes_no.get)
        self._results['has_tested'] = self._results['has_tested'].map(yes_no.get)
        self._results['other_record'] = self._results['other_record'].map(yes_no.get)
        self._results['pregnant'] = self._results['pregnant'].map(yes_no.get)
        self._results['permanent_resident'] = self._results['permanent_resident'].map(yes_no.get)
        self._results['cd4_tested'] = self._results['cd4_tested'].map(yes_no.get)
        self._results['self_reported_result'] = self._results['self_reported_result'].map(hiv_options.get)
        self._results['result_recorded'] = self._results['result_recorded'].map(hiv_options.get)
        self._results['recorded_hiv_result'] = self._results['recorded_hiv_result'].map(hiv_options.get)
        self._results['today_hiv_result'] = self._results['today_hiv_result'].map(hiv_options.get)
        self._results['referred'] = self._results['referred'].map(yes_no_str.get)
        self._results['part_time_resident'] = self._results['part_time_resident'].map(tf.get)

    def add_derived_columns(self):
        self._results['timestamp'] = timezone.now()
        self._results['age_in_years'] = self._results.apply(
            lambda row: relativedelta(row['consent_datetime'].date(), row['dob']).years, axis=1)
        self._results['prev_result'] = self._results.apply(
            lambda row: DerivedVariables(row).prev_result, axis=1)
        self._results['prev_result_known'] = self._results.apply(
            lambda row: DerivedVariables(row).prev_result_known, axis=1)
        self._results['prev_result_date'] = self._results.apply(
            lambda row: DerivedVariables(row).prev_result_date, axis=1)
        self._results['final_hiv_status'] = self._results.apply(
            lambda row: DerivedVariables(row).final_hiv_status, axis=1)
        self._results['final_arv_status'] = self._results.apply(
            lambda row: DerivedVariables(row).final_arv_status, axis=1)

    @property
    def df_subject_consents(self):
        """Return a dataframe of a selection of the subject's consent values."""
        if self._subject_consents.empty:
            columns = [SUBJECT_IDENTIFIER, 'id', 'citizen', 'dob', 'gender', 'consent_datetime',
                       'identity', 'identity_type', 'household_member_id', 'registered_subject_id',
                       'community', 'legal_marriage']
            qs = SubjectConsent.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            self._subject_consents = pd.DataFrame(list(qs), columns=columns)
        return self._subject_consents

    @property
    def df_subject_households(self):
        """Return a dataframe of the subject's household and plot identifier."""
        if self._subject_households.empty:
            qs = SubjectConsent.objects.values_list(
                SUBJECT_IDENTIFIER, 'household_member__household_structure__household__household_identifier',
                'household_member__household_structure__household__plot__plot_identifier',
                'household_member__household_structure__survey__survey_slug').filter(
                    household_member__household_structure__survey__survey_slug=self.survey_name)
            self._subject_households = pd.DataFrame(
                list(qs), columns=[SUBJECT_IDENTIFIER, 'household_identifier', 'plot_identifier', 'survey'])
        return self._subject_households

    @property
    def df_subject_referrals(self):
        """Return a dataframe of a selection of the subject's referral values."""
        if self._subject_referrals.empty:
            columns = [
                'subject_visit__household_member__registered_subject__subject_identifier',
                'arv_clinic', 'export_uuid', 'referral_clinic', 'referral_code', 'subject_referred',
                'hiv_result_datetime', 'part_time_resident', 'vl_sample_drawn_datetime']
            qs = SubjectReferral.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._subject_referrals = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER})
        return self._subject_referrals

    @property
    def df_today_hiv_result(self):
        """Return a dataframe of a selection of values from today's hiv test result, if performed."""
        if self._today_hiv_test.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'hiv_result', 'hiv_result_datetime', 'why_not_tested']
            qs = HivResult.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._today_hiv_test = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'hiv_result': 'today_hiv_result',
                'hiv_result_datetime': 'today_hiv_result_datetime',
                'why_not_tested': 'reason_not_tested_today'})

        return self._today_hiv_test

    @property
    def df_hiv_testing_history(self):
        if self._hiv_testing_history.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'has_tested', 'other_record', 'verbal_hiv_result']
            qs = HivTestingHistory.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_testing_history = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER})
        return self._hiv_testing_history

    @property
    def df_hiv_test_review(self):
        if self._hiv_test_review.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'recorded_hiv_result', 'hiv_test_date']
            qs = HivTestReview.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_test_review = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'hiv_test_date': 'recorded_hiv_result_date'})

        return self._hiv_test_review

    @property
    def df_hiv_result_documentation(self):
        if self._hiv_result_documentation.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'result_recorded', 'result_date']
            qs = HivResultDocumentation.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_result_documentation = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'result_date': 'result_recorded_date'})
        return self._hiv_result_documentation

    @property
    def df_hiv_care_adherence(self):
        if self._hiv_care_adherence.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'ever_taken_arv', 'on_arv', 'arv_evidence']
            qs = HivCareAdherence.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._hiv_care_adherence = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER})
        return self._hiv_care_adherence

    @property
    def df_circumcised(self):
        if self._circumcised.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'circumcised']
            qs = Circumcision.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._circumcised = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER})
        return self._circumcised

    @property
    def df_reproductive_health(self):
        if self._reproductive_health.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'currently_pregnant']
            qs = ReproductiveHealth.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._reproductive_health = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER})
        return self._reproductive_health

    @property
    def df_residency_mobility(self):
        if self._residency_mobility.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'permanent_resident']
            qs = ResidencyMobility.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._residency_mobility = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER})
        return self._residency_mobility

    @property
    def df_subject_pimas(self):
        """Return a dataframe of a selection of the subject's pima/cd4 values."""
        if self._subject_pimas.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'pima_today', 'pima_today_other', 'cd4_datetime', 'cd4_value']
            qs = Pima.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._subject_pimas = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER})
        return self._subject_pimas

    def derived_fields(self):
        return [
            'vl_assay_datetime',
            'vl_result'
            'vl_sample_drawn',
        ]

    @property
    def export_columns(self):
        return [
            'subject_identifier',
            'age_in_years',
            'arv_clinic',
            'cd4_date',
            'cd4_not_tested_reason',
            'cd4_tested',
            'cd4_value',
            'circumcised',
            'citizen',
            'community',
            'consent_datetime',
            'dob',
            'export_uuid',
            'final_arv_status',
            'final_hiv_status',
            'gender',
            'has_tested',
            'hiv_result_date',
            'household_identifier',
            'household_member',
            'identity',
            'identity_type',
            'part_time_resident',
            'permanent_resident',
            'plot_identifier',
            'pregnant',
            'prev_result',
            'prev_result_date',
            'prev_result_known',
            'referral_clinic',
            'referral_code',
            'referred',
            'registered_subject',
            'self_reported_result',
            'spouse_of_citizen',
            'survey',
            'timestamp',
            'unique_key',
            'vl_drawn_datetime',
        ]
