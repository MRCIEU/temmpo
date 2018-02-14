from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from temmpo.prepopulate import pre_populate_genes

class Command(BaseCommand):
    args = ''
    help = 'Imports genes from the Homo_sapiens.gene_info fixture in the temmpo/temmpo/prepopulate directory.'

    def handle(self, *args, **options):
        #print "fooo"
        pre_populate_genes()
