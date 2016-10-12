import pandas as pd
import numpy as np

from bcpp_export.dataframes.longitudinal_subjects import LongitudinalSubjects

pd.set_option('display.width', None)

# load saved files (generated using bcpp_export)
df_s1 = pd.read_csv('/Users/erikvw/Documents/bcpp/cdc/20161007/bcpp_export_year1_20161006_results.csv', low_memory=False)
df_s1['timepoint'] = 'T0'
df_s1 = df_s1.query('pair >= 1 and pair <= 12 and intervention == True').drop_duplicates('subject_identifier')

df_s2 = pd.read_csv('/Users/erikvw/Documents/bcpp/cdc/20161007/bcpp_export_year2_20161006_results.csv', low_memory=False)
df_s2 = df_s2.rename(columns={'appointment__visit_definition__code': 'timepoint'})
df_s2 = df_s2.query('pair >= 1 and pair <= 12 and intervention == True').drop_duplicates('subject_identifier')

# merge to create  Y2 dataframe and run through class to calculate derived vars
df = pd.merge(df_s2, df_s1, how='left', on='subject_identifier', suffixes=['', '_y1'])
subjects = LongitudinalSubjects(df)
df = subjects.df

# override two values for final_arv_status (agreed w/ Kara and Kathleen)
df.loc[df['subject_identifier'] == '066-19260006-2', 'final_arv_status'] = 2.0
df.loc[df['subject_identifier'] == '066-31310013-6', 'final_arv_status'] = 2.0

# use same export columns as before
subjects_columns = [
    'age_in_years', 'arv_clinic', 'cd4_date', 'cd4_tested', 'cd4_value',
    'circumcised', 'community', 'consent_date', 'final_arv_status', 'final_hiv_status',
    'final_hiv_status_date', 'gender', 'identity', 'identity256', 'pregnant',
    'prev_result_known', 'prev_result', 'prev_result_date', 'referred', 'self_reported_result',
    'subject_identifier', 'timepoint', 'survey', 'pair', 'timestamp']

# write final file
path_or_buf_y2 = '/Users/erikvw/Documents/bcpp/cdc/20161007/df_tmp20161010E_y2.csv'
df.to_csv(columns=subjects_columns, path_or_buf=path_or_buf_y2, index=False)

df_s1 = pd.read_csv('/Users/erikvw/Documents/bcpp/cdc/20161007/bcpp_export_year1_20161006_results.csv', low_memory=False)
df_s1 = df_s1[df_s1['intervention'] == True]
path_or_buf_y1 = '/Users/erikvw/Documents/bcpp/cdc/20161007/df_tmp20161010E_y1.csv'
df_s1.to_csv(columns=subjects_columns, path_or_buf=path_or_buf_y1, index=False)

df_y1 = pd.read_csv(path_or_buf_y1, low_memory=False)
df_y1['timepoint'] = 'T0'
df_y2 = pd.read_csv(path_or_buf_y2, low_memory=False)
df_final = pd.concat([df_y1, df_y2])

path_or_buf_final = '/Users/erikvw/Documents/bcpp/cdc/20161007/bcpp_subjects_20161012_pairs1-12.csv'
df_final.to_csv(path_or_buf=path_or_buf_final, index=False)

# viral load

# file from Moyo, 2016-10-12
df_vl = pd.read_csv('/Users/erikvw/Documents/bcpp/cdc/20161007/bhp066_auvl_all.csv', low_memory=True)

# fix datetimes
df_vl['sample_date_drawn'] = pd.to_datetime(df_vl['sample_date_drawn'])
df_vl['date_received'] = pd.to_datetime(df_vl['date_received'])
df_vl['sample_assay_date'] = pd.to_datetime(df_vl['sample_assay_date'])
df_vl['report_date'] = pd.to_datetime(df_vl['reportDate'])
df_vl = df_vl.drop('reportDate', axis=1)
df_vl['specimen_identifier'] = df_vl['edc_specimen_identifier'].str.slice(0, 12)
df_vl = df_vl.rename(columns={'edc_specimen_identifier': 'aliquot_identifier', 'RESULT': 'result'})
df_vl = df_vl[pd.notnull(df_vl['specimen_identifier'])]

# file from bcpp-rdb (through runserver)
df_req = pd.read_csv('/Users/erikvw/Documents/bcpp/cdc/20161007/bcpp_requisitions_2016-10-11.csv', low_memory=True)
df_req = df_req[pd.notnull(df_req['specimen_identifier'])]

df_vl2 = pd.merge(df_vl, df_req, on=['specimen_identifier'], how='left', suffixes=['', '_vl'])
df_vl2 = df_vl2[pd.notnull(df_vl2['result'])]
df_vl2 = df_vl2[df_vl2['result'] != '*']
# df_vl2['dupl'] = df_vl2.duplicated(['subject_identifier', 'specimen_identifier']) & (df_vl2['code'] == 'T1')
# df_vl2['dupl'] = df_vl2.duplicated(['subject_identifier', 'specimen_identifier']) & (df_vl2['code'] == 'T0') & (df_vl2['dupl'] == False)
# df_vl2 = df_vl2[df_vl2['dupl']==False]
# df_vl2 = df_vl2.drop('dupl', axis=1)

df_vl2 = df_vl2.rename(columns={'code': 'timepoint'})
df_vl2 = df_vl2.sort_values(['subject_identifier', 'timepoint', 'report_date'])
df_vl2 = df_vl2.drop_duplicates(['subject_identifier', 'timepoint', 'report_date'], keep='last')
df_vl2 = df_vl2.drop_duplicates(['subject_identifier', 'timepoint'], keep='last')  # 4308 rows x 20 columns

# returns an empty series
# df_vl2[df_vl2.duplicated(['subject_identifier', 'code'])]

df = pd.merge(df, df_vl2[['subject_identifier', 'timepoint', 'result', 'result_quantifier', 'sample_assay_date', 'is_drawn']],
              how='left', on=['subject_identifier', 'timepoint'], suffixes=['', '_vl'])
