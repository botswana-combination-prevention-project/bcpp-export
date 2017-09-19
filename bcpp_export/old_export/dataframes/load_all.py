import sys
from datetime import datetime
from bcpp_export.dataframes.members import Members
from bcpp_export.dataframes.subjects import Subjects
from bcpp_export.dataframes.residences import Residences
from django.core.management.color import color_style

style = color_style()


def load_all(survey=None):
    """Load all dataframes except CombinedDataFrames and return a dictionary of objects.

    For exapmple:

        objects = load_all('bcpp-year-1')
        members = objects.get('members_object')
        subjects = objects.get('subjects_object')
        residences = objects.get('residences_object')

    The returned objects can be passed directly to CombinedDataFrames

        dfs = CombinedDataFrames('bcpp-year-1', **objects)
        dfs.to_csv()
    """

    def start_message(name):
        sys.stdout.write(style.NOTICE('Loading {} dataframe ...\n'.format(name)))
        return datetime.today()

    def end_message(dte_start):
        td = (datetime.today() - dte_start)
        sys.stdout.write(style.SQL_FIELD('Done. {} minutes {} seconds\n'.format(
            *divmod(td.days * 86400 + td.seconds, 60))))

    survey = survey or 'bcpp-year-1'
    dte = datetime.today()
    dte_start = start_message('subjects')
    subjects = Subjects('bcpp-year-1')
    subjects.results
    end_message(dte_start)

    dte_start = start_message('members')
    members = Members('bcpp-year-1', subjects=subjects.results)
    members.results
    end_message(dte_start)

    dte_start = start_message('residences')
    residences = Residences('bcpp-year-1', subjects=subjects.results, members=members.results)
    residences.residences
    end_message(dte_start)

    td = (datetime.today() - dte)
    sys.stdout.write(style.SQL_FIELD('All done. {} minutes {} seconds\n\n\n'.format(*divmod(td.days * 86400 + td.seconds, 60))))

    return {'members_object': members, 'subjects_object': subjects, 'residences_object': residences}
