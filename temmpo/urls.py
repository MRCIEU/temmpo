"""URL patterns for the TeMMPo applications."""

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.views.decorators.cache import cache_page
from django.views.static import serve

from browser.views import (HomeView, CreditsView, HelpView, SearchOvidMEDLINE, ResultsView,
                           SearchExisting, ResultsListingView, FilterSelector,
                           ExposureSelector, MediatorSelector, OutcomeSelector,
                           CriteriaView, CountDataView, AbstractDataView,
                           JSONDataView, SearchExistingUpload, MeshTermsAsJSON,
                           MeshTermsAllAsJSON, MeshTermSearchJSON, SelectSearchTypeView,
                           SearchPubMedView, ReuseSearchView, DeleteSearch)

urlpatterns = [

    # auto complete functionality
    url(r'^simple-autocomplete/', include('simple_autocomplete.urls', namespace='simple_autocomplete')),

    # browser app
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^credits/$', CreditsView.as_view(), name='credits'),
    url(r'^help/$', HelpView.as_view(), name='help'),
    url(r'^search/$', SelectSearchTypeView.as_view(), name='search'),
    url(r'^search/select/$', ReuseSearchView.as_view(), name='reuse_search'),
    url(r'^search/ovidmedline/$', SearchOvidMEDLINE.as_view(), name='search_ovid_medline'),
    url(r'^search/pubmed/$', SearchPubMedView.as_view(), name='search_pubmed'),
    url(r'^search/edit/(?P<pk>\d+)/$', SearchExisting.as_view(), name="edit_search"),  # Create a new search based on an existing search criteria
    url(r'^search/reuse/(?P<pk>\d+)/$', SearchExistingUpload.as_view(), name="reuse_upload"),  # Create a new search based on previously uploaded set of abstracts
    url(r'^exposure/(?P<pk>\d+)/$', ExposureSelector.as_view(), name="exposure_selector"),
    url(r'^mediator/(?P<pk>\d+)/$', MediatorSelector.as_view(), name="mediator_selector"),
    url(r'^outcome/(?P<pk>\d+)/$', OutcomeSelector.as_view(), name="outcome_selector"),
    url(r'^filter/(?P<pk>\d+)/$', FilterSelector.as_view(), name="filter_selector"),
    url(r'^results/(?P<pk>\d+)/$', ResultsView.as_view(), name='results'),
    url(r'^results/$', ResultsListingView.as_view(), name='results_listing'),
    url(r'^search-criteria/(?P<pk>\d+)/$', CriteriaView.as_view(), name='criteria'),
    url(r'^data/count/(?P<pk>\d+)/$', CountDataView.as_view(), name='count_data'),
    url(r'^data/abstracts/(?P<pk>\d+)/$', AbstractDataView.as_view(), name='abstracts_data'),
    url(r'^data/json/(?P<pk>\d+)/$', JSONDataView.as_view(), name='json_data'),
    url(r'^data/delete/(?P<pk>\d+)/$', DeleteSearch.as_view(), name='delete_data'),

    url(r'^mesh-terms-json/$', cache_page(60 * 60 * 24 * 355)(MeshTermsAllAsJSON.as_view()), name="mesh_terms_as_json"),
    url(r'^mesh_terms_search_json/$', MeshTermSearchJSON.as_view(), name="mesh_terms_search_json"),
    url(r'^mesh-terms-json-for-criteria/(?P<pk>\d+)/(?P<type>(exposure|mediator|outcome))/$', MeshTermsAsJSON.as_view(), name="mesh_terms_as_json_for_criteria"),

    # Django admin
    url(r'^admin/', include(admin.site.urls)),

    # Django user authentication
    url(r'^logout/$', LogoutView.as_view(), name="logout"),
    url(r'^', include('registration.backends.default.urls')),
    url(r'^', include('django.contrib.auth.urls')),
]

# For non Apache fronted Django development server scenarios.
if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]
