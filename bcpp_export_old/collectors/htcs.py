from bhp066.apps.bcpp_household_member.models import SubjectHtc

from ..classes import Htc

from .base_collector import BaseCollector


class Htcs(BaseCollector):

    """Exports helper.household instances to CSV.

    For example::
        from bhp066.apps.bcpp_export.collectors import Members

        htcs = Htcs(isoformat=True, floor_datetime=True)
        htcs.export_by_community()
    """

    def __init__(self, export_plan=None, community=None, survey_slug=None, exception_cls=None, **kwargs):
        super(Htcs, self).__init__(export_plan=export_plan, community=community, exception_cls=exception_cls, **kwargs)
        self._subject_htcs = None
        self.exclude_options = {}
        self.survey_slug = survey_slug

    @property
    def subject_htcs(self):
        """Returns a unique filtered list of subject_htc identifiers."""
        if not self._subject_htcs:
            subject_htcs = SubjectHtc.objects.values_list('id').filter(
                **self.filter_options).exclude(
                **self.exclude_options)
            self._subject_htcs = list(set([i[0] for i in subject_htcs]))
        return self._subject_htcs

    def export_htcs(self, filter_options=None, filename_prefix=None):
        """Creates then exports Htc instances from the current list of Htcs."""
        self.filename_prefix = filename_prefix or self.filename_prefix
        try:
            self.filter_options.update(filter_options)
        except TypeError:
            pass
        count = len(self.subject_htcs)
        self.output_to_console('\n{} {}\n'.format(count, 'Htc'))
        for index, subject_htc in enumerate(self.subject_htcs, start=1):
            self.progress_to_console('Htcs', index, count)
            htc = Htc(
                subject_htc, isoformat=self.isoformat,
                dateformat=self.dateformat, floor_datetime=self.floor_datetime)
            self.export(htc)
        self._subject_htcs = None

    def export_by_community(self, communities=None, filter_options=None, filename_prefix=None):
        """Exports subject instances one at a time to csv for each community."""
        try:
            self.filter_options.update(filter_options)
        except TypeError:
            pass
        self.filename_prefix = filename_prefix or self.filename_prefix
        community_list = communities or self.community_list
        if self.order == '-':
            community_list.reverse()
        for community in self.community_list:
            self.output_to_console('{} **************************************\n'.format(community))
            self.filter_options.update({'household_member__household_structure__household__plot__community': community})
            self.export_htcs()
