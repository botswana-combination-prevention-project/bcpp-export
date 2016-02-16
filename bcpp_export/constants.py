import numpy as np
from edc_constants.constants import (ALIVE as edc_ALIVE, DEAD as edc_DEAD, YES as edc_YES, NO as edc_NO,
                                     POS as edc_POS, NEG as edc_NEG, IND as edc_IND, UNK as edc_UNK,
                                     NOT_APPLICABLE as edc_NOT_APPLICABLE,
                                     MALE as edc_MALE, FEMALE as edc_FEMALE)

edc_DWTA = 'DWTA'
ALIVE = 1
ART_PRESCRIPTION = 'ART Prescription'
DEAD = 0
DEFAULTER = 2
DWTA = 4
FEMALE = 2
IND = 2
MALE = 1
NAIVE = 1
NEG = 0
NO = 2
NOT_APPLICABLE = 3
ON_ART = 3
POS = 1
UNK = 3
YES = 1

gender = {edc_MALE: MALE, edc_FEMALE: FEMALE}

hiv_options = {edc_POS: POS, edc_NEG: NEG, edc_IND: IND, edc_UNK: UNK, 'not_answering': DWTA, None: np.nan}

tf = {True: YES, False: NO, None: np.nan}

yes_no = {
    edc_YES: YES, edc_NO: NO, '1': YES, '2': NO, edc_NOT_APPLICABLE: NOT_APPLICABLE,
    None: np.nan, edc_DWTA: DWTA, 'Not Sure': 5}

survival = {edc_ALIVE: ALIVE, edc_DEAD: DEAD, None: np.nan}
