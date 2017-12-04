"""Management command to import or update MeSH terms.

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

# TODO: There are removals and changes to tree_number that need to be handled.

e.g.
./temmpo/prepopulate/mtrees2015.bin:Unnecessary Procedures;N02.421.380.900
to

./temmpo/prepopulate/mtrees2018.bin:Unnecessary Procedures;N02.421.380.450.500

Need to consider versioning results - as based on 2015 MeshTerms,l 2018 MeshTerms

Do we consider versioning MeshTerms

year 2015, 2018

Need to consider when re-using search terms what happens

BUGS - Was finding duplicate parent objects for no reason

Needs review


"""

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from browser.models import MeshTerm


class Command(BaseCommand):
    """Management command for importing Mesh Terms."""

    args = '<mesh-term-file-path>'
    help = 'Creates Mesh Term objects based on importing terms from a MeSH in ASCII format file, e.g. mtrees2018.bin http://www.nlm.nih.gov/mesh/'

    def handle(self, *args, **options):
        """Main function of command."""
        if args:

            filename = args[0]
            self.stdout.write("About to parse %s and create MeSH Terms vocabulary" % filename)

            try:
                with open(filename, 'r') as f:
                    for line in f:
                        parent = None
                        name, location = line.split(";")
                        location = location.strip()
                        level = location.find('.')

                        self.stdout.write("###########")
                        self.stdout.write("line:     " + line)
                        self.stdout.write("name:     " + name)
                        self.stdout.write("location: " + location)
                        self.stdout.write("level:    " + str(level))

                        if level > 0:
                            try:
                                parent_tree_number = location[:-4]
                                try:
                                    parent = MeshTerm.objects.get(tree_number=parent_tree_number)
                                except MultipleObjectsReturned:
                                    raise CommandError("Found more than one term with the same tree_number in the database: " + parent_tree_number)

                            except ObjectDoesNotExist:
                                self.stderr.write("Could not find parent object " + parent_tree_number)

                        # Try to update term, if it does not exist then create it.
                        try:
                            updated = MeshTerm.objects.filter(tree_number=location).update(term=name, parent=parent)
                            if updated:
                                self.stdout.write("Updated " + str(updated) + " item, term : " + name + ";" + location)

                        except ObjectDoesNotExist:
                            term = MeshTerm.objects.create(term=name, tree_number=location, parent=parent)
                            self.stdout.write("Created: " + term.get_term_with_tree_number())

            except Exception as e:
                self.stderr.write("Some kind of error")
                self.stderr.write(repr(e))

        else:
            raise CommandError("Please supply the file path to the Mesh Tree ASCII format file to parse.")
