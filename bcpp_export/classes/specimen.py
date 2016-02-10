import pyodbc

from collections import namedtuple
from dateutil.parser import parse

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned

from edc_constants.constants import YES

from bhp066.apps.bcpp_lab.models import Receive, Aliquot as AliquotModel

from .base import Base

ReceivedTuple = namedtuple(
    'ReceivedTuple',
    'edc_specimen_identifier, drawn_datetime, lis_specimen_identifier, lis_subject_identifier, lis_received_datetime')
ResultTuple = namedtuple(
    'ResultTuple',
    'edc_specimen_identifier, drawn_datetime, lis_specimen_identifier, lis_patient_ref, lis_received_datetime, '
    'lis_report_date, panel, lis_assay_date, lis_utestid, lis_result, lis_result_quantifier lis_result_id')


class Specimen(Base):
    def __init__(self, subject_requisition, subject_identifier=None, survey_abbrev=None, **kwargs):
        super(Specimen, self).__init__(**kwargs)
        self.sql = {}
        self.lis_receive = {}
        self.subject_requisition = subject_requisition
        self.specimen_identifier = self.subject_requisition.specimen_identifier
        self.subject_identifier = subject_identifier or self.household_member.registered_subject.subject_identifier
        self.survey_abbrev = survey_abbrev or self.household_member.household_structure.survey.survey_abbrev.lower()
        self.requisition_identifier = self.subject_requisition.requisition_identifier
        self.requisition_datetime = self.subject_requisition.requisition_datetime
        self.requisition_panel = self.subject_requisition.panel.name
        self.drawn = True if self.subject_requisition.is_drawn == YES else False
        self.reason_not_drawn = self.subject_requisition.reason_not_drawn
        self.drawn_datetime = self.subject_requisition.drawn_datetime
        try:
            self.receive = Receive.objects.only(
                'receive_datetime', 'receive_identifier').get(
                receive_identifier=self.specimen_identifier)
        except Receive.DoesNotExist:
            self.output_to_console(
                'Warning! Specimen \'{}\' has not been received on the EDC. See {}\n'.format(
                    self.specimen_identifier, self.subject_identifier))
            self.receive = Receive()
        except MultipleObjectsReturned:
            self.output_to_console('Warning! Specimen \'{}\' received on EDC more than once. See {}\n'.format(
                self.specimen_identifier, self.subject_identifier))
            self.receive = Receive()
        self.receive_datetime = self.receive.receive_datetime  # where does this date come from??
        self.receive_identifier = self.receive.receive_identifier
        self.aliquots = {a.aliquot_identifier: a for a in AliquotModel.objects.only(
            'aliquot_identifier').filter(receive__id=self.receive.id)}
        self.dmis_column = 'edc_specimen_identifier'
        self.lis_results = {}
        self.fetch_receiving()
        self.fetch_result()

    def __repr__(self):
        return '{0}({1.specimen_identifier!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.specimen_identifier!s}'.format(self)

    @property
    def household_member(self):
        return self.subject_requisition.subject_visit.household_member

    def fetch_receiving(self):
        """Fetches the receiving data from the LIS for each identifier."""
        def fetchall(cursor):
            self.sql.update(
                received_items=(
                    'select edc_specimen_identifier, pid, pat_id, headerdate from lab01response as l where '
                    'edc_specimen_identifier LIKE \'{specimen_identifier}%\'').format(
                        specimen_identifier=self.specimen_identifier)
            )
            return cursor.execute(self.sql.get('received_items')).fetchall()
        if self.verbose:
            print "Querying dmis for {} {}".format(self.specimen_identifier, self.aliquot_type)
        try:
            with pyodbc.connect(settings.LAB_IMPORT_DMIS_DATA_SOURCE, timeout=3) as cnxn:
                with cnxn.cursor() as cursor:
                    for edc_specimen_identifier, lis_specimen_identifier, lis_subject_identifier, lis_received_datetime in fetchall(cursor):
                        if lis_subject_identifier != self.subject_identifier:
                            print ("Warning! LIS pat_ref differs with EDC subject_identifier for {}. Got {}"
                                   ).format(self.subject_identifier, lis_subject_identifier)
                        if edc_specimen_identifier in self.aliquots and lis_subject_identifier == self.subject_identifier:
                            self.lis_receive.update({
                                edc_specimen_identifier: ReceivedTuple(
                                    edc_specimen_identifier,
                                    self.drawn_datetime,
                                    lis_specimen_identifier,
                                    lis_subject_identifier,
                                    lis_received_datetime)
                            })
            self.lis_results = {edc_specimen_identifier: [] for edc_specimen_identifier in self.lis_receive}
        except pyodbc.Error as e:
            print(e)
            pass

    def fetch_result(self):
        """Fetches the receiving data from the LIS for each identifier."""
        receive = {rcv.lis_specimen_identifier: rcv for rcv in self.lis_receive.itervalues()}

        def fetchall(cursor):
            self.sql.update(
                resulted_items=(
                    'select PID as sample_id, reportdate, sample_assay_date, utestid, result, result_quantifier, L21.id as lis_result_id '
                    'from BHPLAB.DBO.LAB21Response as L21 '
                    'left join BHPLAB.DBO.LAB21ResponseQ001X0 as L21D on L21.Q001X0=L21D.QID1X0 '
                    'where PID IN (\'{lis_specimen_identifiers}\')').format(
                        dmis_column=self.dmis_column,
                        lis_specimen_identifiers='\',\''.join(receive)))
            return cursor.execute(self.sql.get('resulted_items')).fetchall()

        if self.verbose:
            print "Querying dmis for {} resulted items".format(self.lis_specimen_identifier)
        try:
            with pyodbc.connect(settings.LAB_IMPORT_DMIS_DATA_SOURCE, timeout=3) as cnxn:
                with cnxn.cursor() as cursor:
                    for lis_specimen_identifier, report_date, assay_date, utestid, result, result_quantifier, lis_result_id in fetchall(cursor):
                        try:
                            report_date = parse(report_date, dayfirst=True)
                        except AttributeError:
                            pass
                        try:
                            assay_date = parse(assay_date, dayfirst=True)
                        except AttributeError:
                            pass
                        rcv = receive.get(lis_specimen_identifier)
                        result_tuple = ResultTuple(
                            rcv.edc_specimen_identifier,
                            self.drawn_datetime,
                            lis_specimen_identifier,
                            self.subject_identifier,
                            rcv.lis_received_datetime,
                            report_date,
                            self.subject_requisition.panel.name,
                            assay_date,
                            utestid,
                            result,
                            result_quantifier,
                            lis_result_id)
                        self.lis_results[rcv.edc_specimen_identifier].append(result_tuple)
        except pyodbc.Error as e:
            print(e)
            pass
