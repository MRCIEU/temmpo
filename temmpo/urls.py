from django.conf.urls import patterns, include, url
from django.contrib import admin

from browser.views import (HomeView, CreditsView, SearchView, ResultsView,
                           MeshTermSelector, ResultsListingView)

urlpatterns = patterns('',
    # browser app
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^credits/$', CreditsView.as_view(), name='credits'),
    url(r'^search/$', SearchView.as_view(), name='search'),
    url(r'^term-selector/$', MeshTermSelector.as_view(), name="term-selector"),
    url(r'^results/(?P<hash>[-\w]+)$', ResultsView.as_view(), name='results'),
    url(r'^results/$', ResultsListingView.as_view(), name='results-listing'),

    # Django admin
    url(r'^admin/', include(admin.site.urls)),
)
