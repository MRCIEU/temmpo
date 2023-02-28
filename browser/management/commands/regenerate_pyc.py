import compileall
import re

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Regnerate .pyc files"

    def handle(self, *args, **options):
        # Regenerate all pyc files
        compileall.compile_dir(settings.PROJECT_ROOT, rx=re.compile(r'[/\\][.]git'), force=True)

