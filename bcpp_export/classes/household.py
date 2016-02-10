from bhp066.apps.bcpp_household.models import (
    HouseholdStructure, HouseholdLogEntry, HouseholdRefusal,
    HouseholdAssessment, Household as HouseholdModel)
from bhp066.apps.bcpp_household.choices import HH_STATUS
from bhp066.apps.bcpp_household.constants import (
    SEASONALLY_NEARLY_ALWAYS_OCCUPIED,
    UNKNOWN_OCCUPIED, RARELY_NEVER_OCCUPIED)

from .base import Base
from .plot import Plot
from .survey import Survey


class Household(Base):

    def __init__(self, household, **kwargs):
        super(Household, self).__init__(**kwargs)
        try:
            self.household = HouseholdModel.objects.get(id=household)
        except HouseholdModel.DoesNotExist:
            self.household = household
        try:
            self.household_identifier = self.household.household_identifier
        except AttributeError:
            self.household_identifier = None
        self.update_plot()
        self.survey = Survey(self.community, verbose=self.verbose)
        self.update_household_structure()
        self.update_household_log()
        self.update_household_refusal()
        self.update_household_assessment()
        self.update_replacement()
        self.update_household_status()

    def __repr__(self):
        return '{0}({1.household!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.household_identifier!s}'.format(self)

    @property
    def unique_key(self):
        return self.household_identifier

    def prepare_csv_data(self, delimiter=None):
        super(Household, self).prepare_csv_data(delimiter=delimiter)
        del self.csv_data['household']
        del self.csv_data['household_structures']
        del self.csv_data['survey']

    def update_plot(self):
        self.plot = Plot(household=self.household, verbose=self.verbose)
        attrs = [
            ('community', 'community'),
            ('gps_lat', 'gps_lat'),
            ('gps_lon', 'gps_lon'),
            ('confirmed', 'confirmed'),
            ('confirmed_date', 'confirmed_date'),
            ('plot_identifier', 'plot_identifier'),
            ('status', 'plot_status'),
            ('log_status', 'plot_log_status')]
        for attr in attrs:
            setattr(self, attr[1], getattr(self.plot, attr[0]))

    def update_household_status(self):
        for attr_suffix in self.survey.survey_abbrevs:
            status = None
            hh_status = {s[0]: s[1] for s in HH_STATUS}
            enumerated = getattr(self, '{}_{}'.format('enumerated', attr_suffix))
            enrolled = getattr(self, '{}_{}'.format('enrolled', attr_suffix))
            refused = getattr(self, '{}_{}'.format('refusal_datetime', attr_suffix))
            last_seen = getattr(self, '{}_{}'.format('assessment_last_seen', attr_suffix))
            if enumerated and enrolled:
                status = hh_status['enrolled']
            elif enumerated and not enrolled:
                status = hh_status['enumerated_not_enrolled']
            elif not enumerated:
                if refused:
                    status = hh_status['not_enum_hh_refused']
                elif last_seen:
                    if last_seen == SEASONALLY_NEARLY_ALWAYS_OCCUPIED:
                        status = hh_status['not_enum_almost_always_there_or_seasonally_occupied']
                    elif last_seen == RARELY_NEVER_OCCUPIED:
                        status = hh_status['not_enum_rarely_there_or_never_there']
                    elif last_seen == UNKNOWN_OCCUPIED:
                        status = hh_status['not_enum_unknown_status']
                    else:
                        raise TypeError('cannot determine HH_STATUS')
            else:
                status = hh_status['not_enum_hh'] if self.household else None
            # if not status and self.household:
            #     print ('Warning! Unable to determine HH_STATUS for {0!s}. '
            #            'enumerated={1}, enrolled={2}, refused={3}, last_seen={4}, '
            #            ).format(self.household, enumerated, enrolled, refused, last_seen)
            setattr(self, '{}_{}'.format('household_status', attr_suffix), status)

    def update_household_structure(self):
        self.household_structures = {}
        for survey_abbrev in self.survey.survey_abbrevs:
            try:
                self.household_structures.update({survey_abbrev: HouseholdStructure.objects.get(
                    household=self.household, survey__survey_abbrev=survey_abbrev.upper())})
            except HouseholdStructure.DoesNotExist:
                if self.verbose:
                    print 'Warning: No household_structure(s) for household {} {}'.format(
                        self.household_identifier, survey_abbrev)
                self.household_structures.update({survey_abbrev: None})
        for survey_abbrev in self.survey.survey_abbrevs:
            attr_suffix = survey_abbrev
            fieldattrs = [
                ('enrolled', 'enrolled'),
                ('enrolled_datetime', 'enrolled_datetime'),
                ('enumerated', 'enumerated'),
                ('enumeration_attempts', 'enumeration_attempts'),
                ('eligible_members', 'eligible_members'),
                ('refused_enumeration', 'refused_enumeration'),
                ('failed_enumeration', 'failed_enumeration')]
            self.denormalize(
                attr_suffix, fieldattrs,
                instance=self.household_structures.get(survey_abbrev))

    def update_household_log(self):
        """Adds HouseholdLog attrs to self denormalized on survey."""
        for survey_abbrev in self.survey.survey_abbrevs:
            fieldattrs = [
                ('report_datetime', 'log_date'),
                ('household_status', 'log_status')]
            self.denormalize(
                survey_abbrev, fieldattrs,
                lookup_model=HouseholdLogEntry,
                lookup_string='household_log__household_structure',
                lookup_instance=self.household_structures.get(survey_abbrev))
            try:
                setattr(
                    self, '{}_{}'.format('log_first_date', survey_abbrev),
                    min(getattr(self, '{}_{}'.format('log_date', survey_abbrev))))
            except TypeError:
                setattr(
                    self, '{}_{}'.format('log_first_date', survey_abbrev),
                    getattr(self, '{}_{}'.format('log_date', survey_abbrev)))
            try:
                setattr(
                    self, '{}_{}'.format('log_last_date', survey_abbrev),
                    max(getattr(self, '{}_{}'.format('log_date', survey_abbrev))))
            except TypeError:
                setattr(
                    self, '{}_{}'.format('log_last_date', survey_abbrev),
                    getattr(self, '{}_{}'.format('log_date', survey_abbrev)))

    def update_household_refusal(self):
        """Adds HouseholdRefusal attrs to self denormalized on survey."""
        lookup_string = 'household_structure'
        for survey_abbrev in self.survey.survey_abbrevs:
            attr_suffix = survey_abbrev
            fieldattrs = [('report_datetime', 'refusal_datetime')]
            household_refusal = self.denormalize(
                attr_suffix, fieldattrs,
                lookup_model=HouseholdRefusal,
                lookup_string=lookup_string,
                lookup_instance=self.household_structures.get(survey_abbrev))
            self.denormalize_other(
                attr_suffix,
                [('refusal_reason', 'reason_other', 'refusal_reason')],
                household_refusal)
        return household_refusal

    def update_household_assessment(self):
        """Adds HouseholdAssessment attrs to self denormalized on survey."""
        lookup_string = 'household_structure'
        for survey_abbrev in self.survey.survey_abbrevs:
            attr_suffix = survey_abbrev
            fieldattrs = [
                ('created', 'assessment_datetime'),
                ('last_seen_home', 'assessment_last_seen'),
                ('member_count', 'assessment_count'),
                ('eligibles', 'assessment_eligible'),
                ('ineligible_reason', 'assessment_ineligible_reason')]
            self.denormalize(
                attr_suffix, fieldattrs,
                lookup_model=HouseholdAssessment,
                lookup_string=lookup_string,
                lookup_instance=self.household_structures.get(survey_abbrev))

    def update_replacement(self):
        try:
            self.replaced_by_plot = self.household.replaced_by
            self.replaced = True if self.replaced_by_plot else False
        except AttributeError:
            self.replaced_by_plot = None
            self.replaced = None
