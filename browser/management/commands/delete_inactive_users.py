"""This management command is used as a one off setup for new projects to import and list of known gene names."""

from django.core.management.base import BaseCommand

from browser.utils import user_clean_up


class Command(BaseCommand):
    """ Django management command to warn/delete inactive users """

    help = "Warns users that haven't logged in for 10 months."\
           "Deletes users that didn't complete registration or those that haven't logged in for a year."

    def handle(self, *args, **options):
        """ Pass off to the utility """
        # For the first 60 days of use we just want this to warn users.
        user_clean_up(no_deletion=True)
        # After 60 days revert to
        #user_clean_up()