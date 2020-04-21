import requests
from mongoengine.queryset.visitor import Q
import datetime
from models import Article, Publication

def iProfesional_to_db(art, publication_name='iProfesional'):
    publication=Publication.objects(name=publication_name).get()
    publication_id = str(art['id'])
    query = Article.objects(Q(url=art['absoluteUrl']) | Q(publication=publication, pub_art_id=publication_id))
    if len(query)>0:
        # Duplicate!!!
        return None
    article = Article()
    article.title = art['title']
    article.summary = art['summary']
    article.text = art['text']
    article.publish_date = art['publication']
    article.url = art['absoluteUrl']
    if type(art['author']) == str:
        article.author = [art['author']]
    elif type(art['author']) == list:
        article.author = art['author']
    else:
        print('author error')
    # article.keywords = art['keywords']
    # article.categories = art['title']
    article.publication = publication
    
    article.pub_art_id = publication_id
    return article

def wordpress_to_db(art, publication_name):
    publication=Publication.objects(name=publication_name).get()
    query = Article.objects(Q(url=art['link']) | Q(publication=publication, pub_art_id=str(art['id'])))
    if len(query)>0:
        # Duplicate!!!
        return None
    
    if type(art['content']['rendered']) == bool:
        print('Article with no content')
        return
    article = Article()
    article.title = art['title']['rendered']
    article.summary = art['excerpt']['rendered']
    article.text = art['content']['rendered']
    article.publish_date = datetime.datetime.strptime(art['date'], "%Y-%m-%dT%H:%M:%S")
    article.url = art['link']
    if type(art['author']) == str:
        article.author = [art['author']]
    elif type(art['author']) == list:
        article.author = art['author']
    elif type(art['author']) == int:
        article.author = [str(art['author'])]
    else:
        print('author error')
    # article.keywords = art['keywords']
    # article.categories = art['title']
    article.publication = publication
    publication_id = str(art['id'])
    article.pub_art_id = publication_id
    return article

def get_wp_url(url_endpoint, page, per_page, date):
    date_str = date.strftime("%Y-%m-%dT%H:%M:%S%Z")
    return f'{url_endpoint}posts?page={page}&per_page={per_page}&orderby=date&order=asc&after={date_str}'

def get_iProfesional_url(url_endpoint, page, per_page, date):
    date_str = date.strftime("%Y-%m-%d")
    today = datetime.datetime.now()
    end_date_str = today.strftime("%Y-%m-%d")
    url = f'{url_endpoint}?start={date_str}&end={end_date_str}&limit={per_page}&page={page}'
    return url

def get_iProfesional_articles(response):
    json_response = response.json()
    articles = json_response['data']['news']
    return articles, int(json_response['total_pages'])

def get_wp_articles(response):
    articles = response.json()
    return articles, int(response.headers['X-WP-TotalPages'])

def fetch_articles(publication_name, art_to_db=wordpress_to_db, get_url=get_wp_url, get_articles=get_wp_articles, api_url=None, per_page = 50, starting_page=1):
    publication = Publication.objects(name=publication_name).get()
    if api_url is not None:
        publication.api_url = api_url
        publication.save()
    
    articles=Article.objects(publication=publication).order_by('-publish_date').limit(1).first()
    if articles is None or len(articles) == 0:
        print('No articles')
        date = datetime.date.fromtimestamp(-10000000000)
    else:
        date = articles['publish_date']
        
    url_endpoint = publication.api_url
    if url_endpoint is None:
        print('api_url not defined in publication')
        return
    page = starting_page
    total_pages = None
    while True:
        url = get_url(url_endpoint, page, per_page, date)
        # url = f'{url_endpoint}posts?page={page}&per_page={per_page}&orderby=date&order=asc&after={date_str}'
        
        if total_pages:
            print(f'\rPage: {page}/{total_pages} - {url}', end='')
        else:
            print(f'\rPage: {page} - {url}', end='')
        
        response = requests.get(url)
        articles, total_pages = get_articles(response) # int(response.headers['X-WP-TotalPages'])
        
        for article in articles:
            art = art_to_db(article, publication_name)
            # print(art.publish_date)
            if art is not None:
                art.save()
            else:
                print('\rAlready in DB')
                    
        if page == total_pages:
            break
        page+=1
        if 'code' in articles:
            print()
            print(articles['code'])
            break


