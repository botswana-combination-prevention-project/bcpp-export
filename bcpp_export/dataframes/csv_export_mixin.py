import os

from datetime import date

MIN = 0
MAX = 1
INTERVENTION = 1
NON_INTERVENTION = 0


class CsvExportMixin(object):

    default_export_pairs = (1, 15)
    default_export_arms = (INTERVENTION, )
    default_export_dataset_name = 'results'
    default_filename_template = 'bcpp_export_{timestamp}_{datasetname}.csv'
    export_dataset_names = ['results']

    def __init__(self, *args, **kwargs):
        super(CsvExportMixin, self).__init__(*args, **kwargs)
        self.export_folder = kwargs.get('export_folder', os.path.expanduser('~/'))
        self.export_pairs = kwargs.get('export_pairs', self.default_export_pairs)
        self.export_arms = kwargs.get('export_arms', self.default_export_arms)

    def filtered_export_dataframe(self, df, export_arms=None, export_pairs=None):
        """Return a DF filtered by intervention arm(s) and pair(s).

        This is the DF that exports by default."""
        arms = export_arms or self.export_arms  # tuple, e.g. (INTERVENTION, NON_INTERVENTION)
        pairs = export_pairs or self.export_pairs  # tuple, e.g. (1, 15)
        return df[df['intervention'].isin(arms) & df['pair'].isin(range(pairs[MIN], pairs[MAX] + 1))]

    def to_csv(self, dataset_name=None, **kwargs):
        dataset_name = dataset_name or self.default_export_dataset_name
        columns = kwargs.get('columns', {})
        for name in self.dataset_names(dataset_name):
            df = getattr(self, name)
            df = self.filtered_export_dataframe(df, **kwargs)
            options = dict(
                path_or_buf=os.path.expanduser(
                    kwargs.get('path_or_buf') or
                    os.path.join(self.export_folder, self.default_filename_template.format(
                        timestamp=date.today().strftime('%Y%m%d'), datasetname=name))),
                na_rep='',
                encoding='utf8',
                date_format=kwargs.get('date_format', '%Y-%m-%d %H:%M:%S'),
                index=kwargs.get('index', False),
                columns=columns.get(name))
            df.to_csv(**options)

    def dataset_names(self, dataset_name):
        """Return the dataset_name(s) to export as a list or
        if dataset_name == all return a list of all dataset_names."""
        valid_dataset_names = self.valid_dataset_names + ['all']
        if dataset_name not in self.valid_dataset_names + ['all']:
            raise TypeError('Invalid dataset name, expected one of {}'.format(valid_dataset_names))
        if dataset_name == 'all':
            dataset_names = valid_dataset_names
        else:
            dataset_names = [dataset_name]
        return dataset_names
