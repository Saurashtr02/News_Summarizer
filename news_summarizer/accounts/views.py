
# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserProfileForm
from .models import UserProfile
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LogoutView
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from core.models import Article  
from django.urls import reverse





@login_required
def remove_saved_article(request, article_id):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    article = get_object_or_404(Article, id=article_id)

    if article in user_profile.saved_articles.all():
        user_profile.saved_articles.remove(article)
    
    return HttpResponseRedirect(reverse('profile_detail'))  


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)  
            return redirect('update_profile')  
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})





@login_required
def update_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = UserProfile(user=request.user)
        user_profile.save()

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('profile_detail')  
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'accounts/update_profile.html', {'form': form})



@login_required
def profile_detail(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None


    saved_articles = user_profile.saved_articles.all() if user_profile else []


    return render(request, 'accounts/profile_detail.html', {
        'user_profile': user_profile,
        'saved_articles': saved_articles
    })




def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next', 'profile')  

            return redirect(next_url)  
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


