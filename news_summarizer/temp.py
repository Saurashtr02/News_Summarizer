# AIzaSyDL3ljPqOa_78KM3QJ8J3x34HiS-sEFJTE

# 31589af3d2c1a46b6


#lauren boebert, elon musk cnn, ratan tata


# claim buster : 8bfce314e550491286e274ca96fb6202



# <!-- accounts/templates/accounts/profile_detail.html -->
# <!DOCTYPE html>
# <html>
# <head>
#     <title>Profile Details</title>
#     <!-- Optional: Add Bootstrap for styling -->
#     <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" rel="stylesheet">
# </head>
# <body>
#     <div class="container">
#         <h2>Profile Details</h2>

#         {% if user_profile %}
#             <p><strong>Username:</strong> {{ user_profile.user.username }}</p>
#             <p><strong>Email:</strong> {{ user_profile.user.email }}</p>

#             <p><strong>Bio:</strong> {{ user_profile.bio }}</p>

#             {% if user_profile.profile_picture %}
#                 <p><strong>Profile Picture:</strong><br><img src="{{ user_profile.profile_picture.url }}" alt="Profile Picture" width="150"></p>
#             {% else %}
#                 <p><strong>Profile Picture:</strong> No picture uploaded</p>
#             {% endif %}
#         {% else %}
#             <p>No profile found. Please update your profile.</p>
#         {% endif %}

#         <!-- Logout Button -->
# <form method="POST" action="{% url 'logout' %}">
#     {% csrf_token %}
#     <button type="submit">Logout</button>
# </form>

#         <h3>Saved Articles</h3>
#         {% if saved_articles %}
#             <ul>
#                 {% for article in saved_articles %}
#                     <li>{{ article.title }}</li>
#                 {% endfor %}
#             </ul>
#         {% else %}
#             <p>No saved articles yet.</p>
#         {% endif %}
        
#         <a href="{% url 'update_profile' %}" class="btn btn-primary">Edit Profile</a>
#     </div>
# </body>
# </html>






# views.py core


import requests
from datetime import datetime
from django.shortcuts import render, redirect
from .models import Article, Summary
from transformers import pipeline
from .utils import aggregate_articles, extract_named_entities_from_text, extract_keywords_and_claims
import re
from langdetect import detect  
from django.core.paginator import Paginator
from langdetect.lang_detect_exception import LangDetectException
import spacy
from googleapiclient.discovery import build
import wikipedia
from spacy.matcher import Matcher
from urllib.parse import quote
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile






claim_buster_key = "8bfce314e550491286e274ca96fb6202"

claim_buster_url = "https://idir.uta.edu/claimbuster/api/v2/query/fact_matcher/"



# def extract_claims_from_article(article_text):
#     # Prepare the data to send to the API
#     data = {
#         'text': article_text,  # Text of the article
#         'language': 'en'  # Language of the text (optional, default is English)
#     }

#     headers = {
#         'Authorization': f'Bearer {claim_buster_key}'  # Authorization header with the API key
#     }

#     # Make the POST request to the ClaimBuster API
#     response = requests.post(claim_buster_url, json=data, headers=headers)

#     if response.status_code == 200:
#         # If the request is successful, parse the returned JSON
#         claims = response.json()['claims']  # The list of detected claims
#         return claims
#     else:
#         print(f"Error: {response.status_code}, {response.text}")
#         return []


nlp = spacy.load("en_core_web_sm")  

claim_extractor = pipeline("text2text-generation", model="t5-small",device=0)



# def extract_claims(content):
#     claims = []
#     sentences = content.split('.')

#     for sentence in sentences:
#         sentence = sentence.strip()
        
#         # Skip if sentence is too short (e.g., filler sentence)
#         if len(sentence) < 10:
#             continue
        
#         # Here we focus on extracting key claim parts (subject, verb, object)
#         claim_input = f"Extract key claims from the following sentence: {sentence}"
        
#         # Extract claims using T5 model
#         extracted_claims = claim_extractor(claim_input, max_length=200, num_return_sequences=1)
        
#         # Simplify the claim output and add it to the list
#         for claim in extracted_claims:
#             claims.append(claim['generated_text'].strip())
    
#     return claims



NEWS_API_KEY = 'cfb604f736444785b44d7a9e70c39c5d'  
# FACT_CHECK_API_KEY = 'AIzaSyDL3ljPqOa_78KM3QJ8J3x34HiS-sEFJTE'  
# SEARCH_KEY = "AIzaSyDL3ljPqOa_78KM3QJ8J3x34HiS-sEFJTE"
# CSE_ID = "31589af3d2c1a46b6"



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
# summarizer = pipeline("summarization", model="t5-large", device=0)


# def extract_keywords_from_summary(summary_text):
#     keywords = extract_named_entities_from_text(summary_text)  
#     return keywords


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
                # If the 'publishedAt' field is present, parse it to a datetime object
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            else:
                # If 'publishedAt' is missing, set it to None (or use the current date if you prefer)
                published_at = None  # Or datetime.now() if you want to use the current date



            Article.objects.get_or_create(
                title=item['title'],
                source=item['source']['name'],
                url=item['url'],
                content=content,
                description=description,
                # published_at=datetime.fromisoformat(item['publishedAt'].replace("Z", "+00:00")),
                published_at=published_at,  # Use the safely retrieved or default date

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

    # search_url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?key={FACT_CHECK_API_KEY}"



    fact_check_results = []
    listOfEntities = []

    # keywords, entities = preprocess_claim(keywords)

    
    for keyword in keywords:
        # extClaims, entities = preprocess_claim(keyword)
        # listOfEntities += entities
        # print(f"this is extCalims: {extClaims}")

        # for extClaim in extClaims:
            # print(f"second loop")
            # refined_query = f"{extClaim} {', '.join(entities)}"
            # refined_query = extClaim

            input_claim = quote(keyword)  # URL-encode the claim to be safe for the request
            api_endpoint = f"{claim_buster_url}{input_claim}"
            request_headers = {"x-api-key": claim_buster_key}




            # fact_check_url = f"{claim_buster_url}{keyword}?api_key={claim_buster_key}"
            response = requests.get(url=api_endpoint, headers=request_headers)



            entities = extract_named_entities_from_text(keyword)
            listOfEntities += entities
            

            # params = {"query": keyword, "pageSize": 5}
            # response = requests.get(search_url, params=params)

            # response = requests.get(fact_check_url)


            print(f"response code is : {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()  # Parse the JSON response
                    print(f"response from ClaimBuster API: {data}")

                    # if data.get('status') == 'OK':
                    # claim_data = data.get('data', {})
                    claim_text = data.get('claim', 'No claim text found')
                    justifications = data.get('justification', [])

                    # Add to the results list
                    fact_check_results.append({
                        'claim_text': claim_text,   
                        'justifications': [{
                        'truth_rating': justification.get('truth_rating', 'No rating available'),  # Ensure default value
                        'url': justification.get('url', 'No URL available'),
                        'search': justification.get('search', 'No search information available'),
                        'speaker': justification.get('speaker', 'No speaker information available'),
                        'claim': justification.get('claim', 'No claim text available'),
                        'host': justification.get('host', 'No host information available'),
                    } for justification in justifications]
                    })

                    print(f"this is the fact-check-results array : {fact_check_results}")
                    # else:
                    #     fact_check_results.append({
                    #         'claim_text': keyword,
                    #         'fact_check_status': 'Failed to retrieve data'
                    #     })

                except ValueError as e:
                    print(f"Error parsing JSON response: {e}")
                    return None  # Handle the case where the JSON response is invalid
            else:
                fact_check_results.append({
                    'claim_text': keyword,
                    'fact_check_status': f"Error: {response.status_code} - {response.text}"
                })

                
            # if response.status_code == 200:
            #     data = response.json()

            #     print(f"response from claimbuster: {data}")

            #     if data.get('status') == 'OK':
            #         claim_data = data.get('data', {})
            #         claim_text = claim_data.get('claim', 'No claim text found')
            #         justifications = claim_data.get('justification', [])

            #         # Add to the results list
            #         fact_check_results.append({
            #             'claim_text': claim_text,
            #             'justifications': [{
            #                 'truth_rating': justification['truth_rating'],
            #                 'url': justification['url'],
            #                 'search': justification['search'],
            #                 'speaker': justification['speaker'],
            #                 'claim': justification['claim'],
            #                 'host': justification['host'],
            #             } for justification in justifications]
            #         })
            #     else:
            #         fact_check_results.append({
            #             'claim_text': keyword,
            #             'fact_check_status': 'Failed to retrieve data'
            #         })
            #     # claims = data.get('claims', [])

            #     # print(f"Fact-Check API response for keyword '{keyword}': {data}")
                
            #     # if claims:
            #     #     claim = claims[0]
            #     #     review = claim.get('claimReview', [{}])[0]
            #     #     # print(f"printing the review got from api : {review}")
            #     #     fact_check_results.append({
            #     #         'claim_text': claim['text'],
            #     #         'review_title': review.get('title', 'No title available'),
            #     #         'review_url': review.get('url', '#'),
            #     #         'review_rating': review.get('textualRating', 'Unknown'),
            #     #         'review_date': review.get('reviewDate', 'Unknown'),
            #     #     })
            #     #     # print(f"printing the relevant data from review : {fact_check_results}")
            #     # else:
            #     #     print(f"No claims found for keyword '{keyword}'.")
            #     #     fact_check_results.append({"claim_text": "No claim found"})
            # else:
            #     # print(f"Failed to fetch fact-check data for '{keyword}'. HTTP Status: {response.status_code}")
            #     # fact_check_results.append({"claim_text": "Error fetching data"})

            #     fact_check_results.append({
            #         'claim_text': keyword,
            #         'fact_check_status': f"Error: {response.status_code} - {response.text}"
            #     })

    return fact_check_results , listOfEntities


def is_english(text):
    try:
        return detect(text) == 'en'
    except LangDetectException:
        return False  

def filter_english_claims(fact_check_info):
    return [entry for entry in fact_check_info if is_english(entry['claim_text'])]

# def preprocess_claim(claim):
#     # Remove punctuation and common stopwords to focus the query
#     doc = nlp(claim)
#     entities = [ent.text for ent in doc.ents]

#     # verbs_and_objects = []
#     # for token in doc:
#     #     if token.dep_ == 'ROOT':  # Identify the main verb (root)
#     #         # Get the subject and object related to the verb
#     #         subj = [child for child in token.lefts if child.dep_ == 'nsubj']
#     #         obj = [child for child in token.rights if child.dep_ in ['dobj', 'prep']]
#     #         if subj and obj:
#     #             verbs_and_objects.append((subj[0].text, token.text, obj[0].text))  # (subject, verb, object)
      
#     #     # Construct a more focused claim
#     claims = []
#     # for subj, verb, obj in verbs_and_objects:
#     #     # If entities are found, use them to form a more complete query
#     #     if subj in entities and obj in entities:
#     #         claim = f"{subj} {verb} {obj}"  # "Elon Musk bought CNN"
#     #     else:
#     #         claim = f"{subj} {verb} {obj}"  # We still use the subject-verb-object pair even without full entity matches
#     #     claims.append(claim)
    
#     # return claims, entities 

#     matcher = Matcher(nlp.vocab)

#     action_patterns = [
#     {"dep": "nsubj", "pos": "NOUN"},  # Subject (NOUN)
#     {"dep": "ROOT", "pos": "VERB"},   # Verb (ROOT)
#     {"dep": "dobj", "pos": "NOUN"},   # Direct Object (NOUN)
#     {"dep": "prep", "pos": "ADP"},    # Prepositions (e.g., "in", "for")
#     {"dep": "pobj", "pos": "NOUN"}    # Object of Preposition
# ]

#     matcher.add("ActionPattern", [action_patterns])

#     matches = matcher(doc)

#     print(f"Number of matches found: {len(matches)}")



#     for match_id, start, end in matches:
#         span = doc[start:end]
#         subj = ""
#         verb = ""
#         obj = ""

#         # Debugging: print the matched span and its dependency tags
#         print(f"Matched Span: {span.text}")
#         print(f"Span dependencies: {[token.dep_ for token in span]}")

#         # Extract subject, verb, and object from the matched span
#         for token in span:
#             print(f"Token: {token.text}, Dependency: {token.dep_}")
#             if token.dep_ in ['nsubj', 'nsubjpass']:  # Subject (active/passive)
#                 subj = token.text
#             elif token.dep_ == 'ROOT':  # Verb (ROOT)
#                 verb = token.text
#             elif token.dep_ in ['dobj', 'prep', 'pobj']:  # Direct object or prepositional object
#                 obj = token.text

#         # Construct a meaningful claim (subject, verb, object)
#         if subj and verb:
#             claim_text = f"{subj} {verb} {obj}" if obj else f"{subj} {verb}"
#             claims.append(claim_text)

#     # Extracting additional named entities (for the sake of facts)
#     entities = [ent.text for ent in doc.ents]

#     return claims, entities


#     claim_cleaned = re.sub(r'[^\w\s]', '', claim)
    
#     return claim_cleaned

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
        # published_at = datetime.fromisoformat(article_data['publishedAt'].replace("Z", "+00:00"))
        
        # Safely parse 'publishedAt'
        published_at_str = article_data.get('publishedAt', None)
        if published_at_str:
            try:
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
            except ValueError:
                published_at = None  # Or datetime.now() if you want the current time
                print(f"Error parsing 'publishedAt' for article: {title}")
        else:
            published_at = None  # Or datetime.now() if you want the current time


        if not content or '[Removed]' in content:
            print(f"Skipping article due to invalid content: {title}")
            continue

         
        summary_text = summarize_article(content)
        if not summary_text:
            continue  

         # Extract keywords and claims
        # claims = extract_keywords_and_claims(summary_text)

        claims = summary_text.split('. ')
        claims = [claim.strip() for claim in claims if claim]  # Clean and separate claims

        # claims = extract_claims_from_article(summary_text)







        # keywords = extract_keywords_from_summary(summary_text)
        # print(f"Extracted Keywords for article '{title}': {keywords}")
        print(f"Extracted Claims from article '{title}': {claims}")
        print(f"\n\n")

        fact_check_info, tempEntities = fact_check(claims)
        # print(f"Fact-check response: {fact_check_info}")

        fact_check_info = filter_english_claims(fact_check_info)

        print(f"Fact-check response after filteration: {fact_check_info}")
        print(f"\n\n")


        # print(f"this are the tempEntities : {tempEntities}")

        # matched_claims = match_claims_with_article(tempEntities, fact_check_info)
        # print(f"Matched Claims: {matched_claims}")


        # review_title = "No review available"
        # review_url = "#"
        # review_rating = "Unknown"
        # review_date = "Unknown"
        # fact_check_text = "No fact-check information available for these keywords."

        # Prepare fact-check summary
        fact_check_text = "No fact-check information available for these keywords."
        review_title = "No review available"
        review_url = "#"
        review_rating = "Unknown"
        review_date = "Unknown"

        if fact_check_info:
            first_claim = fact_check_info[0]
            print(f"this is first claim []: {first_claim}")
            fact_check_text = ", ".join([
                 f"{claim['claim_text']} (Rating: {justification.get('truth_rating', 'No rating available')})"
                for claim in fact_check_info
                for justification in claim.get('justifications', [])
            ])
            

            # Set review details if available
            # review_title = first_claim.get('review_title', review_title)
            
            # review_url = first_claim.get('review_url', review_url)
            # review_rating = first_claim.get('review_rating', review_rating)
            # review_date = first_claim.get('review_date', review_date)

            justifications = first_claim.get('justifications', [])
            if justifications:
                first_justification = justifications[0]  # Assuming we want the first justification
                
                # Review URL - extracted from the 'url' field in justification
                review_url = first_justification.get('url', review_url)
                
                # Review Rating - extracted from the 'truth_rating' field in justification
                review_rating = first_justification.get('truth_rating', review_rating)
                
                # Review Title - set to 'claim_text' from the first claim, but can be customized
                review_title = first_justification.get('claim', review_title)
                
                # Review Date - Here, we don't see an explicit 'date' field in the example.
                # We'll use a fallback (like the `search` field or `host`).
                review_date = first_justification.get('search', review_date)  # You can adjust this if you find a date field


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


        # if matched_claims:
        #             fact_check_text = ", ".join([
        #                 f"{claim['claim_text']} (Rating: {claim.get('review_rating', 'No rating available')})"
        #                 for claim in matched_claims
        #             ])

        #             first_claim = matched_claims[0]
        #             review_title = first_claim.get('review_title', review_title)
        #             review_url = first_claim.get('review_url', review_url)
        #             review_rating = first_claim.get('review_rating', review_rating)
        #             review_date = first_claim.get('review_date', review_date)

       


        # try:
        #     article, created = Article.objects.get_or_create(
        #         url=url,
        #         defaults={
        #             'title': title,
        #             'description': description,
        #             'content': content,
        #             'published_at': published_at,
        #             'image_url': image_url,  

        #         }
        #     )

        #     if created:
        #         Summary.objects.create(
        #             article=article,
        #             summary_text=summary_text,
        #             fact_check=fact_check_text,
        #             review_title=review_title,
        #             review_url=review_url,
        #             review_rating=review_rating,
        #             review_date=review_date,
        #         )
        #         print(f"Article added: {title}")
        #         articles.append(article)
        # except Exception as e:
        #     print(f"Error saving article: {e}")
        #     continue

    return render(request, 'core/news.html', {'articles': articles, 'keyword': keyword})




# @login_required
# def save_selected_articles(request):
#     """
#     Save selected articles to the user's profile.
#     """
#     if request.method == 'POST':
#         # Get the list of selected article titles from the form
#         selected_articles_titles = request.POST.getlist('selected_articles')

#         # Get the Article objects based on the selected titles
#         selected_articles = Article.objects.filter(title__in=selected_articles_titles)

#         # Add the selected articles to the user's profile
#         user_profile = request.user.profile  # Access the user's profile
#         user_profile.saved_articles.add(*selected_articles)  # Add selected articles to saved_articles field

#         return redirect('profile_detail')  # Redirect to profile page to view saved articles

#     # If GET request, redirect to the article selection page
#     return redirect('news_view')  # Assuming you have a view that displays articles to choose from



from django.shortcuts import render, redirect, get_object_or_404


@login_required
def save_article(request, article_id):
    """
    Save a selected article to the user's profile.
    """
    article = get_object_or_404(Article, id=article_id)

    # Get the user's profile
    user_profile = request.user.profile  # Access the logged-in user's profile

    # Add the article to the saved_articles field in the user's profile
    user_profile.saved_articles.add(article)

    return redirect('news_view')  # Redirect back to the news page or to the profile page


