import pyodbc

from collections import namedtuple
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from django.conf import settings

from edc_constants.constants import YES

from bhp066.apps.bcpp_lab.models import SubjectRequisition, Receive

from .base import Base
from .subject import Subject
from .specimen import Specimen
ReceivedTuple = namedtuple(
    'ReceivedTuple',
    'edc_specimen_identifier, lis_specimen_identifier, lis_patient_ref, received_datetime')
ResultTuple = namedtuple(
    'ResultTuple',
    'edc_specimen_identifier, lis_specimen_identifier, lis_patient_ref, received_datetime, report_date, panel_id, sample_assay_date, utestid, result, result_quantifier lis_result_id')


class Lab(Base):
    def __init__(self, aliquots, verbose=None):
        super(Lab, self).__init__(verbose=verbose)
        self.sql = {}
        self.specimen = Specimen(aliquots, verbose=verbose)
        self.aliquots = aliquots
        try:
            self.aliquot_identifiers = [a.aliquot_identifier for a in aliquots]
        except AttributeError:
            self.aliquot_identifiers = aliquots
        self.dmis_column = 'edc_specimen_identifier'
        self.subject_requisition = SubjectRequisition.objects.get(specimen_identifier=self.aliquot_identifiers[0][:-4])
        self.specimen_identifier = self.subject_requisition.specimen_identifier
        self.survey = self.subject_requisition.subject_visit.household_member.household_structure.survey.survey_abbrev.lower()
        self.subject = Subject(self.subject_requisition.subject_visit.household_member, verbose=False)
        self.subject_identifier = self.subject_requisition.subject_visit.get_subject_identifier()
        self.gender = self.subject.gender
        self.age = self.subject.age_in_years
        self.hiv_status = getattr(self.subject, '{}_{}'.format('hiv_result', self.survey))
        self.hiv_result_datetime = getattr(self.subject, '{}_{}'.format('hiv_result_date', self.survey))
        self.community = self.subject.community
        self.survey_consented = self.subject.survey_consented
        self.survey_pair = self.subject.survey.pair
        self.consent_datetime = self.subject.consent_datetime
        self.receive = Receive.objects.get(receive_identifier=self.subject_requisition.specimen_identifier)
        self.receive_datetime = self.receive.receive_datetime  # where does this date come from??
        self.receive_identifier = self.receive.receive_identifier
        self.requisition_identifier = self.subject_requisition.requisition_identifier
        self.requisition_datetime = self.subject_requisition.requisition_datetime
        self.requisition_panel = self.subject_requisition.panel.name
        self.drawn = True if self.subject_requisition.is_drawn == YES else False
        self.reason_not_drawn = self.subject_requisition.reason_not_drawn
        self.drawn_datetime = self.subject_requisition.drawn_datetime
        self.lis_received = {}
        self.lis_received_datetime = None
        self.lis_subject_identifier = None
        self.lis_specimen_identifier = []
        self.lis_assay = None
        self.lis_assay_date = None
        self.lis_result = None
        self.lis_result_int = None
        self.lis_result_qnt = None
        self.lis_results = []
        self.fetch_receiving()
        self.fetch_result()
        self.date_sequence = (
            relativedelta(self.requisition_datetime, self.consent_datetime).days,
            relativedelta(self.drawn_datetime, self.requisition_datetime).days,
            relativedelta(self.receive_datetime, self.drawn_datetime).days,
            relativedelta(self.lis_received_datetime, self.receive_datetime).days,
            relativedelta(self.lis_assay_date, self.lis_received_datetime).days,
        )

    def __repr__(self):
        return '{0}({1.specimen_identifier!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.specimen_identifier!s}'.format(self)

    def fetch_receiving(self):
        """Fetches the receiving data from the LIS for each identifier."""
        def fetchall(cursor):
            self.sql.update(
                received_items=(
                    'select pid, pat_id, headerdate from lab01response as l where '
                    '{dmis_column} LIKE \'{specimen_identifier}%\'').format(
                        dmis_column=self.dmis_column, specimen_identifier=self.specimen_identifier)
            )
            return cursor.execute(self.sql.get('received_items')).fetchall()
        if self.verbose:
            print "Querying dmis for {} {}".format(self.specimen_identifier, self.aliquot_type)
        try:
            with pyodbc.connect(settings.LAB_IMPORT_DMIS_DATA_SOURCE) as cnxn:
                with cnxn.cursor() as cursor:
                    for lis_specimen_identifier, lis_subject_identifier, lis_received_datetime in fetchall(cursor):
                        self.lis_received.update({lis_specimen_identifier: (lis_specimen_identifier, lis_subject_identifier, lis_received_datetime)})
                        if lis_specimen_identifier == self.aliquot_identifier:
                            self.lis_specimen_identifier = lis_specimen_identifier
                            if not self.lis_received_datetime:
                                self.lis_received_datetime = lis_received_datetime
                            if not self.lis_subject_identifier:
                                self.lis_subject_identifier = self.subject_identifier
                                if self.lis_subject_identifier != self.subject_identifier:
                                    print "Warning! LIS pat_ref differs with EDC subject_deintifier for {}. Got {}".format(
                                        self.subject_identifier, self.lis_subject_identifier)
                            if not self.specimen_identifier:
                                self.lis_subject_identifier = self.subject_identifier
                                if self.lis_subject_identifier != self.subject_identifier:
                                    print "Warning! LIS pat_ref differs with EDC subject_deintifier for {}. Got {}".format(
                                        self.subject_identifier, self.lis_subject_identifier)

        except pyodbc.Error as e:
            raise pyodbc.Error(e)

    def fetch_result(self):
        """Fetches the receiving data from the LIS for each identifier."""
        def fetchall(cursor):
            self.sql.update(
                resulted_items=(
                    'select PID as sample_id, reportdate, panel_id, sample_assay_date, utestid, result, result_quantifier, L21.id as lis_result_id '
                    'from BHPLAB.DBO.LAB21Response as L21 '
                    'left join BHPLAB.DBO.LAB21ResponseQ001X0 as L21D on L21.Q001X0=L21D.QID1X0 '
                    'where PID=\'{lis_specimen_identifier}\'').format(
                        dmis_column=self.dmis_column, lis_specimen_identifier=self.lis_specimen_identifier))
            return cursor.execute(self.sql.get('resulted_items')).fetchall()
        if self.verbose:
            print "Querying dmis for {} resulted items".format(self.lis_specimen_identifier)
        try:
            with pyodbc.connect(settings.LAB_IMPORT_DMIS_DATA_SOURCE) as cnxn:
                with cnxn.cursor() as cursor:
                    for lis_specimen_identifier, report_date, panel_id, sample_assay_date, utestid, result, result_quantifier, lis_result_id in fetchall(cursor):
                        try:
                            report_date = parse(report_date, dayfirst=True)
                        except AttributeError:
                            pass
                        try:
                            sample_assay_date = parse(sample_assay_date, dayfirst=True)
                        except AttributeError:
                            pass
                        result_tuple = ResultTuple(
                            self.aliquot_identifier,
                            self.lis_specimen_identifier,
                            self.lis_subject_identifier,
                            self.lis_received_datetime,
                            report_date,
                            None,
                            sample_assay_date,
                            utestid,
                            result,
                            result_quantifier,
                            lis_result_id)
                        self.lis_results.append(result_tuple)
                        if not self.lis_result:
                            self.lis_result = '{}{}'.format(result_quantifier if result_quantifier in '<>' else '', result)
                            try:
                                self.lis_result_int = int(result)
                            except TypeError:
                                pass
                            self.lis_result_qnt = result_quantifier
                            self.lis_assay = utestid
                            self.lis_assay_date = sample_assay_date
                        else:
                            print 'Warning! More than one result for {}.'.format(self.aliquot_identifier)

        except pyodbc.Error as e:
            raise pyodbc.Error(e)
