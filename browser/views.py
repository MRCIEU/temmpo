from django.shortcuts import render
from django.views.generic.base import TemplateView
# from django.views.generic.edit import FormView
# from django.views.generic.list import ListView


class HomeView(TemplateView):

    template_name = "home.html"


class CreditsView(TemplateView):

    template_name = "credits.html"


class SearchView(TemplateView):

    template_name = "search.html"


class ResultsView(TemplateView):

    template_name = "results.html"


# class ResultsListingView(TemplateView):

#     template_name = "browser/templates/results_listing.html"
