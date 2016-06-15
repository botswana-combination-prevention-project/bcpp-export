import re
import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from tabulate import tabulate
from bcpp_export import urls  # DO NOT DELETE
from bcpp_export.undash import undash
from bcpp_export.private_settings import Lis as LisCredentials
from bcpp_export.dataframes.edc import ClinicConsent
from bcpp_export.dataframes.edc.edc_requisition import Requisition
from bcpp_export.dataframes.edc.edc_registered_subject import RegisteredSubject


class Lis(object):

    def __init__(self, df=pd.DataFrame(), engine=None, protocol=None,
                 protocol_prefix=None, df_currentstudyparticipant=pd.DataFrame()):
        if not df.empty:
            self.results = df
        else:
            self.engine = engine or create_engine('mssql+pymssql://{user}:{passwd}@{host}:{port}/{db}'.format(
                user=LisCredentials.user, passwd=LisCredentials.password,
                host=LisCredentials.host, port=LisCredentials.port,
                db=LisCredentials.name))
            self.protocol = protocol or 'BHP066'
            self.protocol_prefix = protocol_prefix or '066'
            self.results = self.fetch_results_as_dataframe()
            self.df_clinic_consent = ClinicConsent().df
            self.requisition = Requisition()
            self.update_final_subject_identifier_from_lab_identifier()
            self.update_final_subject_identifier_from_htc_identifier()
            self.update_final_subject_identifier_from_requisitions()
            self.update_final_subject_identifier_from_identity()
            self.update_edc_specimen_identifier_from_requisition()
            self.update_final_subject_identifier_from_cdc(df_currentstudyparticipant)
            # self.update_edc_specimen_identifier_from_receive()
            self.update_requisition_columns()

    def print_df(self, df, headers):
        print(tabulate(df, headers=headers, tablefmt='psql'))

    def show_final_subject_identifier_source(self):
        return self.results.groupby('final_subject_identifier_source').size()

    def show_missing_subject_identifier_k_only(self, format=None):
        """show unmatched K numbers"""
        columns = ['lis_identifier', 'received_datetime', 'subject_identifier', 'drawn_datetime',
                   'result']
        df = self.results[
            (pd.isnull(self.results['final_subject_identifier'])) &
            (self.results['subject_identifier'].str.startswith('K'))]
        if format == 'dataframe':
            return df[columns].sort_values('subject_identifier')
        else:
            self.print_df(df[columns].sort_values('subject_identifier'),
                          ['received_as', 'received_on', 'subject_identifier', 'drawn'])

    def show_missing_subject_identifier(self, format=None):
        columns = ['lis_identifier', 'received_datetime',
                   'subject_identifier', 'drawn_datetime', 'test_id', 'utestid', 'result']
        df = self.results[pd.isnull(self.results['final_subject_identifier'])]
        df = df[columns].sort_values('received_datetime')
        df.drop_duplicates()
        df.reset_index()
        if format == 'dataframe':
            return df
        else:
            self.print_df(df, headers=[
                'received_as', 'received_on', 'subject_identifier',
                'drawn', 'test', 'testid', 'result'])

    def show_missing_edc_specimen_identifier(self, format=None):
        df = self.results[
            (pd.isnull(self.results['edc_specimen_identifier'])) &
            (pd.notnull(self.results['final_subject_identifier']))][
            ['final_subject_identifier', 'lis_identifier', 'received_datetime', 'test_id',
             'drawn_datetime', 'result']]
        df = df.sort_values('received_datetime')
        df.drop_duplicates()
        df.reset_index()
        if format == 'dataframe':
            return df
        else:
            self.print_df(df, headers=[
                'subject_identifier', 'received_as', 'received_on', 'test',
                'drawn', 'result'])

    def fetch_results_as_dataframe(self, edc_panels=None):
        with self.engine.connect() as conn, conn.begin():
            df = pd.read_sql_query(self.sql_results, conn)
        df.fillna(value=np.nan, inplace=True)
        df['result'] = df['result'].str.replace('<', '')
        df['result'] = df['result'].str.replace('>', '')
        df['result'] = df['result'].str.replace('*', '')
        df['result'] = df['result'].str.replace('=', '')
        df['result'] = df.apply(
            lambda row: np.nan if row['result'] == '' else row['result'], axis=1)
        # df['result_float'] = df[df['result'].str.contains('\d+')]['result'].astype(float, na=False)
        for column in list(df.select_dtypes(include=['datetime64[ns, UTC]']).columns):
            df[column] = df[column].astype('datetime64[ns]')
        df['result_datetime'] = pd.to_datetime(df['result_datetime'])
        df['received_datetime'] = pd.to_datetime(df['received_datetime'])
        df['drawn_datetime'] = pd.to_datetime(df['drawn_datetime'])
        df['drawn_datetime'] = pd.to_datetime(df['drawn_datetime'].dt.date)
        df['specimen_identifier'] = df.apply(lambda row: np.nan if row['specimen_identifier'] == 'NA' else row['specimen_identifier'], axis=1)
        df['aliquot_identifier'] = df.apply(lambda row: self.aliquot_identifier(row), axis=1)
        df['edc_specimen_identifier'] = df.apply(lambda row: self.edc_specimen_identifier(row, self.protocol_prefix), axis=1)
        df['subject_identifier'] = df.apply(lambda row: undash(row['subject_identifier'], '^{}-'.format(self.protocol_prefix)), axis=1)
        df['final_subject_identifier'] = df[df['subject_identifier'].str.startswith('{}-'.format(self.protocol_prefix))]['subject_identifier']
        df['final_subject_identifier_source'] = df.apply(lambda row: np.nan if pd.isnull(row['final_subject_identifier']) else 'lis', axis=1)
        return df

    @property
    def sql_results(self):
        return """select L.PID as lis_identifier, pat_id as subject_identifier,
        edc_specimen_identifier as specimen_identifier, sample_date_drawn as drawn_datetime,
        l.tid as test_id, l.headerdate as received_datetime,
        L21D.utestid, L21D.result, L21D.result_quantifier, L21D.sample_assay_date as result_datetime,
        sample_condition
        from BHPLAB.DBO.LAB01Response as L
        left join BHPLAB.DBO.LAB21Response as L21 ON L21.PID=L.PID
        left join BHPLAB.DBO.LAB21ResponseQ001X0 as L21D on L21D.QID1X0=L21.Q001X0
        where sample_protocolnumber='BHP066'"""

    @property
    def sql_getresults(self):
        return """SELECT * FROM "getresults_dst_history"""

    def update_final_subject_identifier_from_lab_identifier(self):
        """Matches lab_identifier from clinic consent to lis.subject_identifier."""
        df = pd.merge(self.results[pd.isnull(self.results['final_subject_identifier'])],
                      self.df_clinic_consent[['subject_identifier', 'lab_identifier']],
                      left_on='subject_identifier',
                      right_on='lab_identifier',
                      suffixes=['', '_edc'])[['subject_identifier', 'subject_identifier_edc']]
        df.rename(columns={'subject_identifier_edc': 'final_subject_identifier'}, inplace=True)
        df['final_subject_identifier_source'] = 'clinic_consent (lab id)'
        df.drop_duplicates(inplace=True)
        df.set_index('subject_identifier', inplace=True)
        self.results.set_index('subject_identifier', inplace=True)
        self.results = self.results.combine_first(df)
        self.results.reset_index(inplace=True)

    def update_final_subject_identifier_from_htc_identifier(self):
        """Matches htc_identifier from clinic consent to lis.subject_identifier."""
        df = pd.merge(self.results[pd.isnull(self.results['final_subject_identifier'])],
                      self.df_clinic_consent[['subject_identifier', 'htc_identifier']],
                      left_on='subject_identifier',
                      right_on='htc_identifier',
                      suffixes=['', '_edc'])[['subject_identifier', 'subject_identifier_edc']]
        df.rename(columns={'subject_identifier_edc': 'final_subject_identifier'}, inplace=True)
        df['final_subject_identifier_source'] = 'clinic_consent (htc id)'
        df.drop_duplicates(inplace=True)
        df.set_index('subject_identifier', inplace=True)
        self.results.set_index('subject_identifier', inplace=True)
        self.results = self.results.combine_first(df)
        self.results.reset_index(inplace=True)

    def update_final_subject_identifier_from_requisitions(self):
        # find with lis_identifier > 7 but no subject identifier
        # assume are edc specimen identifiers or aliquot numbers
        for df_req in [self.requisition.subject, self.requisition.clinic]:
            df = self.results[
                pd.isnull(self.results['final_subject_identifier']) &
                ~(self.results['subject_identifier'].str.startswith('K')) &
                (self.results['lis_identifier'].str.len() > 7)][['lis_identifier']]
            df['edc_specimen_identifier'] = df['lis_identifier'].str[0:12]
            df.drop_duplicates(inplace=True)
            df = pd.merge(df, df_req[['edc_specimen_identifier', 'subject_identifier']],
                          on='edc_specimen_identifier',
                          how='inner',
                          suffixes=['', '_edc'])[['lis_identifier', 'subject_identifier']]
            df.rename(columns={'subject_identifier': 'final_subject_identifier'}, inplace=True)
            df['final_subject_identifier_source'] = 'edc requisition'
            df.drop_duplicates(inplace=True)
            df.set_index('lis_identifier', inplace=True)
            self.results.set_index('lis_identifier', inplace=True)
            self.results = self.results.combine_first(df)
            self.results.reset_index(inplace=True)

    def update_final_subject_identifier_from_identity(self):
        df_rs = RegisteredSubject().df
        df = pd.merge(self.results[pd.isnull(self.results['final_subject_identifier'])],
                      df_rs[['subject_identifier', 'identity']],
                      left_on='subject_identifier',
                      right_on='identity',
                      suffixes=['', '_edc'])[['subject_identifier', 'subject_identifier_edc']]
        df.rename(columns={'subject_identifier_edc': 'final_subject_identifier'}, inplace=True)
        df['final_subject_identifier_source'] = 'edc registered_subject'
        df.drop_duplicates(inplace=True)
        df.set_index('subject_identifier', inplace=True)
        self.results.set_index('subject_identifier', inplace=True)
        self.results = self.results.combine_first(df)
        self.results.reset_index(inplace=True)

    def update_final_subject_identifier_from_cdc(self, df_currentstudyparticipant):
        """Update identifier from CDC HTC data."""
        if not df_currentstudyparticipant.empty:
            df = df_currentstudyparticipant
            df['htcid'].fillna(value=np.nan, inplace=True)
            df['htcid'] = df.apply(lambda row: undash(row['htcid']), axis=1)
            df['ssid'].fillna(value=np.nan, inplace=True)
            df['ssid'] = df.apply(lambda row: undash(row['ssid']), axis=1)
            df = df.replace('unk', np.nan)
            df = df[pd.notnull(df['omangnumber'])]
            self.df_htc = df.copy()
            self.df_htc = self.df_htc.rename(columns={'htcid': 'subject_identifier_cdc', 'omangnumber': 'identity'})
            self.df_htc = pd.merge(
                self.results[pd.isnull(self.results['final_subject_identifier'])],
                self.df_htc[['subject_identifier_cdc', 'identity']],
                left_on='subject_identifier',
                right_on='subject_identifier_cdc',
                suffixes=['', '_cdc'])[['subject_identifier', 'subject_identifier_cdc']]
            self.df_htc.rename(columns={'subject_identifier_edc': 'final_subject_identifier'}, inplace=True)
            self.df_htc['final_subject_identifier_source'] = 'cdc (htc)'
            self.df_htc.drop_duplicates(inplace=True)
            self.df_htc.set_index('subject_identifier', inplace=True)
            self.results.set_index('subject_identifier', inplace=True)
            self.results = self.results.combine_first(self.df_htc)
            self.results.reset_index(inplace=True)
            self.df_htc.reset_index(inplace=True)

            self.df_ccc = df.copy()
            self.df_ccc = self.df_ccc.rename(columns={'ssid': 'subject_identifier_cdc', 'omangnumber': 'identity'})
            self.df_ccc = pd.merge(
                self.results[pd.isnull(self.results['final_subject_identifier'])],
                self.df_ccc[['subject_identifier_cdc', 'identity']],
                left_on='subject_identifier',
                right_on='subject_identifier_cdc',
                suffixes=['', '_cdc'])[['subject_identifier', 'subject_identifier_cdc']]
            self.df_ccc.rename(columns={'subject_identifier_edc': 'final_subject_identifier'}, inplace=True)
            self.df_ccc['final_subject_identifier_source'] = 'cdc (ccc)'
            self.df_ccc.drop_duplicates(inplace=True)
            self.df_ccc.set_index('subject_identifier', inplace=True)
            self.results.set_index('subject_identifier', inplace=True)
            self.results = self.results.combine_first(self.df_ccc)
            self.results.reset_index(inplace=True)
            self.df_ccc.reset_index(inplace=True)

    def update_requisition_columns(self):
        columns = ['edc_specimen_identifier', 'survey', 'visit_code',
                   'drawn_datetime', 'requisition_datetime', 'is_drawn',
                   'requisition_source', 'community']
        self.results = pd.merge(
            self.results,
            self.requisition.all[pd.notnull(self.requisition.all['edc_specimen_identifier'])][columns],
            on='edc_specimen_identifier',
            how='left', suffixes=['', '_edc'])
        self.results['requisition_datetime'] = pd.to_datetime(self.results['requisition_datetime'].dt.date)

#     def update_final_subject_identifier_from_getresults(self):
#         df_rs = RegisteredSubject().df

    def update_edc_specimen_identifier_from_requisition(self, edc_panels=None):
        edc_panels = edc_panels or {'610': 1, '401': 2, '974': 3, '201': 4, '101': 5}
        self.results['edc_panel_id'] = self.results.apply(
            lambda row: edc_panels.get(row['test_id'], 0) if pd.notnull(row['test_id']) else np.nan,
            axis=1)
        df_req = self.requisition.all[pd.notnull(self.requisition.all['edc_specimen_identifier'])].copy()
        df_req['requisition_datetime'] = pd.to_datetime(df_req['requisition_datetime'].dt.date)
        df_req = df_req[
            ~(df_req['edc_specimen_identifier'].isin(
                self.results['edc_specimen_identifier']))]
        panel_ids = [1, 3, 4, 5, 2]
        for panel_id in panel_ids:
            self.results = pd.merge(
                self.results,
                df_req[df_req['panel_id'] == panel_id][
                    ['edc_specimen_identifier', 'subject_identifier', 'requisition_datetime',
                     'panel_id']],
                how='left',
                left_on=['final_subject_identifier', 'drawn_datetime', 'edc_panel_id'],
                right_on=['subject_identifier', 'requisition_datetime', 'panel_id'],
                suffixes=['', '_merge'])
            self.results['edc_specimen_identifier'] = self.results.apply(
                lambda row: self.fill_edc_specimen_identifier(row), axis=1)
            self.results.drop(
                ['edc_specimen_identifier_merge', 'subject_identifier_merge',
                 'panel_id', 'requisition_datetime'],
                axis=1, inplace=True)

    def update_final_subject_identifier(self, suffix=None, drop_column=None):
        suffix = suffix or '_edc'
        drop_column = True if drop_column is None else drop_column
        self.results['final_subject_identifier'] = self.results.apply(
            lambda row: self.fill_final_subject_identifier(row, suffix=suffix), axis=1)
        if drop_column:
            del self.results['subject_identifier{}'.format(suffix)]

    def fill_final_subject_identifier(self, row, suffix=None):
        suffix = suffix or '_edc'
        final_subject_identifier = row['final_subject_identifier']
        if pd.isnull(row['final_subject_identifier']):
            if pd.notnull(row['subject_identifier{}'.format(suffix)]):
                final_subject_identifier = row['subject_identifier{}'.format(suffix)]
        return final_subject_identifier

    def fill_edc_specimen_identifier(self, row):
        if (pd.isnull(row['edc_specimen_identifier']) and
                pd.notnull(row['edc_specimen_identifier_merge'])):
            return row['edc_specimen_identifier_merge']
        return row['edc_specimen_identifier']

    def other_identifier(self, row):
        if pd.notnull(row['htc_identifier']) and row['htc_identifier'].strip() != '':
            other_identifier = row['htc_identifier'].replace('-', '')
        elif pd.notnull(row['lab_identifier']) and row['lab_identifier'].strip() != '':
            other_identifier = row['lab_identifier'].replace('-', '')
        else:
            other_identifier = np.nan
        return other_identifier

    def edc_specimen_identifier(self, row, prefix):
        edc_specimen_identifier = np.nan
        if pd.notnull(row['aliquot_identifier']):
            edc_specimen_identifier = row['aliquot_identifier'][0:12]
        elif pd.notnull(row['specimen_identifier']):
            if row['specimen_identifier'].startswith(prefix):
                edc_specimen_identifier = row['specimen_identifier']
        return edc_specimen_identifier

    def aliquot_identifier(self, row):
        aliquot_identifier = np.nan
        for column in ['lis_identifier', 'specimen_identifier']:
            if pd.notnull(row[column]):
                if re.match('^066\w+[0-9]{4}$', row[column]):
                    aliquot_identifier = row[column]
                    break
        return aliquot_identifier
