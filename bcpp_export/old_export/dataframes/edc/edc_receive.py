import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from bcpp_export import urls  # DO NOT DELETE
from bhp066.apps.bcpp_lab.models import Receive as EdcReceive


class Receive(object):

    def __init__(self):
        qs = EdcReceive.objects.all()
        columns = qs[0].__dict__.keys()
        columns = self.safe_remove(columns, '_state')
        columns = self.safe_remove(columns, '_user_container_instance')
        columns = self.safe_remove(columns, 'using')
        columns = self.safe_remove(columns, 'id')
        columns = self.safe_remove(columns, 'subject_identifier')
        columns.append('registered_subject__subject_identifier')
        qs = EdcReceive.objects.values_list(*columns).all()
        df = pd.DataFrame(list(qs), columns=columns)
        df.rename(columns={
            'registered_subject__subject_identifier': 'subject_identifier',
        }, inplace=True)
        df.fillna(value=np.nan, inplace=True)
        for column in list(df.select_dtypes(include=['datetime64[ns, UTC]']).columns):
            df[column] = df[column].astype('datetime64[ns]')
        self.df = df

    def safe_remove(self, columns, name):
        try:
            columns.remove(name)
        except ValueError:
            pass
        return columns
