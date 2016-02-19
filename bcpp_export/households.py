import pandas as pd
import os

from bcpp_export import urls
from bcpp_export.subjects import Subjects

from bhp066.apps.bcpp_household.models import HouseholdStructure, Plot

from bhp066.apps.bcpp_household_member.models.household_member import HouseholdMember

from .communities import communities
from .constants import (YES, NO, gender, yes_no, edc_NOT_APPLICABLE, survival)


PLOT_IDENTIFIER = 'plot_identifier'


class Households(object):

    def __init__(self, survey_name, merge_subjects_on=None, add_identity256=None):
        self._households = pd.DataFrame()
        self._plots = pd.DataFrame()
        self._members = pd.DataFrame()
        self._households = pd.DataFrame()
        self._df_households = pd.DataFrame()
        self.survey_name = survey_name
        self.subjects = Subjects(self.survey_name, merge_subjects_on, add_identity256).results
        self.merge_dataframes()
        self.add_derived_columns()

    def to_csv(self, dataset_name, path=None, columns=None):
        for name in self.dataset_names(dataset_name):
            df = getattr(self, name)
            df.to_csv(
                path_or_buf=os.path.expanduser(path or '~/bcpp_export_{}.csv'.format(name)),
                na_rep='',
                encoding='utf8',
                date_format='%Y-%m-%d %H:%M',
                cols=columns)

    def dataset_names(self, dataset_name):
        """Return the dataset_name(s) to export as a list or if dataset_name == all return a
        list of all dataset_names."""
        valid_dataset_names = ['plots', 'households', 'members', 'subjects', 'all']
        if dataset_name not in valid_dataset_names:
            raise TypeError('Invalid dataset name, expected one of {}'.format(valid_dataset_names))
        if dataset_name == 'all':
            dataset_names = ['plots', 'households', 'members', 'subjects']
        else:
            dataset_names = [dataset_name]
        return dataset_names

    @property
    def households(self):
        return self._households

    @property
    def plots(self):
        return self.df_plots

    @property
    def members(self):
        return self.df_members

    def merge_dataframes(self):
        self._households = pd.merge(
            self.df_households, self.df_plots, how='left', on=PLOT_IDENTIFIER)

    def add_derived_columns(self):
        self._households['enumerated'] = self._households.apply(
            lambda row: self.enumerated(row), axis=1)
        self._households['enrolled'] = self._households.apply(
            lambda row: self.enrolled(row, 'household_identifier'), axis=1)
        self._households['intervention'] = self._households.apply(
            lambda row: self.intervention(row), axis=1)
        self._households['pair'] = self._households.apply(
            lambda row: communities.get(row['community']).pair, axis=1)
        self._plots['enrolled'] = self._plots.apply(lambda row: self.enrolled(row, 'plot_identifier'), axis=1)
        self._plots['intervention'] = self._plots.apply(
            lambda row: self.intervention(row), axis=1)
        self._plots['pair'] = self._plots.apply(
            lambda row: communities.get(row['community']).pair, axis=1)
        self._members['intervention'] = self._members.apply(
            lambda row: self.intervention(row), axis=1)
        self._members['pair'] = self._members.apply(
            lambda row: communities.get(row['community']).pair, axis=1)
        self._members['enrolled'] = self._members.apply(
            lambda row: self.enrolled(row, 'registered_subject'), axis=1)
        self.subjects['pair'] = self.subjects.apply(
            lambda row: communities.get(row['community']).pair, axis=1)
        self.subjects['intervention'] = self.subjects.apply(
            lambda row: self.intervention(row), axis=1)

    def intervention(self, row):
        return 1 if communities.get(row['community']).intervention else 0

    def enumerated(self, row):
        if self.members[self.members['household_identifier'].isin([row['household_identifier']])].empty:
            return NO
        return YES

    def enrolled(self, row, field):
        if self.subjects[self.subjects[field].isin([row[field]])].empty:
            return NO
        return YES

    @property
    def df_plots(self):
        if self._plots.empty:
            columns = [PLOT_IDENTIFIER, 'gps_lat', 'gps_lon', 'action', 'status', 'selected',
                       'community', 'modified']
            qs = Plot.objects.values_list(*columns).exclude(status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            self._plots = df.rename(columns={
                'modified': 'plot_modified',
                'action': 'confirmed',
                'status': 'plot_status'})
            self._plots['confirmed'] = self._plots['confirmed'].map({'confirmed': 1, 'unconfirmed': 0}.get)
        return self._plots

    @property
    def df_households(self):
        """Return a dataframe of a selection of the household values."""
        if self._df_households.empty:
            columns = [
                'household__household_identifier',
                'household__plot__plot_identifier', 'survey__survey_slug', 'modified']
            qs = HouseholdStructure.objects.values_list(*columns).filter(
                survey__survey_slug=self.survey_name).exclude(household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            self._df_households = df.rename(columns={
                'household__household_identifier': 'household_identifier',
                'household__plot__plot_identifier': PLOT_IDENTIFIER,
                'modified': 'household_modified',
                'survey__survey_slug': 'survey',
            })
        return self._df_households

    @property
    def df_members(self):
        if self._members.empty:
            columns = [
                'registered_subject', 'gender', 'age_in_years', 'survival_status', 'study_resident',
                'household_structure__household__household_identifier',
                'household_structure__household__plot__plot_identifier',
                'household_structure__household__plot__community',
                'household_structure__survey__survey_slug',
                'inability_to_participate', 'modified',
            ]
            qs = HouseholdMember.objects.values_list(*columns).filter(
                household_structure__survey__survey_slug=self.survey_name).exclude(
                    household_structure__household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            self._members = df.rename(columns={
                'household_structure__household__household_identifier': 'household_identifier',
                'household_structure__household__plot__plot_identifier': PLOT_IDENTIFIER,
                'household_structure__household__plot__community': 'community',
                'household_structure__survey__survey_slug': 'survey',
                'inability_to_participate': 'able_to_participate',
                'modified': 'member_modified',
            })
            self._members['able_to_participate'] = self._members.apply(
                lambda row: 1 if row['able_to_participate'] == edc_NOT_APPLICABLE else 2, axis=1)
            self._members['gender'] = self._members['gender'].map(gender.get)
            self._members['study_resident'] = self._members['study_resident'].map(yes_no.get)
            self._members['survival_status'] = self._members['survival_status'].map(survival.get)
        return self._members
