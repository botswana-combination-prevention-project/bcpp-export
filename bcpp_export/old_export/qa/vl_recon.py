import pandas as pd
import numpy as np

from tabulate import tabulate

from bcpp_export import urls  # DO NOT DELETE

from bhp066.apps.bcpp_lab.models import ClinicRequisition, Panel
from bhp066.apps.bcpp_clinic.models import (
    ClinicVlResult, ViralLoadTracking, Questionnaire, ClinicConsent)

from bcpp_export.dataframes.edc import EdcModelToDataFrame
from bcpp_export.dataframes.lis import Lis


class report(object):

    def __init__(self, title, dataframe):
        self.title = title
        self.dataframe = dataframe

    def __repr__(self):
        return self.title

    @property
    def print_df(self):
        headers = list(self.dataframe.columns)
        print(tabulate(self.dataframe, headers=headers, tablefmt='psql'))


class VlRecon(object):

    """
    Clinic Viral Load Result Reconciliation

    from bcpp_export.qa import VlRecon

    vl_recon = VlRecon()
    vl_recon.print_all()
    """

    def __init__(self, df_lis=None):
        self.issues = {}
        self.statistics = {}
#         # lis dataframe
#         if df_lis:
#             self.df_lis = df_lis
#         else:
#             self.df_lis = Lis().results
        # bcpp dataframes
        self.df_consent = EdcModelToDataFrame(ClinicConsent).dataframe
        self.df_consent['is_verified'] = self.df_consent.apply(lambda row: 'Yes' if row['is_verified'] == True else 'No', axis=1)
        self.df_track = EdcModelToDataFrame(ViralLoadTracking, add_columns_for='clinic_visit').dataframe
        self.df_req = EdcModelToDataFrame(ClinicRequisition, add_columns_for='clinic_visit').dataframe
        self.df_panel = EdcModelToDataFrame(Panel).dataframe
        self.df_result = EdcModelToDataFrame(ClinicVlResult, add_columns_for='clinic_visit').dataframe
        self.df_q = EdcModelToDataFrame(Questionnaire, add_columns_for='clinic_visit').dataframe
        self.df_q['track'] = self.df_q.apply(lambda row: self.vl_track(row), axis=1)
        self.df_req = pd.merge(self.df_req, self.df_panel[['id', 'name']], left_on='panel_id', right_on='id', how='left', suffixes=['', '_panel'])
        self.df_req.rename(columns={'name': 'panel'}, inplace=True)
        self.df_req = self.df_req.sort_values(['subject_identifier', 'specimen_identifier'])
        self.df_req['dup'] = self.df_req.query('panel == \'Clinic Viral Load\' and visit_code == \'C0\'').duplicated('subject_identifier')
        self.df_q = pd.merge(self.df_q, self.df_track[['clinic_visit_id', 'is_drawn']], on='clinic_visit_id', how='left', suffixes=['', '_track'])
        self.df_q['has_vl_track'] = self.df_q.apply(lambda row: 'Yes' if pd.notnull(row['is_drawn']) else 'No', axis=1)
        self.df_q['requisition'] = self.df_q.apply(lambda row: self.requisition(row), axis=1)
        self.df_q = pd.merge(
            self.df_q,
            self.df_req.query('panel == \'Clinic Viral Load\' and visit_code == \'C0\'')[['clinic_visit_id', 'is_drawn', 'is_receive']],
            on='clinic_visit_id', how='left', suffixes=['', '_req'])
        self.df_q['has_requisition'] = self.df_q['is_drawn_req']
        self.df_q = pd.merge(self.df_q, self.df_result[['clinic_visit_id', 'result_value']], on='clinic_visit_id', how='left', suffixes=['', '_result'])
        self.df_q['has_result'] = self.df_q['result_value'].notnull()
        self.df_q['has_result'] = self.df_q.apply(lambda row: 'Yes' if row['has_result'] == True else 'No', axis=1)
        self.df_q['has_result'] = self.df_q.apply(
            lambda row: row['has_result'] if (row['is_drawn_req'] == 'Yes' and row['track'] == 'BHP') or row['track'] == 'MOH' else 'ND',
            axis=1)

        self.issues.update({
            'duplicate_requisitions':
            self.df_req.query('dup == True')['subject_identifier'].drop_duplicates()
        })
        self.statistics.update(
            {'track':
             report(
                 'Responsibility for VL Testing',
                 pd.DataFrame({'freq': self.df_q.groupby(['track']).size()}).reset_index()),
             'has_tracking_form':
             report(
                 'Requiring Requisition',
                 pd.DataFrame({'freq': self.df_q.groupby(
                     ['track', 'has_vl_track']).size()}).reset_index()),
             'requisition':
             report(
                 'Has Requisition',
                 pd.DataFrame({'freq': self.df_q.groupby(
                     ['track', 'has_vl_track', 'requisition', 'has_requisition']).size()}).reset_index()),
             'result':
             report(
                 'Missing Viral Load Result',
                 pd.DataFrame({'freq': self.df_q.query('has_result == \'No\'').groupby(
                     ['track', 'has_vl_track', 'has_result']).size()}).reset_index()),
             'result_by_community MOH':
             report(
                 'Missing Viral Load Result by Community (MOH)',
                 pd.DataFrame({'freq': self.df_q.query('track == \'MOH\' and has_result == \'No\'').groupby(
                     ['community', 'track', 'has_result']).size()}).reset_index()),
             'result_by_community BHP':
             report(
                 'Missing Viral Load Result by Community (BHP)',
                 pd.DataFrame({'freq': self.df_q.query('track == \'BHP\' and has_result == \'No\'').groupby(
                     ['community', 'track', 'has_result']).size()}).reset_index()),
             'unverified_consents':
             report(
                 'Consent verification',
                 pd.DataFrame({'freq': self.df_consent.groupby(
                     ['is_verified']).size()}).reset_index()),
             'unverified_consents_by_community':
             report(
                 'Unverified Consents by Community',
                 pd.DataFrame({'freq': self.df_consent.query('is_verified == \'No\'').groupby(
                     ['community', 'is_verified']).size()}).reset_index()),
             })

    def print_all(self):
        n = 1
        for report in self.statistics.values():
            print('\n\n{}. {}'.format(n, report.title))
            report.print_df
            n += 1

    def vl_track(self, row):
        track = ['ccc_scheduled', 'etc_scheduled', 'masa_vl_scheduled']
        if row['registration_type'] in track:
            return 'MOH'
        return 'BHP'

    def requisition(self, row):
        if pd.notnull(row['is_drawn']):
            return 'Yes' if row['is_drawn'] == 'No' else 'No'
        else:
            return 'NA'
