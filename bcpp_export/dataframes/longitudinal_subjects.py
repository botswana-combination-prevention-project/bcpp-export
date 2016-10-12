import numpy as np
import pandas as pd

from bcpp_export.constants import (
    NEG, POS, UNK, YES, IND, NAIVE, NO, DEFAULTER, ON_ART)


class LongitudinalSubjects:

    def __init__(self, df, suffix=None):
        self.suffix = '_y1'

        df['tmp_final_hiv_status'] = df.apply(
            lambda row: self.final_hiv_status(row),
            axis=1)
        df['tmp_final_hiv_status_date'] = df.apply(
            lambda row: self.final_hiv_status_date(row),
            axis=1)
        df['tmp_final_arv_status'] = df.apply(
            lambda row: self.final_arv_status(row),
            axis=1)

        df['tmp_prev_result'] = df.apply(
            lambda row: self.prev_result(row),
            axis=1)

        df['tmp_prev_result_date'] = df.apply(
            lambda row: self.prev_result_date(row),
            axis=1)

        df['tmp_prev_result_known'] = df.apply(
            lambda row: NO if pd.isnull(row['tmp_prev_result']) else YES,
            axis=1)

        df['final_hiv_status'] = df['tmp_final_hiv_status']
        df['final_hiv_status_date'] = df['tmp_final_hiv_status_date']
        df['final_arv_status'] = df['tmp_final_arv_status']
        df['prev_result'] = df['tmp_prev_result']
        df['prev_result_date'] = df['tmp_prev_result_date']
        df['prev_result_known'] = df['tmp_prev_result_known']

        # drop tmp columns
        df = df.drop('tmp_final_hiv_status', axis=1)
        df = df.drop('tmp_final_hiv_status_date', axis=1)
        df = df.drop('tmp_final_arv_status', axis=1)
        df = df.drop('tmp_prev_result', axis=1)
        df = df.drop('tmp_prev_result_date', axis=1)
        df = df.drop('tmp_prev_result_known', axis=1)

        # fix datetimes
        df['consent_date'] = pd.to_datetime(df['consent_date'])
        df['prev_result_date'] = pd.to_datetime(df['prev_result_date'])
        df['final_hiv_status_date'] = pd.to_datetime(df['final_hiv_status_date'])

        df = df.rename(columns={'appointment__visit_definition__code': 'timepoint'})

        self.df = df

    @property
    def dataframe(self):
        return self.df

    def final_hiv_status(self, row):
        previous_result = row['final_hiv_status{}'.format(self.suffix)]
        current_result = row['final_hiv_status']
        if pd.isnull(previous_result):
            final_hiv_status = current_result
        elif pd.isnull(current_result):
            if previous_result == NEG or previous_result == UNK or previous_result == IND:
                final_hiv_status = np.nan
            else:
                final_hiv_status = previous_result
        elif current_result == UNK and previous_result != NEG:
            final_hiv_status = previous_result
        elif current_result == NEG and previous_result == POS:
            final_hiv_status = previous_result
        else:
            final_hiv_status = current_result
        return final_hiv_status

    def final_hiv_status_date(self, row):
        previous_result = row['final_hiv_status{}'.format(self.suffix)]
        current_result = row['final_hiv_status']
        previous_result_date = row['final_hiv_status_date{}'.format(self.suffix)]
        current_result_date = row['final_hiv_status_date']
        if pd.isnull(current_result):
            if previous_result == NEG or previous_result == UNK or previous_result == IND:
                final_hiv_status_date = np.nan
            else:
                final_hiv_status_date = previous_result_date
        elif current_result == UNK and previous_result != NEG:
            final_hiv_status_date = previous_result_date
        elif current_result == NEG and previous_result == POS:
            final_hiv_status_date = previous_result_date
        elif current_result == POS and previous_result == POS:
            final_hiv_status_date = previous_result_date
        else:
            final_hiv_status_date = current_result_date
        return final_hiv_status_date

    def final_arv_status(self, row):
        final_hiv_status = self.final_hiv_status(row)
        if pd.isnull(final_hiv_status):
            final_arv_status = np.nan
        elif final_hiv_status != POS:
            final_arv_status = np.nan
        else:
            previous_arv = row['final_arv_status{}'.format(self.suffix)]
            current_arv = row['final_arv_status']
            if pd.isnull(current_arv):
                if previous_arv == ON_ART:
                    final_arv_status = DEFAULTER
                else:
                    final_arv_status = NAIVE
            elif previous_arv == ON_ART and current_arv != ON_ART:
                final_arv_status = DEFAULTER
            elif (previous_arv == ON_ART or previous_arv == DEFAULTER) and current_arv == NAIVE:
                final_arv_status = DEFAULTER
            else:
                final_arv_status = current_arv
        return final_arv_status

    def prev_result(self, row):
        previous_result = row['final_hiv_status{}'.format(self.suffix)]
        if pd.isnull(row['prev_result']):
            prev_result = previous_result
        elif previous_result == POS:
            prev_result = POS
        elif previous_result == NEG and row['prev_result'] == POS:
            prev_result = row['prev_result']
        elif previous_result == NEG and row['prev_result'] == NEG:
            prev_result = row['prev_result']
        elif previous_result == NEG and row['prev_result'] not in [POS, NEG]:
            prev_result = previous_result
        else:
            prev_result = row['prev_result']
        if prev_result == UNK:
            prev_result = np.nan
        return prev_result

    def prev_result_date(self, row):
        previous_result = row['final_hiv_status{}'.format(self.suffix)]
        previous_result_date = row['final_hiv_status_date{}'.format(self.suffix)]
        if pd.isnull(row['prev_result']):
            prev_result_date = previous_result_date
        elif previous_result == POS:
            prev_result_date = previous_result_date
        elif previous_result == NEG and row['prev_result'] == POS:
            prev_result_date = row['prev_result_date']
        elif previous_result == NEG and row['prev_result'] == NEG:
            prev_result_date = row['prev_result_date']
        elif previous_result == NEG and row['prev_result'] not in [POS, NEG]:
            prev_result_date = previous_result_date
        else:
            prev_result_date = row['prev_result_date']
        prev_result = self.prev_result(row)
        if prev_result == UNK:
            prev_result_date = np.nan
        return prev_result_date
