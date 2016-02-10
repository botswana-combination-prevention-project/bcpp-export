from collections import OrderedDict
from copy import copy
from datetime import datetime
from uuid import uuid4

from django_revision import site_revision
from edc.map.classes import site_mappers

from ..mixins import DenormalizeMixin, FormatForExportMixin, ConsoleMixin


class NewOrderedDict(OrderedDict):
    @property
    def unique_key(self):
        return self['unique_key']


class Base(DenormalizeMixin, FormatForExportMixin, ConsoleMixin):

    def __init__(self, verbose=None, dateformat=None, isoformat=None, floor_datetime=None):
        site_mappers.autodiscover()
        self.verbose = verbose
        self.customized = False
        self.csv_data = NewOrderedDict()
        self.export_uuid = unicode(uuid4())
        self.timestamp = datetime.today().isoformat()
        self.dateformat = dateformat or '%Y-%m-%d'
        self.isoformat = isoformat
        self.floor_datetime = floor_datetime

    def prepare_csv_data(self, delimiter=None):
        """Modifies values in the 'csv_data' attribute to be more friendly for CSV export."""
        delimiter = delimiter or ','
        if self.customized:
            raise TypeError('Method cannot be called twice')
        self.copy_all_into_csv_data()
        self.remove_unwanted_from_csv_data()
        self.add_to_csv_data()
        self.customized = True
        for key, value in self.csv_data.iteritems():
            value = self.format_if_none(value)
            value = self.format_if_boolean(value)
            value = self.format_if_date(value, floor_datetime=self.floor_datetime)
            value = self.format_if_list(value, delimiter=delimiter)
            self.csv_data[key] = value
        del self.csv_data['customized']

    @property
    def export_revision(self):
        return site_revision.tag

    @property
    def csv_keys(self):
        """Copy and sort keys from __dict__ for use to create csv_data dict.

        Add export_revision, revision and unique_key."""
        csv_keys = self.__dict__.keys()
        csv_keys.append('export_revision')
        csv_keys.append('revision')
        csv_keys.sort()
        csv_keys.insert(0, 'unique_key')
        return csv_keys

    def remove_unwanted_from_csv_data(self):
        """Removes columns from the csv_data dict that are not to be exposed."""
        try:
            del self.csv_data['csv_data']
        except KeyError:
            pass
        try:
            del self.csv_data['_data_errors']
        except KeyError:
            pass
        try:
            del self.csv_data['errors']
        except KeyError:
            pass
        try:
            del self.csv_data['verbose']
        except KeyError:
            pass
        try:
            del self.csv_data['dateformat']
        except KeyError:
            pass
        try:
            del self.csv_data['isoformat']
        except KeyError:
            pass
        try:
            del self.csv_data['floor_datetime']
        except KeyError:
            pass

    def copy_all_into_csv_data(self):
        """Copies ___dict___ into csv_data ordered dictionary."""
        for csv_key in self.csv_keys:
            try:
                self.csv_data[csv_key] = copy(self.__dict__[csv_key])
            except KeyError:
                self.csv_data[csv_key] = None

    def add_to_csv_data(self):
        """Adds custom values to the csv_data dict."""
        self.csv_data['export_revision'] = self.export_revision
        self.csv_data['unique_key'] = self.unique_key
