# -*- coding: utf-8 -*-
# import copy
import logging
import math

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.core.urlresolvers import reverse
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView

from browser.forms import OvidMedLineFileUploadForm, PubMedFileUploadForm, TermSelectorForm, FilterForm
from browser.models import SearchCriteria, SearchResult, MeshTerm, Upload  # Gene,
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

class HelpView(TemplateView):
    template_name = "help.html"

    def get_context_data(self, **kwargs):
        context = super(HelpView, self).get_context_data(**kwargs)
        context['active'] = 'help'
        return context

class SelectSearchTypeView(TemplateView):
    template_name = "select_search_type.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the search form
        """
        return super(SelectSearchTypeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SelectSearchTypeView, self).get_context_data(**kwargs)
        context['active'] = 'search'
        return context


class ReuseSearchView(TemplateView):
    template_name = "reuse_search.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the reuse search list
        """
        return super(ReuseSearchView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReuseSearchView, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['uploads'] = Upload.objects.filter(user_id=self.request.user.id)
        context['criteria'] = SearchCriteria.objects.filter(upload__user_id=self.request.user.id).order_by('-created')
        return context


class SearchOvidMEDLINE(CreateView):
    form_class = OvidMedLineFileUploadForm
    template_name = "search.html"

    def get_success_url(self):
        # This should redirect to newly create search criteria tied to
        # uploaded file
        # Create a new SearchCriteria object
        self.search_criteria = SearchCriteria(upload=self.object)
        self.search_criteria.save()
        return reverse('exposure_selector',
                       kwargs={'pk': self.search_criteria.id})

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the search form
        """
        return super(SearchOvidMEDLINE, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SearchOvidMEDLINE, self).get_context_data(**kwargs)
        context['active'] = 'search'
        context['form_action'] = reverse('search_ovid_medline')
        context['file_type'] = "Ovid MEDLINE®"
        return context

    def get_initial(self):
        return {'user': self.request.user}

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super(SearchOvidMEDLINE, self).form_valid(form)


class SearchPubMedView(SearchOvidMEDLINE):
    form_class = PubMedFileUploadForm

    def get_context_data(self, **kwargs):
        context = super(SearchPubMedView, self).get_context_data(**kwargs)
        context['file_type'] = "PubMed MEDLINE®"
        context['form_action'] = reverse('search_pubmed')
        return context


class TermSelectorAbstractUpdateView(UpdateView):
    template_name = "term_selector.html"
    model = SearchCriteria
    form_class = TermSelectorForm
    move_type = 'progress'
    # Required implementations
    # type = None
    # def set_terms(self, node_terms)

    def get_form_kwargs(self):
        kwargs = super(TermSelectorAbstractUpdateView, self).get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['type'] = self.type
        return kwargs

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the form
        """

        # Prevent one user viewing data for another
        scid = int(kwargs['pk'])
        if SearchCriteria.objects.filter(pk=scid).exists():
            sccheck = SearchCriteria.objects.get(pk=scid)
            if not request.user.is_superuser and request.user.id != sccheck.upload.user.id:
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
        context['type'] = self.type
        context['pre_selected_term_names'] = "; ".join(self.object.get_wcrf_input_variables(self.type))
        context['json_url'] = reverse('mesh_terms_as_json_for_criteria', kwargs={'pk': self.object.id, 'type': self.type})
        context['json_search_url'] = reverse("mesh_terms_search_json")
        context['pre_selected'] = ",".join(self.object.get_form_codes(self.type))
        return context

    def form_valid(self, form):
        """Auto select any children of selected nodes
        """

        if form.is_valid():
            cleaned_data = form.cleaned_data

            if 'btn_submit' in cleaned_data:
                self.move_type = cleaned_data['btn_submit']

            if 'mesh_term_ids' in cleaned_data:
                self.set_terms(cleaned_data['mesh_term_ids'])

            return super(TermSelectorAbstractUpdateView, self).form_valid(form)


class ExposureSelector(TermSelectorAbstractUpdateView):
    type = 'exposure'

    def get_success_url(self):
        if self.move_type in ('choose', 'replace',):
            return reverse('exposure_selector', kwargs={'pk': self.object.id})
        else:
            return reverse('mediator_selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(ExposureSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select exposures'
        context['next_type'] = 'mediators'
        context['next_url'] = reverse('mediator_selector', kwargs={'pk': self.object.id})
        return context

    def set_terms(self, node_terms):
        # NB: Any selected nodes should have all children included in selected set
        self.object.exposure_terms.clear()
        self.object.exposure_terms.add(*node_terms)


class MediatorSelector(TermSelectorAbstractUpdateView):
    type = 'mediator'

    def get_success_url(self):
        if self.move_type in ('choose', 'replace',):
            return reverse('mediator_selector', kwargs={'pk': self.object.id})
        else:
            return reverse('outcome_selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(MediatorSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select mediators'

        context['next_type'] = 'outcomes'
        context['next_url'] = reverse('outcome_selector', kwargs={'pk': self.object.id})
        return context

    def set_terms(self, node_terms):
        # NB: Any selected nodes should have all children included in selected set
        self.object.mediator_terms.clear()
        self.object.mediator_terms.add(*node_terms)


class OutcomeSelector(TermSelectorAbstractUpdateView):
    type = 'outcome'

    def get_success_url(self):
        if self.move_type in ('choose', 'replace',):
            return reverse('outcome_selector', kwargs={'pk': self.object.id})
        else:
            return reverse('filter_selector', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(OutcomeSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select outcomes'
        context['next_type'] = 'Genes and Filters'
        context['next_url'] = reverse('filter_selector', kwargs={'pk': self.object.id})
        return context

    def set_terms(self, node_terms):
        # NB: Any selected nodes should have all children included in selected set
        self.object.outcome_terms.clear()
        self.object.outcome_terms.add(*node_terms)


class SearchExistingUpload(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        upload = get_object_or_404(Upload, pk=kwargs['pk'])
        criteria = SearchCriteria(upload=upload)
        criteria.save()
        return reverse('exposure_selector', kwargs={'pk': criteria.pk})


class SearchExisting(RedirectView):
    """TODO: Change to allow separate term collection reuse
       Create new search criteria based on existing one and pass to
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

        return reverse('exposure_selector', kwargs={'pk': criteria_copy.pk})


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
        if SearchCriteria.objects.filter(pk=scid).exists():
            sccheck = SearchCriteria.objects.get(pk=scid)
            if not request.user.is_superuser and request.user.id != sccheck.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(FilterSelector, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(FilterSelector, self).get_context_data(**kwargs)
        context['form_title'] = 'Select a filter'
        context['active'] = 'search'
        context['type'] = 'filter'
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
        return reverse('results_listing')


class ResultsView(TemplateView):
    template_name = "results.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ Ensure user logs in before viewing the results pages
        """

        # Prevent user viewing data for another user
        self.id = int(kwargs['pk'])
        if SearchResult.objects.filter(pk=self.id).exists():
            self.search_result = SearchResult.objects.select_related('criteria__upload').get(pk=self.id)
            if not request.user.is_superuser and request.user.id != self.search_result.criteria.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(ResultsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ResultsView, self).get_context_data(**kwargs)
        context['active'] = 'results'

        # TODO: TMMA-30 Add tabular version of results table as per PDF
        json_filename = reverse('json_data', kwargs=kwargs)
        csv_filename = reverse('count_data', kwargs=kwargs)
        context['search_result'] = self.search_result
        context['json_url'] = json_filename
        context['csv_url'] = csv_filename
        context['criteria_url'] = reverse('criteria', kwargs={'pk': self.search_result.criteria.id})
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

    def get_context_data(self, **kwargs):
        context = super(ResultsListingView, self).get_context_data(**kwargs)
        context['active'] = 'results'
        return context


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
            if not request.user.is_superuser and request.user.id != criteria.upload.user.id:
                raise PermissionDenied

        except ObjectDoesNotExist:
            raise Http404("Not found")

        return super(CriteriaView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CriteriaView, self).get_context_data(**kwargs)

        context['exposures'] = "; ".join(self.object.get_wcrf_input_variables('exposure'))
        context['mediators'] = "; ".join(self.object.get_wcrf_input_variables('mediator'))
        context['outcomes'] = "; ".join(self.object.get_wcrf_input_variables('outcome'))
        context['genes'] = ", ".join(self.object.get_wcrf_input_variables('gene'))
        context['reuse_criteria_url'] = reverse('edit_search', kwargs={'pk': self.object.id})
        context['reuse_abstract_url'] = reverse('reuse_upload', kwargs={'pk': self.object.upload.id})

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
        if SearchResult.objects.filter(pk=srid).exists():
            srcheck = SearchResult.objects.get(pk=srid)
            if not request.user.is_superuser and request.user.id != srcheck.criteria.upload.user.id:
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
        if SearchResult.objects.filter(pk=srid).exists():
            srcheck = SearchResult.objects.get(pk=srid)
            if not request.user.is_superuser and request.user.id != srcheck.criteria.upload.user.id:
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
        if SearchResult.objects.filter(pk=srid).exists():
            srcheck = SearchResult.objects.get(pk=srid)
            if not request.user.is_superuser and request.user.id != srcheck.criteria.upload.user.id:
                raise PermissionDenied
        else:
            raise Http404("Not found")

        return super(JSONDataView, self).dispatch(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        search_result = get_object_or_404(SearchResult, pk=kwargs['pk'])
        url = settings.MEDIA_URL + 'results/%s.json' % search_result.filename_stub
        return url


class MeshTermsAsJSON(TemplateView):

    def node_to_dict(self, node):
        result = {
            'id': "mtid_" + str(node.id),
            'text': node.term,
        }

        if self.selected and node in self.selected:
            result['state'] = {'selected': True}

        elif self.ancestor_ids and node.id in self.ancestor_ids:
            # Get parent nodes to be partially shaded in trees
            result['state'] = {'undetermined': True}

        if node.get_descendant_count():
            result['children'] = True

        return result

    def _get_int_id(self):
        id_part = self.requested_node_id[5:]
        result = ''
        try:
            result = int(id_part)
        except ValueError:
            raise ValidationError

        return result

    def dispatch(self, request, *args, **kwargs):

        # When selecting root nodes # is sent; otherwise node id prefixed with mtid_
        self.requested_node_id = request.GET.get('id', '#')
        self.search_criteria_id = kwargs.get('pk', None)
        self.type = kwargs.get('type', None)
        self.selected = None
        self.ancestor_ids = []

        if self.requested_node_id == '#':
            nodes = MeshTerm.objects.root_nodes()
        else:
            nodes = get_object_or_404(MeshTerm, id=self._get_int_id()).get_children()

        if self.search_criteria_id:
            sc = get_object_or_404(SearchCriteria, id=self.search_criteria_id)
            self.selected = getattr(sc, self.type + '_terms').all()
            for node in self.selected:
                self.ancestor_ids.extend(node.get_ancestors().values_list("id", flat=True))

        dicts = []
        for n in nodes:
            dicts.append(self.node_to_dict(n))

        return JsonResponse(dicts, safe=False)


class MeshTermsAllAsJSON(TemplateView):

    def recursive_node_to_dict(self, node):
        """Recursive """

        node_id = "mtid_" + str(node.id)
        result = {
            'id': node_id,
            'text': node.term,
        }

        children = [self.recursive_node_to_dict(c) for c in node.get_children()]
        if children:
            result['children'] = children

        return result

    def dispatch(self, request, *args, **kwargs):

        root_nodes = MeshTerm.objects.root_nodes()
        dicts = []
        for n in root_nodes:
            dicts.append(self.recursive_node_to_dict(n))

        return JsonResponse(dicts, safe=False)


class MeshTermSearchJSON(TemplateView):

    # def node_to_dict_with_ancestors(self, node):
    #     nodes = node.get_ancestors(ascending=True, include_self=True)
    #     chain = {}

    #     for n in nodes:
    #         link = {'id': "mtid_" + str(n.id), 'text': n.term, }
    #         if chain:
    #             link['children'] = copy.copy(chain)
    #         elif n.get_descendant_count():
    #             link['children'] = True
    #         chain = link

    #     return chain

    def dispatch(self, request, *args, **kwargs):
        search_term = request.GET.get("str", "").strip()
        results = []
        if search_term:
            root_nodes = MeshTerm.objects.filter(term__istartswith=search_term)
            for n in root_nodes:
                results.extend(n.get_ancestors(include_self=True).values_list("id", flat=True))  # self.node_to_dict_with_ancestors(n)

        results = ["mtid_%d" % x for x in results]
        return JsonResponse(results, safe=False)
