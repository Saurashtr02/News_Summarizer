from django.urls import path
from . import views

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('search/', views.news_view, name='news_view'),        
    path('save_article/<int:article_id>/', views.save_article, name='save_article'),

]


