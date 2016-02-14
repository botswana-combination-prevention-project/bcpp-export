import os

import pandas as pd
from collections import OrderedDict


class VariableCounts(object):
    """
        from bhp066.apps.bcpp_export.analysis import VariableCounts
        vc = VariableCounts()
        vc.update_results('y1')
        for k,v in vc.results.iteritems():
            print k,v
    """
    def __init__(self):
        self.communities = [
            'digawana', 'ranaka', 'molapowabojang', 'otse', 'lentsweletau', 'letlhakeng',
            'bokaa', 'oodi', 'mmankgodi', 'mmathethe', 'lerala', 'sefophe']
        self.load_data()
        self.results = OrderedDict()

    def load_data(self):
        self.df_plots = pd.read_csv(
            os.path.expanduser(
                '/Users/erikvw/Documents/bcpp/research_database/csv/20150328/Plot_20150328163229.csv'
            ), delimiter='|')
        self.df_households = pd.read_csv(
            os.path.expanduser(
                '/Users/erikvw/Documents/bcpp/research_database/csv/20150328/Household_20150328155653.csv'
            ), delimiter='|')
        self.df_members = pd.read_csv(
            os.path.expanduser(
                '/Users/erikvw/Documents/bcpp/research_database/csv/20150328/Member_20150328155720.csv'
            ), delimiter='|', low_memory=False)
        self.df_htcs = pd.read_csv(
            os.path.expanduser(
                '/Users/erikvw/Documents/bcpp/research_database/csv/20150328/Htc_20150328163321.csv'
            ), delimiter='|')
        self.df_subjects = pd.read_csv(
            os.path.expanduser(
                '/Users/erikvw/Documents/bcpp/research_database/csv/20150328/Subject_20150328155721.csv'
            ), delimiter='|')

    def update_results(self, survey_abbrev):
        self.survey_abbrev = survey_abbrev
        self.results.update({'header': self.communities})
        self.results.update({'plots': self.plots()})
        self.results.update({'plots confirmed': self.plots_confirmed()})
        self.results.update({'plots enrolled': self.plots_enrolled()})
        self.results.update({'households': self.households()})
        self.results.update({'households enumerated': self.households_enumerated()})
        self.results.update({'households replaced': []})
        self.results.update({'households enrolled': self.households_enrolled()})

        self.results.update({'subject enrolled': self.subjects_enrolled()})
        self.results.update({'subject on ART': self.subjects_on_art()})
        self.results.update({'subject ever taken ART': self.subjects_ever_taken_arv()})
        self.results.update({'subject recorded HIV(+)': self.subjects_recorded_hiv_result()})
        self.results.update({'subject verbal HIV(+)': self.subjects_verbal_hiv_result()})
        self.results.update({'subject todays HIV(+)': self.subjects_todays_hiv_result()})
        self.results.update({'subjects HIV (+)': self.subjects_hiv_pos_result()})

    def plots(self):
        items = self.df_plots.groupby(['community']).size().to_dict()
        return [items[c] for c in self.communities]

    def plots_confirmed(self):
        items = self.df_plots[
            (self.df_plots['confirmed'] == 'confirmed')].groupby(['community']).size().to_dict()
        return [items[c] for c in self.communities]

    def plots_enrolled(self):
        items = self.df_plots[
            (self.df_plots['confirmed'] == 'confirmed') &
            (self.df_plots['enrolled'] == 'Yes')].groupby(['community']).size().to_dict()
        return [items[c] for c in self.communities]

    def households(self):
        items = self.df_households.groupby(['community']).size().to_dict()
        return [items[c] for c in self.communities]

    def households_enumerated(self):
        items = self.df_households[
            (self.df_households['enumerated_{}'.format(self.survey_abbrev)] == 'Yes')
        ].groupby(['community']).size().to_dict()
        return [items[c] for c in self.communities]

    def households_enrolled(self):
        items = self.df_households[
            (self.df_households['enrolled_{}'.format(self.survey_abbrev)] == 'Yes')
        ].groupby(['community']).size().to_dict()
        return [items[c] for c in self.communities]

    def subjects_enrolled(self):
        # subjects enrolled
        items = self.df_subjects[
            (self.df_subjects['consent_datetime'].notnull()) &
            (self.df_subjects['location'] == 'household') &
            (self.df_subjects['survey_consented'] == self.survey_abbrev.upper())
        ].groupby(['community']).size().to_dict()
        return [items[c] for c in self.communities]

    def subjects_on_art(self):
        items = self.df_subjects[
            (self.df_subjects['consent_datetime'].notnull()) &
            (self.df_subjects['location'] == 'household') &
            (self.df_subjects['survey_consented'] == self.survey_abbrev.upper()) &
            (self.df_subjects['on_art_{}'.format(self.survey_abbrev)] == 'Yes')
        ].groupby(['community']).size()
        return [items[c] for c in self.communities]

    def subjects_ever_taken_arv(self):
        items = self.df_subjects[
            (self.df_subjects['consent_datetime'].notnull()) &
            (self.df_subjects['location'] == 'household') &
            (self.df_subjects['survey_consented'] == self.survey_abbrev.upper()) &
            (self.df_subjects['ever_taken_arv_{}'.format(self.survey_abbrev)] == 'Yes')
        ].groupby(['community']).size()
        return [items[c] for c in self.communities]

    def subjects_recorded_hiv_result(self):
        items = self.df_subjects[
            (self.df_subjects['consent_datetime'].notnull()) &
            (self.df_subjects['location'] == 'household') &
            (self.df_subjects['survey_consented'] == self.survey_abbrev.upper()) &
            (self.df_subjects['recorded_hiv_result_{}'.format(self.survey_abbrev)] == 'POS')
        ].groupby(['community']).size()
        return [items[c] for c in self.communities]

    def subjects_verbal_hiv_result(self):
        items = self.df_subjects[
            (self.df_subjects['consent_datetime'].notnull()) &
            (self.df_subjects['location'] == 'household') &
            (self.df_subjects['survey_consented'] == self.survey_abbrev.upper()) &
            (self.df_subjects['verbal_hiv_result_{}'.format(self.survey_abbrev)] == 'POS')
        ].groupby(['community']).size()
        return [items.get(c, 'None') for c in self.communities]

    def subjects_todays_hiv_result(self):
        items = self.df_subjects[
            (self.df_subjects['consent_datetime'].notnull()) &
            (self.df_subjects['location'] == 'household') &
            (self.df_subjects['survey_consented'] == self.survey_abbrev.upper()) &
            (self.df_subjects['todays_hiv_result_{}'.format(self.survey_abbrev)] == 'POS')
        ].groupby(['community']).size()
        return [items.get(c, 'None') for c in self.communities]

    def subjects_hiv_pos_result(self):
        items = self.df_subjects[
            (self.df_subjects['consent_datetime'].notnull()) &
            (self.df_subjects['location'] == 'household') &
            (self.df_subjects['survey_consented'] == self.survey_abbrev.upper()) &
            (self.df_subjects['hiv_result_{}'.format(self.survey_abbrev)] == 'POS')
        ].groupby(['community']).size()
        return [items.get(c, 'None') for c in self.communities]
