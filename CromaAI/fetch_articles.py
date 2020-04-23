import sys
config_found = True
sys.path.append('..')
try:
    import config
except ModuleNotFoundError:
    config_found = False

from mongoengine import connect
from ArticlesFetch import fetch_articles, iProfesional_to_db, wordpress_to_db, get_wp_url, get_iProfesional_url, get_iProfesional_articles, get_wp_articles
from models import Publication

def create_publications():
    connect(config.database['db_name'], host=config.database['host'], port=config.database['port'])    
    print('Verificando publicaciones')
    for pub_dict in config.publications:
        pub_list = Publication.objects(name=pub_dict.get('name'))
        if len(pub_list) == 0:
            new_pub = Publication(name=pub_dict.get('name'), url=pub_dict.get('url'), location=pub_dict.get('location'), 
            fetch_method=pub_dict.get('fetch_method'), api_url=pub_dict.get('api_url'))
            new_pub.save()
            print(f'Publication creada: {pub_dict.get("name")}')
        else:
            exitent_pub = pub_list.get()
            exitent_pub.name = pub_dict.get('name')
            exitent_pub.url = pub_dict.get('url')
            exitent_pub.location = pub_dict.get('location')
            exitent_pub.fetch_method = pub_dict.get('fetch_method')
            exitent_pub.api_url = pub_dict.get('api_url')
            exitent_pub.save()
            print(f'Publication Modificada: {pub_dict.get("name")}')
    pubs = Publication.objects()
    print(f'Total de publicaciones en la db: {len(pubs)}')
    for p in pubs:
        print(f'- {p.name}')
    print('#################################')


def main():
    if not config_found:
        print('config.py file must be present')
        return

    print('config.py found')    
    create_publications()
    if len(sys.argv) < 2 and config.fetching_config['publication'] is None:
        print('You need to pass publication_name as argv. For example:')
        print('python fetch_wordpress_articles.py "CNN esp"')
        return

    if len(sys.argv) == 2:
        pub_name = sys.argv[1]
    else:
        pub_name = config.fetching_config['publication']

    pub = Publication.objects(name=pub_name).get()
    print(f'url ro fetch: {pub.api_url}')
    if pub == 'iProfesional':
        art_to_db=iProfesional_to_db
        get_url=get_iProfesional_url
        get_articles=get_iProfesional_articles
    else:
        art_to_db=wordpress_to_db
        get_url=get_wp_url
        get_articles=get_wp_articles
    fetch_articles(
        pub_name, 
        art_to_db=art_to_db, 
        get_url=get_url, 
        get_articles=get_articles, 
        api_url=pub.api_url,
        date_after=config.fetching_config['date_after'],
        date_before=config.fetching_config['date_before']
    )

if __name__ == "__main__":
    main()