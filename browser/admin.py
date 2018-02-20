"""Register custom models in Django admin interface for super user local UoB access only."""

from django.contrib import admin

from browser.models import Gene, MeshTerm, Upload, SearchCriteria, SearchResult

admin.site.register(Gene)
admin.site.register(MeshTerm)
admin.site.register(Upload)
admin.site.register(SearchCriteria)
admin.site.register(SearchResult)