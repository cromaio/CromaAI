import config_train
from mongoengine import connect
from models import Article
import numpy as np
from Train import Train, SentenceIterator

def train_all():
    connect(config_train.database['db_name'], 
            host=config_train.database['host'], 
            port=config_train.database['port'])

    # print(f'Cantidad de articlus en db: {len(Article.objects())}')

    train = Train(config_train.spacy_model, config_train.publication_name, config_train.chunk_size, 
                config_train.models_folder, config_train.faiss_folder, config_train.word2vect_model)

    if config_train.enabled_processes['tokenize_articles']:
        print('tokenizing articles ...')
        error = train.save_training_tokens()
        if error<0:
            return
    
    if config_train.enabled_processes['vectorizers']:
        print('Training vectorizers ...')
        
        train.train_vectorizers(min_df=config_train.vectorizeers_hyperparams['min_df'], 
                                max_df=config_train.vectorizeers_hyperparams['max_df'])

    if config_train.enabled_processes['w2v'] and config_train.word2vect_model is None:
        print('Training w2vect ...')

        train.Word2Vec(
            size=config_train.w2v_hyperparams['size'],
            epochs=config_train.w2v_hyperparams['epochs'],
            min_count=config_train.w2v_hyperparams['min_count'], 
            workers=config_train.w2v_hyperparams['workers'], 
        )

    if config_train.enabled_processes['faiss']:
        print('Training faiss ...')
        total_vectors, added_to_faiss, already_got_faiss_in_db = train.add_faiss_vectors_db(config_train.word2vect_model)
        print(f'Faiss tenía {total_vectors} vectores, se agregaron {added_to_faiss} y se intentaron agregar {already_got_faiss_in_db} que ya estaban')

if __name__ == "__main__":


    train_all()