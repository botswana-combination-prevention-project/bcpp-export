import pandas as pd
import os

from datetime import date
from bcpp_export import urls  # DO NOT DELETE

from .residences import Residences
from .members import Members
from .subjects import Subjects


class CombinedDataFrames(object):

    """A class to generate and format for CSV export based on data in objects Members, Subjects and
    Residences.
    
    For example:
        # if members, subjects, residences already exist
        dfs = CombinedDataFrames(
            'bcpp-year-1', members_object=members, subjects_object=subject, residences_object=residences)
    """

    def __init__(self, survey_name, pair_range=None, merge_subjects_on=None, add_identity256=None,
                 export_folder=None, members_object=None, subjects_object=None, residences_object=None):
        self.pair = pair_range or (1, 15)
        self.export_folder = export_folder or os.path.expanduser('~/')
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
                'pair >= {pair_min} and pair <= {pair_max} and intervention == 1 and '
                'household_log_status != "refused"'.format(pair_min=self.pair[0], pair_max=self.pair[1])
            ),
        }

    def to_csv(self, dataset_name=None, **kwargs):
        dataset_name = dataset_name or 'all'
        columns = kwargs.get('columns', {})
        for name in self.dataset_names(dataset_name):
            df = getattr(self, name)
            options = dict(
                path_or_buf=os.path.expanduser(
                    kwargs.get('path_or_buf') or
                    os.path.join(self.export_folder, 'bcpp_export_{}_{}.csv'.format(
                        date.today().strftime('%Y%m%d'), name))),
                na_rep='',
                encoding='utf8',
                date_format=kwargs.get('date_format', '%Y-%m-%d %H:%M:%S'),
                index=kwargs.get('index', False),
                columns=columns.get(name))
            df.to_csv(**options)

    def dataset_names(self, dataset_name):
        """Return the dataset_name(s) to export as a list or
        if dataset_name == all return a list of all dataset_names."""
        valid_dataset_names = ['plots', 'residences', 'members', 'subjects', 'all']
        if dataset_name not in valid_dataset_names:
            raise TypeError('Invalid dataset name, expected one of {}'.format(valid_dataset_names))
        if dataset_name == 'all':
            dataset_names = ['plots', 'residences', 'members', 'subjects']
        else:
            dataset_names = [dataset_name]
        return dataset_names
