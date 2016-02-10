from bhp066.apps.bcpp_household.models import Plot as PlotModel

from ..classes import Plot

from .base_collector import BaseCollector


class Plots(BaseCollector):

    """Exports helper.plot instances to CSV.

    For example::
        from edc.map.classes import site_mappers

        from bhp066.apps.bcpp_export.collectors import Plots

        site_mappers.autodiscover()
        plots = Plots(isoformat=True, floor_datetime=True)
        plots.export_to_csv()
        plots.export_by_community(site_mappers.get_by_pair(1), filename_prefix='AD')
    """

    def __init__(self, export_plan=None, community=None, exception_cls=None,
                 include_clinic_plots=False, **kwargs):
        self.include_clinic_plots = include_clinic_plots
        super(Plots, self).__init__(
            export_plan=export_plan, community=community, exception_cls=exception_cls, **kwargs)
        self._plot_ids = None

    @property
    def plots(self):
        """Returns a list of plot ids ordered on plot identifier."""
        if not self._plot_ids:
            plots = PlotModel.objects.values_list('id').filter(**self.filter_options).order_by('plot_identifier')
            self._plot_ids = [i[0] for i in plots]
        return self._plot_ids

    def export_plots(self, filter_options=None, filename_prefix=None):
        self.filename_prefix = filename_prefix or self.filename_prefix
        try:
            self.filter_options.update(filter_options)
        except TypeError:
            pass
        count = len(self.plots)
        self.output_to_console('\n{} {}\n'.format(count, 'Plots'))
        for index, plot_id in enumerate(self.plots, start=1):
            self.progress_to_console('Plots', index, count)
            plot = Plot(
                plot=plot_id, isoformat=self.isoformat,
                dateformat=self.dateformat, floor_datetime=self.floor_datetime)
            if not plot.plot_identifier.endswith('CLIN-IC') or self.include_clinic_plots:
                self.export(plot, filename_prefix)
        self._plot_ids = None

    def export_by_community(self, communities=None, filter_options=None, filename_prefix=None):
        self.filename_prefix = filename_prefix or self.filename_prefix
        try:
            self.filter_options.update(filter_options)
        except TypeError:
            pass
        community_list = communities or self.community_list
        if self.order == '-':
            community_list.reverse()
        for community in community_list:
            self.output_to_console('{} **************************************\n'.format(community))
            self.filter_options.update({'community': community})
            self.export_plots()
