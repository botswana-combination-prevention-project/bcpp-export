from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from edc.map.classes import site_mappers

from apps.bcpp_export.collectors import Plots, Communities, Households, Htcs, Members, SubjectIdentifiers, Subjects


class Command(BaseCommand):

    args = '<name> <filename_prefix>'
    help = 'Export collectors'
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        collectors = ['Plots', 'Communities', 'Households', 'Htcs', 'Members', 'SubjectIdentifiers', 'Subjects']
        try:
            name = args[0]
            filename_prefix = args[1]
        except IndexError:
            raise CommandError(
                'Usage: export_collector <name> <filename_prefix>. For example:\n\n'
                '    python manage.py export_collector Plots AA\n\n'
                'Options for <name> are: {}'.format(', '.join(collectors)))
        if name not in ['Plots', 'Communities', 'Households', 'Htcs', 'Members', 'SubjectIdentifiers', 'Subjects']:
            raise CommandError('Invalid collector name')
        site_mappers.autodiscover()
        print('Starting export of \'{}\' at {}.'.format(name, datetime.today()))
        if name == 'Plots':
            collector = Plots(isoformat=True, floor_datetime=True)
        elif name == 'Communities':
            collector = Communities(isoformat=True, floor_datetime=True)
        elif name == 'Households':
            collector = Households(isoformat=True, floor_datetime=True)
        elif name == 'Htcs':
            collector = Htcs(isoformat=True, floor_datetime=True)
        elif name == 'Members':
            collector = Members(isoformat=True, floor_datetime=True)
        elif name == 'SubjectIdentifiers':
            collector = SubjectIdentifiers(isoformat=True, floor_datetime=True)
        elif name == 'Subjects':
            collector = Subjects(isoformat=True, floor_datetime=True)
        collector.export_by_community(filename_prefix=filename_prefix)
        print('Done at {}.'.format(datetime.today()))
