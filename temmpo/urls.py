from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.decorators.cache import cache_page

# browser app dependencies TODO: Clean up if not used with TMMA-68
import autocomplete_light
autocomplete_light.autodiscover()

from browser.views import (HomeView, CreditsView, SearchView, ResultsView,
                           SearchExisting, ResultsListingView, FilterSelector,
                           ExposureSelector, MediatorSelector, OutcomeSelector,
                           CriteriaView, CountDataView, AbstractDataView,
                           JSONDataView, SearchExistingUpload, MeshTermsAsJSON,
                           MeshTermsAllAsJSON, MeshTermSearchJSON)

urlpatterns = patterns('',
    # autocomplete_light
    url(r'^autocomplete/', include('autocomplete_light.urls')),

    # browser app
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^credits/$', CreditsView.as_view(), name='credits'),
    url(r'^search/$', SearchView.as_view(), name='search'), # Upload new abstract set
    url(r'^search/edit/(?P<pk>\d+)/$', SearchExisting.as_view(), name="edit-search"), # Create a new search based on an existing search criteria
    url(r'^search/reuse/(?P<pk>\d+)/$', SearchExistingUpload.as_view(), name="reuse-upload"), # Create a new search based on previously uploaded set of abstracts
    url(r'^exposure/(?P<pk>\d+)/$', ExposureSelector.as_view(), name="exposure-selector"),
    url(r'^exposure/(?P<pk>\d+)/(?P<tree_number>\w+)/$', ExposureSelector.as_view(), name="exposure-selector-by-family"),
    url(r'^mediator/(?P<pk>\d+)/$', MediatorSelector.as_view(), name="mediator-selector"),
    url(r'^mediator/(?P<pk>\d+)/(?P<tree_number>\w+)/$', MediatorSelector.as_view(), name="mediator-selector-by-family"),
    url(r'^outcome/(?P<pk>\d+)/$', OutcomeSelector.as_view(), name="outcome-selector"),
    url(r'^outcome/(?P<pk>\d+)/(?P<tree_number>\w+)/$', OutcomeSelector.as_view(), name="outcome-selector-by-family"),
    url(r'^filter/(?P<pk>\d+)/$', FilterSelector.as_view(), name="filter-selector"),
    url(r'^results/(?P<pk>\d+)/$', ResultsView.as_view(), name='results'),
    url(r'^results/$', ResultsListingView.as_view(), name='results-listing'),
    url(r'^search-criteria/(?P<pk>\d+)/$', CriteriaView.as_view(), name='criteria'),
    url(r'^data/count/(?P<pk>\d+)/$', CountDataView.as_view(), name='count-data'),
    url(r'^data/abstracts/(?P<pk>\d+)/$', AbstractDataView.as_view(), name='abstracts-data'),
    url(r'^data/json/(?P<pk>\d+)/$', JSONDataView.as_view(), name='json-data'),

    url(r'^mesh-terms-json/$', cache_page(60 * 60 * 24 * 355)(MeshTermsAllAsJSON.as_view()), name="mesh-terms-as-json"),
    url(r'^mesh-terms-search-json/$', MeshTermSearchJSON.as_view(), name="mesh-terms-search-json"),
    url(r'^mesh-terms-json-for-criteria/(?P<pk>\d+)/(?P<type>(exposure|mediator|outcome))/$', MeshTermsAsJSON.as_view(), name="mesh-terms-as-json-for-criteria"),

    # Django admin
    url(r'^admin/', include(admin.site.urls)),

    # Django user authentication
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name="logout"),
    url(r'^', include('registration.backends.default.urls')),
    url(r'^', include('django.contrib.auth.urls')),
)

urlpatterns += patterns('',
                        (r'^media/(?P<path>.*)$',
                         'django.views.static.serve',
                         {'document_root': settings.MEDIA_ROOT}),
                        )
# ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
