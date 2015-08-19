from datetime import datetime

from edc.export.classes import ExportDictAsCsv
from edc.export.helpers import ExportObjectHelper
from edc.map.classes import site_mappers

from ..plans import export_plan as default_export_plan
from ..mixins import ConsoleMixin


class BaseCollector(ConsoleMixin):

    def __init__(self, export_plan=None, community=None, exception_cls=None, delimiter=None,
                 reverse_order=None, dateformat=None,
                 isoformat=None, floor_datetime=None):
        self.delimiter = delimiter or "|"
        self.for_csv = False
        self.filename = None
        self.test_run = False
        self.write_header = True
        self.export_plan = export_plan or default_export_plan
        self.export_plan.notification_plan = 'rdb'
        self.exception_cls = exception_cls or TypeError
        self.instances = []
        self.dateformat = dateformat
        self.isoformat = isoformat
        self.floor_datetime = floor_datetime
        self.order = '-' if reverse_order else ''
        self.filter_options = {}
        self.filename_prefix = None

        site_mappers.autodiscover()
        try:
            del site_mappers._registry['bhp']
        except KeyError:
            pass
        try:
            del site_mappers._registry['test_community']
        except KeyError:
            pass
        if community:
            self.community_list = [community]
        else:
            self.mappers = site_mappers.sort_by_pair()
            self.community_list = [mapper().community for mapper in self.mappers.itervalues()]

    def __repr__(self):
        return '{0}({1.export_plan!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.export_plan!r}'.format(self)

    def export(self, instance, filename_prefix=None):
        """Calls the csv writer to append each instance to the current file."""
        self.filename_prefix = filename_prefix or self.filename_prefix
        instance.prepare_csv_data()
        if not self.filename:
            self.filename = '{0}{1}_{2}.csv'.format(
                self.filename_prefix or '', instance.__class__.__name__, datetime.today().strftime('%Y%m%d%H%M%S'))
        if self.write_header:
            self.output_to_console('Writing to {}\n'.format(self.filename))
        export_model_helper = ExportObjectHelper(
            self.export_plan,
            delimiter=self.delimiter,
            fields=instance.csv_data.keys(),
            filename=self.filename,
            exception_cls=self.exception_cls)
        export_model_helper.writer_cls = ExportDictAsCsv
        export_model_helper.writer.write_to_file([instance.csv_data], self.write_header)
        self.write_header = False  # only write header once

    def export_all(self):
        """Calls the csv writer to append each instance to a list then write all to file at once."""
        instances_for_csv = (instance.prepare_csv_data() for instance in self.instances)
        if not self.filename:
            self.filename = '{0}{1}_{2}.csv'.format(
                self.instances[0].__class__.__name__, datetime.today().strftime('%Y%m%d%H%M%S'))
        self.output_to_console('Writing to {}\n'.format(self.filename))
        export_model_helper = ExportObjectHelper(
            self.export_plan,
            delimiter=self.delimiter,
            fields=self.instances[0].csv_data.keys(),
            filename=self.filename,
            exception_cls=self.exception_cls)
        export_model_helper.writer.write_to_file(instances_for_csv, self.write_header)
