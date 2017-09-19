import sys

import numpy as np
import pandas as pd

from django.core.management.color import color_style

from bcpp_export import urls  # DO NOT DELETE

from bhp066.apps.bcpp_household.models import (
    HouseholdStructure, Plot, RepresentativeEligibility, HouseholdLogEntry)

from ..communities import communities, intervention
from ..constants import PLOT_IDENTIFIER, yes_no, YES, NO
from ..enrolled import enrolled
from ..enumerated import enumerated

style = color_style()


class Residences(object):

    """Residences prepares three main dataframes where the most useful is "residences":

        * residences: a merge of plot left joined into household on plot identifier. This DF
            is the best to use as it contains all of household and plot.
        * households: a dataframe of the bcpp Household model with a few add fields
        * plots: a dataframe of the bcpp Plot model with a few add fields

    """

    def __init__(self, survey_name, subjects=None, members=None):
        self._df_household_log = pd.DataFrame()
        self._df_households = pd.DataFrame()
        self._df_plots = pd.DataFrame()
        self._df_representative_eligibility = pd.DataFrame()
        self._df_residences = pd.DataFrame()
        self.survey_name = survey_name
        try:
            self.subjects = pd.DataFrame() if subjects.empty else subjects
        except AttributeError:
            self.subjects = pd.DataFrame()
        if self.subjects.empty:
            sys.stdout.write(style.NOTICE('Warning: Subjects dataframe is empty. Some values cannot be determined.'))
        try:
            self.members = pd.DataFrame() if members.empty else members
        except AttributeError:
            self.members = pd.DataFrame()
        if self.members.empty:
            sys.stdout.write(style.NOTICE('Warning: Members dataframe is empty. Some values cannot be determined.'))

    @property
    def residences(self):
        """Return a dataframe that is the merge of households and plots."""
        if self._df_residences.empty:
            self._df_residences = pd.merge(
                self.df_households,
                self.df_plots[[PLOT_IDENTIFIER, 'plot_modified', 'confirmed',
                               'plot_status', 'gps_lat', 'gps_lon', 'selected']],
                how='left', on=PLOT_IDENTIFIER)
        return self._df_residences

    @property
    def households(self):
        return self.df_households

    @property
    def plots(self):
        return self.df_plots

    @property
    def df_representative_eligibility(self):
        """Return a dataframe with a column that indicates whether
        the head of household was verbally consented for household
        enumeration."""
        if self._df_representative_eligibility.empty:
            columns = ['household_structure', 'verbal_script']
            qs = RepresentativeEligibility.objects.values_list(*columns).filter(
                household_structure__survey__survey_slug=self.survey_name).exclude(
                    household_structure__household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={'verbal_script': 'household_consented'})
            df['household_consented'] = df['household_consented'].map(yes_no.get)
            self._df_representative_eligibility = df
        return self._df_representative_eligibility

    @property
    def df_household_log(self):
        """Return a dataframe with a column that indicates whether
        the head of household was verbally consented for household
        enumeration."""
        if self._df_household_log.empty:
            columns = ['household_log__household_structure', 'household_status', 'report_datetime']
            qs = HouseholdLogEntry.objects.values_list(*columns).filter(
                household_log__household_structure__survey__survey_slug=self.survey_name).exclude(
                    household_log__household_structure__household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'household_log__household_structure': 'household_structure',
                'report_datetime': 'household_log_date',
                'household_status': 'household_log_status'})
            self._df_household_log = df
        return self._df_household_log

    @property
    def df_plots(self):
        """Return a dataframe of a selection of the plot model columns."""
        if self._df_plots.empty:
            columns = [PLOT_IDENTIFIER, 'gps_lat', 'gps_lon', 'action', 'status', 'selected',
                       'community', 'modified']
            qs = Plot.objects.values_list(*columns).exclude(status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'action': 'confirmed',
                'modified': 'plot_modified',
                'status': 'plot_status'})
            df['confirmed'] = df['confirmed'].map({'confirmed': 1, 'unconfirmed': 0}.get)
            df['enrolled'] = df.apply(lambda row: enrolled(self.subjects, row, 'plot_identifier'), axis=1)
            df['intervention'] = df.apply(lambda row: intervention(row), axis=1)
            df['pair'] = df.apply(lambda row: communities.get(row['community']).pair, axis=1)
            df['selected'] = df.apply(lambda row: int(row['selected']) if pd.notnull(row['selected']) else np.nan, axis=1)
            self._df_plots = df
        return self._df_plots

    @property
    def df_households(self):
        """Return a dataframe of a selection of the household
        model columns."""
        if self._df_households.empty:
            columns = [
                'household__household_identifier', 'id',
                'household__plot__plot_identifier', 'survey__survey_slug', 'modified']
            qs = HouseholdStructure.objects.values_list(*columns).filter(
                survey__survey_slug=self.survey_name).exclude(household__plot__status='bcpp_clinic')
            df = pd.DataFrame(list(qs), columns=columns)
            df = df.rename(columns={
                'id': 'household_structure',
                'household__household_identifier': 'household_identifier',
                'household__plot__plot_identifier': PLOT_IDENTIFIER,
                'modified': 'household_modified',
                'survey__survey_slug': 'survey'})
            df['enumerated'] = df.apply(lambda row: enumerated(self.members, row), axis=1)
            df['enrolled'] = df.apply(
                lambda row: enrolled(self.subjects, row, 'household_identifier'), axis=1)
            df = pd.merge(
                df, self.df_plots[[PLOT_IDENTIFIER, 'intervention', 'pair', 'community']],
                how='left', on=PLOT_IDENTIFIER)
            df = pd.merge(df, self.df_representative_eligibility, how='left', on='household_structure')
            df['household_consented'] = df.apply(
                lambda row: NO if pd.isnull(row['household_consented']) else YES, axis=1)
            df_log = self.df_household_log.sort_values(['household_structure', 'household_log_date'])
            df_log = df_log.drop_duplicates('household_structure', keep='last')
            df = pd.merge(df, df_log, how='left', on='household_structure')
            self._df_households = df
        return self._df_households
