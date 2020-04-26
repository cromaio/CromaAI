import requests
from mongoengine.queryset.visitor import Q
import datetime
from models import Article, Publication

def get_wp_url_by_ids(url_endpoint, ids):
    """
    Gets wordpress url
  
    Gets wordpress url to get articles by ids
  
    Parameters: 
    url_endpoint (str): endpoint url  
    ids (list): list of ids
  
    Returns: 
    str: url to call API
    """
    url = url_endpoint + 'posts?'
    return url + '&'.join([f'include[]={_id}' for _id in ids])

def get_article_by_cms_id(publication_name, cms_id):
    """
    Gets article from publication API by cmd_id
  
    Gets an article from publication API (like wordpress for example). At the moment only support wordpress 
  
    Parameters: 
    publication_name (str): name of publication 
    cms_id (str): id of article to fetch 
  
    Returns: 
    json: article as JSON
    """
    api_url = Publication.objects(name=publication_name).get()['api_url']
    url_by_ids = get_wp_url_by_ids(api_url, [cms_id])
    response = requests.get(url_by_ids)
    return response.json()[0]

def iProfesional_to_db(art, publication_name='iProfesional'):
    """
    Converts iProfesional data to mongodb format
  
    Parameters: 
    art (json): iProfesional article as JSON
    publication_name (str): should be iProfesional
  
    Returns: 
    json: article as Article instance
    """
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
    """
    Converts wordpress data to mongodb format
  
    Parameters: 
    art (json): wordpress article as JSON
    publication_name (str): name of publication
  
    Returns: 
    json: article as Article instance
    """
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
    


def get_wp_url(url_endpoint, page=1, per_page=10, date_after=None, date_before=None):
    """
    Gets formated wordpress url
  
    Gets wordpress url to get multiple articles by with paging and dates
  
    Parameters: 
    url_endpoint (str): endpoint url  
    page (int): page number - First page is 1
    per_page (int): number of articles per page
    date_after (str): Get articles after this date with format: '%Y-%m-%d'
    date_before (str): Get articles before this date with format: '%Y-%m-%d'
  
    Returns: 
    str: url to call wordpress API
    """
    if date_after is None:
            date_after = datetime.date.fromtimestamp(-10000000000)
    elif type(date_after) == str:
        date_after = datetime.datetime.strptime(date_after, '%Y-%m-%d')
        
    if date_before is None:
        date_before = datetime.datetime.now()
    elif type(date_before) == str:
        date_before = datetime.datetime.strptime(date_before, '%Y-%m-%d')

    date_str = date_after.strftime("%Y-%m-%dT%H:%M:%S%Z")
    date_before = date_before.strftime("%Y-%m-%dT%H:%M:%S%Z")
    return f'{url_endpoint}posts?page={page}&per_page={per_page}&orderby=date&order=asc&after={date_str}&before={date_before}'


def get_iProfesional_url(url_endpoint, page, per_page, date_after, date_before):
    """
    Gets formated iProfesional url
  
    Gets iProfesional url to get multiple articles by with paging and dates
  
    Parameters: 
    url_endpoint (str): endpoint url  
    page (int): page number - First page is 1
    per_page (int): number of articles per page
    date_after (str): Get articles after this date with format: '%Y-%m-%d'
    date_before (str): Get articles before this date with format: '%Y-%m-%d'
  
    Returns: 
    str: url to call iProfesional API
    """
    if type(date_after) == str:
        date_after = datetime.datetime.strptime(date_after, '%Y-%m-%d')
    if type(date_before) == str:
        date_before = datetime.datetime.strptime(date_before, '%Y-%m-%d')
        
    date_str = date_after.strftime("%Y-%m-%d")
    if date_before is None:
        today = datetime.datetime.now()
        end_date_str = today.strftime("%Y-%m-%d")
    else:
        end_date_str = date_before
    
    url = f'{url_endpoint}?start={date_str}&end={end_date_str}&limit={per_page}&page={page}'
    return url

def get_iProfesional_articles(response):
    """
    Gets iProfesional articles and total pages from API response
  
    This makes sense to make the get_articles uniform from diferent publications
  
    Parameters: 
    response (json): response from iProfesional API
    
    Returns: 
    json: articles as json
    int: number of pages 
    """
    json_response = response.json()
    articles = json_response['data']['news']
    return articles, int(json_response['total_pages'])

def get_wp_articles(response):
    """
    Gets wp articles and total pages from API response
  
    This makes sense to make the get_articles uniform from diferent publications
  
    Parameters: 
    response (json): response from wp API
    
    Returns: 
    json: articles as json
    int: number of pages 
    """
    articles = response.json()
    return articles, int(response.headers['X-WP-TotalPages'])

def fetch_articles(publication_name, art_to_db=wordpress_to_db, get_url=get_wp_url, get_articles=get_wp_articles, api_url=None, per_page = 50, starting_page=1, date_after=None, date_before=None):
    """
    Fetch articles from publication
  
    Fetch articles from publication by date and independent of publication (wordpress, iProfesional). Saves them to mongodb database
  
    Parameters: 
    publication_name (str): name of publication in db. Needs it to get api url from db
    art_to_db (func): iProfesional_to_db or wordpress_to_db are the only supported for the moment 
    get_url (func):  get_wp_url or get_iProfesional_url are the only supported for the moment 
    get_articles (func): get_iProfesional_articles or get_wp_articles are the only supported for the moment 
    api_url (str): if not None rewrite api_url in db
    per_page (int): number of articles per page
    starting_page (int): page number - First page is 1
    date_after (str): Get articles after this date with format: '%Y-%m-%d'
    date_before (str): Get articles before this date with format: '%Y-%m-%d'

    Returns: 
    None
    """
    publication = Publication.objects(name=publication_name).get()
    if api_url is not None:
        publication.api_url = api_url
        publication.save()
    
    articles=Article.objects(publication=publication).order_by('-publish_date').limit(1).first()
    if articles is None or len(articles) == 0:
        # No hay articulos
        print('No articles')
        if date_after is None:
            date_after = datetime.date.fromtimestamp(-10000000000)
    else:
        if date_after is None:
            date_after = articles['publish_date']
    
    if date_before is None:
        date_before = datetime.datetime.now()
        
    url_endpoint = publication.api_url
    if url_endpoint is None:
        print('api_url not defined in publication')
        return
    page = starting_page
    total_pages = None
    while True:
        url = get_url(url_endpoint, page, per_page, date_after, date_before)
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
                    
        if page == total_pages or total_pages == 0:
            break
        page+=1
        if 'code' in articles:
            print()
            print(articles['code'])
            break



