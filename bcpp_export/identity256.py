import hashlib
import numpy as np
import pandas as pd

from django.core.exceptions import ImproperlyConfigured
from edc.core.crypto_fields.classes import FieldCryptor


def identity256(row):
    identity256 = np.nan
    if pd.notnull(row['identity']):
        field_cryptor = FieldCryptor('rsa', 'restricted')
        identity = field_cryptor.decrypt(row['identity'])
        if identity.startswith('enc1::'):
            raise ImproperlyConfigured(
                'Cannot decrypt identity, specify path to the encryption keys in settings.KEYPATH')
        identity256 = hashlib.sha256(identity).digest().encode("hex")
    return identity256
