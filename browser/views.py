from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView  # , DetailView
from django.views.generic.edit import FormView, CreateView, UpdateView
# from django.views.generic.list import ListView

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
        # TODO this should direct to newly create search criteria tied to
        # uploaded file
        # Create a new SearchCriteria object
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
        return context

    def get_initial(self):
        return {'user': self.request.user}

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super(SearchView, self).form_valid(form)


class ExposureSelector(UpdateView):
    template_name = "term_selector.html"
    form_class = ExposureForm
    model = SearchCriteria

    def get_success_url(self):
        return reverse('mediator-selector', kwargs={'pk': self.object.id})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the form
        """
        self.tree_number = kwargs.get('tree_number', 'A')
        return super(ExposureSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ExposureSelector, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['type'] = 'Exposure'
        context['term_selector_by_family_url'] = 'exposure-selector-by-family'
        context['root_nodes'] = MeshTerm.objects.root_nodes()
        context['selected_node'] = get_object_or_404(context['root_nodes'], tree_number=self.tree_number)   # TODO Selecting could be based on person preferences
        context['nodes'] = context['selected_node'].get_descendants(include_self=False) # MeshTerm.objects.filter(parent=context['selected_node'])# context['selected_node'].get_descendants(include_self=True)

        return context


class MediatorSelector(UpdateView):
    template_name = "term_selector.html"
    form_class = MediatorForm
    model = SearchCriteria

    def get_success_url(self):
        return reverse('outcome-selector', kwargs={'pk': self.object.id})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the form
        """
        return super(MediatorSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MediatorSelector, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['type'] = 'Mediator'
        return context


class OutcomeSelector(UpdateView):
    template_name = "term_selector.html"
    form_class = OutcomeForm
    model = SearchCriteria

    def get_success_url(self):
        # TODO adjust to use newly created object
        return reverse('filter-selector', kwargs={'pk': self.search_result.id})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the form
        """
        return super(OutcomeSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OutcomeSelector, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['type'] = 'Outcome'
        return context

    def form_valid(self, form):
        # Create a new SearchCriteria object
        self.search_result = SearchResult(criteria=self.object)
        self.search_result.save()
        return super(OutcomeSelector, self).form_valid(form)


class SearchExisting(TemplateView):
    """TODO: Replace with CreateView/UpdateView akin to ExposureSelector """
    template_name = "term_selector.html"

    def get_context_data(self, **kwargs):
        context = super(SearchExisting, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['type'] = 'Exposure'
        return context


class FilterSelector(UpdateView):
    # TODO should be a single select version of template
    template_name = "term_selector.html"
    form_class = FilterForm
    model = SearchResult

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the search form
        """
        return super(FilterSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FilterSelector, self).get_context_data(**kwargs)
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
