import pandas as pd
import numpy as np

from .constants import (YES, NO, DEFAULTER, NAIVE, NEG, ON_ART, POS, UNK)


class DerivedVariables(object):

    def __init__(self, row, counter=None):
        self.subject_identifier = row['subject_identifier']
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

    def prepare_previous_status_date_and_awareness(self):
        if self.recorded_hiv_result == POS:
            self.prev_result = POS
            self.prev_result_date = self.recorded_hiv_result_date
            self.prev_result_known = YES
        elif self.result_recorded == POS:
            self.prev_result = POS
            self.prev_result_date = self.result_recorded_date
            self.prev_result_known = YES
        elif self.final_arv_status in (DEFAULTER, ON_ART):
            self.prev_result = POS
            self.prev_result_date = pd.NaT
            self.prev_result_known = YES
        elif self.recorded_hiv_result == NEG:
            self.prev_result = NEG
            self.prev_result_date = self.result_recorded_date
            self.prev_result_known = YES
        elif self.result_recorded == NEG:
            self.prev_result = NEG
            self.prev_result_date = self.result_recorded_date
            self.prev_result_known = YES
        else:
            self.prev_result = np.nan
            self.prev_result_date = pd.NaT
            self.prev_result_known = NO
        if self.final_hiv_status == NEG and self.prev_result == POS:
            self.prev_result = NEG
            self.prev_result_date = pd.NaT
            self.prev_result_known = NO

    def prepare_final_arv_status(self):
        self.final_arv_status = np.nan
        if self.final_hiv_status == POS:
            if pd.isnull(self.ever_taken_arv):
                self.final_arv_status = NAIVE
            elif self.ever_taken_arv in (NO, 'DWTA'):
                self.final_arv_status = NAIVE
            elif self.ever_taken_arv == YES and self.on_arv == NO:
                self.final_arv_status = DEFAULTER
            elif self.arv_evidence == YES and self.on_arv == NO:
                self.final_arv_status = DEFAULTER
            elif self.arv_evidence == YES and self.on_arv == YES:
                self.final_arv_status = ON_ART
            elif self.ever_taken_arv == YES and self.on_arv == YES:
                self.final_arv_status = ON_ART
            elif self.arv_evidence == YES and pd.isnull(self.on_arv) and pd.isnull(self.ever_taken_arv):
                # unreachable !!
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

#     @property
#     def prev_result_known(self):
#         prev_result_known = np.nan
#         if self.recorded_hiv_result in (POS, NEG) or self.final_arv_status in (DEFAULTER, ON_ART):
#             prev_result_known = YES
#         elif self.result_recorded == POS and self.final_hiv_status == NEG:
#             prev_result_known = NO
#         elif self.result_recorded in (NEG, POS):
#             prev_result_known = YES
#         elif ((pd.isnull(self.recorded_hiv_result) or self.recorded_hiv_result == UNK) and
#               (pd.isnull(self.result_recorded) or self.result_recorded == UNK) and
#               (pd.isnull(self.final_arv_status) or self.final_arv_status == NAIVE)):
#             prev_result_known = NO
#         else:
#             raise TypeError('Cannot determine prev_result_known. '
#                             'Got recorded_hiv_result={}, final_arv_status={}, final_hiv_status={}, '
#                             'result_recorded={}'.format(
#                                 self.recorded_hiv_result, self.final_arv_status, self.final_hiv_status,
#                                 self.result_recorded))
#         return prev_result_known

#     @property
#     def prev_result(self):
#                 prev_result = np.nan
#                 if self.prev_result_known == YES:
#                     if (self.recorded_hiv_result == POS or self.result_recorded == POS or
#                             self.final_arv_status in (DEFAULTER, ON_ART)):
#                         prev_result = POS
#                     elif (self.recorded_hiv_result == NEG or self.result_recorded == NEG or
#                           self.final_arv_status == NAIVE):
#                         prev_result = NEG
#                     if self.final_hiv_status == NEG and prev_result != NEG:
#                         prev_result = NEG
#                     else:
#                         raise TypeError('Cannot determine prev_result for prev_result_known=YES.')
#                 return prev_result
#
#     @property
#     def prev_result_date(self):
#         """Return the date for the previous result, None or raise an exception.
#
#         Return None if prev_result was determined by a final negative status or
#         a final arv status of "ON ART"."""
#         prev_result_date = pd.NaT
#         if self.prev_result_known == YES:
#             if pd.notnull(self.recorded_hiv_result_date):
#                 prev_result_date = self.recorded_hiv_result_date
#             else:
#                 prev_result_date = self.result_recorded_date
#             if pd.isnull(prev_result_date):
#                 if (self.final_hiv_status != NEG and pd.isnull(self.final_arv_status)):
#                     raise TypeError('Cannot determine prev_result_date for {}. Got prev_result_known=YES, '
#                                     'recorded_hiv_result_date={}, result_recorded_date={}, '
#                                     'prev_result={}, final_arv_status={}'.format(
#                                         self.subject_identifier, self.recorded_hiv_result_date,
#                                         self.result_recorded_date, self.prev_result, self.final_arv_status))
#         return prev_result_date

#     @property
#     def final_hiv_status(self):
#         final_hiv_status = np.nan
#         if self.elisa_hiv_result in (POS, NEG):
#             final_hiv_status = self.elisa_hiv_result
#         elif self.today_hiv_result in (POS, NEG):
#             final_hiv_status = self.today_hiv_result
#         elif self.documented_pos == YES:
#             final_hiv_status = POS
#         else:
#             final_hiv_status = UNK
#         return final_hiv_status
