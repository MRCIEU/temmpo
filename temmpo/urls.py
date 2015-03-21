from django.conf.urls import patterns, include, url
from django.contrib import admin

from browser.views import (HomeView, CreditsView, SearchView, ResultsView,
                           SearchExisting, ResultsListingView, FilterSelector,
                           ExposureSelector, MediatorSelector, OutcomeSelector)

urlpatterns = patterns('',
    # browser app
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^credits/$', CreditsView.as_view(), name='credits'),
    url(r'^search/$', SearchView.as_view(), name='search'), # Upload new abstract set
    url(r'^exposure/(?P<pk>\d+)/$', ExposureSelector.as_view(), name="exposure-selector"),
    url(r'^exposure/(?P<pk>\d+)/(?P<tree_number>\w+)/$', ExposureSelector.as_view(), name="exposure-selector-by-family"),
    url(r'^mediator/(?P<pk>\d+)/$', MediatorSelector.as_view(), name="mediator-selector"),
    url(r'^mediator/(?P<pk>\d+)/(?P<tree_number>\w+)/$', MediatorSelector.as_view(), name="mediator-selector-by-family"),
    url(r'^outcome/(?P<pk>\d+)/$', OutcomeSelector.as_view(), name="outcome-selector"),
    url(r'^outcome/(?P<pk>\d+)/(?P<tree_number>\w+)/$', OutcomeSelector.as_view(), name="outcome-selector-by-family"),
    url(r'^filter/(?P<pk>\d+)/$', FilterSelector.as_view(), name="filter-selector"),
    url(r'^search/edit/(?P<pk>\d+)/$', SearchExisting.as_view(), name="edit-search"), # Create a new search based on an existing abstract set
    url(r'^results/(?P<pk>\d+)/$', ResultsView.as_view(), name='results'),
    url(r'^results/$', ResultsListingView.as_view(), name='results-listing'),

    # Django admin
    url(r'^admin/', include(admin.site.urls)),

    # Django user authentication
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name="logout"),
    url(r'^', include('registration.backends.default.urls')),
    url(r'^', include('django.contrib.auth.urls')),
)
