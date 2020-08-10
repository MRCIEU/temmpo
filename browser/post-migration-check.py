#Identify strange counts after reprocessing

from django.conf import settings
from django.db.models import F

from browser.models import SearchResult

print("How many search reuslts in total")
print(SearchResult.objects.all().count())

print("How many valid version 1 matches exist")
v1 = SearchResult.objects.filter(mediator_match_counts__isnull=False)
print(v1.count())

print("How many version 3 matches exist at the moment")
v3 = SearchResult.objects.filter(mediator_match_counts_v3__isnull=False)
print(v3.count())

print("How many version 4 matches exist at the moment")
v4 = SearchResult.objects.filter(mediator_match_counts_v4__isnull=False)
print(v4.count())

odd_results_v1_vs_v3 = v1.filter(mediator_match_counts__gt=F('mediator_match_counts_v3'))
print("How many results have more matches in v1 than v3")
print(odd_results_v1_vs_v3.count())

print("How many results have more matches in v3 than v4")
v4_vs_v3 = v4.filter(mediator_match_counts_v3__gt=F('mediator_match_counts_v4'))
print(v4_vs_v3.count())
print([x.id for x in v4_vs_v3])

print("How many results have more matches in v1 than v4")
v4_vs_v1 = v4.filter(mediator_match_counts__gt=F('mediator_match_counts_v4'))
print(v4_vs_v1.count())
print([x.id for x in v4_vs_v1])

for search_result in v4:
    with open(settings.RESULTS_PATH_V4 + search_result.filename_stub + "_edge.csv", "r") as edge_file:
        # Confirm mediator counts match edge file lines
        data_rows_count = -1 # Less the header
        for line in edge_file.xreadlines(  ): data_rows_count += 1
        if search_result.mediator_match_counts_v4 <> data_rows_count:
            print("Result %d has %d rows in the edge file and %d as a mediator count recorded." % (search_result.id, data_rows_count, search_result.mediator_match_counts_v4))

priority_users = ('BMLynch', 'drbrigidmlynch', 'anndrummond', )
priority_results = SearchResult.objects.filter(criteria__upload__user__username__in=priority_users)    
print("How many priority results have more matches in v3 than v4")
priority_results_v4_vs_v3 = priority_results.filter(mediator_match_counts_v3__gt=F('mediator_match_counts_v4'))
print(priority_results_v4_vs_v3.count())
print([x.id for x in priority_results_v4_vs_v3])

print("How many priority results have more matches in v1 than v4")
priority_results_v4_vs_v1 = priority_results.filter(mediator_match_counts__gt=F('mediator_match_counts_v4'))
print(priority_results_v4_vs_v1.count())
print([x.id for x in priority_results_v4_vs_v1])