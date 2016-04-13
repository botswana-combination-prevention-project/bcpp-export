import os
import numpy as np
import pandas as pd
from bcpp_export.identity256 import identity256

NOT_LINKED = 0
LINKED = 1
ALREADY_LINKED = 2


class Ltc(object):

    def __init__(self, df_subjects_path=None, df_pims_path=None):
        df_pims_path = df_pims_path or '/Users/erikvw/Documents/bcpp/nealia_pimspatient.csv'
        self.df_pims = pd.read_csv(os.path.expanduser(df_pims_path), low_memory=False)
        subjects_path = df_subjects_path or '/Users/erikvw/Documents/bcpp/nealia_subjects.csv'
        self.df_subjects = pd.read_csv(os.path.expanduser(subjects_path), low_memory=False)
        self.drop_columns(self.df_subjects, ['regdate', 'pims_reg_date', 'ltc', 'ltc_timing'])
        self.df_subjects = pd.merge(
            self.df_subjects, self.df_pims[['regdate', 'identity256']], how='left', on='identity256')
        self.df_subjects.rename(columns={'regdate': 'pims_reg_date'}, inplace=True)
        self.df_subjects['consent_date'] = self.df_subjects.apply(
            lambda row: pd.to_datetime(row['consent_date']), axis=1)
        self.df_subjects['pims_reg_date'] = self.df_subjects.apply(
            lambda row: pd.to_datetime(row['pims_reg_date']), axis=1)
        self.df_subjects['ltc'] = self.df_subjects.apply(lambda row: self.linkage_to_care(row), axis=1)
        self.df_subjects['ltc_timing'] = self.df_subjects.apply(lambda row: self.linkage_to_care_timing(row), axis=1)

    def linkage_to_care(self, row):
        linkage_to_care = NOT_LINKED
        if pd.isnull(row.pims_reg_date):
            linkage_to_care = NOT_LINKED
        elif row.consent_date <= row.pims_reg_date:
            linkage_to_care = LINKED
        elif row.consent_date > row.pims_reg_date:
            linkage_to_care = ALREADY_LINKED
        return linkage_to_care

    def linkage_to_care_timing(self, row):
        if row['ltc'] in [LINKED, ALREADY_LINKED]:
            ltc_timing = (row.pims_reg_date - row.consent_date).days
        else:
            ltc_timing = np.nan
        return ltc_timing

    def drop_columns(self, df, columns):
        for column in columns:
            try:
                df.drop([column], inplace=True)
            except ValueError:
                pass
