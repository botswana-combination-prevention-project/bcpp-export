import re
import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from tabulate import tabulate
from bcpp_export import urls  # DO NOT DELETE
from bcpp_export.private_settings import Lis as LisCredentials


class Storage(object):

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
            self.received = self.fetch_as_dataframe(self.sql_storage_received)
            self.received['edc_specimen_identifier'] = self.received['aliquot_identifier'].str[0:12]
            self.not_received = self.fetch_as_dataframe(self.sql_storage_not_received)
            self.not_received['edc_specimen_identifier'] = self.not_received['aliquot_identifier'].str[0:12]

    def fetch_as_dataframe(self, sql, edc_panels=None):
        with self.engine.connect() as conn, conn.begin():
            df = pd.read_sql_query(sql, conn)
        df.fillna(value=np.nan, inplace=True)
        for column in list(df.select_dtypes(include=['datetime64[ns, UTC]']).columns):
            df[column] = df[column].astype('datetime64[ns]')
        return df

    @property
    def sql_storage_received(self):
        return """SELECT L.pat_id as subject_identifier, l.sample_date_drawn as drawn_datetime,
        sample_id as aliquot_identifier, sample_type, pid_name AS label, box_col, st505.pid AS box,
        ST405.PID as RACK, ST305.PID as FREEZER,
        FREEZER_NAME, st505d.datecreated as created
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
    def sql_storage_not_received(self):
        return """SELECT L.pat_id as subject_identifier, l.sample_date_drawn as drawn_datetime,
        sample_id as aliquot_identifier, sample_type, pid_name AS label, box_col, st505.pid AS box,
        ST405.PID as RACK, ST305.PID as FREEZER,
        FREEZER_NAME, st505d.datecreated as created
        FROM bhplab.dbo.st505responseQ001x0 AS st505d
        LEFT join bhplab.dbo.st505response AS st505 ON st505D.qid1x0=st505.q001x0
        LEFT join bhplab.dbo.st515response AS st515 ON st505d.sample_type=st515.pid
        LEFT join bhplab.dbo.lab01response AS l ON st505d.sample_id=l.pid
        left join BHPLAB.DBO.ST405ResponseQ001X0 as ST405D on ST505.PID=ST405D.BOX_ID
        left join BHPLAB.DBO.ST405Response as ST405 on ST405.Q001X0=ST405D.QID1X0
        left join BHPLAB.DBO.ST305ResponseQ001X0 as ST305D on ST405.PID=ST305D.RACK_ID
        left join BHPLAB.DBO.ST305Response as ST305 on ST305.Q001X0=ST305D.QID1X0
        WHERE substring(sample_id, 1, 3)='{}'""".format(self.protocol_prefix)
