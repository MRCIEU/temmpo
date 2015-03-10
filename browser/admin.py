from django.contrib import admin

# Register your models here.
from browser.models import (Gene, MeshTerm, Upload, Abstract,
    SearchCriteria, SearchResult)

admin.site.register(Gene)
admin.site.register(MeshTerm)
admin.site.register(Upload)
admin.site.register(Abstract)
admin.site.register(SearchCriteria)
admin.site.register(SearchResult)