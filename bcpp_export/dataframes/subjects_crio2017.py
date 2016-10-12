"""
# Education Level - primary; secondary or higher
'bcpp_subject.Education.education'

# Employment status - full; part-time; seasonal; student; retired; not working;
'bcpp_subject.Education.working'
'bcpp_subject.Education.job_type'

# Relationship/Marital Status - single; cohab/married; divorced/separated; widowed
'bcpp_subject.Demographics.marital_status'

# Current partner - spouse/cohabitation; boyfriend/girlfriend; casual sex partner; one time sex partner; none
'bcpp_subject.MonthsRecentPartner.first_relationship'

# Partner HIV status
'bcpp_subject.MonthsRecentPartner.first_partner_hiv'

#  Length of time in Community
'bcpp_subject.ResidencyMobility.length_residence'
"""

import pandas as pd

from bhp066.apps.bcpp_subject.models import LabourMarketWages, Demographics, Education, MonthsRecentPartner, ResidencyMobility

from bcpp_export.constants import SUBJECT_IDENTIFIER, HOUSEHOLD_MEMBER

from ..constants import hiv_options

from .subjects import Subjects


class SubjectsCrio2017(Subjects):

    """A class to generate a dataset of bcpp subject data for a given survey year.

        from bcpp_export.dataframes.subjects_croi_2017 import SubjectsCrio2017
        s = SubjectsCrio2017('bcpp-year-1')
        s.results

        from bcpp_export.dataframes.subjects_croi2017 import SubjectsCrio2017
        s = SubjectsCrio2017('bcpp-year-1')
        s.to_csv()
    """

    def __init__(self, survey_name, merge_on=None, add_identity256=None, **kwargs):
        self._demographics = pd.DataFrame()
        self._education = pd.DataFrame()
        self._labour_market_wages = pd.DataFrame()
        self._months_recent_partner = pd.DataFrame()
        super(SubjectsCrio2017, self).__init__(survey_name, merge_on, add_identity256, **kwargs)

    def map_edc_responses_to_numerics(self):
        self._results['first_partner_hiv'] = self._results['first_partner_hiv'].map(hiv_options.get)
        super(SubjectsCrio2017, self).map_edc_responses_to_numerics()

    @property
    def df_labour_market_wages(self):
        if self._labour_market_wages.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'employed', 'days_worked', 'monthly_income', 'salary_payment']
            qs = LabourMarketWages.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._labour_market_wages = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'employed': 'employed',
                'days_worked': 'days_worked',
                'monthly_income': 'monthly_income',
                'salary_payment': 'salary_payment'})
        return self._labour_market_wages

    @property
    def df_demographics(self):
        if self._demographics.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'marital_status']
            qs = Demographics.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._demographics = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'marital_status': 'marital_status'})
        return self._demographics

    @property
    def df_education(self):
        if self._education.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'education', 'working', 'job_type']
            qs = Education.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._education = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'education': 'education',
                'working': 'working',
                'job_type': 'job_type'})
        return self._education

    @property
    def df_months_recent_partner(self):
        if self._months_recent_partner.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'first_relationship', 'first_partner_hiv']
            qs = MonthsRecentPartner.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._months_recent_partner = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'first_relationship': 'first_relationship',
                'first_partner_hiv': 'first_partner_hiv'})
        return self._months_recent_partner

    @property
    def df_residency_mobility(self):
        if self._residency_mobility.empty:
            columns = ['subject_visit__household_member__registered_subject__subject_identifier',
                       'subject_visit__household_member',
                       'permanent_resident', 'length_residence']
            qs = ResidencyMobility.objects.values_list(*columns).filter(
                subject_visit__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            self._residency_mobility = df.rename(columns={
                'subject_visit__household_member__registered_subject__subject_identifier': SUBJECT_IDENTIFIER,
                'subject_visit__household_member': HOUSEHOLD_MEMBER,
                'permanent_resident': 'permanent_resident',
                'length_residence': 'length_residence'})
        return self._residency_mobility
