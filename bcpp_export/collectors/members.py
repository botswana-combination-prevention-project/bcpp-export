from bhp066.apps.bcpp_household_member.models import HouseholdMember

from ..classes import Member

from .base_collector import BaseCollector


class Members(BaseCollector):

    """Exports helper.household instances to CSV.

    For example::
        from bhp066.apps.bcpp_export.collectors import Members

        members = Members()
        members.export_by_community()
    """

    def __init__(self, export_plan=None, community=None, survey_slug=None,
                 exception_cls=None, **kwargs):
        super(Members, self).__init__(
            export_plan=export_plan, community=community,
            exception_cls=exception_cls, **kwargs)
        self._household_members = None
        if survey_slug:
            self.filter_options.update({'household_structure__survey__survey_slug': survey_slug})
        self.exclude_options = {'household_structure__household__plot__plot_identifier__endswith': '0000-00'}

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
            self.filter_options.update({'household_structure__household__plot__community': community})
            self.export_household_members()

    def export_household_members(self, filter_options=None, filename_prefix=None):
        """Creates then exports a Member instances from the current list of household members."""
        self.filename_prefix = filename_prefix or self.filename_prefix
        try:
            self.filter_options.update(filter_options)
        except TypeError:
            pass
        count = len(self.household_members)
        self.output_to_console('\n{} {}\n'.format(count, 'Members'))
        for index, household_member in enumerate(self.household_members, start=1):
            self.progress_to_console('Members', index, count)
            member = Member(
                household_member, isoformat=self.isoformat,
                dateformat=self.dateformat, floor_datetime=self.floor_datetime)
            self.export(member)
        self._household_members = None

    @property
    def household_members(self):
        """Returns a unique filtered list of household_member internal identifiers."""
        if not self._household_members:
            household_members = HouseholdMember.objects.values_list('internal_identifier').filter(
                **self.filter_options).exclude(
                **self.exclude_options)
            self._household_members = list(set([i[0] for i in household_members]))
        return self._household_members
