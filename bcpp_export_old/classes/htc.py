from edc_constants.constants import NO

from bhp066.apps.bcpp_household_member.models import SubjectHtc

from .base import Base
from .member import Member
from .survey import Survey


class Htc(Base):
    def __init__(self, subject_htc, **kwargs):
        super(Htc, self).__init__(**kwargs)
        self.errors = {}
        try:
            subject_htc = SubjectHtc.objects.get(id=subject_htc)
        except SubjectHtc.DoesNotExist:
            subject_htc = subject_htc
        self.member = Member(subject_htc.household_member.internal_identifier, **kwargs)
        self.revision = self.member.household_member.revision
        self.update_from_member()
        self.update_survey(**kwargs)
        self.update_htc()

    def __repr__(self):
        return 'Htc({0.member!r})'.format(self)

    def __str__(self):
        return '{0.member!r}'.format(self)

    @property
    def unique_key(self):
        return self.internal_identifier

    def prepare_csv_data(self, delimiter=None):
        super(Htc, self).prepare_csv_data(delimiter=delimiter)
        del self.csv_data['registered_subject']
        del self.csv_data['survey']
        del self.csv_data['survey_slugs']
        del self.csv_data['survey_abbrevs']
        del self.csv_data['plot_count_all']
        del self.csv_data['member']
        for survey_abbrev in self.survey.survey_abbrevs:
            del self.csv_data['survey_name_{}'.format(survey_abbrev)]

    def update_htc(self):
        self.surveys_offered = []
        for hm in self.member.household_member.membership.members:
            if SubjectHtc.objects.filter(household_member=hm).exists():
                self.surveys_offered.append(hm.household_structure.survey.survey_abbrev.lower())
        self.surveys_offered.sort()
        attrs_to_denormalize = [
            ('report_datetime', 'offered_date'),
            ('offered', 'offered'),
            ('accepted', 'accepted'),
            ('tracking_identifier', 'tracking_identifier'),
            ('referred', 'referred'),
            ('referral_clinic', 'referral_clinic'),
        ]
        for survey_abbrev in self.survey.survey_abbrevs:
            attr_suffix = survey_abbrev
            subject_htc = self.denormalize(
                attr_suffix, attrs_to_denormalize,
                lookup_model=SubjectHtc,
                lookup_string='household_member',
                lookup_instance=self.member.household_member.membership.by_survey.get(survey_abbrev))
            if subject_htc:
                if getattr(self, 'accepted_{}'.format(survey_abbrev)) == NO:
                    setattr(self, 'refusal_reason_{}'.format(survey_abbrev), subject_htc.refusal_reason or None)
                else:
                    setattr(self, 'refusal_reason_{}'.format(survey_abbrev), None)
            else:
                setattr(self, 'refusal_reason_{}'.format(survey_abbrev), None)

    def update_survey(self, **kwargs):
        self.survey = Survey(self.community, **kwargs)
        for attr, value in self.survey.__dict__.iteritems():
            setattr(self, attr, value)

    def update_from_member(self):
        """Set attributes from the HouseholdMember class (not model) instance."""
        attrs = [
            ('age_in_years', 'age_in_years'),
            ('community', 'community'),
            ('enumeration_first_date', 'enumeration_first_date'),
            ('enumeration_last_date', 'enumeration_last_date'),
            ('gender', 'gender'),
            ('household_identifier', 'household_identifier'),
            ('internal_identifier', 'internal_identifier'),
            ('plot_identifier', 'plot_identifier'),
            ('registered_subject', 'registered_subject'),
            ('study_resident', 'study_resident'),
        ]
        for attr in attrs:
            setattr(self, attr[1], getattr(self.member, attr[0]))
