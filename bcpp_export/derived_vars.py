import pandas as pd
import numpy as np

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from .constants import (YES, NO, DEFAULTER, NAIVE, NEG, ON_ART, POS, UNK, SUBJECT_IDENTIFIER, edc_ART_PRESCRIPTION)


class DerivedVariables(object):

    def __init__(self, row, counter=None):
        self.subject_identifier = row[SUBJECT_IDENTIFIER]
        self.arv_evidence = row['arv_evidence']
        self.ever_taken_arv = row['ever_taken_arv']
        self.has_tested = row['has_tested']
        self.on_arv = row['on_arv']
        self.other_record = row['other_record']
        self.recorded_hiv_result = row['recorded_hiv_result']
        self.recorded_hiv_result_date = row['recorded_hiv_result_date']
        self.result_recorded = row['result_recorded']
        self.result_recorded_date = row['result_recorded_date']
        self.self_reported_result = row['self_reported_result']
        self.today_hiv_result = row['today_hiv_result']
        self.today_hiv_result_date = row['today_hiv_result_date']
        self.elisa_hiv_result = row['elisa_hiv_result']
        self.elisa_hiv_result_date = row['elisa_hiv_result_date']
        self.result_recorded_document = row['result_recorded_document']
        if self.result_recorded_document == edc_ART_PRESCRIPTION:
            self.arv_evidence = YES
        self.age_in_years = relativedelta(row['consent_datetime'].date(), row['dob']).years
        self.timestamp = timezone.now()
        self.final_hiv_status = np.nan
        self.final_hiv_date = np.nan
        self.final_arv_status = np.nan
        self.documented_pos = np.nan
        self.documented_pos_date = pd.NaT
        self.prev_result = np.nan
        self.prev_result_date = pd.NaT
        self.prev_result_known = np.nan
        self.prepare_documented_status_and_date()
        self.prepare_final_hiv_status_and_date()
        self.prepare_final_arv_status()
        self.prepare_previous_status_date_and_awareness()

    @property
    def final_hiv_status_date(self):
        if self.prev_result_known == YES and self.prev_result == POS:
            final_hiv_status_date = self.prev_result_date
        elif self.prev_result_known == YES and self.prev_result == NEG:
            if pd.notnull(self.today_hiv_result_date):
                final_hiv_status_date = self.today_hiv_result_date
            else:
                final_hiv_status_date = self.prev_result_date
        else:
            final_hiv_status_date = self.today_hiv_result_date
        return final_hiv_status_date

    def prepare_previous_status_date_and_awareness(self):
        """Prepare prev_result, prev_result_date, and prev_result_known."""
        if self.recorded_hiv_result == POS:
            self.prev_result = POS
            self.prev_result_date = self.recorded_hiv_result_date
            self.prev_result_known = YES
        elif self.recorded_hiv_result == NEG:
            self.prev_result = NEG
            self.prev_result_date = self.recorded_hiv_result_date
            self.prev_result_known = YES
        elif self.result_recorded == POS:
            self.prev_result = POS
            self.prev_result_date = self.result_recorded_date
            self.prev_result_known = YES
        elif self.result_recorded == NEG:
            self.prev_result = NEG
            self.prev_result_date = self.result_recorded_date
            self.prev_result_known = YES
        else:
            self.prev_result = np.nan
            self.prev_result_date = pd.NaT
            self.prev_result_known = np.nan
        self.previous_status_date_and_awareness_exceptions()

    def previous_status_date_and_awareness_exceptions(self):
        """Overwrite invalid result sequence and/or derive from arv status if possible."""
        if self.final_arv_status in (DEFAULTER, ON_ART) and (self.prev_result == NEG or pd.isnull(self.prev_result)):
            self.prev_result = POS
            self.prev_result_date = pd.NaT
            self.prev_result_known = YES
        if self.final_hiv_status == NEG and self.prev_result == POS:
            self.prev_result = np.nan
            self.prev_result_date = pd.NaT
            self.prev_result_known = np.nan

    def prepare_final_arv_status(self):
        self.final_arv_status = np.nan
        if self.final_hiv_status == POS:
            if ((pd.isnull(self.ever_taken_arv) or self.ever_taken_arv in (NO, 'DWTA')) and
                    (self.arv_evidence == NO or pd.isnull(self.arv_evidence))):
                self.final_arv_status = NAIVE
            elif (self.ever_taken_arv == YES or self.arv_evidence == YES) and self.on_arv == NO:
                self.final_arv_status = DEFAULTER
            elif (self.arv_evidence == YES or self.ever_taken_arv == YES) and self.on_arv == YES:
                self.final_arv_status = ON_ART
            elif self.arv_evidence == YES and pd.isnull(self.on_arv) and pd.isnull(self.ever_taken_arv):
                self.final_arv_status = ON_ART
            else:
                raise TypeError('Cannot determine final_arv_status for {}. '
                                'Got ever_taken_arv={}, on_arv={}, arv_evidence={}'.format(
                                    self.subject_identifier, self.ever_taken_arv, self.on_arv, self.arv_evidence))

    def prepare_documented_status_and_date(self):
        if self.recorded_hiv_result == POS:
            self.documented_pos = YES
            self.documented_pos_date = self.recorded_hiv_result_date
        elif self.other_record == YES and self.result_recorded == POS:
            self.documented_pos = YES
            self.documented_pos_date = self.result_recorded_date
        elif self.arv_evidence == YES:
            self.documented_pos = YES
            self.documented_pos_date = pd.NaT
        elif (self.recorded_hiv_result not in (POS, NEG) and
                not (self.other_record == YES and self.result_recorded == POS)):
            self.documented_pos = NO
            self.documented_pos_date = pd.NaT
        else:
            self.documented_pos = NO
            self.documented_pos_date = pd.NaT

    def prepare_final_hiv_status_and_date(self):
        if self.elisa_hiv_result in (POS, NEG):
            self.final_hiv_status = self.elisa_hiv_result
            self.final_hiv_date = self.elisa_hiv_result_date
        elif self.today_hiv_result in (POS, NEG):
            self.final_hiv_status = self.today_hiv_result
            self.final_hiv_date = self.today_hiv_result_date
        elif self.documented_pos == YES:
            self.final_hiv_status = POS
            self.final_hiv_date = self.documented_pos_date
        else:
            self.final_hiv_status = UNK
            self.final_hiv_date = pd.NaT