from mongoengine import connect
import config
from models import Publication
import os

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

def create_models_folders():
    root_folder = config.models_folder
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)
        print(f'{root_folder} created')
    else:
        print(f'{root_folder} already created')
    
    mod_folders = [config.faiss_folder, config.w2vect_folder, config.vectorizers_folder, config.ner_folder] 

    for folder in mod_folders:
        folder = f'{root_folder}{folder}'
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f'{folder} created')
        else:
            print(f'{folder} already created')
    

if __name__ == "__main__":
    create_publications()
    create_models_folders()