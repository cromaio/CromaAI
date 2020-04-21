import config_train
from mongoengine import connect

from Train import Train

if __name__ == "__main__":
    connect(config_train.database['db_name'], 
            host=config_train.database['host'], 
            port=config_train.database['port'])
    train = Train(config_train.spacy_model, config_train.publication_name, config_train.chunk_size, 
                config_train.model_name)

    if config_train.enabled_processes['tokenize_articles']:
        print('tokenizing articles ...')
        train.save_training_tokens()
    
    if config_train.enabled_processes['vectorizers']:
        print('Training vectorizers ...')
        
        train.train_vectorizers(min_df=config_train.vectorizeers_hyperparams['min_df'], 
                                max_df=config_train.vectorizeers_hyperparams['max_df'])

    if config_train.enabled_processes['w2v']:
        print('Training w2vect ...')

        train.Word2Vec(
            size=config_train.w2v_hyperparams['size'],
            epochs=config_train.w2v_hyperparams['epochs'],
            min_count=config_train.w2v_hyperparams['min_count'], 
            workers=config_train.w2v_hyperparams['workers'], 
        )

    if config_train.enabled_processes['faiss']:
        print('Training faiss ...')
        train.add_faiss_vectors()