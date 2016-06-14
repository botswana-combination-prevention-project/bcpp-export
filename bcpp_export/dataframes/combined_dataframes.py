import pandas as pd
import os

from datetime import date
from bcpp_export import urls  # DO NOT DELETE

from .csv_export_mixin import CsvExportMixin
from .members import Members
from .residences import Residences
from .subjects import Subjects


class CombinedDataFrames(CsvExportMixin):

    """A class to generate and format for CSV export based on data in objects Members, Subjects and
    Residences.

    For example:
        # all from scratch for pairs 1-13 only
        dfs = CombinedDataFrames('bcpp-year-1', pair_range=(1, 13))

        # if instances members, subjects, residences already exist
        dfs = CombinedDataFrames(
            'bcpp-year-1', members_object=members, subjects_object=subjects, residences_object=residences)

    """
    export_dataset_names = ['plots', 'residences', 'members', 'subjects']
    default_export_dataset_name = 'all'

    def __init__(self, survey_name, merge_subjects_on=None, add_identity256=None,
                 members_object=None, subjects_object=None, residences_object=None, **kwargs):
        super(CombinedDataFrames, self).__init__(**kwargs)
        self.survey_name = survey_name
        self.obj_subjects = subjects_object or Subjects(self.survey_name, merge_subjects_on, add_identity256)
        self.subjects = self.obj_subjects.results
        self.obj_members = members_object or Members(self.survey_name, subjects=self.subjects)
        self.members = self.obj_members.results
        self.obj_residences = residences_object or Residences(self.survey_name, subjects=self.subjects, members=self.members)
        self.plots = self.obj_residences.plots
        self.residences = self.obj_residences.residences
        residences_columns = [
            'household_structure', 'household_consented', 'household_log_status', 'household_log_date',
            'confirmed', 'plot_status', 'plot_modified', 'selected', 'gps_lat',
            'gps_lon', 'enumerated', 'household_modified']
        self.members = pd.merge(
            self.members, self.residences[residences_columns], how='left', on='household_structure')
        self.subjects = pd.merge(
            self.subjects, self.residences[residences_columns], how='left', on='household_structure')

    def validate(self):
        assert len(self.plots.query('enrolled == 1')) == len(pd.unique(self.subjects.plot_identifier.ravel()))
        assert len(self.residences.query('enrolled == 1')) == len(pd.unique(self.subjects.household_identifier.ravel()))

    def plot_summary(self):
        return {
            'total plots': len(self.plots),
            'bhs plots': self.plots[self.plots['selected'].isin([1, 2]) & (pd.notnull(self.plots['plot_status']))],
            'enumerated': self.members.query(
                'pair >= {pair_min} and pair <= {pair_max} and intervention in {arm} and '
                'household_log_status != "refused"'.format(pair_min=self.pair[0], pair_max=self.pair[1], self.arm)
            ),
        }
