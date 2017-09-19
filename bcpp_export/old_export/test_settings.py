import os

from .settings import *

INSTALLED_APPS = list(INSTALLED_APPS) + [
    'edc.core.identifier',
    'edc.core.crypto_fields',
    'edc.core.bhp_variables',
    'edc.subject.registration',
    'edc.subject.appointment',
    'edc.subject.appointment_helper',
    'edc.apps.app_configuration',
    'edc.subject.adverse_event',
    'edc.lab.lab_clinic_api',
    'edc.lab.lab_packing',
    'edc.subject.visit_schedule',
    'edc.core.bhp_content_type_map',
    'edc_consent',
    'bhp066.apps.bcpp_clinic',
    'bhp066.apps.bcpp',
    'bhp066.apps.bcpp_list',
    'bhp066.apps.bcpp_household',
    'bhp066.apps.bcpp_household_member',
    'bhp066.apps.bcpp_survey',
    'bhp066.apps.bcpp_lab',
    'bhp066.apps.bcpp_subject',
]

KEY_PATH = os.path.join(BASE_DIR.ancestor(1), 'crypto_fields')
ALLOW_MODEL_SERIALIZATION = False
MAX_HOUSEHOLDS_PER_PLOT = 9
PROJECT_IDENTIFIER_PREFIX = '066'
DISPATCH_APP_LABELS = []
MAX_SUBJECTS = {'subject': 10000}
