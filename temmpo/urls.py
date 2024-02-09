"""URL patterns for the TeMMPo applications."""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from django.views.decorators.cache import cache_page
from django.views.static import serve

from browser.probe import ProbeView
from browser.views import (HomeView, CreditsView, HelpView, SearchOvidMEDLINE, ResultsSankeyView,
                           ResultsBubbleView, SearchExisting, ResultsListingView, FilterSelector,
                           ExposureSelector, MediatorSelector, OutcomeSelector,
                           CriteriaView, CountDataView, AbstractDataView,
                           JSONDataView, SearchExistingUpload, MeshTermsAsJSON,
                           MeshTermsAllAsJSON, MeshTermSearchJSON, SelectSearchTypeView,
                           SearchPubMedView, ReuseSearchView, DeleteSearch, UserAccountView,
                           CloseAccount, AccountClosedConfirmation, UsersListingView, DeleteUser,
                           CountDataViewV1, AbstractDataViewV1, JSONDataViewV1,
                           CountDataViewV3, AbstractDataViewV3, JSONDataViewV3,
                           MeSHTermAutocomplete, PrivacyPolicyView)

urlpatterns = [

    # browser app
    re_path(r'^$', HomeView.as_view(), name='home'),
    re_path(r'^credits/$', CreditsView.as_view(), name='credits'),
    re_path(r'^help/$', HelpView.as_view(), name='help'),
    re_path(r'^privacy/$', PrivacyPolicyView.as_view(), name="privacy"),

    re_path(r'^search/$', SelectSearchTypeView.as_view(), name='search'),
    re_path(r'^search/select/$', ReuseSearchView.as_view(), name='reuse_search'),
    re_path(r'^search/ovidmedline/$', SearchOvidMEDLINE.as_view(), name='search_ovid_medline'),
    re_path(r'^search/pubmed/$', SearchPubMedView.as_view(), name='search_pubmed'),
    re_path(r'^search/edit/(?P<pk>\d+)/$', SearchExisting.as_view(), name="edit_search"),  # Create a new search based on an existing search criteria
    re_path(r'^search/reuse/(?P<pk>\d+)/$', SearchExistingUpload.as_view(), name="reuse_upload"),  # Create a new search based on previously uploaded set of abstracts
    re_path(r'^exposure/(?P<pk>\d+)/$', ExposureSelector.as_view(), name="exposure_selector"),
    re_path(r'^mediator/(?P<pk>\d+)/$', MediatorSelector.as_view(), name="mediator_selector"),
    re_path(r'^outcome/(?P<pk>\d+)/$', OutcomeSelector.as_view(), name="outcome_selector"),
    re_path(r'^filter/(?P<pk>\d+)/$', FilterSelector.as_view(), name="filter_selector"),

    re_path(r'^mesh-terms-json/$', cache_page(60 * 60 * 24 * 355)(MeshTermsAllAsJSON.as_view()), name="mesh_terms_as_json"),
    re_path(r'^mesh_terms_search_json/$', MeshTermSearchJSON.as_view(), name="mesh_terms_search_json"),
    re_path(r'^mesh-terms-json-for-criteria/(?P<pk>\d+)/(?P<type>(exposure|mediator|outcome))/$', MeshTermsAsJSON.as_view(), name="mesh_terms_as_json_for_criteria"),

    re_path(r'^results/(?P<pk>\d+)/$', ResultsSankeyView.as_view(), name='results'),
    re_path(r'^results/bubble/(?P<pk>\d+)/$', ResultsBubbleView.as_view(), name='results_bubble'),
    re_path(r'^results/$', ResultsListingView.as_view(), name='results_listing'),

    re_path(r'^search-criteria/(?P<pk>\d+)/$', CriteriaView.as_view(), name='criteria'),

    re_path(r'^data/delete/(?P<pk>\d+)/$', DeleteSearch.as_view(), name='delete_data'),

    re_path(r'^data/v4/count/(?P<pk>\d+)/$', CountDataView.as_view(), name='count_data'),
    re_path(r'^data/v4/abstracts/(?P<pk>\d+)/$', AbstractDataView.as_view(), name='abstracts_data'),
    re_path(r'^data/v4/json/(?P<pk>\d+)/$', JSONDataView.as_view(), name='json_data'),

    re_path(r'^data/v3/count/(?P<pk>\d+)/$', CountDataViewV3.as_view(), name='count_data_v3'),
    re_path(r'^data/v3/abstracts/(?P<pk>\d+)/$', AbstractDataViewV3.as_view(), name='abstracts_data_v3'),
    re_path(r'^data/v3/json/(?P<pk>\d+)/$', JSONDataViewV3.as_view(), name='json_data_v3'),

    re_path(r'^data/v1/count/(?P<pk>\d+)/$', CountDataViewV1.as_view(), name='count_data_v1'),
    re_path(r'^data/v1/abstracts/(?P<pk>\d+)/$', AbstractDataViewV1.as_view(), name='abstracts_data_v1'),
    re_path(r'^data/v1/json/(?P<pk>\d+)/$', JSONDataViewV1.as_view(), name='json_data_v1'),

    re_path(r'^account/$', UserAccountView.as_view(), name='account'),
    re_path(r'^close-account/(?P<pk>\d+)/$', CloseAccount.as_view(), name='close_account'),
    re_path(r'^account-closed/$', AccountClosedConfirmation.as_view(), name='account_closed'),
    re_path(r'^manage-users/$', UsersListingView.as_view(), name='manage_users'),
    re_path(r'^delete-user/(?P<pk>\d+)/$', DeleteUser.as_view(), name='delete_user'),

    # Favicon
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")),
    ),

    # Probe page
    re_path(r'^probe/$',
        cache_page(15)(ProbeView.as_view()),
        name='probe'),

    # Django admin
    path('admin/', admin.site.urls),

    # Django user authentication
    re_path(r'^logout/$', LogoutView.as_view(), name="logout"),
    re_path(r'^', include('registration.backends.default.urls')),
    re_path(r'^', include('django.contrib.auth.urls')),

    # django-rq Redis backed message queue
    re_path(r'^django-rq/', include('django_rq.urls')),

    # autocomplete
    re_path(r'^meshterm-autocomplete/$', MeSHTermAutocomplete.as_view(), name='meshterm-autocomplete'),
]

# For non Apache fronted Django development server scenarios.
if not settings.USING_APACHE:

    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]

if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            re_path(r'^__debug__/', include(debug_toolbar.urls)),
        ]
