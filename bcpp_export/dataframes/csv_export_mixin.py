import os

from datetime import date

MIN = 0
MAX = 1
INTERVENTION = 1
NON_INTERVENTION = 0


class CsvExportMixin(object):

    default_export_pairs = tuple(range(1, 16))
    default_export_arms = (INTERVENTION, )
    default_export_dataset_name = 'results'
    default_filename_template = 'bcpp_export_{timestamp}_{datasetname}.csv'
    export_dataset_names = ['results']

    def __init__(self, *args, **kwargs):
        self.export_folder = kwargs.get('export_folder', os.path.expanduser('~/'))
        self.export_pairs = tuple(kwargs.get('export_pairs', self.default_export_pairs))
        self.export_arms = kwargs.get('export_arms', self.default_export_arms)

    def filtered_export_dataframe(self, df, export_arms=None, export_pairs=None, **kwargs):
        """Return a DF filtered by intervention arm(s) and pair(s).

        This is the DF that exports by default."""
        arms = export_arms or self.export_arms  # tuple, e.g. (INTERVENTION, NON_INTERVENTION)
        pairs = export_pairs or self.export_pairs  # tuple, e.g. (1, 15)
        return df[df['intervention'].isin(arms) & df['pair'].isin(pairs)]

    def to_csv(self, dataset_name=None, **kwargs):
        dataset_name = dataset_name or self.default_export_dataset_name
        export_folder = kwargs.get('export_folder', self.export_folder)
        for name in self.dataset_names(dataset_name):
            columns = self.get_export_columns(name, columns_list=kwargs.get('columns'))
            df = getattr(self, name)
            df = self.filtered_export_dataframe(df, **kwargs)
            options = dict(
                path_or_buf=os.path.expanduser(
                    kwargs.get('path_or_buf') or
                    os.path.join(export_folder, self.default_filename_template.format(
                        timestamp=date.today().strftime('%Y%m%d'), datasetname=name))),
                na_rep='',
                encoding='utf8',
                date_format=kwargs.get('date_format', '%Y-%m-%d %H:%M:%S'),
                index=kwargs.get('index', False),
                columns=columns.get(name))
            self._to_csv(df, **options)

    def _to_csv(self, df, **options):
        df.to_csv(**options)

    def get_export_columns(self, dataset_name, columns_list=None):
        """Return a dictionary with the {dataset_name: [list of columns]}"""
        columns = {}
        if not columns_list:
            try:
                columns.update(
                    {dataset_name: getattr(self, '{dataset_name}_columns'.format(dataset_name=dataset_name))})
            except AttributeError:
                columns.update({dataset_name: None})
        else:
            if dataset_name:
                columns = {dataset_name: columns_list}
        return columns

    def dataset_names(self, dataset_name):
        """Return the dataset_name(s) to export as a list or
        if dataset_name == all return a list of all dataset_names."""
        if dataset_name not in self.export_dataset_names + ['all']:
            raise TypeError('Invalid dataset name, expected one of {}'.format(self.export_dataset_names + ['all']))
        if dataset_name == 'all':
            dataset_names = self.export_dataset_names
        else:
            dataset_names = [dataset_name]
        return dataset_names
