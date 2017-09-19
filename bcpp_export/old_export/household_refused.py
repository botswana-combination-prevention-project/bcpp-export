import numpy as np

from .constants import YES, NO


def household_refused(household_refusal, row, column=None):
    column = 'household_identifier' if column is None else column
    if household_refusal.empty:
        return NO
    if household_refusal[household_refusal[column].isin([row[column]])].empty:
        return NO
    return YES
