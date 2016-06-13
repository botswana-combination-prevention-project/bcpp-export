import hashlib
import numpy as np
import pandas as pd

from .decrypt import decrypt


def identity(row, column_name=None):
    return decrypt(row, column_name or 'identity', 'rsa', 'restricted')


def identity256(row, column_name=None):
    identity256 = np.nan
    column_name = column_name or 'identity'
    if pd.notnull(row[column_name]):
        identity = identity(row, column_name)
        identity256 = hashlib.sha256(identity).digest().encode("hex")
    return identity256
