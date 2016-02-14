from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.db.models import get_models
from django.views.generic import RedirectView

import django_databrowse

from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from edc.data_manager.classes import data_manager
from edc.dashboard.section.classes import site_sections
from edc.lab.lab_profile.classes import site_lab_profiles
from edc.dashboard.subject.views import additional_requisition
from edc.map.classes import site_mappers
from edc.subject.lab_tracker.classes import site_lab_tracker
from edc.subject.rule_groups.classes import site_rule_groups
from edc.subject.visit_schedule.classes import site_visit_schedules

from bhp066.apps.bcpp_household.mappers.central_server_mapper import CentralServerMapper
from bhp066.apps.bcpp.app_configuration.classes import bcpp_app_configuration

site_lab_profiles.autodiscover()
site_mappers.autodiscover()
# bcpp_app_configuration.prepare()
# site_visit_schedules.autodiscover()
# site_visit_schedules.build_all()
# site_rule_groups.autodiscover()
# site_lab_tracker.autodiscover()
# data_manager.prepare()
# site_sections.autodiscover()
# site_sections.update_section_lists()
admin.autodiscover()

site_mappers.registry['digawana'] = {}

site_mappers.get_current_mapper().verify_survey_dates()

for model in get_models():
    try:
        django_databrowse.site.register(model)
    except:
        pass

APP_NAME = 'bcpp_export'

urlpatterns = patterns(
    '',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/logout/$', RedirectView.as_view(url='/{app_name}/logout/'.format(app_name=APP_NAME))),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
