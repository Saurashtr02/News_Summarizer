
# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Article(models.Model):
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=100)
    url = models.URLField(unique=True)
    content = models.TextField()
    description = models.TextField(null=True, blank=True)  
    published_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    keywords = models.JSONField(default=list)  
    image_url = models.URLField(blank=True, null=True)  


    def __str__(self):
        return self.title

class Summary(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    summary_text = models.TextField()
    sentiment = models.CharField(max_length=50, null=True, blank=True)
    fact_check = models.CharField(max_length=255, null=True, blank=True)  
    review_title = models.CharField(max_length=255, null=True, blank=True)
    review_url = models.URLField(null=True, blank=True)
    review_rating = models.CharField(max_length=50, null=True, blank=True)
    review_date = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary of {self.article.title}"
