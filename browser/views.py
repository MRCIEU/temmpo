from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView

from browser.forms import (AbstractFileUploadForm, ExposureForm, MediatorForm,
                           OutcomeForm, FilterForm)
from browser.models import SearchCriteria, SearchResult, MeshTerm


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


class SearchView(CreateView):
    form_class = AbstractFileUploadForm
    template_name = "search.html"

    def get_success_url(self):
        # This should redirect to newly create search criteria tied to
        # uploaded file
        # Create a new SearchCriteria object
        print "SEARCH VIEW"
        self.search_criteria = SearchCriteria(upload=self.object)
        self.search_criteria.save()
        return reverse('exposure-selector',
                       kwargs={'pk': self.search_criteria.id})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the search form
        """
        return super(SearchView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['criteria'] = SearchCriteria.objects.filter(upload__user_id=self.request.user.id).order_by('-created')
        return context

    def get_initial(self):
        return {'user': self.request.user}

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super(SearchView, self).form_valid(form)


class TermSelectorAbstractUpdateView(UpdateView):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the form
        """
        self.tree_number = kwargs.get('tree_number', None)
        return super(TermSelectorAbstractUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Sub class should define type, term_selector_url,
            term_selector_by_family_url """

        context = super(TermSelectorAbstractUpdateView, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['root_nodes'] = MeshTerm.objects.root_nodes()
        if self.tree_number:
            context['selected_tree_root_node'] = get_object_or_404(context['root_nodes'], tree_number=self.tree_number)   # TODO Selecting could be based on person preferences
            context['nodes'] = context['selected_tree_root_node'].get_descendants(include_self=False)

        return context


class ExposureSelector(TermSelectorAbstractUpdateView):

    template_name = "term_selector.html"
    form_class = ExposureForm
    model = SearchCriteria

    def get_success_url(self):
        return reverse('mediator-selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(ExposureSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select an exposure'
        context['type'] = 'Exposure'
        context['term_selector_by_family_url'] = 'exposure-selector-by-family'

        return context

#    def form_valid(self, form):
#        print form.cleaned_data
#        self.object = form.save(commit=False)
#        for person in form.cleaned_data['members']:
#            membership = Membership()
#            membership.group = self.object
#            membership.person = person
#            membership.save()
#        return super(ModelFormMixin, self).form_valid(form)


class MediatorSelector(TermSelectorAbstractUpdateView):

    template_name = "term_selector.html"
    form_class = MediatorForm
    model = SearchCriteria

    def get_success_url(self):
        return reverse('outcome-selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(MediatorSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select a mediator'
        context['type'] = 'Mediator'
        context['term_selector_by_family_url'] = 'outcome-selector-by-family'
        return context


class OutcomeSelector(TermSelectorAbstractUpdateView):

    template_name = "term_selector.html"
    form_class = OutcomeForm
    model = SearchCriteria

    def get_success_url(self):
        return reverse_lazy('filter-selector', kwargs={'pk': self.search_result.id})

    def get_context_data(self, **kwargs):
        context = super(OutcomeSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select an outcome'
        context['type'] = 'Outcome'
        context['term_selector_by_family_url'] = 'outcome-selector-by-family'
        return context

    def form_valid(self, form):
        # Create a new SearchResult object
        # TODO test
        print "OutcomeSelector:form_valid"
        print "self.object", self.object
        print "self.form.instance"
        self.search_result = SearchResult(criteria=form.instance)
        self.search_result.save()

        result = super(OutcomeSelector, self).form_valid(form)
        return result


class SearchExisting(RedirectView):
    """Create new search criteria based on existing one and pass to
       ExposureSelector view """
    permanant = False

    def get_redirect_url(self, *args, **kwargs):
        criteria = get_object_or_404(SearchCriteria, pk=kwargs['pk'])
        criteria.pk = None
        criteria.save()
        return reverse('exposure-selector', kwargs={'pk': criteria.pk})


class FilterSelector(UpdateView):
    template_name = "filter_selector.html"
    form_class = FilterForm
    model = SearchResult

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the search form
        """
        return super(FilterSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FilterSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select a filter'
        context['active'] = 'search'
        return context

    def get_success_url(self):
        return reverse('results', kwargs={'pk': self.object.id})


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

        # TODO flesh out results object

        context['mesh_term_filter'] = 'Human'
        context['article_count'] = 17217
        context['json_url'] = '/static/js/Human_topresults_v5.csv.json'
        # TODO TBC: group by mediator
        context['mediators'] = ['ATM'] # Gene or mediator mesh
        context['results'] = [{'exposure':'Diary Products', 'lcount': '5', 'mediator':'IL6', 'outcome':'Prostatic Neoplasms', 'rcount': '1', 'count':'1'},
                              {'exposure':'Diarying', 'lcount': '46', 'mediator':'IL6', 'outcome':'Prostatic Neoplasms', 'rcount': '2', 'count': '55'},
                              {'exposure':'Recombinant Proteins AND Growth Hormone AND Cattle', 'lcount': '...', 'mediator':'PROC', 'outcome':'Prostatic Neoplasms', 'rcount': '...', 'count': '6'}, ]
        return context


class ResultsListingView(ListView):
    """ TODO: Convert to a ListView """
    template_name = "results_listing.html"
    context_object_name = "results"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
         """ Ensure user logs in before viewing the results listing page
         """
         return super(ResultsListingView, self).dispatch(request, *args, **kwargs)

#    def get_context_data(self, **kwargs):
#        context = super(ResultsListingView, self).get_context_data(**kwargs)
#        context['results'] = SearchResult.objects.filter(criteria__upload__user = self.request.user)
#
#        #Application.objects.filter(status='IP', principle_investigator=self.request.user
#        context['active'] = 'results'
#
#        return context

    def get_queryset(self):
        print SearchResult.objects.filter(criteria__upload__user = self.request.user)
        return SearchResult.objects.filter(criteria__upload__user = self.request.user)

#class ResultsListingView(TemplateView):
#    """ TODO: Convert to a ListView """
#    template_name = "results_listing.html"
#
#    @method_decorator(login_required)
#    def dispatch(self, request, *args, **kwargs):
#         """ Ensure user logs in before viewing the results listing page
#         """
#         return super(ResultsListingView, self).dispatch(request, *args, **kwargs)
#
#    def get_context_data(self, **kwargs):
#        context = super(ResultsListingView, self).get_context_data(**kwargs)
#        context['active'] = 'results'
#
#        return context
