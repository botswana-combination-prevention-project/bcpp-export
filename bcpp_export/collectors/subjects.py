from bhp066.apps.bcpp_clinic.models import ClinicConsent
from bhp066.apps.bcpp_subject.models import SubjectConsent

from ..classes import Subject

from .base_collector import BaseCollector


class Subjects(BaseCollector):

    """Exports helper.household instances to CSV.

    For example::
        from bhp066.apps.bcpp_export.collectors import Subjects

        subjects = Subjects()
        #export everything (all consents, all communities)
        subjects.export_by_community()

        # export all consents for two communities
        subjects.export_by_community((['digawana', 'ranaka'])
        # export all consents by pair, write to a file prefixed by 'AA'.
        subjects.export_by_community(site_mappers.get_by_pair(3), filename_prefix='AA')
        # export only subject consents for two communities
        subjects.export_by_community((['digawana', 'ranaka'], exclude_clinic_consents=True)
        # inspect or count subject consents
        len(subjects.subject_consents)
        # inspect or count a subset of subject consents
        subjects.subject_consents.filter(is_minor=True)
    """

    def __init__(self, export_plan=None, community=None, survey_slug=None,
                 exception_cls=None, **kwargs):
        super(Subjects, self).__init__(
            export_plan=export_plan, community=community,
            exception_cls=exception_cls, **kwargs)
        self._clinic_consents = None
        self._subject_consents = None
        if survey_slug:
            self.filter_options.update({
                'household_member__household_structure__survey__survey_slug': survey_slug})

    @property
    def subject_consents(self):
        """Returns a ValuesSet from a SubjectConsents queryset.

        * Use a values_list to maintain order;
        * Is filtered on community and possibly survey;
        * excludes "clinic" plots."""
        if not self._subject_consents:
            self._subject_consents = SubjectConsent.objects.values_list('household_member').filter(
                **self.filter_options
                ).exclude(
                    household_member__household_structure__household__plot__plot_identifier__endswith='0000-00'
                    ).order_by('{}registered_subject__subject_identifier'.format(self.order))
        return self._subject_consents

    @property
    def clinic_consents(self):
        """Returns a ValuesSet from a ClinicConsents queryset.

        * Use a values_list to maintain order;
        * Is filtered on community and possibly survey."""
        if not self._clinic_consents:
            self._clinic_consents = ClinicConsent.objects.values_list('household_member').filter(
                **self.filter_options).order_by(
                    '{}registered_subject__subject_identifier'.format(self.order))
        return self._clinic_consents

    def export_subject_consents(self, filter_options=None, filename_prefix=None):
        """Instantiates Subject with a household_member id for a given subject consent and exports."""
        name = 'Subject Consents'
        self.filter_options.update(filter_options)
        count = len(self.subject_consents)
        self.output_to_console('\n{} {}\n'.format(count, name))
        for index, subject_consent in enumerate(self.subject_consents, start=1):
            self.progress_to_console(name, index, count)
            subject = Subject(
                subject_consent[0], isoformat=self.isoformat,
                dateformat=self.dateformat, floor_datetime=self.floor_datetime)
            self.export(subject, filename_prefix)
        self._subject_consents = None

    def export_clinic_consents(self, filter_options=None, filename_prefix=None):
        """Instantiates Subject with a household_member id for a given clinic consent and exports."""
        name = 'Clinic Consents'
        self.filter_options.update(filter_options)
        count = len(self.clinic_consents)
        self.output_to_console('\n{} {}\n'.format(count, name))
        for index, clinic_consent in enumerate(self.clinic_consents, start=1):
            self.progress_to_console(name, index, count)
            subject = Subject(
                clinic_consent[0], isoformat=self.isoformat,
                dateformat=self.dateformat, floor_datetime=self.floor_datetime)
            self.export(subject, filename_prefix)
        self._clinic_consents = None

    def export_by_community(self, communities=None, exclude_subject_consents=None,
                            exclude_clinic_consents=None, filter_options=None,
                            filename_prefix=None):
        """Exports subject instances one at a time to csv for each community."""
        filter_options = filter_options or {}
        community_list = communities or self.community_list
        if self.order == '-':
            community_list.reverse()
        for community in community_list:
            self.output_to_console('{} **************************************\n'.format(community))
            filter_options.update({
                'household_member__household_structure__household__plot__community': community})
            if not exclude_subject_consents:
                self.export_subject_consents(filter_options, filename_prefix)
            if not exclude_clinic_consents:
                self.export_clinic_consents(filter_options, filename_prefix)
