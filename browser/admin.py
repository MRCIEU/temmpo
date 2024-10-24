"""Register custom models in Django admin interface for super user local UoB access only."""

from django.contrib import admin
from django.db import models
from django.forms.widgets import Textarea

from browser.models import Gene, MeshTerm, Upload, SearchCriteria, SearchResult, Message

@admin.register(Upload)
class UploadAdmin(admin.ModelAdmin):
    list_display = ('filename', 'user', )
    readonly_fields = ('user', 'abstracts_upload', 'file_format', )
    search_fields = ('user__email', 'user__username', )

@admin.register(SearchCriteria)
class SearchCriteriaAdmin(admin.ModelAdmin):
    list_display = ('created', 'upload', )
    readonly_fields = ('created', 'mesh_terms_year_of_release', 'exposure_terms',  'mediator_terms', 'outcome_terms', 'genes', )
    search_fields = ('upload__user__email', 'upload__user__username', )
    raw_id_fields = ('upload', )

@admin.register(Gene)
class GeneAdmin(admin.ModelAdmin):
    readonly_fields = ('name', 'synonym_for', )
    ordering = ('name',)
    search_fields = ('name',)

@admin.register(MeshTerm)
class MeshTermAdmin(admin.ModelAdmin):
    list_display = ('get_term_with_details', )
    search_fields = ('term', 'year', )
    readonly_fields = ('term', 'parent', 'tree_number', 'year', )

@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    exclude = ('results', )
    search_fields = ('criteria__upload__user__email', 'criteria__upload__user__username', 'filename_stub')
    readonly_fields = ('mesh_filter', 'has_completed', 'filename_stub', 'started_processing', 'ended_processing', 'mediator_match_counts', 'mediator_match_counts_v3', 'mediator_match_counts_v4', 'has_edge_file_changed')
    raw_id_fields = ('criteria', )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):

    formfield_overrides = {
        models.CharField: {'widget': Textarea},
    }

