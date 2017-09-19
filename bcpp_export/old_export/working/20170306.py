import pandas as pd
import os
from django.db.models.loading import get_apps, get_models

from ..dataframes.edc import EdcModelToDataFrame
from django.db.utils import OperationalError

# separate models, with encrypted fields and without


class Export:

    def __init__(self, path=None):
        self.path = path or '/Users/erikvw/bcpp_201703'
        self.unencrypted_models = []
        self.encrypted_models = []
        excluded_models = [
            'incomingtransaction', 'outgoingtransaction', 'crypt']
        for app in get_apps():
            for model in get_models(app):
                for field in model._meta.fields:
                    if hasattr(field, 'field_cryptor'):
                        self.encrypted_models.append(model)
                        model = None
                        break
                if model:
                    self.unencrypted_models.append(model)
        self.unencrypted_models = [
            m for m in self.unencrypted_models
            if m._meta.model_name not in excluded_models]
        self.encrypted_models = [
            m for m in self.encrypted_models
            if m._meta.model_name not in excluded_models]
        self.make_folders()

    def make_folders(self):
        """mkdir a folder for each app that has models relative to path.
        """
        # build folder structure for CSV files
        for models in [self.unencrypted_models, self.encrypted_models]:
            paths = []
            for model in models:
                path_or_buf = os.path.join(
                    self.path, model._meta.app_label)
                paths.append(path_or_buf)
            paths = list(set(paths))
            for p in paths:
                try:
                    os.mkdir(p)
                except OSError:
                    pass

    def export_model_to_csv(self, model):
        if model.objects.all().exists():
            try:
                e = EdcModelToDataFrame(model)
            except OperationalError as err:
                print('Error. {}. Got {}'.format(
                    model._meta.model_name, str(err)))
            else:
                path_or_buf = os.path.join(
                    self.path, model._meta.app_label,
                    '{}.csv'.format(model._meta.model_name))
                e.dataframe.to_csv(
                    columns=e.columns(model.objects.all(), None),
                    path_or_buf=path_or_buf,
                    index=False,
                    encoding='utf-8')

    def export_unencrypted(self, models=None):
        """Creates a CSV file for each model and places in
        path/app_label/modelname.csv.
        """
        models = models or self.unencrypted_models
        for model in models:
            print(model._meta.model_name)
            self.export_model_to_csv(model)

    def export_encrypted(self, models=None):
        """Creates a CSV file for each model and places in
        path/app_label/modelname.csv.
        """
        models = models or self.encrypted_models
        for model in models:
            print('{} (encrypted)'.format(model._meta.model_name))
            self.export_model_to_csv(model)
