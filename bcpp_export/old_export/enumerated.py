import numpy as np


from .constants import YES, NO


def enumerated(members, row):
    if members.empty:
        return np.nan
    if members[members['household_identifier'].isin([row['household_identifier']])].empty:
        return NO
    return YES
