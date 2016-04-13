import re
import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# from bcpp_export import urls  # DO NOT DELETE

from bcpp_export.private_settings import Lis
from bcpp_export.communities import pair
from bhp066.apps.bcpp_clinic.models import ClinicConsent as EdcClinicConsent, ClinicRequisition
from bhp066.apps.bcpp_lab.models import SubjectRequisition
from bhp066.apps.bcpp_lab.models import ClinicRequisition

engine = create_engine('mssql+pymssql://{user}:{passwd}@{host}:{port}/{db}'.format(
    user=Lis.user, passwd=Lis.password, host=Lis.host, port=Lis.port, db=Lis.name))

from bcpp_export.dataframes.lis import Lis
from bcpp_export.dataframes.edc import Requisition, ClinicConsent

lis = Lis(engine)
df_lis = lis.df_results
requisition = Requisition()
df_req_subject = requisition.subject
df_req_clinic = requisition.clinic

df1 = pd.merge(df_req[pd.notnull(df_req['edc_specimen_identifier']) & (df_req['panel_id'] == VL)], df_lis, on='edc_specimen_identifier', how='left', suffixes=['', '_lis'])
df1 = pd.merge(df_req[(df_req['survey'] == 'bcpp-year-1') &
                      (df_req['visit_code'] == 'T0') &
                      (df_req['panel_id'] == VL)],
               df_lis, on='edc_specimen_identifier', how='left', suffixes=['', '_lis'])
# edc_specimen_identifier not found in LIS
pd.merge(df_req[pd.notnull(df_req['edc_specimen_identifier']) & (df_req['panel_id'] == VL)], df_lis, on='edc_specimen_identifier', how='right', suffixes=['_edc', ''])

# edc_specimen_identifier not found in EDC
# subject identifier mismatch (matched on edc_speciment_identifier)
df1[df1['subject_identifier'] != df1['subject_identifier_lis']][['subject_identifier', 'subject_identifier_lis', 'edc_specimen_identifier','drawn_datetime', 'survey', 'sample_condition', 'panel_id']]

df1[pd.isnull(df1['result'])][['subject_identifier', 'subject_identifier_lis', 'edc_specimen_identifier','drawn_datetime', 'survey', 'sample_condition']]

# fill df_lis in missing subject identifiers from clinic
# match to lab_identifier
df = pd.merge(df_lis[pd.isnull(df_lis['final_subject_identifier'])], df_clinic[['subject_identifier', 'lab_identifier']], left_on='subject_identifier', right_on='lab_identifier', suffixes=['', '_clinic'])[['subject_identifier', 'subject_identifier_clinic']]
df.drop_duplicates(inplace=True)
df_lis = pd.merge(df_lis, df, on='subject_identifier', how='left')
df_lis['final_subject_identifier'] = df_lis.apply(lambda row: fill_final_subject_identifier(row), axis=1)
del df_lis['subject_identifier_clinic']
# match to htc_identifier
df = pd.merge(df_lis[pd.isnull(df_lis['final_subject_identifier'])], df_clinic[['subject_identifier', 'htc_identifier']], left_on='subject_identifier', right_on='htc_identifier', suffixes=['', '_clinic'])[['subject_identifier', 'subject_identifier_clinic']]
df.drop_duplicates(inplace=True)
df_lis = pd.merge(df_lis, df, on='subject_identifier', how='left')
df_lis['final_subject_identifier'] = df_lis.apply(lambda row: fill_final_subject_identifier(row), axis=1)
# show unmatched K numbers
unmatched = df_lis[pd.isnull(df_lis['final_subject_identifier']) & (df_lis['subject_identifier'].str.startswith('K'))]
print(tabulate(
    unmatched[['lis_identifier', 'received_datetime', 'subject_identifier', 'drawn_datetime']].sort_values('subject_identifier'),
    headers=['received_as', 'received_on', 'subject_identifier', 'drawn'],
    tablefmt='psql'))

# find with lis_identifier > 7 but no subject identifier
# assume are edc specimen identifiers or aliquot numbers
df = df_lis[pd.isnull(df_lis['final_subject_identifier']) & ~(df_lis['subject_identifier'].str.startswith('K')) & (df_lis['lis_identifier'].str.len() > 7)][['lis_identifier']]
df['edc_specimen_identifier'] = df['lis_identifier'].str[0:12]
df.drop_duplicates(inplace=True)
df = pd.merge(df, df_req[['edc_specimen_identifier', 'subject_identifier']], on='edc_specimen_identifier', how='inner', suffixes=['', '_clinic'])[['lis_identifier', 'subject_identifier']]
df_lis = pd.merge(df_lis, df, on='lis_identifier', how='left', suffixes=['', '_clinic'])
df_lis['final_subject_identifier'] = df_lis.apply(lambda row: fill_final_subject_identifier(row), axis=1)

df = df_lis[pd.isnull(df_lis['final_subject_identifier']) & ~(df_lis['subject_identifier'].str.startswith('K')) & (df_lis['lis_identifier'].str.len() > 7)][['lis_identifier']]
df['edc_specimen_identifier'] = df['lis_identifier'].str[0:12]
df.drop_duplicates(inplace=True)
df = pd.merge(df, df_req_clinic[['edc_specimen_identifier', 'subject_identifier']], on='edc_specimen_identifier', how='inner', suffixes=['', '_clinic'])[['lis_identifier', 'subject_identifier']]
df_lis = pd.merge(df_lis, df, on='lis_identifier', how='left', suffixes=['', '_clinic'])
df_lis['final_subject_identifier'] = df_lis.apply(lambda row: fill_final_subject_identifier(row), axis=1)



df1 = pd.merge(df, df_clinic[['other_identifier', 'subject_identifier']], on='other_identifier', how='left')
df1[~(df['other_identifier'].str.startswith('066'))][['subject_identifier_x', 'other_identifier', 'subject_identifier_y', 'result']]


