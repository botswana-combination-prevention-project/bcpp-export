import pandas as pd

from bcpp_export import urls  # DO NOT DELETE

from bhp066.apps.bcpp_household_member.models import (
    SubjectAbsenteeEntry, SubjectRefusal, SubjectMoved, SubjectUndecided, SubjectDeath)

ABSENT = 2
BHS_INELIGIBLE = 7
DECEASED = 6
ENROLLED = 1
MOVED = 4
REFUSED = 3
UNDECIDED = 5
UNKNOWN = 0


class ParticipationStatus(object):

    def __init__(self, survey_name):
        self._results = pd.DataFrame()
        self._df_all = pd.DataFrame()
        self._df_subject_absentee = pd.DataFrame()
        self._df_subject_death = pd.DataFrame()
        self._df_subject_moved = pd.DataFrame()
        self._df_subject_refusal = pd.DataFrame()
        self._df_subject_undecided = pd.DataFrame()
        self.survey_name = survey_name

    @property
    def results(self):
        if self._results.empty:
            df = self.df_all.sort_values(['registered_subject', 'created'])
            df = self.df_all.drop_duplicates(subset='registered_subject', keep='last')
            df = df.rename(columns={'created': 'participation_datetime'})
            df.drop('modified', axis=1, inplace=True)
            self._results = df
        return self._results

    @property
    def df_all(self):
        if self._df_all.empty:
            self._df_all = pd.concat(
                [self.df_subject_absentee,
                 self.df_subject_refusal,
                 self.df_subject_undecided,
                 self.df_subject_moved], ignore_index=True)
        return self._df_all

    @property
    def df_subject_absentee(self):
        if self._df_subject_absentee.empty:
            columns = 'subject_absentee__household_member__registered_subject', 'created', 'modified'
            qs = SubjectAbsenteeEntry.objects.values_list(*columns).filter(
                subject_absentee__household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'subject_absentee__household_member__registered_subject': 'registered_subject'})
            if df.empty:
                self._df_subject_absentee = pd.DataFrame()
            else:
                df['participation_status'] = ABSENT
                self._df_subject_absentee = df
        return self._df_subject_absentee

    @property
    def df_subject_refusal(self):
        if self._df_subject_refusal.empty:
            columns = 'household_member__registered_subject', 'created', 'modified'
            qs = SubjectRefusal.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_member__registered_subject': 'registered_subject'})
            if df.empty:
                self._df_subject_refusal = pd.DataFrame()
            else:
                df['participation_status'] = REFUSED
                self._df_subject_refusal = df
        return self._df_subject_refusal

    @property
    def df_subject_moved(self):
        if self._df_subject_moved.empty:
            columns = 'household_member__registered_subject', 'created', 'modified'
            qs = SubjectMoved.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_member__registered_subject': 'registered_subject'})
            if df.empty:
                self._df_subject_moved = pd.DataFrame()
            else:
                df['participation_status'] = MOVED
                self._df_subject_moved = df
        return self._df_subject_moved

    @property
    def df_subject_undecided(self):
        if self._df_subject_undecided.empty:
            columns = 'household_member__registered_subject', 'created', 'modified'
            qs = SubjectUndecided.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_member__registered_subject': 'registered_subject'})
            if df.empty:
                self._df_subject_undecided = pd.DataFrame()
            else:
                df['participation_status'] = UNDECIDED
                self._df_subject_undecided = df
        return self._df_subject_undecided

    @property
    def df_subject_death(self):
        if self._df_subject_death.empty:
            columns = 'household_member__registered_subject', 'created', 'modified'
            qs = SubjectDeath.objects.values_list(*columns).filter(
                household_member__household_structure__survey__survey_slug=self.survey_name)
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_member__registered_subject': 'registered_subject'})
            if df.empty:
                self._df_subject_death = pd.DataFrame()
            else:
                df['participation_status'] = DECEASED
                self._df_subject_death = df
        return self._df_subject_death
