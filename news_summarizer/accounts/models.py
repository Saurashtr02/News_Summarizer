from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from core.models import Article  


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    saved_articles = models.ManyToManyField(Article, blank=True, related_name="saved_by")


    def __str__(self):
        return self.user.username
