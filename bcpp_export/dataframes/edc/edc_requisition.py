import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from tabulate import tabulate
from bcpp_export import urls  # DO NOT DELETE
from bhp066.apps.bcpp_lab.models import SubjectRequisition, ClinicRequisition


class Requisition(object):

    def __init__(self):
        self.subject = self.requisition_df(SubjectRequisition, 'subject_visit')
        self.subject['requisition_source'] = 'subject'
        self.clinic = self.requisition_df(ClinicRequisition, 'clinic_visit')
        self.clinic['requisition_source'] = 'clinic'
        columns = ['subject_identifier', 'edc_specimen_identifier', 'survey',
                   'visit_code', 'community', 'drawn_datetime', 'requisition_identifier',
                   'requisition_datetime', 'is_drawn', 'panel_id', 'requisition_source']
        self.all = pd.concat(
            [self.subject[columns], self.clinic[columns]], ignore_index=True)

    def not_drawn_with_edc_specimen_identifier(self, format=None):
        columns = ['subject_identifier', 'edc_specimen_identifier', 'requisition_identifier']
        df = self.all[pd.notnull(self.all['edc_specimen_identifier']) & ~(self.drawn(self.all))][columns]
        if format == 'dataframe':
            return df
        else:
            print(tabulate(df[columns].sort_values('subject_identifier'),
                           headers=columns, tablefmt='psql'))

    def drawn(self, df):
        return ~df['requisition_identifier'].str.contains(
            '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}')

    def requisition_df(self, model, visit_model_name):
        qs = model.objects.all()
        columns = qs[0].__dict__.keys()
        columns.remove('_state')
        columns.remove('_user_container_instance')
        columns.remove('using')
        columns.remove('subject_identifier')
        columns.remove('community')
        columns.append('{}__household_member__household_structure__survey__survey_slug'.format(visit_model_name))
        columns.append('{}__household_member__household_structure__household__plot__community'.format(visit_model_name))
        columns.append('{}__appointment__visit_definition__code'.format(visit_model_name))
        columns.append('{}__appointment__registered_subject__subject_identifier'.format(visit_model_name))
        qs = model.objects.values_list(*columns).all()
        # qs = model.objects.values_list(*columns).filter(specimen_identifier__isnull=False)
        df_req = pd.DataFrame(list(qs), columns=columns)
        df_req.rename(columns={
            '{}__household_member__household_structure__survey__survey_slug'.format(visit_model_name): 'survey',
            '{}__household_member__household_structure__household__plot__community'.format(visit_model_name): 'community',
            'specimen_identifier': 'edc_specimen_identifier',
            '{}__appointment__visit_definition__code'.format(visit_model_name): 'visit_code',
            '{}__appointment__registered_subject__subject_identifier'.format(visit_model_name): 'subject_identifier'
        }, inplace=True)
        df_req.fillna(value=np.nan, inplace=True)
        for column in list(df_req.select_dtypes(include=['datetime64[ns, UTC]']).columns):
            df_req[column] = df_req[column].astype('datetime64[ns]')
        return df_req
