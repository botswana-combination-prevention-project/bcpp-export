from bhp066.apps.bcpp_household.models import Household as HouseholdModel

from ..classes import Household

from .base_collector import BaseCollector


class Households(BaseCollector):

    """Exports helper.household instances to CSV.

    For example::
        from bhp066.apps.bcpp_export.collectors import Households

        households = Households()
        households.export_to_csv()
    """

    def __init__(self, export_plan=None, community=None, exception_cls=None, **kwargs):
        super(Households, self).__init__(
            export_plan=export_plan, community=community, exception_cls=exception_cls, **kwargs)
        self._households = None
        self.exclude_options = {}

    @property
    def households(self):
        """Returns a unique filtered list of household ids."""
        if not self._households:
            households = HouseholdModel.objects.values_list('id').filter(
                **self.filter_options).exclude(
                **self.exclude_options)
            self._households = list(set([i[0] for i in households]))
        return self._households

    def export_households(self, filter_options=None, filename_prefix=None):
        """Creates then exports Household instances from the current list of Households."""
        self.filename_prefix = filename_prefix or self.filename_prefix
        try:
            self.filter_options.update(filter_options)
        except TypeError:
            pass
        count = len(self.households)
        self.output_to_console('\n{} {}\n'.format(count, 'Households'))
        for index, household in enumerate(self.households, start=1):
            self.progress_to_console('Households', index, count)
            household = Household(
                household, isoformat=self.isoformat,
                dateformat=self.dateformat, floor_datetime=self.floor_datetime)
            self.export(household)
        self._households = None

    def export_by_community(self, communities=None, filter_options=None, filename_prefix=None):
        """Exports household instances one at a time to csv for each community."""
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
            self.filter_options.update({'plot__community': community})
            self.export_households()
