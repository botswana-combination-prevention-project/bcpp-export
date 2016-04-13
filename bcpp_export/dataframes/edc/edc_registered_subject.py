import pymssql
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from bcpp_export import urls  # DO NOT DELETE
from bcpp_export.identity256 import identity
from edc.subject.registration.models import RegisteredSubject as EdcRegisteredSubject


class RegisteredSubject(object):
    def __init__(self):
        qs = EdcRegisteredSubject.objects.all()
        columns = qs[0].__dict__.keys()
        columns.remove('_state')
        columns.remove('_user_container_instance')
        columns.remove('using')
        qs = EdcRegisteredSubject.objects.values_list(*columns).all()
        df = pd.DataFrame(list(qs), columns=columns)
        df.fillna(value=np.nan, inplace=True)
        df.replace('', np.nan, inplace=True)
        df['identity'] = df.apply(lambda row: identity(row, 'identity'), axis=1)
        self.df = df[pd.notnull(df['identity'])]
