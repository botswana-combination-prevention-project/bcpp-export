from django.core.management.base import BaseCommand, CommandError

from edc.export.helpers import ExportObjectHelper
from edc.export.models import ExportPlan


class Command(BaseCommand):

    args = '<object_name>'
    help = 'Export objects a transactions.'
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        try:
            object_name = args[0]
        except IndexError:
            raise CommandError('Usage: export_transactions app_label.modelname, e.g. export_transactions bcpp_subject.subjectreferral')
        export_plan = ExportPlan.objects.get(
            app_label='object', object_name=object_name)
        export_model_helper = ExportObjectHelper(export_plan, object_name, exception_cls=CommandError)
        exit_status = export_model_helper.export()
        print exit_status
        self.stdout.write(exit_status[1])
