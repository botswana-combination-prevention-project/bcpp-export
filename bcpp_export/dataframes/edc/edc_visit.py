import pandas as pd
from bcpp_export import urls  # DO NOT DELETE

from bhp066.apps.bcpp_subject.models import SubjectConsent, SubjectVisit, HicEnrollment

# subject visit
qs = SubjectVisit.objects.all()
columns = qs[0].__dict__.keys()
columns.append('household_member__household_structure__household__plot__community')
columns.append('household_member__household_structure__survey__survey_slug')
columns.append('appointment__visit_definition__code')
columns.remove('_state')
columns.remove('_user_container_instance')
columns.remove('using')
columns.remove('subject_identifier')
qs = SubjectVisit.objects.values_list(*columns).all()
df_subject_visit = pd.DataFrame(list(qs), columns=columns)
df_subject_visit.rename(columns={
    'household_member__household_structure__survey__survey_slug': 'survey',
    'household_member__household_structure__household__plot__community': 'community',
    'appointment__registered_subject__subject_identifier': 'subject_identifier',
    'appointment__visit_definition__code': 'visit_code',
}, inplace=True)

# hic enrollment
qs = HicEnrollment.objects.all()
columns = qs[0].__dict__.keys()
columns.append('subject_visit__household_member__household_structure__household__plot__community')
columns.append('subject_visit__household_member__household_structure__survey__survey_slug')
columns.append('subject_visit__appointment__visit_definition__code')
columns.remove('_state')
columns.remove('_user_container_instance')
columns.remove('using')
qs = HicEnrollment.objects.values_list(*columns).all()
df_hic_enrollment = pd.DataFrame(list(qs), columns=columns)
df_hic_enrollment.rename(columns={
    'subject_visit__household_member__household_structure__household__plot__community': 'community',
    'subject_visit__household_member__household_structure__survey__survey_slug': 'survey',
    'subject_visit__appointment__visit_definition__code': 'visit_code', 'subject_visit_id': 'subject_visit',
}, inplace=True)

df = pd.merge(
    df_subject_visit,
    df_hic_enrollment.query('hic_permission == \'Yes\'')[['hic_permission', 'subject_visit']],
    left_on='id', right_on='subject_visit', how='left')
gb_hic = df.query('hic_permission == \'Yes\'')[['subject_identifier', 'survey', 'visit_code', 'community']].drop_duplicates().groupby(['community', 'survey', 'visit_code'])
df_hic = pd.DataFrame({'hic': gb_hic.size()}).reset_index()
gb_visit = df_subject_visit[['subject_identifier', 'survey', 'visit_code', 'community']].drop_duplicates().groupby(['community', 'survey', 'visit_code']).size()
df_visit = pd.DataFrame({'hh_survey': gb_visit.size()}).reset_index()
df = pd.merge(df_visit, df_hic, on=['community', 'survey', 'visit_code'], how='left')
df.to_csv('/Users/erikvw/Documents/bcpp/unoda_enrollment_with_hic.csv')
