import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from bcpp_export import urls  # DO NOT DELETE
from bhp066.apps.bcpp_lab.models import SubjectRequisition, ClinicRequisition


class Requisition(object):

    def __init__(self):
        self.subject = self.requisition_df(SubjectRequisition, 'subject_visit')
        self.clinic = self.requisition_df(ClinicRequisition, 'clinic_visit')

    def requisition_df(self, model, visit_model_name):
        qs = model.objects.all()
        columns = qs[0].__dict__.keys()
        columns.remove('_state')
        columns.remove('_user_container_instance')
        columns.remove('using')
        columns.append('{}__household_member__household_structure__survey__survey_slug'.format(visit_model_name))
        columns.append('{}__household_member__household_structure__household__plot__community'.format(visit_model_name))
        columns.append('{}__appointment__visit_definition__code'.format(visit_model_name))
        qs = model.objects.values_list(*columns).filter(specimen_identifier__isnull=False)
        df_req = pd.DataFrame(list(qs), columns=columns)
        df_req.rename(columns={
            '{}__household_member__household_structure__survey__survey_slug'.format(visit_model_name): 'survey',
            '{}__household_member__household_structure__household__plot__community'.format(visit_model_name): 'community',
            'specimen_identifier': 'edc_specimen_identifier',
            '{}__appointment__visit_definition__code'.format(visit_model_name): 'visit_code',
        }, inplace=True)
        df_req.fillna(value=np.nan, inplace=True)
        return df_req
