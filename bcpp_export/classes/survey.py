from edc.map.classes import site_mappers

from bhp066.apps.bcpp_household.models import Plot
from bhp066.apps.bcpp_survey.models import Survey as SurveyModel

from .base import Base


class Survey(Base):

    def __init__(self, community, verbose=None, isoformat=None, dateformat=None, floor_datetime=None):
        """Set attributes related to the surveys the member has been enumerated in."""
        super(Survey, self).__init__(
            verbose=verbose, isoformat=isoformat, dateformat=dateformat, floor_datetime=floor_datetime)
        self.community = community
        self.plot_count_all = Plot.objects.filter(community=self.community).count()
        mapper = site_mappers.get_mapper(self.community)
        self.survey_slugs = []
        self.survey_abbrevs = []
        fieldattrs = [
            ('name', 'survey_name'),
            ('start_date', 'survey_start_date'),
            ('full_enrollment_date', 'survey_full_enrollment_date'),
            ('smc_start_date', 'survey_smc_start_date')]
        try:
            self.pair = mapper.pair
        except AttributeError:
            self.pair = None
        for survey in SurveyModel.objects.all().order_by('survey_abbrev'):
            self.survey_slugs.append(survey.survey_slug)
            self.survey_abbrevs.append(survey.survey_abbrev.lower())
        for index, survey_slug in enumerate(self.survey_slugs):
            try:
                dates = mapper.survey_dates.get(survey_slug)
            except AttributeError:
                dates = None
            attrs = {
                'name': dates.name.upper() if dates else None,
                'start_date': dates.start_date if dates else None,
                'full_enrollment_date': dates.full_enrollment_date if dates else None,
                'smc_start_date': dates.smc_start_date if dates else None,
            }
            self.denormalize(
                self.survey_abbrevs[index], fieldattrs,
                instance=type('Instance', (object, ), attrs)
            )

    def __repr__(self):
        return '{0}({1.community!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.community!s}'.format(self)
