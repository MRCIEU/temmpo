from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from browser.matching import perform_search

class Command(BaseCommand):
    args = '<search_result_id>'
    help = 'Performs search on the SearchResult based on passed in pk'

    def handle(self, *args, **options):
        if args:

            sr_id = int(args[0])
            perform_search(sr_id)
        else:
            print "Must provide an id for the Search Results"
