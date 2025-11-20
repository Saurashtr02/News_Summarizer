
# Register your models here.

from django.contrib import admin
from .models import UserProfile

# Register UserProfile to the admin interface
admin.site.register(UserProfile)
