from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from temmpo.prepopulate import pre_populate_genes

class Command(BaseCommand):
    args = ''
    help = 'Imports genes from the files specified'

    def handle(self, *args, **options):
        #print "fooo"
        pre_populate_genes()
