from django.conf.urls import patterns, include
from django.contrib import admin
from django.views.generic import RedirectView

from edc.lab.lab_profile.classes import site_lab_profiles
from edc.map.classes import site_mappers
from bhp066.apps.bcpp_household.mappers.central_server_mapper import CentralServerMapper
from bhp066.apps.bcpp.app_configuration.classes import bcpp_app_configuration

site_lab_profiles.autodiscover()
site_mappers.autodiscover()
admin.autodiscover()

site_mappers.registry['digawana'] = {}
site_mappers.get_current_mapper().verify_survey_dates()

APP_NAME = 'bcpp_export'

urlpatterns = patterns(
    '',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/logout/$', RedirectView.as_view(url='/{app_name}/logout/'.format(app_name=APP_NAME))),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
