import datetime

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.http import Http404

#from django.core.management import call_command

from browser.forms import (AbstractFileUploadForm, ExposureForm, MediatorForm,
                           OutcomeForm, FilterForm)
from browser.models import SearchCriteria, SearchResult, MeshTerm, Gene
from browser.matching import perform_search

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
        
        # Prevent one user viewing data for another
        scid = int(kwargs['pk'])
        if SearchCriteria.objects.filter(pk = scid).exists():
            sccheck = SearchCriteria.objects.get(pk = scid)
            if request.user.id != sccheck.upload.user.id:
               raise Http404("Not found")
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
            context['selected_tree_root_node'] = get_object_or_404(context['root_nodes'], tree_number=self.tree_number)   # TODO Selecting could be based on person preferences
            context['selected_tree_root_node_id'] = MeshTerm.objects.get(tree_number = self.tree_number).pk
            context['nodes'] = context['selected_tree_root_node'].get_descendants(include_self=False)

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
        # This is a mess, the form model is SearchCriteria but the ID in the
        # URL is for the SearchResult
        #search_result = SearchResult.objects.get(pk = self.object.id)
        context['pre_selected'] = ",".join(self.object.get_form_codes('exposure'))

        #print self.object.id, self.object.get_form_codes('exposure')
        return context

    def form_valid(self, form):
        # Store mapping
        if form.is_valid():
            # TODO test
            #print "ExposureSelector:form_valid"
            #print "self.object", form.instance.id
            #print "self.form.instance", form.cleaned_data

            # Get search result object
            #if not SearchResult.objects.filter(pk = form.instance.id).exists():
            #    search_result = SearchResult(criteria=form.instance)
            #    search_result.save()
            #else:
            #    search_result = SearchResult.objects.get(pk = form.instance.id)
            #    search_result.save()

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

                #self.search_result = search_result
                #self.search_result.save()

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
        # This is a mess
        #search_result = SearchResult.objects.get(pk = self.object.id)
        context['pre_selected'] = ",".join(self.object.get_form_codes('mediator'))

        #print self.object.id, self.object.get_form_codes('mediator')
        return context

    def form_valid(self, form):
        # Store mapping
        if form.is_valid():
            # TODO test
            #print "MediatorSelector:form_valid"
            #print "self.object", form.instance.id
            #print "self.form.instance", form.cleaned_data

            # Get search result object
            #if not SearchResult.objects.filter(pk = form.instance.id).exists():
            #    search_result = SearchResult(criteria=form.instance)
            #    search_result.save()
            #else:
            #    search_result = SearchResult.objects.get(pk = form.instance.id)
            #    search_result.save()

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

                #self.search_result = search_result
                #self.search_result.save()

            #print search_result.id, search_result.criteria.id, search_result.criteria.mediator_terms.all()
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
            # Create search results
            if not SearchResult.objects.filter(criteria = self.object).exists():
                search_results = SearchResult(criteria=self.object)
                search_results.save()
            else:
                search_results = SearchResult.objects.get(criteria=self.object)
            return reverse('filter-selector', kwargs={'pk': search_results.id})


    def get_context_data(self, **kwargs):
        context = super(OutcomeSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select Outcomes'
        context['type'] = 'Outcome'
        context['next_type'] = 'Genes and Filters'
        context['term_selector_by_family_url'] = 'outcome-selector-by-family'
        # This is a mess
        #search_result = SearchResult.objects.get(pk = self.object.id)
        context['pre_selected'] = ",".join(self.object.get_form_codes('outcome'))

        #print self.object.id, self.object.get_form_codes('outcome')
        return context

    def form_valid(self, form):
        # Store mapping
        if form.is_valid():
            # TODO test
            #print "OutcomeSelector:form_valid"
            #print "self.object", form.instance.id
            #print "self.form.instance", form.cleaned_data

            # Get search result object
            #if not SearchResult.objects.filter(pk = form.instance.id).exists():
            #    search_result = SearchResult(criteria=form.instance)
            #    search_result.save()
            #else:
            #    search_result = SearchResult.objects.get(pk = form.instance.id)
            #    search_result.save()

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

                #self.search_result = search_result
                #self.search_result.save()

            #print search_result.id, search_result.criteria.id, search_result.criteria.outcome_terms.all()
            return super(OutcomeSelector, self).form_valid(form)



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
        
        # Prevent user viewing data for another user
        srid = int(kwargs['pk'])
        if SearchResult.objects.filter(pk = srid).exists():
            srcheck = SearchResult.objects.get(pk = srid)
            if request.user.id != srcheck.criteria.upload.user.id:
               raise Http404("Not found")
        else:
            raise Http404("Not found")
        
        return super(FilterSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FilterSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select a filter'
        context['active'] = 'search'
        return context

    def form_valid(self, form):
        # Store genes an filter
        search_result = self.object
        search_criteria = search_result.criteria

        gene_data = form.cleaned_data['genes']
        gene_list = gene_data.split(',')

        for ind_gene in gene_list:
            # Genes have already been checked at this point so we need to get
            # the gene and then add it to the results
            ind_gene = ind_gene.strip()
            this_gene = Gene.objects.get(name__iexact=ind_gene)
            search_criteria.genes.add(this_gene)

        # Set metadata
        search_result.started_processing = datetime.datetime.now()
        search_result.has_completed = False
        search_result.save()

        # Run the search
        perform_search(search_result.id)

        search_result.ended_processing = datetime.datetime.now()
        search_result.has_completed = True
        search_result.save()

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
                raise Http404("Not found")
         else:
             raise Http404("Not found")
         
         return super(ResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        context['active'] = 'results'

        # TODO flesh out results object
        context['mesh_term_filter'] = 'Human'
        context['article_count'] = 17217
        json_filename = 'results_%s_human_topresults.json' % int(kwargs['pk'])
        context['json_url'] = '/static/results/' + json_filename
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

    def get_queryset(self):
        return SearchResult.objects.filter(criteria__upload__user = self.request.user)


class CriteriaView(TemplateView):
    template_name = "criteria.html"
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
         """ Ensure user logs in before viewing
         """
         # Prevent user viewing data for another user
         srid = int(kwargs['pk'])
         if SearchResult.objects.filter(pk = srid).exists():
             srcheck = SearchResult.objects.get(pk = srid)
             if request.user.id != srcheck.criteria.upload.user.id:
                raise Http404("Not found")
         else:
             raise Http404("Not found")
             
         return super(CriteriaView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CriteriaView, self).get_context_data(**kwargs)
        
        searchresult = SearchResult.objects.get(pk = int(kwargs['pk']))
        context['result'] = searchresult
        
        context['exposures'] = ", ".join(searchresult.criteria.get_wcrf_input_variables('exposure'))
        context['mediators'] = ", ".join(searchresult.criteria.get_wcrf_input_variables('mediator'))
        context['outcomes'] = ", ".join(searchresult.criteria.get_wcrf_input_variables('outcome'))
        context['genes'] = ", ".join(searchresult.criteria.get_wcrf_input_variables('gene'))
        
        return context




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
