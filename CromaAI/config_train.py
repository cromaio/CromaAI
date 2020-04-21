database = {
    'db_name': 'cromaAIdb',
    'host': 'localhost',
    'port': 27018
    }

model_name = 'redaccion_2020'
spacy_model = 'ML_models/model-azure-aws-50k'
publication_name = 'Redaccion'
chunk_size = 1_000

enabled_processes = {
    "tokenize_articles": False,
    "vectorizers": False,
    "w2v": False,
    "faiss": True
}

vectorizeers_hyperparams = {
    "min_df": 1,
    "max_df": 1.0
}

w2v_hyperparams = {
    "size": 100,
    "epochs": 6,
    "min_count":2, 
    "workers":4, 
}