import datetime
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from browser.forms import (AbstractFileUploadForm, ExposureForm, MediatorForm,
                           OutcomeForm, FilterForm)
from browser.models import SearchCriteria, SearchResult, MeshTerm, Gene, Upload
from browser.matching import perform_search

logger = logging.getLogger(__name__)


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
        context['uploads'] = Upload.objects.filter(user_id=self.request.user.id)
        context['criteria'] = SearchCriteria.objects.filter(upload__user_id=self.request.user.id).order_by('-created')
        return context

    def get_initial(self):
        return {'user': self.request.user}

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super(SearchView, self).form_valid(form)


class MeshTermListByFamily(TemplateView):

    template_name = "term_selector_trimmed.html"

    def get_context_data(self, **kwargs):
        """ Sub class should define type, term_selector_url,
            term_selector_by_family_url """

        tree_number = kwargs.get('tree_number', None)
        context = super(MeshTermListByFamily, self).get_context_data(**kwargs)
        context['selected_tree_root_node'] = get_object_or_404(MeshTerm, tree_number=tree_number)
        context['nodes'] = context['selected_tree_root_node'].get_descendants(include_self=False)

        return context


class TermSelectorAbstractUpdateView(UpdateView):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the form
        """

        # Prevent one user viewing data for another
        scid = int(kwargs['pk'])
        if SearchCriteria.objects.filter(pk = scid).exists():
            sccheck = SearchCriteria.objects.get(pk = scid)
            if request.user.id != sccheck.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        self.tree_number = kwargs.get('tree_number', None)
        return super(TermSelectorAbstractUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ Sub class should define type, term_selector_url,
            term_selector_by_family_url """

        context = super(TermSelectorAbstractUpdateView, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['root_nodes'] = MeshTerm.objects.root_nodes()
        if self.tree_number:
            context['selected_tree_root_node'] = get_object_or_404(context['root_nodes'], tree_number=self.tree_number)
            context['selected_tree_root_node_id'] = context['selected_tree_root_node'].pk
            context['selected_tree_html_file_name']="includes/mesh-terms-"+self.tree_number+".html"
            # context['nodes'] = context['selected_tree_root_node'].get_descendants(include_self=False)
        return context


class ExposureSelector(TermSelectorAbstractUpdateView):

    template_name = "term_selector.html"
    form_class = ExposureForm
    model = SearchCriteria
    move_type = 'progress'

    def get_success_url(self):
        if self.move_type == 'choose':
            return reverse('exposure-selector', kwargs={'pk': self.object.id})
        else:
            return reverse('mediator-selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(ExposureSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select Exposures'
        context['type'] = 'Exposure'
        context['next_type'] = 'Mediators'
        context['term_selector_by_family_url'] = 'exposure-selector-by-family'
        context['pre_selected'] = ",".join(self.object.get_form_codes('exposure'))
        context['next_url'] = reverse('mediator-selector', kwargs={'pk': self.object.id})
        context['pre_selected_term_names'] = ", ".join(self.object.get_wcrf_input_variables('exposure'))

        return context

    def form_valid(self, form):
        # Store mapping
        if form.is_valid():
            cleaned_data = form.cleaned_data

            if 'btn_submit' in cleaned_data:
                self.move_type = cleaned_data['btn_submit']

            if 'term_data' in cleaned_data:
                search_criteria = self.object
                search_criteria.save()

                # Get root node
                root_node_id = cleaned_data['selected_tree_root_node_id']
                root_node = MeshTerm.objects.get(pk = root_node_id)

                # Need to handle data that's been removed
                orig_terms = search_criteria.get_form_codes('exposure')
                all_node_terms = cleaned_data['term_data'].split(',')
                # Terms that are for this node and were previously present
                same_terms = list(set(orig_terms) & set(all_node_terms))
                # Terms that were present but don't include new terms requested
                different_terms = list(set(orig_terms) - set(all_node_terms))
                # Terms for this node we had before - new request
                to_add = list(set(same_terms) - set(all_node_terms))

                #print "Adding", to_add

                for potential_term in different_terms:
                    # Term could still be present but part of this parent node
                    # so need to remove it
                    term_id = int(potential_term[5:])
                    test_term = MeshTerm.objects.get(pk = term_id)

                    if test_term.get_root() == root_node:
                        # Item has been deselected
                        #print "removing", test_term
                        search_criteria.exposure_terms.remove(test_term)

                for mesh_term_id in all_node_terms:
                    term_id = int(mesh_term_id[5:])

                    mesh_term = MeshTerm.objects.get(pk = term_id)
                    search_criteria.exposure_terms.add(mesh_term)

            #print search_result.id, search_result.criteria.id, search_result.criteria.exposure_terms.all()
            return super(ExposureSelector, self).form_valid(form)


class MediatorSelector(TermSelectorAbstractUpdateView):

    template_name = "term_selector.html"
    form_class = MediatorForm
    model = SearchCriteria
    move_type = 'progress'

    def get_success_url(self):
        if self.move_type == 'choose':
            return reverse('mediator-selector', kwargs={'pk': self.object.id})
        else:
            return reverse('outcome-selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(MediatorSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select Mediators'
        context['type'] = 'Mediator'
        context['next_type'] = 'Outcomes'
        context['term_selector_by_family_url'] = 'mediator-selector-by-family'
        context['pre_selected'] = ",".join(self.object.get_form_codes('mediator'))
        context['next_url'] = reverse('outcome-selector', kwargs={'pk': self.object.id})
        context['pre_selected_term_names'] = ", ".join(self.object.get_wcrf_input_variables('mediator'))
        return context

    def form_valid(self, form):
        # Store mapping
        if form.is_valid():
            cleaned_data = form.cleaned_data

            if 'btn_submit' in cleaned_data:
                self.move_type = cleaned_data['btn_submit']

            if 'term_data' in cleaned_data:
                search_criteria = self.object
                search_criteria.save()

                # Get root node
                root_node_id = cleaned_data['selected_tree_root_node_id']
                root_node = MeshTerm.objects.get(pk = root_node_id)

                # Need to handle data that's been removed
                orig_terms = search_criteria.get_form_codes('mediator')
                all_node_terms = cleaned_data['term_data'].split(',')
                # Terms that are for this node and were previously present
                same_terms = list(set(orig_terms) & set(all_node_terms))
                # Terms that were present but don't include new terms requested
                different_terms = list(set(orig_terms) - set(all_node_terms))
                # Terms for this node we had before - new request
                to_add = list(set(same_terms) - set(all_node_terms))

                #print "Adding", to_add

                for potential_term in different_terms:
                    # Term could still be present but part of this parent node
                    # so need to remove it
                    term_id = int(potential_term[5:])
                    test_term = MeshTerm.objects.get(pk = term_id)

                    if test_term.get_root() == root_node:
                        # Item has been deselected
                        #print "removing", test_term
                        search_criteria.mediator_terms.remove(test_term)

                for mesh_term_id in all_node_terms:
                    term_id = int(mesh_term_id[5:])

                    mesh_term = MeshTerm.objects.get(pk = term_id)
                    search_criteria.mediator_terms.add(mesh_term)

            return super(MediatorSelector, self).form_valid(form)


class OutcomeSelector(TermSelectorAbstractUpdateView):

    template_name = "term_selector.html"
    form_class = OutcomeForm
    model = SearchCriteria
    move_type = 'progress'

    def get_success_url(self):
        if self.move_type == 'choose':
            return reverse('outcome-selector', kwargs={'pk': self.object.id})
        else:
            return reverse('filter-selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(OutcomeSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select Outcomes'
        context['type'] = 'Outcome'
        context['next_type'] = 'Genes and Filters'
        context['term_selector_by_family_url'] = 'outcome-selector-by-family'
        context['pre_selected'] = ",".join(self.object.get_form_codes('outcome'))
        context['next_url'] = reverse('filter-selector', kwargs={'pk': self.object.id})
        context['pre_selected_term_names'] = ", ".join(self.object.get_wcrf_input_variables('outcome'))

        return context

    def form_valid(self, form):
        # Store mapping
        if form.is_valid():

            cleaned_data = form.cleaned_data

            if 'btn_submit' in cleaned_data:
                self.move_type = cleaned_data['btn_submit']

            if 'term_data' in cleaned_data:
                search_criteria = self.object
                search_criteria.save()

                # Get root node
                root_node_id = cleaned_data['selected_tree_root_node_id']
                root_node = MeshTerm.objects.get(pk = root_node_id)

                # Need to handle data that's been removed
                orig_terms = search_criteria.get_form_codes('outcome')
                all_node_terms = cleaned_data['term_data'].split(',')
                # Terms that are for this node and were previously present
                same_terms = list(set(orig_terms) & set(all_node_terms))
                # Terms that were present but don't include new terms requested
                different_terms = list(set(orig_terms) - set(all_node_terms))
                # Terms for this node we had before - new request
                to_add = list(set(same_terms) - set(all_node_terms))

                #print "Adding", to_add

                for potential_term in different_terms:
                    # Term could still be present but part of this parent node
                    # so need to remove it
                    term_id = int(potential_term[5:])
                    test_term = MeshTerm.objects.get(pk = term_id)

                    if test_term.get_root() == root_node:
                        # Item has been deselected
                        #print "removing", test_term
                        search_criteria.outcome_terms.remove(test_term)

                for mesh_term_id in all_node_terms:
                    term_id = int(mesh_term_id[5:])

                    mesh_term = MeshTerm.objects.get(pk = term_id)
                    search_criteria.outcome_terms.add(mesh_term)

            #print search_result.id, search_result.criteria.id, search_result.criteria.outcome_terms.all()
            return super(OutcomeSelector, self).form_valid(form)


class SearchExistingUpload(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        upload = get_object_or_404(Upload, pk=kwargs['pk'])
        criteria = SearchCriteria(upload=upload)
        criteria.save()
        return reverse('exposure-selector', kwargs={'pk': criteria.pk})


class SearchExisting(RedirectView):
    """Create new search criteria based on existing one and pass to
       ExposureSelector view """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """ Copy across existing search criteria and allow user to amend """
        original_criteria = get_object_or_404(SearchCriteria, pk=kwargs['pk'])

        # NB: Need to deep copy to ensure Many to Many relationship is captured
        criteria_copy = SearchCriteria(upload=original_criteria.upload)
        criteria_copy.save()
        criteria_copy.genes = original_criteria.genes.all()
        criteria_copy.exposure_terms = original_criteria.exposure_terms.all()
        criteria_copy.outcome_terms = original_criteria.outcome_terms.all()
        criteria_copy.mediator_terms = original_criteria.mediator_terms.all()
        criteria_copy.save()

        return reverse('exposure-selector', kwargs={'pk': criteria_copy.pk})


class FilterSelector(UpdateView):
    template_name = "filter_selector.html"
    form_class = FilterForm
    model = SearchCriteria

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the form
        """

        # Prevent one user viewing data for another
        scid = int(kwargs['pk'])
        if SearchCriteria.objects.filter(pk = scid).exists():
            sccheck = SearchCriteria.objects.get(pk = scid)
            if request.user.id != sccheck.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(FilterSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FilterSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select a filter'
        context['active'] = 'search'
        return context

    def form_valid(self, form):
        """Store genes and filter"""

        # Save genes to search criteria
        form.save()

        # Create search result object and save mesh filter term
        search_result = SearchResult(criteria=self.object)
        mesh_filter = form.cleaned_data['mesh_filter']
        search_result.mesh_filter = mesh_filter
        search_result.save()

        # Run the search
        perform_search(search_result.id)

        return super(FilterSelector, self).form_valid(form)

    def get_success_url(self):
        return reverse('results-listing')


class ResultsView(TemplateView):
    template_name = "results.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the results pages
        """

        # Prevent user viewing data for another user
        srid = int(kwargs['pk'])
        if SearchResult.objects.filter(pk = srid).exists():
            srcheck = SearchResult.objects.get(pk = srid)
            if request.user.id != srcheck.criteria.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(ResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        context['active'] = 'results'

        # TODO: TMMA-30 Add tabular version of results table as per PDF
        json_filename = reverse('json-data', kwargs=kwargs)
        context['json_url'] = json_filename
        return context


class ResultsListingView(ListView):
    template_name = "results_listing.html"
    context_object_name = "results"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the results listing page
        """
        return super(ResultsListingView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return SearchResult.objects.filter(criteria__upload__user=self.request.user)


class CriteriaView(DetailView):
    template_name = "criteria.html"
    model = SearchCriteria

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing
        """
        # Prevent user viewing data for another user
        criteria_id = int(kwargs['pk'])
        try:
            criteria = SearchCriteria.objects.get(pk=criteria_id)
            if request.user.id != criteria.upload.user.id:
                raise PermissionDenied

        except ObjectDoesNotExist:
            raise Http404("Not found")

        return super(CriteriaView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CriteriaView, self).get_context_data(**kwargs)

        context['exposures'] = ", ".join(self.object.get_wcrf_input_variables('exposure'))
        context['mediators'] = ", ".join(self.object.get_wcrf_input_variables('mediator'))
        context['outcomes'] = ", ".join(self.object.get_wcrf_input_variables('outcome'))
        context['genes'] = ", ".join(self.object.get_wcrf_input_variables('gene'))
        context['url'] = reverse('edit-search', kwargs={'pk': self.object.id})

        return context


class CountDataView(RedirectView):
    permanent = True
    query_string = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing
        """
        # Prevent user viewing data for another user
        # Pretty dirty but OK for now...
        srid = int(kwargs['pk'])
        if SearchResult.objects.filter(pk = srid).exists():
            srcheck = SearchResult.objects.get(pk = srid)
            if request.user.id != srcheck.criteria.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(CountDataView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        search_result = get_object_or_404(SearchResult, pk=kwargs['pk'])
        url = settings.MEDIA_URL + 'results/%s_edge.csv' % search_result.filename_stub
        return url


class AbstractDataView(RedirectView):
    permanent = True
    query_string = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing
        """
        # Prevent user viewing data for another user
        # Pretty dirty but OK for now...
        srid = int(kwargs['pk'])
        if SearchResult.objects.filter(pk = srid).exists():
            srcheck = SearchResult.objects.get(pk = srid)
            if request.user.id != srcheck.criteria.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(AbstractDataView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        search_result = get_object_or_404(SearchResult, pk=kwargs['pk'])
        url = settings.MEDIA_URL + 'results/%s_abstracts.csv' % search_result.filename_stub
        return url


class JSONDataView(RedirectView):
    permanent = True
    query_string = False

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing
        """
        # Prevent user viewing data for another user
        # Pretty dirty but OK for now...
        srid = int(kwargs['pk'])
        if SearchResult.objects.filter(pk = srid).exists():
            srcheck = SearchResult.objects.get(pk = srid)
            if request.user.id != srcheck.criteria.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(JSONDataView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        search_result = get_object_or_404(SearchResult, pk=kwargs['pk'])
        url = settings.MEDIA_URL + 'results/%s.json' % search_result.filename_stub
        return url
