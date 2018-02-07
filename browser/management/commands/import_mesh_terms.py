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
# """
# MeSH in XML format sample
# <DescriptorRecord ...><!-- Descriptor  -->
#    <DescriptorUI>D000005</DescriptorUI>
#    <DescriptorName><String>Abdomen</String></DescriptorName>
#    <Annotation> region & abdominal organs...
#    </Annotation>
#    <ConceptList>
#       <Concept PreferredConceptYN="Y"><!-- Concept  -->
#           <ConceptUI>M0000005</ConceptUI>
#           <ConceptName><String>Abdomen</String></ConceptName>
#           <ScopeNote> That portion of the body that lies
#           between the thorax and the pelvis.</ScopeNote>
#           <TermList>
#              <Term ... PrintFlagYN="Y" ... ><!-- Term  -->
#                 <TermUI>T000012</TermUI>
#                 <String>Abdomen</String><!-- String = the term itself -->
#                 <DateCreated>
#                    <Year>1999</Year>
#                    <Month>01</Month>
#                    <Day>01</Day>
#                 </DateCreated>
#              </Term>
#              <Term IsPermutedTermYN="Y" LexicalTag="NON">
#                  <TermUI>T000012</TermUI>
#                  <String>Abdomens</String>
#              </Term>
#           </TermList>
#       </Concept>
#    </ConceptList>
# </DescriptorRecord>
# """

# from lxml import etree

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from browser.models import MeshTerm


class Command(BaseCommand):
    args = '<mesh-term-file-path> <year>'
    help = 'Creates Mesh Term objects based on importing terms from a given years edition of the MeSH terms in ASCII format e.g. mtrees2015.bin http://www.nlm.nih.gov/mesh/'

    def handle(self, *args, **options):
        if args:

            filename = args[0]
            year = args[1]
            self.stdout.write("About to parse %s and create MesH Terms vocabulary for year %s" % (filename, year,))

            try:
                with open(filename, 'r') as f:
                    for line in f:
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
                                    parent = MeshTerm.objects.get(tree_number=parent_tree_number)
                                except:
                                    self.stderr.write("Found more than one term with tree_number "+ tree_number)

                            except ObjectDoesNotExist:
                                self.stderr.write("Could not find parent object " + parent_tree_number)
                                parent = None
                        else:
                            # TODO: TMMA-131 Use year MeSHTerm filter
                            parent = None

                        if parent:
                            term = MeshTerm.objects.create(term=name, tree_number=location, parent=parent)
                        else:
                            term = MeshTerm.objects.create(term=name, tree_number=location)

                        self.stdout.write("Created:" + term.get_term_with_tree_number())

            except Exception as e:
                self.stderr.write("Some kind of error")
                self.stderr.write(repr(e))

        else:
            raise CommandError("Please supply the file path to the Mesh Tree ASCII format file to parse and the year of release YYYY.")
