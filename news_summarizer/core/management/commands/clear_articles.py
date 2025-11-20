from django.core.management.base import BaseCommand
from core.models import Article

class Command(BaseCommand):
    help = 'Clears all articles from the database'

    def handle(self, *args, **kwargs):
        # Delete all articles
        Article.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all articles'))
