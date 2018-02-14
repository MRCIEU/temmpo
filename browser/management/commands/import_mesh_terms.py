"""
Management command to import or update MeSH terms.

Example format for ASCII MeSH input file.

Ref: ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/meshtrees/

Body Regions;A01
Anatomic Landmarks;A01.111
Breast;A01.236
Mammary Glands, Human;A01.236.249
Nipples;A01.236.500
Extremities;A01.378
Amputation Stumps;A01.378.100
Lower Extremity;A01.378.610
Buttocks;A01.378.610.100
Foot;A01.378.610.250
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from browser.models import MeshTerm

# TODO: 1. TMMA-131 Add explicit tests for importing different years from a test sample files


class Command(BaseCommand):
    """Management command to manage importing MeshTerms."""

    args = '<mesh-term-file-path> <year>'
    help = 'Creates Mesh Term objects based on importing terms from a given years edition of the MeSH terms in ASCII format e.g. mtrees2015.bin http://www.nlm.nih.gov/mesh/'

    def add_arguments(self, parser):
        """Define required command line arguments for management command."""
        parser.add_argument('mesh_term_file_path', type=str)  # TODO TMMA-131 Should I be using type=argparse.FileType('r')
        parser.add_argument('year', type=int)

    def handle(self, *args, **options):
        """Process file and create MeshTerm objects."""
        if args:
            filename = options["mesh_term_file_path"]
            year = options["year"]
            self.stdout.write("About to parse %s and create MesH Terms vocabulary for year %d" % (filename, year,))

            try:
                with open(filename, 'r') as f:
                    # Create parent node for importing a Tree of MeSH terms which will be rooted by a faux term, the year of release.
                    root_node = MeshTerm.objects.create(term=str(year), tree_number="N/A", year=year)
                    self.stdout.write("Created: Root term %s." % root_node)
                    for line in f:
                        parent = None
                        name, location = line.split(";")
                        location = location.strip()
                        level = location.find('.')

                        self.stdout.write("name:     " + name)
                        self.stdout.write("location: " + location)
                        self.stdout.write("level:    " + str(level))

                        if level > 0:
                            try:
                                parent_tree_number = location[:-4]
                                try:
                                    parent = MeshTerm.objects.get(tree_number=parent_tree_number, year=year)

                                except MultipleObjectsReturned:
                                    self.stderr.write("Found more than one term with tree_number: %s for year %s" % (parent_tree_number, year,))

                                except ObjectDoesNotExist:
                                    self.stderr.write("Could not find parent term with tree_number: %s for year %s" % (parent_tree_number, year,))
                            except:
                                self.stderr.write("Problems finding parent tree number from this location: %s" % location)
                        else:
                            parent = root_node

                        if parent:
                            term = MeshTerm.objects.create(term=name, tree_number=location, parent=parent, year=year)

                        self.stdout.write("Created:" + term.get_term_with_details())

            except Exception as e:
                self.stderr.write("Some kind of error:")
                self.stderr.write(repr(e))

        else:
            raise CommandError("Please supply the file path to the Mesh Tree ASCII format file to parse and the year of release YYYY.")
