"""
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
    args = '<mesh-term-file-path>'
    help = 'Creates Mesh Term objects based on importing terms from 2015 MeSH in ASCII format mtrees2015.bin http://www.nlm.nih.gov/mesh/'

    def handle(self, *args, **options):
        if args:

            filename = args[0]
            self.stdout.write("About to parse %s and create MesH Terms vocabulary" % filename)

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
                            parent = None

                        if parent:
                            term = MeshTerm.objects.create(term=name, tree_number=location, parent=parent)
                        else:
                            term = MeshTerm.objects.create(term=name, tree_number=location)

                        self.stdout.write("Created:" + term.get_term_with_tree_number())

                # MeshTerm

                # tree = etree.parse(filename)
                # self.stdout.write("Before parse")
                # tree = etree.parse(filename)
                # self.stdout.write("After parse")
                #tree.getroot()
                #parser = etree.XMLParser(remove_blank_text=True) # lxml.etree only!
                # >>> for element in root.iter("*"):
                # ...     if element.text is not None and not element.text.strip():
                # ...         element.text = None
                # The XML parser
                # boolean dtd_validation, remove_comments
                # keyword args - schema   - an XMLSchema to validate against
                # - target   - a parser target object that will receive the parse events

                # Interate DescriptorRecord
                # DescriptorName > String
                # Then interate TermList
                # Term > String

                # for record in tree.iter("DescriptorRecord"):
                #     print("%s, %s" % (element.tag, element.text))
                #     name = etree.SubElement(tree, "DescriptorName")
                #     print(name.tag)
                #     heading = record.find('//DescriptorName/String').text
                #     print(heading)
                #     break
                #     # if element.text is not None and not element.text.strip():
                #     #    element.text = None

            except Exception as e:
                self.stderr.write("Some kind of error")
                self.stderr.write(repr(e))

        else:
            raise CommandError("Please supply the file path to the Mesh Tree ASCII format file to parse.")
