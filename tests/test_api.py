import requests
import datetime
import json
import time

def eval_func(func, expected, params=[]):
    json_response = func(*params)
    if type(expected) == list:
        if (json_response['status'] in ['ok', 'warning']):
            print('***', func.__name__, '\t--->\t', 'passed')
        else:
            print('***', 'test_add_article_from_wp_post', 'NOT passed')
    elif type(expected) == str and expected=='article':
        if 'article' in json_response:
            print('***', func.__name__, '\t--->\t', 'passed')
            return json_response['article']['_id']['$oid']
        else:
            print('***', 'test_add_article_from_wp_post', 'NOT passed')
    elif type(expected) == str and expected=='articles':
        if 'articles_page' in json_response:
            print('***', func.__name__, '\t--->\t', 'passed')
            return
        else:
            print('***', 'test_add_article_from_wp_post', 'NOT passed')

    return json_response

def convert_to_croma_api(_id, title, summary, content, date, link, author=None):
    art_simplified = {}
    art_simplified['id'] = _id
    art_simplified['title'] = {}
    art_simplified['title']['rendered'] = title

    art_simplified['excerpt'] = {}
    art_simplified['excerpt']['rendered'] = summary

    art_simplified['content'] = {}
    art_simplified['content']['rendered'] = content

    art_simplified['date'] = date #"%Y-%m-%dT%H:%M:%S"
    art_simplified['link'] = link
    art_simplified['author'] = author
    return art_simplified

def get_redaccion_article(_id):
    url = f'https://www.redaccion.com.ar/wp-json/wp/v2/posts?include[]={_id}'
    response = requests.get(url)
    art = response.json()[0]
    return art

def test_add_article_from_wp_post(_id='29897'):
    art = get_redaccion_article(_id)
    art_simplified = convert_to_croma_api(
        art['id'], 
        art['title']['rendered'],
        art['excerpt']['rendered'],
        art['content']['rendered'],
        art['date'],
        art['link']
    )
    response = requests.post('http://localhost:5000/api/v1/add', json=art_simplified)
    return response.json()

def test_add_article_from_wp_get(_id='29897'):
    response = requests.get(f'http://localhost:5000/api/v1/add?cmsid={_id}')
    return response.json()

def test_get_article_by_cms_id(_id='29897'):
    response = requests.get(f'http://localhost:5000/api/v1/article?cmsid={_id}')
    return response.json()

def test_get_articles():
    response = requests.get('http://localhost:5000/api/v1/articles')
    return response.json()

def test_get_article_by_id(_id):
    response = requests.get(f'http://localhost:5000/api/v1/article?id={_id}')
    return response.json()

def test_get_related_by_cmsid(_id):
    response = requests.get(f'http://localhost:5000/api/v1/related?cmsid={_id}')
    return response.json()

def test_get_add_faiss(_id):
    response = requests.get(f'http://localhost:5000/api/v1/add_faiss?cmsid={_id}')
    return response.json()

def test_all():
    cms_id='29897' # Redacción wordpress id
    eval_func(test_add_article_from_wp_post, ['ok', 'warning'], [cms_id])
    eval_func(test_add_article_from_wp_get, ['ok', 'warning'], [cms_id])
    mongo_id = eval_func(test_get_article_by_cms_id, 'article', [cms_id])
    mongo_id = eval_func(test_get_article_by_id, 'article', [mongo_id])
    eval_func(test_get_articles, 'articles')

def get_wordpress_ids(cms_url='https://www.redaccion.com.ar/wp-json/wp/v2/posts'):
    response = requests.get(cms_url)
    ids = []
    for art in response.json():
        ids.append(art['id'])
    return ids

def from_scratch():
    # ids = get_wordpress_ids()
    ids = [80659, 80634, 80109, 80162, 80604, 80416, 80193, 80453, 80493, 80451]
    print(ids)
    for _id in ids:
        print(test_add_article_from_wp_post(_id))
    
    json_resp = test_get_article_by_cms_id(ids[0])
    mongo_id = json_resp['article']['_id']['$oid']
    test_get_article_by_id(mongo_id)
    json_response = test_get_related_by_cmsid(ids[0])
    print(json_response)
    json_response = test_get_related_by_cmsid(ids[1])
    print(json_response)

def test_faiss():
    ids = [80659, 80634, 80109, 80162, 80604, 80416, 80193, 80453, 80493, 80451]
    print(len(ids))
    for _id in ids:
        print(test_get_add_faiss(_id))

if __name__ == "__main__":
    # from_scratch()
    # test_faiss()
    
    # ids = [80659, 80634, 80109, 80162, 80604, 80416, 80193, 80453, 80493, 80451]

    # for _id in ids:
    #     # json_response = test_get_article_by_cms_id(_id)
    #     # print(json_response['article']['faiss_index'])

    #     json_response = test_get_related_by_cmsid(_id)
    #     print(_id, json_response)

    json_response = test_get_articles()
    for article in json_response['articles_page']:
        cms_id = article['pub_art_id']
        json_response = test_get_related_by_cmsid(cms_id)
        print(cms_id, json_response['related_articles'][0])
        print()



    