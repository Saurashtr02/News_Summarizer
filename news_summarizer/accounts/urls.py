# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings



urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    # path('profile/', views.user_profile, name='profile'),  # User profile URL

    path('profile/update/', views.update_profile, name='update_profile'),  # URL for updating the profile
    path('profile/', views.profile_detail, name='profile_detail'),  # URL for
    path('profile/remove_saved_article/<int:article_id>/', views.remove_saved_article, name='remove_saved_article'),


]


# Serve media files during development (only in DEBUG mode)
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
