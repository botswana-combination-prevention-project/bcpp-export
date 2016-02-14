from datetime import datetime

from edc_constants.constants import YES, NO


class FormatForExportMixin(object):
    def format_if_boolean(self, value):
        """Formats a value as YES/NO if boolean."""
        if value is True:
            value = YES
        elif value is False:
            value = NO
        return value

    def format_if_none(self, value):
        """Formats a value as blank if None."""
        if value is None:
            value = ''
        return value

    def format_if_date(self, value, floor_datetime=None, isoformat=None):
        """Formats a date ro datetime to string.

        Hours, minutes and seconds in datetime are floored if floor_datetime is True."""
        floor_datetime = floor_datetime or self.floor_datetime
        isoformat = isoformat or self.isoformat
        if floor_datetime:
            try:
                value = value.replace(hour=0, minute=0, second=0, microsecond=0)
            except (AttributeError, TypeError):
                try:
                    value = datetime(value.year, value.month, value.day)
                except (AttributeError, ):
                    pass
        try:
            value = value.isoformat() if self.isoformat else value.strftime(self.dateformat)
        except (AttributeError, TypeError):
            pass
        return value

    def format_if_list(self, value, delimiter):
        if isinstance(value, (list, tuple)):
            for index, v in enumerate(value):
                value[index] = self.format_if_boolean(v)
                value[index] = self.format_if_none(v)
                value[index] = self.format_if_date(v)
            try:
                value = '{}'.format(delimiter).join(value)
            except TypeError:
                pass
        return value
