import pandas as pd
from tabulate import tabulate

from bcpp_export.dataframes.ltc import Ltc

"""
df.query('final_hiv_status == 1 and final_arv_status == 1 and prev_result_known != 1')
"""

ltc = Ltc()
df = ltc.df_subjects

df_kadima = pd.read_csv('/Users/erikvw/Documents/bcpp/kadima_LTC_table_2-ew.csv')
df_kadima.rename(
    columns={'pims_reg_date': 'ek_pims_reg_date', 'pims_initiation_date': 'ek_pims_initiation_date'},
    inplace=True)
df_kadima['ek_in_pims'] = df_kadima.apply(
    lambda row: 0 if row['ek_pims_reg_date'] == 'Not in PIMS at the site' else 1, axis=1)

df1 = pd.merge(
    df.query('intervention == 1'), df_kadima[
        [u'ek_pims_reg_date', u'ek_pims_initiation_date', u'pims_identifier',
         u'ek_in_pims', 'subject_identifier']], how='left', on='subject_identifier')

df2 = pd.DataFrame(
    {'all': df1.query('final_hiv_status == 1').groupby(df1['community']).size()}).reset_index()
df2 = pd.merge(
    df2, pd.DataFrame(
        {'rdb': df1.query('final_hiv_status == 1')[pd.notnull(df1['pims_reg_date'])].groupby(
            df1['community']).size()}).reset_index(), how='left', on='community')

df2 = pd.merge(df2, pd.DataFrame(
    {'ek': df1.query('final_hiv_status == 1 and ek_in_pims == 1')[pd.notnull(df1['ek_pims_reg_date'])].groupby(
        df1['community']).size()}).reset_index(), how='left', on='community')

print(tabulate(df2, headers=['community', 'bhs', 'rdb', 'ettiene'], tablefmt='psql'))
