import requests
from datetime import datetime
from django.shortcuts import render, redirect
from .models import Article, Summary
from transformers import pipeline
from .utils import aggregate_articles, extract_named_entities_from_text
import re
from langdetect import detect  
from django.core.paginator import Paginator
from langdetect.lang_detect_exception import LangDetectException
import spacy
from spacy.matcher import Matcher
from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile


@login_required
def save_article(request, article_id):
    # Fetch the article from the database
    try:
        article = Article.objects.get(id=article_id)
    except Article.DoesNotExist:
        return redirect('home')  
    
    user_profile = UserProfile.objects.get(user=request.user)
    user_profile.saved_articles.add(article)  
    
    return redirect('profile_detail')  





claim_buster_key = "8bfce314e550491286e274ca96fb6202"
claim_buster_url = "https://idir.uta.edu/claimbuster/api/v2/query/fact_matcher/"


nlp = spacy.load("en_core_web_sm")  
claim_extractor = pipeline("text2text-generation", model="t5-small",device=0)

NEWS_API_KEY = 'cfb604f736444785b44d7a9e70c39c5d'  




def match_claims_with_article(keywords, fact_check_info):
    matched_claims = []
    keywords_lower = [keyword.lower() for keyword in keywords]

    for claim in fact_check_info:
        claim_text = claim.get('claim_text', '').lower()
        
        for keyword in keywords_lower:
            if keyword in claim_text:  
                matched_claims.append(claim)
                break  

    return matched_claims



def article_list(request):
    query = request.GET.get('query', 'latest')
    
    if not Article.objects.exists():
        fetch_news(query)  
    
    articles = Article.objects.all().order_by('-published_at') 

    page_number = request.GET.get('page')  
    paginator = Paginator(articles, 10)  
    page_obj = paginator.get_page(page_number)  
    
    return render(request, 'core/article_list.html', {'articles': articles, 'page_obj': page_obj})


summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=0)


def clean_article_content(content):
    content = re.sub(r'\+?\d+\s?chars?', '', content)  
    return content.strip()

def fetch_news(query):
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        for item in articles:
            content = item.get('content', '')
            description = item.get('description', '')
            image_url = item.get('urlToImage')  

            if not image_url:
                image_url = None

            if not content or '[Removed]' in content or '[removed]' in content:
                continue

            published_at_str = item.get('publishedAt', None)

            if published_at_str:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            else:
                published_at = None  



            Article.objects.get_or_create(
                title=item['title'],
                source=item['source']['name'],
                url=item['url'],
                content=content,
                description=description,
                published_at=published_at,  
                image_url=image_url  

            )
    else:
        print("Failed to fetch news")

def summarize_article(content):
    min_length_for_summary = 150
    if len(content) < min_length_for_summary:
        # print(f"Skipping summarization for article with content length {len(content)}")
        return content
    
    cleaned_content = clean_article_content(content)
    summary = summarizer(cleaned_content, max_length=150, min_length=50, do_sample=False)
    return summary[0]['summary_text']




def fact_check(keywords):

    fact_check_results = []
    listOfEntities = []

    for keyword in keywords:

            input_claim = quote(keyword) 
            api_endpoint = f"{claim_buster_url}{input_claim}"
            request_headers = {"x-api-key": claim_buster_key}

            response = requests.get(url=api_endpoint, headers=request_headers)

            entities = extract_named_entities_from_text(keyword)
            listOfEntities += entities
            

            # print(f"response code is : {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()  
                    print(f"response from ClaimBuster API: {data}")

                    claim_text = data.get('claim', 'No claim text found')
                    justifications = data.get('justification', [])

                    fact_check_results.append({
                        'claim_text': claim_text,   
                        'justifications': [{
                        'truth_rating': justification.get('truth_rating', 'No rating available'),  
                        'url': justification.get('url', 'No URL available'),
                        'search': justification.get('search', 'No search information available'),
                        'speaker': justification.get('speaker', 'No speaker information available'),
                        'claim': justification.get('claim', 'No claim text available'),
                        'host': justification.get('host', 'No host information available'),
                    } for justification in justifications]
                    })

                    print(f"this is the fact-check-results array : {fact_check_results}")

                except ValueError as e:
                    print(f"Error parsing JSON response: {e}")
                    return None  
            else:
                fact_check_results.append({
                    'claim_text': keyword,
                    'fact_check_status': f"Error: {response.status_code} - {response.text}"
                })

    return fact_check_results , listOfEntities


def is_english(text):
    try:
        return detect(text) == 'en'
    except LangDetectException:
        return False  

def filter_english_claims(fact_check_info):
    return [entry for entry in fact_check_info if is_english(entry['claim_text'])]




def news_view(request):

    keyword = request.GET.get('keyword', '').strip()
    country = str(request.GET.get('country', "US"))

    if not keyword:
        return render(request, 'core/news.html', {'error': 'Please enter a keyword to search.'})
        
    articles = Article.objects.filter(title__icontains=keyword)
    if articles.exists():
        print(f"Articles found in database for keyword: {keyword}")
        return render(request, 'core/news.html', {'articles': articles, 'keyword': keyword})
    

    articles_data = aggregate_articles(keyword, NEWS_API_KEY, "gvqaUbei0iYvNYrw54mI6X2lBmi9DTc--Aqo7UnSNNtJMs2U", country)[:7]
    if not articles_data:
        return render(request, 'core/news.html', {'error': 'No articles found for this keyword.'})

    articles = []
    for article_data in articles_data:
        title = article_data['title']
        content = article_data.get('content', '')
        description = article_data.get('description', '')
        url = article_data['url']
        image_url = article_data.get('image_url', '')  
        published_at_str = article_data.get('publishedAt', None)
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            except ValueError:
                published_at = None  
                print(f"Error parsing 'publishedAt' for article: {title}")
        else:
            published_at = None  


        if not content or '[Removed]' in content:
            print(f"Skipping article due to invalid content: {title}")
            continue

         
        summary_text = summarize_article(content)
        if not summary_text:
            continue  

        # Extract keywords and claims
        # claims = extract_keywords_and_claims(summary_text)

        claims = summary_text.split('. ')
        claims = [claim.strip() for claim in claims if claim]  

        print(f"Extracted Claims from article '{title}': {claims}")

        fact_check_info, tempEntities = fact_check(claims)
        # print(f"Fact-check response: {fact_check_info}")

        fact_check_info = filter_english_claims(fact_check_info)

        print(f"Fact-check response after filteration: {fact_check_info}")

        fact_check_text = "No fact-check information available for these keywords."
        review_title = "No review available"
        review_url = "#"
        review_rating = "Unknown"
        review_date = "Unknown"

        if fact_check_info:
            first_claim = fact_check_info[0]
            # print(f"this is first claim []: {first_claim}")
            fact_check_text = ", ".join([
                 f"{claim['claim_text']} (Rating: {justification.get('truth_rating', 'No rating available')})"
                for claim in fact_check_info
                for justification in claim.get('justifications', [])
            ])
            


            justifications = first_claim.get('justifications', [])
            if justifications:
                first_justification = justifications[0]  
                review_url = first_justification.get('url', review_url)
                review_rating = first_justification.get('truth_rating', review_rating)
                review_title = first_justification.get('claim', review_title)
                review_date = first_justification.get('search', review_date)  


        try:
            article, created = Article.objects.get_or_create(
                url=url,
                defaults={
                    'title': title,
                    'description': description,
                    'content': content,
                    'published_at': published_at,
                    'image_url': image_url
                }
            )

            if created:
                Summary.objects.create(
                    article=article,
                    summary_text=summary_text,
                    fact_check=fact_check_text,
                    review_title=review_title,
                    review_url=review_url,
                    review_rating=review_rating,
                    review_date=review_date,
                )
                articles.append(article)
        except Exception as e:
            print(f"Error saving article: {e}")
            continue



    return render(request, 'core/news.html', {'articles': articles, 'keyword': keyword})








