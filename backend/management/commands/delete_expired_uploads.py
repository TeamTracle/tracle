from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from backend.models import ChunkedVideoUpload

class Command(BaseCommand):
    def handle(self, *args, **options):
        expired_uploads = [ cu for cu in ChunkedVideoUpload.objects.all() if cu.expired ]
        for cu in expired_uploads:
            self.stdout.write(f'Deleting {str(cu)} ...')
            try:
                cu.delete()
            except Exception as e:
                self.stdout.write(f'Failed to delete {str(cu)}')
                self.stdout.write(str(e))
