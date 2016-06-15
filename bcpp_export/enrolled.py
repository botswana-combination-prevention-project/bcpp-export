import numpy as np

from .constants import YES, NO


def enrolled(subjects, row, column):
    """Return NO if row value is not in subjects dataframe column, else YES.

    column might be 'household_identifier', 'plot_identifier', 'registered_subject', etc."""
    if subjects.empty:
        return np.nan
    if subjects[subjects[column].isin([row[column]])].empty:
        return NO
    return YES
