import pyodbc
import re

from django.conf import settings

from bhp066.apps.bcpp_clinic.models import ClinicConsent


class Reconcile(object):
    """Reconcile specimens between Lab and EDC clinic

    from bhp066.apps.bcpp_export.utils.reconcile import Reconcile
    r = Reconcile()
    r.missing_in_lab  # found in LIS but not in EDC
    """

    def __init__(self, sql=None):
        self.sql = sql or """
            select edc_specimen_identifier, pid, pat_id, headerdate, tid
            from lab01response where sample_protocolnumber='BHP066'
            and substring(pat_id, 1, 3) <> '066'
            """
        self._missing_in_edc = None
        self._identifiers_in_edc = None
        self._identifiers_in_lis = None
        self.data = None
        self.test_code = '610'
        self.fetch()

    def fetch(self):
        with pyodbc.connect(settings.LAB_IMPORT_DMIS_DATA_SOURCE) as cnxn:
            with cnxn.cursor() as cursor:
                self.data = cursor.execute(self.sql).fetchall()

    @property
    def htc_identifiers(self):
        """List of HTC identifiers in the LIS."""
        identifiers = []
        pattern = re.compile('^[0-9]{7}\-[0-9]{2}$')
        for item in self.data:
            if re.match(pattern, item[2]) and item[4] == self.test_code:
                identifiers.append('{}-{}-{}{}'.format(item[2][0:2], item[2][2:4], item[2][4:7], item[2][7:10]))
        identifiers.sort()
        return identifiers

    @property
    def pims_identifiers(self):
        """List of PIMS identifiers in the LIS."""
        identifiers = []
        pattern = re.compile('^[0-9]{3}\-[0-9]{4}$')
        for item in self.data:
            if re.match(pattern, item[2]) and item[4] == self.test_code:
                identifiers.append(item[2])
        identifiers.sort()
        return identifiers

    @property
    def lab_identifiers(self):
        """List of LAB allocated identifiers in the LIS (K numbers)."""
        identifiers = []
        pattern = re.compile('^K[0-9]{5}\-[0-9]{1}$')
        for item in self.data:
            if re.match(pattern, item[2]):
                identifiers.append(item[2])
        identifiers.sort()
        return identifiers

    @property
    def clinic_consents(self):
        if not self._clinic_consents:
            self._clinic_consents = ClinicConsent.objects.all()
        return self._clinic_consents

    @property
    def missing_in_edc(self):
        """Returns a list of identifiers not found in the EDC but seen in the LIS."""
        if not self._missing_in_edc:
            self._missing_in_edc = [item for item in self.htc_identifiers if item not in self.identifiers_in_edc]
            self._missing_in_edc.extend([item for item in self.pims_identifiers if item not in self.identifiers_in_edc])
            self._missing_in_edc.extend([item for item in self.lab_identifiers if item not in self.identifiers_in_edc])
        return self._missing_in_edc

#     @property
#     def missing_in_lis(self):
#         """Returns a list of identifiers not found in the EDC but seen in the LIS."""
#         if not self._missing_in_lis:
#             self._missing_in_lis = [item for item in self.htc_identifiers if item not in self.identifiers_in_lis]
#             self._missing_in_lis.extend([item for item in self.pims_identifiers if item not in self.identifiers_in_lis])
#             self._missing_in_lis.extend([item for item in self.lab_identifiers if item not in self.identifiers_in_lis])
#         return self._missing_in_lis

    @property
    def identifiers_in_edc(self):
        """Returns a list of identifiers from each of the three types captured in the EDC."""
        if not self._identifiers_in_edc:
            identifiers = (
                [(c.htc_identifier, c.lab_identifier, c.pims_identifier) for c in self.clinic_consents])
            self._identifiers_in_edc = (
                [i[0] for i in identifiers if i] +
                [i[1] for i in identifiers if i] +
                [i[2] for i in identifiers if i])
        return self._identifiers_in_edc

    @property
    def report(self):
        report = [(c.subject_identifier, c.lab_identifier)
                  for c in ClinicConsent.objects.filter(lab_identifier__in=self.missing_in_edc)]
        report.extend(
            [(c.subject_identifier, c.htc_identifier)
             for c in ClinicConsent.objects.filter(htc_identifier__in=self.missing_in_edc)])
        report.extend(
            [(c.subject_identifier, c.pims_identifier)
             for c in ClinicConsent.objects.filter(pims_identifier__in=self.missing_in_edc)])
        return report
