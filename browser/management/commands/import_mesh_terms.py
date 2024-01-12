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

Year of release and classifications will be imported to augment the data from the import file.

ref: https://www.nlm.nih.gov/bsd/disted/meshtutorial/meshtreestructures/

A. Anatomy
B. Organisms
C. Diseases
D. Chemicals and Drugs
E. Analytical, Diagnostic and Therapeutic Techniques and Equipment
F. Psychiatry and Psychology
G. Phenomena and Processes
H. Disciplines and Occupations
I. Anthropology, Education, Sociology and Social Phenomena
J. Technology, Industry, Agriculture
K. Humanities
L. Information Science
M. Named Groups
N. Health Care
V. Publication Characteristics
Z. Geographicals


To be stored in a tree like this:

YEAR, e.g. 2015
    CLASSIFICATION, e.g. Anatomy (A)
        MESH TERM, e.g. Body Regions (A01)
            SUB TERMS, e.g. Anatomic Landmarks (A01.111)
            ...
        MESH TERM, e.g. Musculoskeletal System (A02)
            ...
"""

# ref: https://nlmpubs.nlm.nih.gov/projects/mesh/2023/meshtrees/mtrees2023.bin

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.management.base import BaseCommand, CommandError

from browser.models import MeshTerm


class Command(BaseCommand):
    """Management command to manage importing MeshTerms."""

    help = 'Creates Mesh Term objects based on importing terms from a given years edition of the MeSH terms in ASCII format e.g. mtrees2015.bin http://www.nlm.nih.gov/mesh/'

    def add_arguments(self, parser):
        """Define required command line arguments for management command."""
        parser.add_argument('mesh_term_file_path', type=str)
        parser.add_argument('year', type=int)

    def handle(self, *args, **options):
        """Process file and create MeshTerm objects."""
        filename = options["mesh_term_file_path"]
        year = options["year"]
        self.stdout.write("Test")
        self.stdout.write("About to parse %s and create MesH Terms vocabulary for year %d" % (filename, year,))

        try:
            with open(filename, 'r') as f:
                # Create parent node for importing a Tree of MeSH terms which will be rooted by a faux term, the year of release.
                (root_node, created) = MeshTerm.objects.get_or_create(term=str(year), tree_number="N/A", year=year)
                if created:
                    self.stdout.write("Created: Year root term %s." % root_node)
                else:
                    self.stdout.write("Year root term already existed %s." % root_node)

                # For each year, pre-populate the term classification nodes - ref: https://www.nlm.nih.gov/bsd/disted/meshtutorial/meshtreestructures/
                term_classifications = [('Anatomy', 'A', ),
                                        ('Organisms', 'B'),
                                        ('Diseases', 'C'),
                                        ('Chemicals and Drugs', 'D'),
                                        ('Analytical, Diagnostic and Therapeutic Techniques and Equipment', 'E'),
                                        ('Psychiatry and Psychology', 'F'),
                                        ('Phenomena and Processes', 'G'),
                                        ('Disciplines and Occupations', 'H'),
                                        ('Anthropology, Education, Sociology and Social Phenomena', 'I'),
                                        ('Technology, Industry, Agriculture', 'J'),
                                        ('Humanities', 'K'),
                                        ('Information Science', 'L'),
                                        ('Named Groups', 'M'),
                                        ('Health Care', 'N'),
                                        ('Publication Characteristics', 'V'),
                                        ('Geographicals', 'Z'), ]
                for (term, tree_number) in term_classifications:
                    (classification_node, created) = MeshTerm.objects.get_or_create(term=term, tree_number=tree_number, year=year, parent=root_node)
                    if created:
                        self.stdout.write("Created: Classification term %s." % classification_node)
                    else:
                        self.stdout.write("Classification term already existed %s." % classification_node)

                for line in f:
                    parent = None
                    name, location = line.split(";")
                    location = location.strip()
                    level = location.find('.')

                    self.stdout.write("name:     " + name)
                    self.stdout.write("location: " + location)
                    self.stdout.write("level:    " + str(level))

                    if level > 0:
                        # Parent should have already been processed as part of the import file.
                        try:
                            parent_tree_number = location[:-4]
                            try:
                                parent = MeshTerm.objects.get(tree_number=parent_tree_number, year=year)

                            except MultipleObjectsReturned:
                                self.stderr.write("Found more than one term with tree_number: %s for year %s" % (parent_tree_number, year,))

                            except ObjectDoesNotExist:
                                self.stderr.write("Could not find parent term with tree_number: %s for year %s for term %s" % (parent_tree_number, year, name, ))
                        except:
                            self.stderr.write("Problems finding parent tree number from this location: %s" % location)
                    else:
                        # Top level terms found in the import file need to have a classification term as a parent.
                        try:
                            classification = location[:1]
                            try:
                                parent = MeshTerm.objects.get(tree_number=classification, year=year)
                            except MultipleObjectsReturned:
                                self.stderr.write("Found more than one term with tree_number: %s for year %s" % (classification, year,))

                            except ObjectDoesNotExist:
                                self.stderr.write("Could not find parent term with tree_number: %s for year %s for term %s" % (classification, year, name, ))
                        except:
                            self.stderr.write("Problems finding parent tree number for this location: %s" % classification)

                    (term, created) = MeshTerm.objects.get_or_create(term=name, tree_number=location, parent=parent, year=year)

                    if created:
                        self.stdout.write("Created:" + term.get_term_with_details())
                    else:
                        self.stdout.write("Already existed:" + term.get_term_with_details())

            cache.clear()
        except Exception as e:
            raise CommandError(repr(e))
