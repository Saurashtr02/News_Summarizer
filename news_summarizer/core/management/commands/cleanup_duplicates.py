from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import Article

class Command(BaseCommand):
    help = 'Deletes duplicate articles, keeping only the first instance of each URL.'

    def handle(self, *args, **kwargs):
        # Find duplicate URLs and keep only one instance of each
        duplicate_urls = Article.objects.values('url').annotate(url_count=Count('url')).filter(url_count__gt=1)

        for duplicate in duplicate_urls:
            # Get all articles with this duplicate URL
            articles = Article.objects.filter(url=duplicate['url'])
            # Keep the first article and delete the rest
            articles.exclude(id=articles.first().id).delete()

        self.stdout.write(self.style.SUCCESS('Duplicate articles cleaned up successfully!'))
