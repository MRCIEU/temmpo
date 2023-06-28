"""This management command is used warn/delete inactive users."""

from django.core.management.base import BaseCommand

from browser.utils import remove_incompleted_registrations


class Command(BaseCommand):
    """ Django management command to warn/delete inactive users """

    help = "Deletes users that didn't complete registration within ACCOUNT_ACTIVATION_DAYS days, e.g. 14 days."

    def handle(self, *args, **options):
        """ Pass off to the utility """
        remove_incompleted_registrations()