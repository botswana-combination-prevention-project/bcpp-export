from django.conf.urls import patterns, include
from django.contrib import admin
from django.views.generic import RedirectView

from edc.lab.lab_profile.classes import site_lab_profiles
from edc.map.classes import site_mappers

site_lab_profiles.autodiscover()
site_mappers.autodiscover()
admin.autodiscover()

# site_mappers.get_current_mapper().verify_survey_dates()

APP_NAME = 'bcpp_export'

urlpatterns = patterns(
    '',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/logout/$', RedirectView.as_view(url='/{app_name}/logout/'.format(app_name=APP_NAME))),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
)
