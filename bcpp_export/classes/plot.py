from bhp066.apps.bcpp_household.models import Household, HouseholdStructure, PlotLog, PlotLogEntry, Plot as PlotModel
from bhp066.apps.bcpp_household_member.models import HouseholdMember
from bhp066.apps.bcpp_household.constants import TWENTY_PERCENT, FIVE_PERCENT, CONFIRMED, SEVENTY_FIVE_PERCENT,\
    RESIDENTIAL_NOT_HABITABLE, RESIDENTIAL_HABITABLE, NON_RESIDENTIAL, ACCESSIBLE
from bhp066.apps.bcpp_household.choices import PLOT_STATUS, PLOT_LOG_STATUS
from bhp066.apps.bcpp_subject.models import SubjectConsent

from .base import Base
from .survey import Survey


class Plot(Base):
    def __init__(self, plot=None, household=None, household_structure=None, household_member=None, **kwargs):
        super(Plot, self).__init__(**kwargs)
        self.household = household
        self.household_member = household_member
        self.household_structure = household_structure
        try:
            self.plot = household_member.household_structure.household.plot
        except AttributeError:
            try:
                self.plot = household_structure.household.plot
            except AttributeError:
                try:
                    self.plot = household.plot
                except AttributeError:
                    try:
                        self.plot = PlotModel.objects.get(id=plot)
                    except PlotModel.DoesNotExist:
                        self.plot = plot
        self.update_plot()
        self.survey = Survey(self.community)
        self.update_plot_owner()
        self.update_households()
        self.update_members()
        self.update_plot_log()
        self.check_plot_enrollment()
        self.clean_clinic_plot()

    def __repr__(self):
        return ('{0}(plot={1.plot!r})').format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.plot!s}'.format(self)

    @property
    def unique_key(self):
        return self.plot_identifier

    def prepare_csv_data(self, delimiter=None):
        super(Plot, self).prepare_csv_data(delimiter=delimiter)
        del self.csv_data['plot']
        del self.csv_data['household_member']
        del self.csv_data['household_members']
        del self.csv_data['household_structure']
        del self.csv_data['household_structures']
        del self.csv_data['households']
        del self.csv_data['household']
        del self.csv_data['logs']
        del self.csv_data['survey']

    def clean_clinic_plot(self):
        is_clinic = False
        try:
            if self.plot_identifier.endswith('CLIN-IC'):
                is_clinic = True
        except AttributeError:
            pass
        if is_clinic:
            self.bhs_plot, self.htc_plot = False, False
            self.household_identifiers = []
            self.households = []
            self.household_structures = []
            self.random_selection = None
            self.household_count = 0
            self.confirmed = None

    def update_bhs_plot(self):
        """Sets plot model attributes bhs and htc."""
        self.htc_plot = self.plot.htc
        self.bhs_plot = self.plot.bhs
        # temporary override of stored data********************************************
        self.bhs_plot, self.htc_plot = False, True
        if SubjectConsent.objects.filter(household_member__household_structure__household__plot=self.plot).exists():
            self.bhs_plot, self.htc_plot = True, False
        # end temporary override of stored data****************************************

    def update_plot_owner(self):
        """Updates instance attr for values like bhs, htc, enrolled, selected, replacement."""
        try:
            self.update_bhs_plot()
            self.enrolled = self.bhs_plot
            self.replaced_by = self.plot.replaced_by
            if self.replaced_by and not self.htc_plot:
                print ('Warning: Expected replaced plot {} to '
                       'be an HTC plot, Got \'{}\'').format(self.plot_identifier, self.htc_plot)
            self.replaces = self.plot.replaces
            if self.plot.selected == TWENTY_PERCENT:
                self.handed_to_htc = True if self.plot.htc else False
                self.random_selection = '20%'
            elif self.plot.selected == FIVE_PERCENT:
                self.handed_to_htc = True if self.plot.htc else False
                self.random_selection = '5%'
            elif self.plot.selected is SEVENTY_FIVE_PERCENT:
                self.handed_to_htc = False
                self.random_selection = '75%'
            else:
                raise ValueError('Invalid value for plot.selected for plot {}. Got {}'.format(
                    self.plot.plot_identifier, self.plot.selected))
            if self.plot.selected is SEVENTY_FIVE_PERCENT and self.plot.bhs:
                print ('Warning! Plot {} is in 75%! Got plot.bhs=True'.format(
                    self.plot.plot_identifier, self.plot.selected))
        except AttributeError:
            self.enrolled = None
            self.htc_plot = None
            self.bhs_plot = None
            self.handed_to_htc = None
            self.random_selection = None

    def update_plot_status(self):
        """"Sets and check plot status."""
        self.status = None if self.location == 'clinic' else self.plot.status
        # temporary override of stored data********************************************
        if self.status == 'vacant':
            self.status = RESIDENTIAL_NOT_HABITABLE
        if self.status == 'occupied_no_residents':
            self.status = RESIDENTIAL_HABITABLE
        if self.status == 'occupied':
            self.status = RESIDENTIAL_HABITABLE
        if self.status == 'non-residential':
            self.status = NON_RESIDENTIAL
        # temporary override of stored data********************************************
        if self.status not in [c[0] for c in PLOT_STATUS] and self.status:
            print 'Warning: Invalid plot status for {}. Got {}'.format(self.plot_identifier, self.status)

    def update_plot(self):
        try:
            if self.plot.plot_identifier.endswith('0000-00'):
                self.plot_identifier = '{}CLIN-IC'.format(self.plot.plot_identifier[:2])
                self.location = 'clinic'
            else:
                self.plot_identifier = self.plot.plot_identifier
                self.location = 'household'
            self.community = self.plot.community
            self.gps_lat_target = self.plot.gps_target_lat
            self.gps_lon_target = self.plot.gps_target_lon
            self.gps_lat_actual = self.plot.gps_lat
            self.gps_lon_actual = self.plot.gps_lon
            self.confirmed = self.plot.action
            self.gps_lat = self.plot.gps_lat
            self.gps_lon = self.plot.gps_lon
            self.time_of_day = self.plot.time_of_day
            self.update_plot_status()
        except AttributeError:
            self.plot_identifier = None
            self.community = None
            self.location = None
            self.gps_lat_target = None
            self.gps_lon_target = None
            self.gps_lat_actual = None
            self.gps_lon_actual = None
            self.confirmed = None
            self.gps_lat = None
            self.gps_lon = None
            self.time_of_day = None
            self.status = None

    def update_plot_log(self):
        self.confirmed_date = None
        self.logs = []
        self.log_dates = []
        self.log_first_date = None
        self.log_last_date = None
        self.log_status = []
        self.log_comment = 'missing plot log, values estimated.'
        if self.confirmed == CONFIRMED:
            try:
                self.confirmed_date = PlotLog.objects.filter(plot=self.plot).order_by('created')[0].created
            except IndexError:
                # if not plot log, confirmed date is the date the plot instance was last modidied.
                self.confirmed_date = self.plot.modified.date()
                print 'Warning: Missing plot log for confirmed plot {}.'.format(self.plot)
            try:
                self.logs = PlotLogEntry.objects.filter(plot_log=PlotLog.objects.get(plot=self.plot))
                self.log_dates = list(set([l.report_datetime.date() for l in self.logs] or [self.confirmed_date]))
                self.log_dates.sort()
                self.log_first_date = min(self.log_dates)
                self.log_last_date = max(self.log_dates)
                # log status defaults to ACCESSIBLE for "confirmed" plots without a log status
                self.log_status = [p.log_status.lower() for p in self.logs if p.log_status] or [ACCESSIBLE]
                for log_status in self.log_status:
                    if log_status not in [c[0] for c in PLOT_LOG_STATUS]:
                        print 'Warning: Invalid plot log status for {}. Got {}'.format(self.plot_identifier, log_status)
                self.log_comment = None
            except (PlotLog.DoesNotExist, PlotLogEntry.DoesNotExist):
                # if no plot log or plot log entry default both the confirmed date and log status as above.
                self.logs = []
                self.log_dates = [self.confirmed_date]
                self.log_first_date = self.confirmed_date
                self.log_last_date = self.confirmed_date
                self.log_status = [ACCESSIBLE]
                self.log_comment = 'missing plot log, values estimated.'

    def update_households(self):
        self.households = Household.objects.filter(plot=self.plot)
        self.household_structures = HouseholdStructure.objects.filter(
            household__plot=self.plot).order_by('survey__survey_slug')
        self.household_identifiers = [h.household_identifier for h in self.households]
        self.household_count = self.households.count()

    def update_members(self):
        self.household_members = HouseholdMember.objects.filter(household_structure__household__plot=self.plot)
        self.enumerated = True if self.household_members.count() > 0 else None
        for index, survey_abbrev in enumerate(self.survey.survey_abbrevs):
            attr_suffix = survey_abbrev
            fieldattrs = [('member_count', 'member_count'),
                          ('members_eligible', 'members_eligible')]
            attrs = {
                'member_count': self.household_members.filter(
                    household_structure__survey__survey_slug=self.survey.survey_slugs[index]).count(),
                'members_eligible': self.household_members.filter(
                    household_structure__survey__survey_slug=self.survey.survey_slugs[index], eligible_member=True).count()}
            self.denormalize(attr_suffix, fieldattrs, instance=type('Instance', (object, ), attrs))

    def check_plot_enrollment(self):
        if self.plot:
            if not SubjectConsent.objects.filter(household_member__household_structure__household__plot=self.plot).exists():
                if self.enrolled or not self.htc_plot:
                    print ('Warning! Plot {} ({}) is not Enrolled. Expected HTC=True. Got bhs={}, htc={}'
                           ).format(self.plot.plot_identifier, self.random_selection, self.bhs_plot, self.htc_plot)
            for _ in SubjectConsent.objects.filter(household_member__household_structure__household__plot=self.plot):
                if not self.enrolled or self.htc_plot:
                    print ('Warning! Expected plot {} ({}) is Enrolled. Expected BHS=True.Got bhs={}, htc={}'
                           ).format(self.plot.plot_identifier, self.random_selection, self.bhs_plot, self.htc_plot)
            if self.replaced_by and self.enrolled:
                print ('Warning: Replaced plot {} ({}) is Enrolled, Got bhs={}, htc={}'
                       ).format(self.plot_identifier, self.random_selection, self.bhs_plot, self.htc_plot)
