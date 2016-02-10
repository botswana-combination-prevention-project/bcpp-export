from bhp066.apps.bcpp_survey.models import Survey

from .base import Base


class Community(Base):

    def __init__(self, mapper, verbose=None, isoformat=None, dateformat=None, floor_datetime=None):
        super(Community, self).__init__(
            verbose=verbose, isoformat=isoformat, dateformat=dateformat, floor_datetime=floor_datetime)
        self.mapper_cls = mapper
        self.mapper = self.mapper_cls()
        self.cpc = self.mapper.intervention
        self.ecc = not self.mapper.intervention
        self.community = self.mapper.map_area
        self.community_id = self.mapper.map_code
        self.community_code = self.mapper.map_code
        self.pair = self.mapper.pair
        for survey in Survey.objects.all():
            survey_dates = self.mapper.survey_dates[survey.survey_slug]
            setattr(self, '{}_{}'.format(
                "start_date", survey.survey_abbrev.lower()), survey_dates.start_date)
            setattr(self, '{}_{}'.format(
                "full_enrollment_date", survey.survey_abbrev.lower()), survey_dates.full_enrollment_date)
            setattr(self, '{}_{}'.format(
                "end_date", survey.survey_abbrev.lower()), survey_dates.end_date)
            setattr(self, '{}_{}'.format(
                "smc_start_date", survey.survey_abbrev.lower()), survey_dates.smc_start_date)

    def __repr__(self):
        return '{0}({1.mapper!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.community!s}'.format(self)

    @property
    def unique_key(self):
        return self.community

    def prepare_csv_data(self, delimiter=None):
        super(Community, self).prepare_csv_data(delimiter=delimiter)
        del self.data['mapper']
        del self.data['mapper_cls']
