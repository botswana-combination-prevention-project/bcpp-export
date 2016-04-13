import re
import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from tabulate import tabulate
from bcpp_export import urls  # DO NOT DELETE
from bcpp_export.private_settings import Lis as LisCredentials
from bcpp_export.dataframes.edc import ClinicConsent
from bcpp_export.dataframes.edc.edc_requisition import Requisition
from bcpp_export.dataframes.edc.edc_registered_subject import RegisteredSubject


class Lis(object):

    def __init__(self, df=pd.DataFrame(), engine=None, protocol=None, protocol_prefix=None):
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
            self.update_requisition_columns()

    def print_df(self, df, headers):
        print(tabulate(df, headers=headers, tablefmt='psql'))

    def unmatched_k(self, format=None):
        """show unmatched K numbers"""
        columns = ['lis_identifier', 'received_datetime', 'subject_identifier', 'drawn_datetime']
        df = self.results[
            (pd.isnull(self.results['final_subject_identifier'])) &
            (self.results['subject_identifier'].str.startswith('K'))]
        if format == 'dataframe':
            return df
        else:
            self.print_df(df[columns].sort_values('subject_identifier'),
                          ['received_as', 'received_on', 'subject_identifier', 'drawn'])

    def missing_subject_identifier(self, format=None):
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

    def fetch_results_as_dataframe(self):
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
        df['result_datetime'] = pd.to_datetime(df['result_datetime'])
        df['received_datetime'] = pd.to_datetime(df['received_datetime'])
        df['drawn_datetime'] = pd.to_datetime(df['drawn_datetime'])
        # df['other_identifier'] = df.apply(lambda row: self.other_identifier(row), axis=1)
        df['specimen_identifier'] = df.apply(lambda row: np.nan if row['specimen_identifier'] == 'NA' else row['specimen_identifier'], axis=1)
        df['aliquot_identifier'] = df.apply(lambda row: self.aliquot_identifier(row), axis=1)
        df['edc_specimen_identifier'] = df.apply(lambda row: self.edc_specimen_identifier(row, self.protocol_prefix), axis=1)
        df['subject_identifier'] = df.apply(lambda row: self.undash(row['subject_identifier'], '^{}-'.format(self.protocol_prefix)), axis=1)
        df['final_subject_identifier'] = df[df['subject_identifier'].str.startswith('{}-'.format(self.protocol_prefix))]['subject_identifier']
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
    def sql_storage(self):
        return """SELECT L.pat_id as subject_identifier, l.sample_date_drawn as drawn_datetime,
        sample_id as aliquot_identifier, sample_type, pid_name AS label, box_col, st505.pid AS box,
        ST405.PID as RACK, ST305.PID as FREEZER,
        FREEZER_NAME
        FROM bhplab.dbo.st505responseQ001x0 AS st505d
        LEFT join bhplab.dbo.st505response AS st505 ON st505D.qid1x0=st505.q001x0
        LEFT join bhplab.dbo.st515response AS st515 ON st505d.sample_type=st515.pid
        LEFT join bhplab.dbo.lab01response AS l ON st505d.sample_id=l.pid
        left join BHPLAB.DBO.ST405ResponseQ001X0 as ST405D on ST505.PID=ST405D.BOX_ID
        left join BHPLAB.DBO.ST405Response as ST405 on ST405.Q001X0=ST405D.QID1X0
        left join BHPLAB.DBO.ST305ResponseQ001X0 as ST305D on ST405.PID=ST305D.RACK_ID
        left join BHPLAB.DBO.ST305Response as ST305 on ST305.Q001X0=ST305D.QID1X0
        WHERE l.sample_protocolnumber='{}'""".format(self.protocol)

    @property
    def sql_getresults(self):
        return """SELECT * FROM "getresults_dst_history"""

    def update_final_subject_identifier_from_lab_identifier(self):
        # match to lab_identifier
        df = pd.merge(self.results[pd.isnull(self.results['final_subject_identifier'])],
                      self.df_clinic_consent[['subject_identifier', 'lab_identifier']],
                      left_on='subject_identifier',
                      right_on='lab_identifier',
                      suffixes=['', '_edc'])[['subject_identifier', 'subject_identifier_edc']]
        df.drop_duplicates(inplace=True)
        self.results = pd.merge(self.results, df, on='subject_identifier', how='left')
        self.update_final_subject_identifier()

    def update_final_subject_identifier_from_htc_identifier(self):
        # match to htc_identifier
        df = pd.merge(self.results[pd.isnull(self.results['final_subject_identifier'])],
                      self.df_clinic_consent[['subject_identifier', 'htc_identifier']],
                      left_on='subject_identifier',
                      right_on='htc_identifier',
                      suffixes=['', '_edc'])[['subject_identifier', 'subject_identifier_edc']]
        df.drop_duplicates(inplace=True)
        self.results = pd.merge(self.results, df, on='subject_identifier', how='left')
        self.update_final_subject_identifier()

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
            self.results = pd.merge(
                self.results, df, on='lis_identifier', how='left', suffixes=['', '_edc'])
            self.update_final_subject_identifier()

    def update_final_subject_identifier_from_identity(self):
        df_rs = RegisteredSubject().df
        df = pd.merge(self.results[pd.isnull(self.results['final_subject_identifier'])],
                      df_rs[['subject_identifier', 'identity']],
                      left_on='subject_identifier',
                      right_on='identity',
                      suffixes=['', '_edc'])[['subject_identifier', 'subject_identifier_edc']]
        df.drop_duplicates(inplace=True)
        self.results = pd.merge(self.results, df, on='subject_identifier', how='left')
        self.update_final_subject_identifier()

    def update_requisition_columns(self):
        columns = ['edc_specimen_identifier', 'survey', 'visit_code', 'community',
                   'drawn_datetime', 'requisition_datetime', 'is_drawn']
        df = pd.concat([self.requisition.subject[columns], self.requisition.clinic[columns]])
        self.results = pd.merge(self.results, df, on='edc_specimen_identifier',
                                how='left', suffixes=['', '_edc'])

#     def update_final_subject_identifier_from_getresults(self):
#         df_rs = RegisteredSubject().df

    def update_final_subject_identifier(self):
        self.results['final_subject_identifier'] = self.results.apply(
            lambda row: self.fill_final_subject_identifier(row), axis=1)
        del self.results['subject_identifier_edc']

    def fill_final_subject_identifier(self, row):
        final_subject_identifier = row['final_subject_identifier']
        if pd.isnull(row['final_subject_identifier']):
            if pd.notnull(row['subject_identifier_edc']):
                final_subject_identifier = row['subject_identifier_edc']
        return final_subject_identifier

    def undash(self, value, exclude_pattern):
        if not re.match(exclude_pattern, value):
            value = value.replace('-', '')
        return value

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
