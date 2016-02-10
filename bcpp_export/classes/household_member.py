from django.core.exceptions import MultipleObjectsReturned
from edc.subject.registration.models import RegisteredSubject
from bhp066.apps.bcpp_household_member.models import HouseholdMember as HouseholdMemberModel
from bhp066.apps.bcpp_export.classes.survey import Survey

from .base import Base
from .membership import Membership


class HouseholdMember(Base):
    """A wrapper class for Household Member.

    Use Member for more detail."""
    def __init__(self, household_member, **kwargs):
        """Allows None for attribute inspection."""
        super(HouseholdMember, self).__init__(**kwargs)
        try:
            self.household_member = HouseholdMemberModel.objects.get(internal_identifier=household_member)
        except MultipleObjectsReturned:
            self.household_member = HouseholdMemberModel.objects.filter(internal_identifier=household_member).order_by('created')[0]
        except HouseholdMemberModel.DoesNotExist:
            try:
                self.household_member = HouseholdMemberModel.objects.get(id=household_member)
            except HouseholdMemberModel.DoesNotExist:
                self.household_member = household_member
        if self.household_member:
            self.age_in_years = self.household_member.age_in_years
            self.community = self.household_member.household_structure.household.plot.community
            self.eligible_member = self.household_member.eligible_member
            self.eligible_subject = self.household_member.eligible_subject
            self.enumeration_date = self.household_member.created
            self.gender = self.household_member.gender
            self.household = self.household_member.household_structure.household
            self.household_identifier = self.household_member.household_structure.household.household_identifier
            self.household_structure = self.household_member.household_structure
            self.initials = self.household_member.initials
            self.plot = self.household_member.household_structure.household.plot
            self.plot_identifier = self.household_member.household_structure.household.plot.plot_identifier
            self.revision = self.household_member.revision
            self.study_resident = self.household_member.study_resident
        else:
            self.age_in_years = None
            self.community = None
            self.eligible_member = None
            self.eligible_subject = None
            self.enumeration_date = None
            self.gender = None
            self.household = None
            self.household_identifier = None
            self.household_structure = None
            self.initials = None
            self.plot = None
            self.revision = None
            self.study_resident = None
        try:
            self.internal_identifier = self.household_member.internal_identifier
        except AttributeError:
            self.internal_identifier = None
        self.survey = Survey(self.community, **kwargs)
        self.membership = Membership(self.household_member, self.survey.survey_abbrevs)
        try:
            self.registered_subject = RegisteredSubject.objects.get(
                registration_identifier=self.internal_identifier)
        except RegisteredSubject.DoesNotExist:
            self.registered_subject = None

    def __repr__(self):
        return '{0}({1.household_member!r})'.format(self.__class__.__name__, self)

    def __str__(self):
        return '{0.household_member!s}'.format(self)

    @property
    def unique_key(self):
        return self.internal_identifier

    def prepare_csv_data(self, delimiter=None):
        super(HouseholdMember, self).prepare_csv_data(delimiter=delimiter)
        del self.csv_data['survey']
        del self.csv_data['registered_subject']
        del self.csv_data['household_structure']
        del self.csv_data['household_member']
        del self.csv_data['plot']
        del self.csv_data['household']
