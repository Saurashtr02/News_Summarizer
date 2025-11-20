import requests
import spacy
from nltk.corpus import stopwords
import nltk
from spacy.matcher import Matcher


nltk.download('stopwords')

nlp = spacy.load('en_core_web_sm')


def fetch_articles_from_newsapi(query, api_key,page = 1, page_size=2):
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={api_key}'
    response = requests.get(url,{'language': 'en'})
    return response.json().get('articles', [])


def fetch_articles_from_currents(query, api_key, country='us',page=1, page_size = 2):
    url = f'https://api.currentsapi.services/v1/search'
    params = {
        'apiKey': api_key,
        'keyword': query,
        'country': country,
        'language': 'en'
    }
    
    response = requests.get(url, params=params)
    return response.json().get('news', [])



def aggregate_articles(query, newsapi_key, currents_key, country="US"):

    newsapi_articles = fetch_articles_from_newsapi(query, newsapi_key)

    currents_articles = fetch_articles_from_currents(query, currents_key, country)

    all_articles = newsapi_articles + currents_articles

    for article in all_articles:
        if 'urlToImage' in article:
            article['image_url'] = article['urlToImage']  
        elif 'image' in article:
            article['image_url'] = article['image']  
        else:
            article['image_url'] = None  

    return all_articles



stop_words = set(stopwords.words('english'))


def extract_named_entities_from_text(text):

    doc = nlp(text)
    meaningful_keywords = []

    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'EVENT']:
            if not ent.text.lower() in stop_words:
                meaningful_keywords.append(ent.text)

    for np in doc.noun_chunks:
        if not np.text.lower() in stop_words:
            meaningful_keywords.append(np.text)
    
    action_verbs = [
        'claim', 'argue', 'assert', 'state', 'report', 'believe', 'suggest', 
        'declare', 'insist', 'contend', 'prove', 'dispute', 'allege', 'affirm', 
        'deny', 'accuse', 'maintain', 'reveal', 'question', 'emphasize', 
        'highlight', 'suggest', 'warn', 'confirm'
    ]
    for token in doc:
        if token.pos_ == 'VERB' and token.lemma_ in action_verbs:
            meaningful_keywords.append(token.lemma_)

    for token in doc:
        if token.pos_ == 'ADJ' and token.text.lower() not in stop_words:
            meaningful_keywords.append(token.text)

    return list(set(meaningful_keywords))



def extract_claims_from_text(text):
    doc = nlp(text)
    claims = []


    matcher = Matcher(nlp.vocab)

    patterns = [
        #  (SVO) pattern
        [{"dep": "nsubj"}, {"dep": "ROOT", "pos": "VERB"}, {"dep": "dobj"}],

        # Claims with action verbs 
        [{"dep": "nsubj"}, {"dep": "ROOT", "pos": "VERB"}],  # Simple verb 
        [{"dep": "nsubj"}, {"dep": "ROOT", "pos": "VERB"}, {"dep": "attr", "pos": "ADJ"}],  # Descriptive statements
        [{"dep": "nsubj"}, {"dep": "aux", "pos": "VERB"}, {"dep": "ROOT", "pos": "VERB"}],  # auxiliary verbs 
        
        # Conditional Claims, if or then statements
        [{"dep": "advmod", "pos": "ADV"}, {"dep": "nsubj"}, {"dep": "ROOT", "pos": "VERB"}],

        # Imperative Claims, states that statements
        [{"dep": "nsubj"}, {"dep": "ROOT", "pos": "VERB"}, {"dep": "ccomp", "pos": "VERB"}],  
        
        # preposition based
        [{"dep": "nsubj"}, {"dep": "ROOT", "pos": "VERB"}, {"dep": "prep", "pos": "ADP"}],  

        # question types
        [{"dep": "aux", "pos": "VERB"}, {"dep": "nsubj"}, {"dep": "ROOT", "pos": "VERB"}]
    ]

    for pattern in patterns:
        matcher.add("ClaimPattern", [pattern])

    matches = matcher(doc)

    # Extract claims 
    for match_id, start, end in matches:
        span = doc[start:end]
        claim = ' '.join([token.text for token in span])

        if len(claim.split()) > 2:
            claims.append(claim)

    return claims


def extract_keywords_and_claims(text):
    keywords = extract_named_entities_from_text(text)
    claims = extract_claims_from_text(text)

    return keywords, claims
