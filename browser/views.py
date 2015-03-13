from django.views.generic.base import TemplateView  # , DetailView
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
# from django.views.generic.list import ListView

from forms import AbstractFileUploadForm, MeshFilterSelectorForm


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['active'] = 'home'
        return context


class CreditsView(TemplateView):
    template_name = "credits.html"

    def get_context_data(self, **kwargs):
        context = super(CreditsView, self).get_context_data(**kwargs)
        context['active'] = 'credits'
        return context

class SearchView(FormView):
    form_class = AbstractFileUploadForm
    template_name = "search.html"
    success_url = reverse_lazy("term-selector")

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
         """ Ensure user logs in before viewing the search form
         """
         return super(SearchView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['active'] = 'search'
        return context


class MeshTermSelector(FormView):
    template_name = "term_selector.html"
    form_class = MeshFilterSelectorForm
    # TODO: Make this dynamically send to results page
    success_url = reverse_lazy("results", kwargs={'hash': "EXAMPLE-UUID-HERE"})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
         """ Ensure user logs in before viewing the search form
         """
         return super(MeshTermSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MeshTermSelector, self).get_context_data(**kwargs)
        context['active'] = 'search'
        return context


class ResultsView(TemplateView):
    template_name = "results.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
         """ Ensure user logs in before viewing the results pages
         """
         return super(ResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        context['active'] = 'results'
        return context


class ResultsListingView(TemplateView):
    """ TODO: Convert to a ListView """
    template_name = "results_listing.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
         """ Ensure user logs in before viewing the results listing page
         """
         return super(ResultsListingView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResultsListingView, self).get_context_data(**kwargs)
        context['active'] = 'results'
        return context
