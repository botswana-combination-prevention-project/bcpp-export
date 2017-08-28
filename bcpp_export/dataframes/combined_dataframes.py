import hashlib
import pandas as pd
import os
import sys

from datetime import date, datetime, timedelta
from bcpp_export import urls  # DO NOT DELETE
from bcpp_export.constants import YES, POS
from .csv_export_mixin import CsvExportMixin
from .members import Members
from .residences import Residences
from .subjects import Subjects
from django.core.management.color import color_style
from bcpp_export.identity256 import identity256
from bcpp_export.dataframes.subjects_crio2017 import SubjectsCrio2017

style = color_style()


class CombinedDataFrames(CsvExportMixin):

    """A class to generate and format for CSV export based on data in objects Members, Subjects and
    Residences.

    For example:
        # all from scratch for pairs 1-13 only
        dfs = CombinedDataFrames('bcpp-year-1', export_pairs=range(1, 13))

        dfs = CombinedDataFrames('bcpp-year-1', export_pairs=range(1, 15), add_identity256=True)

        # if instances members, subjects, residences already exist
        dfs = CombinedDataFrames(
            'bcpp-year-1', members_object=members, subjects_object=subjects, residences_object=residences)

    """
    export_dataset_names = ['plots', 'residences', 'members', 'subjects']
    default_export_dataset_name = 'all'

    def __init__(self, survey_name, merge_subjects_on=None, add_identity256=None,
                 members_object=pd.DataFrame(), subjects_object=pd.DataFrame(),
                 residences_object=pd.DataFrame(), **kwargs):
        super(CombinedDataFrames, self).__init__(**kwargs)
        self.survey_name = survey_name
        self.plots = pd.DataFrame()
        self.households = pd.DataFrame()
        if not subjects_object.empty:
            self.subjects = subjects_object
        else:
            self.obj_subjects = self.get_subjects(
                merge_subjects_on, add_identity256)
            self.subjects = self.obj_subjects.results
            self.subjects.to_csv('~/subjects_tmp.csv', index=False)
        if not members_object.empty:
            self.members = members_object
        else:
            self.obj_members = Members(
                self.survey_name, subjects=self.subjects)
            self.members = self.obj_members.results
        if not residences_object.empty:
            self.residences = residences_object
        else:
            self.obj_residences = Residences(
                self.survey_name, subjects=self.subjects, members=self.members)
            self.plots = self.obj_residences.plots
            self.households = self.obj_residences.households
            self.residences = self.obj_residences.residences
        residences_columns = [
            'household_structure', 'household_consented', 'household_log_status', 'household_log_date',
            'confirmed', 'plot_status', 'plot_modified', 'selected', 'gps_lat',
            'gps_lon', 'enumerated', 'household_modified']
        self.members = pd.merge(
            self.members, self.residences[residences_columns], how='left', on='household_structure')
        self.subjects = pd.merge(
            self.subjects, self.residences[residences_columns], how='left', on='household_structure')

    def get_subjects(self, merge_subjects_on, add_identity256):
        return Subjects(self.survey_name, merge_subjects_on, add_identity256)

    def validate(self):
        assert len(self.plots.query('enrolled == 1')) == len(
            pd.unique(self.subjects.plot_identifier.ravel()))
        assert len(self.residences.query('enrolled == 1')) == len(
            pd.unique(self.subjects.household_identifier.ravel()))

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

    export_dataset_names = ['plots', 'households', 'members', 'subjects']

    plots_columns = [
        'community', 'confirmed', 'enrolled', 'plot_identifier', 'plot_status']

    households_columns = [
        'community', 'enrolled', 'enumerated', 'household_identifier', 'plot_identifier', 'survey']

    members_columns = [
        'able_to_participate', 'age_in_years', 'community', 'enrolled', 'gender',
        'household_identifier', 'plot_identifier', 'survey']

    subjects_columns = [
        'age_in_years', 'arv_clinic', 'cd4_date', 'cd4_tested', 'cd4_value',
        'circumcised', 'community', 'consent_date', 'final_arv_status', 'final_hiv_status',
        'final_hiv_status_date', 'gender', 'identity', 'identity256', 'pregnant',
        'prev_result_known', 'prev_result', 'prev_result_date', 'referred', 'self_reported_result',
        'subject_identifier', 'survey', 'timestamp', 'vl_drawn', 'vl_result']

    def __init__(self, survey_name, export_now=None, **kwargs):
        super(CDCDataFrames, self).__init__(survey_name, **kwargs)
        add_identity256 = kwargs.get('add_identity256', True)
        if add_identity256:
            self.add_identity256()
        else:
            sys.stdout.write(
                style.WARNING('WARNING! Not adding column \'identity256\'.\n'))
        if kwargs.get('export_now'):
            sys.stdout.write(
                style.NOTICE('Exporting {} to CSV.\n'.format(self.export_dataset_names)))
            self.to_csv()
            sys.stdout.write(style.SQL_FIELD('Done.\n'))

    def add_identity256(self):
        sys.stdout.write(style.NOTICE('Adding column \'identity256\' to subjects dataframe.\n'
                                      'This may take a few minutes ...\n'))
        dte_start = datetime.today()
        self.subjects['identity256'] = self.subjects.apply(
            lambda row: identity256(row, column_name='identity'), axis=1)
        td = (datetime.today() - dte_start)
        sys.stdout.write(style.SQL_FIELD('Done. {} minutes {} seconds\n'.format(
            *divmod(td.days * 86400 + td.seconds, 60))))


class CDCDataFramesCroi2017(CDCDataFrames):

    export_dataset_names = ['subjects']

    subjects_columns = [
        'age_in_years', 'arv_clinic', 'cd4_date', 'cd4_tested', 'cd4_value',
        'circumcised', 'community', 'consent_date', 'final_arv_status', 'final_hiv_status',
        'gender', 'identity', 'identity256', 'pregnant', 'prev_result_known', 'prev_result',
        'prev_result_date', 'referred', 'self_reported_result', 'subject_identifier',
        'survey', 'timestamp', 'vl_drawn', 'vl_result'] + [
        'days_worked',
        'education',
        'working',
        'job_type',
        'first_partner_hiv',
        'first_relationship',
        'length_residence',
        'marital_status',
    ]

    def get_subjects(self, merge_subjects_on, add_identity256):
        return SubjectsCrio2017(self.survey_name, merge_subjects_on, add_identity256)
