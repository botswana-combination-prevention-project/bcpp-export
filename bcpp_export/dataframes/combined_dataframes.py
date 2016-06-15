import pandas as pd
import os

from datetime import date
from bcpp_export import urls  # DO NOT DELETE
from bcpp_export.constants import YES, POS
from .csv_export_mixin import CsvExportMixin
from .members import Members
from .residences import Residences
from .subjects import Subjects


class CombinedDataFrames(CsvExportMixin):

    """A class to generate and format for CSV export based on data in objects Members, Subjects and
    Residences.

    For example:
        # all from scratch for pairs 1-13 only
        dfs = CombinedDataFrames('bcpp-year-1', export_pairs=range(1, 13))

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
        self.obj_residences = residences_object or Residences(
            self.survey_name, subjects=self.subjects, members=self.members)
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

    def summary(self, **kwargs):
        plots = self.filtered_export_dataframe(self.plots, **kwargs)
        members = self.filtered_export_dataframe(self.members, **kwargs)
        subjects = self.filtered_export_dataframe(self.subjects, **kwargs)
        return {
            'total_plots': len(plots),
            'bhs_plots': len(plots[plots['selected'].isin([1, 2]) & (pd.notnull(plots['plot_status']))]),
            'households_enrolled': len(members[members['household_enrolled'] == 1]),
            'households_not_enrolled': len(members[members['household_enrolled'] == 0]),
            'enumerated': len(members),
            'enumerated_enrolled': len(members[members['enrolled'] == 1]),
            'enumerated_not_enrolled': len(members[members['enrolled'] == 0]),
            'enumerated_hhlog_refused': len(members.query('household_log_status != "refused"')),
            'subjects_interviewed': len(subjects),
            'subjects_interviewed_pos': len(subjects[subjects['final_hiv_status'] == POS]),
            'subjects_interviewed_known_pos': len(
                subjects[subjects['prev_result'] == POS & subjects['prev_result_known'] == YES]),
        }


class CDCDataFrames(CombinedDataFrames):

    default_filename_template = 'bcpp_export_{datasetname}_{timestamp}.csv'

    export_dataset_names = ['plots', 'members', 'subjects']

    plots_columns = ['community', 'confirmed', 'enrolled', 'plot_identifier', 'plot_status']

    households_columns = [
        'community', 'enrolled', 'enumerated', 'household_identifier', 'plot_identifier', 'survey']

    members_columns = [
        'able_to_participate', 'age_in_years', 'community', 'enrolled', 'gender',
        'household_identifier', 'plot_identifier', 'survey']

    subjects_columns = [
        'age_in_years', 'arv_clinic', 'cd4_date', 'cd4_tested', 'cd4_value',
        'circumcised', 'community', 'consent_date', 'final_arv_status', 'final_hiv_status',
        'gender', 'identity', 'identity256', 'pregnant', 'prev_result_known', 'prev_result',
        'prev_result_date', 'referred', 'self_reported_result', 'subject_identifier',
        'survey', 'timestamp', 'vl_drawn', 'vl_result']
