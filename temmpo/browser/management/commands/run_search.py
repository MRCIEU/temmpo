"""Management command that can re-run a matching search based on the ID of an existing SearchResult."""

from django.core.management.base import BaseCommand

from browser.matching import perform_search


class Command(BaseCommand):
    """Django management command wrapper class."""

    help = 'Performs search on a SearchResult object based on the supplied ID'

    def add_arguments(self, parser):
        """Define required command line arguments for management command."""
        parser.add_argument('search_result_id', type=int)

    def handle(self, *args, **options):
        """Perform search where and ID has been supplied."""
        perform_search(options['search_result_id'])
