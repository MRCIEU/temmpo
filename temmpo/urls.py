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
    path('', HomeView.as_view(), name='home'),
    path('credits/', CreditsView.as_view(), name='credits'),
    path('help/', HelpView.as_view(), name='help'),
    path('privacy/', PrivacyPolicyView.as_view(), name="privacy"),

    path('search/', SelectSearchTypeView.as_view(), name='search'),
    path('search/select/', ReuseSearchView.as_view(), name='reuse_search'),
    path('search/ovidmedline/', SearchOvidMEDLINE.as_view(), name='search_ovid_medline'),
    path('search/pubmed/', SearchPubMedView.as_view(), name='search_pubmed'),
    path('search/edit/<int:pk>/', SearchExisting.as_view(), name="edit_search"),  # Create a new search based on an existing search criteria
    path('search/reuse/<int:pk>/', SearchExistingUpload.as_view(), name="reuse_upload"),  # Create a new search based on previously uploaded set of abstracts
    path('exposure/<int:pk>/', ExposureSelector.as_view(), name="exposure_selector"),
    path('mediator/<int:pk>/', MediatorSelector.as_view(), name="mediator_selector"),
    path('outcome/<int:pk>/', OutcomeSelector.as_view(), name="outcome_selector"),
    path('filter/<int:pk>/', FilterSelector.as_view(), name="filter_selector"),

    path('mesh-terms-json/', cache_page(60 * 60 * 24 * 355)(MeshTermsAllAsJSON.as_view()), name="mesh_terms_as_json"),
    path('mesh_terms_search_json/', MeshTermSearchJSON.as_view(), name="mesh_terms_search_json"),
    re_path(r'^mesh-terms-json-for-criteria/(?P<pk>\d+)/(?P<type>(exposure|mediator|outcome))/$', MeshTermsAsJSON.as_view(), name="mesh_terms_as_json_for_criteria"),

    path('results/<int:pk>/', ResultsSankeyView.as_view(), name='results'),
    path('results/bubble/<int:pk>/', ResultsBubbleView.as_view(), name='results_bubble'),
    path('results/', ResultsListingView.as_view(), name='results_listing'),

    path('search-criteria/<int:pk>/', CriteriaView.as_view(), name='criteria'),

    path('data/delete/<int:pk>/', DeleteSearch.as_view(), name='delete_data'),

    path('data/v4/count/<int:pk>/', CountDataView.as_view(), name='count_data'),
    path('data/v4/abstracts/<int:pk>/', AbstractDataView.as_view(), name='abstracts_data'),
    path('data/v4/json/<int:pk>/', JSONDataView.as_view(), name='json_data'),

    path('data/v3/count/<int:pk>/', CountDataViewV3.as_view(), name='count_data_v3'),
    path('data/v3/abstracts/<int:pk>/', AbstractDataViewV3.as_view(), name='abstracts_data_v3'),
    path('data/v3/json/<int:pk>/', JSONDataViewV3.as_view(), name='json_data_v3'),

    path('data/v1/count/<int:pk>/', CountDataViewV1.as_view(), name='count_data_v1'),
    path('data/v1/abstracts/<int:pk>/', AbstractDataViewV1.as_view(), name='abstracts_data_v1'),
    path('data/v1/json/<int:pk>/', JSONDataViewV1.as_view(), name='json_data_v1'),

    path('account/', UserAccountView.as_view(), name='account'),
    path('close-account/<int:pk>/', CloseAccount.as_view(), name='close_account'),
    path('account-closed/', AccountClosedConfirmation.as_view(), name='account_closed'),
    path('manage-users/', UsersListingView.as_view(), name='manage_users'),
    path('delete-user/<int:pk>/', DeleteUser.as_view(), name='delete_user'),

    # Favicon
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")),
    ),

    # Probe page
    path('probe/',
        cache_page(15)(ProbeView.as_view()),
        name='probe'),

    # Django admin
    path('admin/', admin.site.urls),

    # Django user authentication
    path('logout/', LogoutView.as_view(), name="logout"),
    path('', include('registration.backends.default.urls')),
    path('', include('django.contrib.auth.urls')),

    # django-rq Redis backed message queue
    path('django-rq/', include('django_rq.urls')),

    # autocomplete
    path('meshterm-autocomplete/', MeSHTermAutocomplete.as_view(), name='meshterm-autocomplete'),
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
            path('__debug__/', include(debug_toolbar.urls)),
        ]
