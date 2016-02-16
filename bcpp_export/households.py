import pandas as pd
import numpy as np
import os

from dateutil.relativedelta import relativedelta

from django.utils import timezone

from bcpp_export import urls
from bcpp_export.subjects import Subjects

from bhp066.apps.bcpp_household.models import Household, HouseholdStructure, Plot

from bhp066.apps.bcpp_household_member.models.household_member import HouseholdMember

from .constants import (YES, NO, DEFAULTER, DWTA, IND, NAIVE, NEG, NOT_APPLICABLE, ON_ART,
                        POS, UNK, gender, hiv_options, tf, yes_no, edc_NOT_APPLICABLE)
from bcpp_export.constants import survival

PLOT_IDENTIFIER = 'plot_identifier'


class Households(object):

    def __init__(self, survey_name):
        self._households = pd.DataFrame()
        self._plots = pd.DataFrame()
        self._members = pd.DataFrame()
        self._results = pd.DataFrame()
        self.survey_name = survey_name
        self.subjects = Subjects(self.survey_name)

    def to_csv(self, path=None, columns=None):
        self.results.to_csv(
            path_or_buf=os.path.expanduser(path or '~/bcpp_export_households.csv'),
            na_rep='',
            encoding='utf8',
            date_format='%Y-%m-%d %H:%M',
            cols=columns or self.results.columns)

    @property
    def results(self):
        if self._results.empty:
            self.merge_dataframes()
            # self.rename_columns()
            # self.map_responses()
            self.add_derived_columns()
            # self._results = self._results.fillna(value=np.nan)
        return self._results

    def merge_dataframes(self):
        self._results = pd.merge(
            self.df_households, self.df_plots, how='left', on=PLOT_IDENTIFIER)

    def enrolled(self, row):
        df = self.subjects.results
        if not df[df[PLOT_IDENTIFIER] == row[PLOT_IDENTIFIER]].plot_identifier.empty:
            return YES
        return NO

    def add_derived_columns(self):
        # self._results['allocation'] = self._results.apply(lambda row: 'bhs' if row['bhs'] is True else 'htc', axis=1)
        self._results['enrolled'] = self.results.apply(lambda row: self.enrolled(row), axis=1)
        self._plots['enrolled'] = self._plots.apply(lambda row: self.enrolled(row), axis=1)

    @property
    def df_plots(self):
        if self._plots.empty:
            columns = [PLOT_IDENTIFIER, 'gps_lat', 'gps_lon', 'action', 'status', 'selected', 'community', 'modified']
            qs = Plot.objects.values_list(*columns).exclude(status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            self._plots = df.rename(columns={
                'modified': 'plot_modified',
            })
        return self._plots

    @property
    def df_households(self):
        """Return a dataframe of a selection of the household values."""
        if self._households.empty:
            columns = [
                'household__household_identifier',
                'household__plot__plot_identifier', 'survey__survey_slug', 'modified']
            qs = HouseholdStructure.objects.values_list(*columns).filter(
                survey__survey_slug=self.survey_name).exclude(household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            self._households = df.rename(columns={
                'household__household_identifier': 'household_identifier',
                'household__plot__plot_identifier': PLOT_IDENTIFIER,
                'modified': 'household_modified',
                'survey__survey_slug': 'survey',
            })
        return self._households

    @property
    def df_members(self):
        if self._members.empty:
            columns = [
                'gender', 'age_in_years', 'survival_status', 'study_resident',
                'household_structure__household__household_identifier',
                'household_structure__household__plot__plot_identifier',
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
