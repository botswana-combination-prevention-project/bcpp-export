import csv
import os

from datetime import datetime

from bhp066.apps.bcpp_clinic.models import ClinicConsent
from bhp066.apps.bcpp_subject.models import SubjectConsent, HicEnrollment

from .base_collector import BaseCollector


class SubjectIdentifiers(BaseCollector):

    def __init__(self):
        """Generates a file of subject identifiers for each community.

        For example, list can be used by auditors to select subjects to audit.
        """
        super(SubjectIdentifiers, self).__init__()
        self.subject_identifiers = {}
        for community in self.community_list:
            with open(os.path.join(os.path.expanduser('~/export_to_cdc'), 'Enrolled{}-{}.csv'.format(community.title(), datetime.today().strftime('%Y%m%d%H%M%s'))), 'a') as f:
                writer = csv.writer(f)
                writer.writerow(['community', 'subject_identifier', 'type', 'survey'])
                for subject_consent in SubjectConsent.objects.filter(
                        household_member__household_structure__household__plot__community=community).order_by('subject_identifier'):
                    writer.writerow([
                        community, subject_consent.subject_identifier, 'SURVEY',
                        subject_consent.household_member.household_structure.survey.survey_slug])
                for hic_enrollment in HicEnrollment.objects.filter(
                        subject_visit__household_member__household_structure__household__plot__community=community
                        ).order_by('subject_visit__household_member__registered_subject__subject_identifier'):
                    writer.writerow([
                        community, hic_enrollment.subject_visit.household_member.registered_subject.subject_identifier, 'HIC',
                        hic_enrollment.subject_visit.household_member.household_structure.survey.survey_slug])
                for clinic_consent in ClinicConsent.objects.filter(
                        household_member__household_structure__household__plot__community=community
                        ).order_by('household_member__registered_subject__subject_identifier'):
                    writer.writerow([
                        community, clinic_consent.subject_identifier, 'CLINIC_RBD',
                        clinic_consent.household_member.member_status,
                        clinic_consent.household_member.household_structure.survey.survey_slug])
