import sys
import numpy as np
import pandas as pd

from django.core.management.color import color_style

from bcpp_export import urls  # DO NOT DELETE

from bhp066.apps.bcpp_household.models.household_refusal import HouseholdRefusal
from bhp066.apps.bcpp_household_member.models import HouseholdMember, EnrollmentChecklist, SubjectHtc

from ..communities import communities, intervention
from ..constants import (YES, NO, gender, yes_no, tf, edc_NOT_APPLICABLE, survival, PLOT_IDENTIFIER)
from ..datetime_to_date import datetime_to_date
from ..enrolled import enrolled
from ..household_refused import household_refused

from .csv_export_mixin import CsvExportMixin
from .participation_status import (
    ParticipationStatus, ENROLLED, ABSENT, REFUSED, BHS_INELIGIBLE, DECEASED,
    UNKNOWN, MOVED, UNDECIDED)

style = color_style()


class Members(CsvExportMixin):

    def __init__(self, survey_name, subjects=None, **kwargs):
        super(Members, self).__init__(**kwargs)
        self.survey_name = survey_name
        try:
            self.subjects = pd.DataFrame() if subjects.empty else subjects
        except AttributeError:
            self.subjects = pd.DataFrame()
        if self.subjects.empty:
            sys.stdout.write(style.NOTICE('Warning: Subjects dataframe is empty. Some values cannot be determined.'))
        self._results = pd.DataFrame()
        self._df_participation_status = pd.DataFrame()
        self._df_enrollment_checklist = pd.DataFrame()
        self._df_subject_htc = pd.DataFrame()
        self._df_household_refusal = pd.DataFrame()

    @property
    def results(self):
        if self._results.empty:
            columns = [
                'id', 'registered_subject', 'gender', 'age_in_years', 'survival_status', 'study_resident',
                'household_structure',
                'household_structure__household__household_identifier',
                'household_structure__household__plot__plot_identifier',
                'household_structure__household__plot__community',
                'household_structure__survey__survey_slug',
                'inability_to_participate', 'modified', 'visit_attempts', 'created'
            ]
            qs = HouseholdMember.objects.values_list(*columns).filter(
                household_structure__survey__survey_slug=self.survey_name).exclude(
                    household_structure__household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            self._results = df.rename(columns={
                'id': 'household_member',
                'household_structure__household__household_identifier': 'household_identifier',
                'household_structure__household__plot__plot_identifier': PLOT_IDENTIFIER,
                'household_structure__household__plot__community': 'community',
                'household_structure__survey__survey_slug': 'survey',
                'inability_to_participate': 'able_to_participate',
                'modified': 'member_modified',
                'created': 'first_enumeration_date',
            })
            self.merge_dataframes()
            self.map_edc_responses_to_numerics()
            self.add_derived_columns()
            self.remove_members_by_household_refusal()
            self.subjects_value_or_value('gender')
        return self._results

    def remove_members_by_household_refusal(self):
        """Remove members if the household is marked as refused regardless of being enumerated.

        If a member has enrolled (consented), do not remove."""
        if self.subjects.empty:
            sys.stdout.write(style.NOTICE('Subjects dataframe is empty. Cannot determined '
                                          'member\'s enrollment status or exclude those from '
                                          'households that refused.'))
        else:
            df = self._results
            # should be by household enrolled not member enrolled
            self._results = df[~((df['household_refused'] == 1) & (df['household_enrolled'] != 1))]

    def merge_dataframes(self):
        self._results = pd.merge(
            self._results, self.df_participation_status, how='left', on='registered_subject', suffixes=['', '_ps'])
        self._results = pd.merge(
            self._results, self.df_enrollment_checklist, how='left', on='registered_subject', suffixes=['', '_ec'])
        self._results = pd.merge(
            self._results, self.df_subject_htc, how='left', on='registered_subject', suffixes=['', '_sh'])

    def map_edc_responses_to_numerics(self):
        self._results['gender'] = self._results['gender'].map(gender.get)
        self._results['study_resident'] = self._results['study_resident'].map(yes_no.get)
        self._results['survival_status'] = self._results['survival_status'].map(survival.get)

    def subjects_value_or_value(self, attr, astype=None):
        """Replace a column value with that from subjects, if there is a subject value."""
        subject_suffix = '_as_subject'
        subject_attr = '{}{}'.format(attr, subject_suffix)
        self._results = pd.merge(
            self._results, self.subjects[['registered_subject', attr]],
            on='registered_subject', how='left', suffixes=['', subject_suffix])
        self._results[attr] = self._results.apply(
            lambda row: row[attr] if pd.isnull(row[subject_attr]) else row[subject_attr], axis=1)
        self._results.drop([subject_attr], axis=1, inplace=True)
        if astype:
            self._results[attr] = self._results[attr].astype(astype)

    def add_derived_columns(self):
        self._results['first_enumeration_date'] = self._results.apply(
            lambda row: datetime_to_date(row['first_enumeration_date']), axis=1)
        self._results['able_to_participate'] = self._results.apply(
            lambda row: 1 if row['able_to_participate'] == edc_NOT_APPLICABLE else 2, axis=1)
        self._results['enum_eligible'] = self._results.apply(
            lambda row: self.enum_eligible(row), axis=1)
        self._results['intervention'] = self._results.apply(
            lambda row: intervention(row), axis=1)
        self._results['pair'] = self._results.apply(
            lambda row: communities.get(row['community']).pair, axis=1)
        self._results['household_refused'] = self._results.apply(
            lambda row: household_refused(self.df_household_refusal, row), axis=1)
        if self.subjects.empty:
            self._results['household_enrolled'] = np.nan
            self._results['enrolled'] = np.nan
            self._results['participation_status'] = np.nan
        else:
            self._results['household_enrolled'] = self._results['household_identifier'].isin(
                self.subjects['household_identifier'])
            self._results['household_enrolled'] = self._results['household_enrolled'].map(tf.get)
            self._results['enrolled'] = self._results.apply(
                lambda row: enrolled(self.subjects, row, 'registered_subject'), axis=1)
            self._results['participation_status'] = self._results.apply(
                lambda row: self.participation_status(row), axis=1)
        self._results['bhs_checklist'] = self._results.apply(
            lambda row: YES if row['bhs_checklist'] == YES else NO, axis=1)

    def enum_eligible(self, row):
        if (row['able_to_participate'] == 1 and row['age_in_years'] >= 16 and
                row['age_in_years'] <= 64 and row['study_resident'] == 1):
            return YES
        else:
            return NO

    def participation_status(self, row):
        if enrolled(self.subjects, row, 'registered_subject') == YES:
            participation_status = ENROLLED
        elif row['bhs_eligible'] == NO:
            participation_status = BHS_INELIGIBLE
        elif row['participation_status'] == UNDECIDED:
            participation_status = REFUSED
        elif row['participation_status'] not in [ABSENT, ENROLLED, REFUSED, MOVED, UNDECIDED, DECEASED]:
            participation_status = UNKNOWN
        else:
            participation_status = row['participation_status']
        return participation_status

    @property
    def df_participation_status(self):
        if self._df_participation_status.empty:
            participation_status = ParticipationStatus(self.survey_name)
            self._df_participation_status = participation_status.results
        return self._df_participation_status

    @property
    def df_enrollment_checklist(self):
        if self._df_enrollment_checklist.empty:
            columns = [
                'household_member__registered_subject',
                'is_eligible']
            qs = EnrollmentChecklist.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_member__registered_subject': 'registered_subject',
                'is_eligible': 'bhs_eligible'})
            df['bhs_eligible'] = df['bhs_eligible'].map(tf.get)
            df['bhs_checklist'] = YES
            self._df_enrollment_checklist = df
        return self._df_enrollment_checklist

    @property
    def df_subject_htc(self):
        if self._df_subject_htc.empty:
            columns = [
                'household_member__registered_subject', 'tracking_identifier', 'offered', 'accepted',
                'refusal_reason']
            qs = SubjectHtc.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_member__registered_subject': 'registered_subject',
                'tracking_identifier': 'htc_tracking_identifier',
                'offered': 'htc_offered',
                'accepted': 'htc_accepted',
                'refusal_reason': 'htc_refusal_reason'})
            df['htc_offered'] = df['htc_offered'].map(yes_no.get)
            df['htc_accepted'] = df['htc_accepted'].map(yes_no.get)
            self._df_subject_htc = df
        return self._df_subject_htc

    @property
    def df_household_refusal(self):
        if self._df_household_refusal.empty:
            columns = ['household_structure',
                       'household_structure__household__household_identifier',
                       'household_structure__survey__survey_slug']
            qs = HouseholdRefusal.objects.values_list(*columns).filter(
                household_structure__survey__survey_slug=self.survey_name).exclude(
                    household_structure__household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            self._df_household_refusal = df.rename(columns={
                'household_structure__household__household_identifier': 'household_identifier',
                'household_structure__survey__survey_slug': 'survey'})
        return self._df_household_refusal
