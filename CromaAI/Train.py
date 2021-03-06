from models import Article, Publication
from pathlib import Path
import glob
import spacy
import os
import pickle
import numpy as np
from CromaGNI import CromaGNI
from RelatedArticles import RelatedArticles
from gensim.models import Word2Vec, FastText, Doc2Vec
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import scipy.sparse
import faiss
import numpy as np

class SentenceIterator: 
    def __init__(self, folder, files=None, ids=False, debug=True):
        self.debug = debug
        self.ids = ids
        self.iteration = 1
        self.folder = folder
        if files is not None:
            self.files = files
        else:
            self.files, self.ids_files = self.get_files()
        
        
        
    def get_files(self):
        files = []
        ids_files = []
        for file in Path(self.folder).rglob('*'):
            file_name = str(file)
            if 'ids' in file_name:
                ids_files.append(file_name)
            elif 'all' in file_name:
                files.append(file_name)
        return np.sort(files), np.sort(ids_files)
    
    def __iter__(self): 
        for j, (file, ids_file) in enumerate(zip(self.files, self.ids_files)):
            if self.debug:
                print(f'\r{j} - {file} loaded', end='')
            articles = np.load(f'{file}', allow_pickle=True)
            ids = np.load(f'{ids_file}')
            for i, (article, art_id) in enumerate(zip(articles, ids)): 
                if self.debug:
                    print(f'\r{j+1} - {i+1} - {file}', end='')
                if self.ids:
                    yield article, art_id
                else:
                    yield article
        if self.debug:
            print()
            print(f'{self.iteration} finished!')
        self.iteration += 1


class Train:
    def __init__(self, spacy_model_path, publication_name, chunk_size, models_folder, faiss_folder, w2v_model_file):
        # chunk size to generate splits of dataset to save
        self.faiss_folder = faiss_folder
        self.spacy_model_path = spacy_model_path
        self.nlp = spacy.load(spacy_model_path)
        self.chunk_size = chunk_size
        self.dst_folder = models_folder
        if not os.path.exists(self.dst_folder):
            os.makedirs(self.dst_folder)
        self.publication_name = publication_name
        self.w2v_model = w2v_model_file
    
#     def get_filename_prefix(self):
#         return self.dst_folder.replace("/", "")
    
    @staticmethod
    def article2text(article):
        title = CromaGNI.preprocess_aws_data(article['title'])
        text = CromaGNI.preprocess_aws_data(article['text'])
        # text = title + '\n' + text
        return text, title
    
    @staticmethod
    def get_article(article):
        return article
    
    def get_training_folder(self):
        return f'{self.dst_folder}training_data/'

    def get_tokenized_articles_list(self):
        training_data_folder = self.get_training_folder()
        ids = []
        n_files = 0
        if os.path.exists(training_data_folder):
            files = glob.glob(f'{training_data_folder}*id*')
            n_files = len(files)
            for file_name in files:
                ids = ids + list(np.load(file_name))
        return ids, n_files
            
        
    def save_training_tokens(self):
        already_tokenized_ids, n_files = self.get_tokenized_articles_list()
        print(f'Found {len(already_tokenized_ids)} already tokenized articles')
        try:
            publication = Publication.objects(name=self.publication_name).get()
        except:
            print('Problemas buscando publicación. Creo la publicación? Tiene el mismo nombre en config y config_train')
            return -1
        print(publication)
        articles = Article.objects(publication=publication).order_by('-publish_date')
        N = articles.count()
        
        if N==0:
            print(f'No hay articulos en la base de datos. Correr fetch_articles')
            return -1
        else:
            print(f'Total number to tokenize: {N}')
        # N_chunks = np.ceil(N/self.chunk_size)
        texts = []
        titles = []
        texts_titles = []
        ids = []
        # Es necesario para arrancar con la cantidad que había +1
        chunk = n_files
        training_data_folder = self.get_training_folder()
        if not os.path.exists(training_data_folder):
            os.makedirs(training_data_folder)
            
        for i, article in enumerate(articles):
            if len(ids)%self.chunk_size == 0 and len(ids)!=0:
                chunk+=1
                file_name = f'{training_data_folder}all_{chunk}.npy'
                np.save(file_name, texts_titles)
                texts_titles = []
                file_name = f'{training_data_folder}titles_{chunk}.npy'
                np.save(file_name, titles)
                titles = []
                file_name = f'{training_data_folder}content_{chunk}.npy'
                np.save(file_name, texts)
                texts = []
                
        
                print()
                print(f'{file_name} saved!')
                file_name_ids = f'{training_data_folder}ids_{chunk}.npy'
                np.save(file_name_ids, ids)
                ids = []
            if str(article['id']) not in already_tokenized_ids:
                text, title = Train.article2text(article)
                print(f'\r{i}/{N}', end=' ')
                doc_text = self.nlp(text)
                doc_title = self.nlp(title)
                tokens_text = RelatedArticles.doc2tokens(doc_text)
                tokens_title = RelatedArticles.doc2tokens(doc_title)
                texts.append(tokens_text)
                titles.append(tokens_title)
                texts_titles.append(tokens_title+['\n']+tokens_text)
                ids.append(str(article['id']))
        
        if len(ids)>0:
            chunk+=1
            file_name = f'{training_data_folder}all_{chunk}.npy'
            np.save(file_name, texts_titles)
            texts_titles = []
            file_name = f'{training_data_folder}titles_{chunk}.npy'
            np.save(file_name, titles)
            titles = []
            file_name = f'{training_data_folder}content_{chunk}.npy'
            np.save(file_name, texts)
            texts = []
            print()
            print(f'{file_name} saved!')
            file_name_ids = f'{training_data_folder}ids_{chunk}.npy'
            np.save(file_name_ids, ids)

        return 0
        
    def Word2Vec(self, size=100, min_count=2, workers=4, epochs=6):
        training_data_folder = self.get_training_folder()
        sentence_iterator = SentenceIterator(training_data_folder)
        model = Word2Vec(sentence_iterator, size=size, min_count=min_count, workers=workers, iter=epochs)
        w2v_dst_folder = f'{self.dst_folder}w2vect/'
        if not os.path.exists(w2v_dst_folder):
            os.makedirs(w2v_dst_folder)
        w2v_filename = f'{w2v_dst_folder}epochs_{epochs}-min_count_{min_count}.wv'
        model.save(w2v_filename)
        print(f'Model saved in {w2v_filename}')
        self.w2v_model = model
        return model
    
    
    
    def train_vectorizers(self, min_df=1, max_df=1.0):
        sentence_iterator = SentenceIterator(self.get_training_folder())
        count_vectorizer = CountVectorizer(analyzer=Train.get_article, min_df=min_df, max_df=max_df)
        count_vectorizer_matrix = count_vectorizer.fit_transform(sentence_iterator)
        
        print(f'Matrix size: {count_vectorizer_matrix.shape}')
        vect_folder = f'{self.dst_folder}vectorizers/'
        if not os.path.exists(vect_folder):
            os.makedirs(vect_folder)
        filename = f'{vect_folder}count_vectorizer-max_df_{max_df}-min_df_{min_df}.pickle'
        pickle.dump(count_vectorizer, open(filename, "wb"))
        print(f'Saved to: {filename}')
        
        
        filename_matrix = f'{vect_folder}count_vectorizer_matrix-max_df_{max_df}-min_df_{min_df}.npz'
        scipy.sparse.save_npz(filename_matrix, count_vectorizer_matrix)
        
        tfidf_transformer = TfidfTransformer(norm=None, use_idf=True, smooth_idf=True, sublinear_tf=False)
        tfidf_vectorizer_matrix = tfidf_transformer.fit_transform(count_vectorizer_matrix)
        words_tfidf = np.array(tfidf_vectorizer_matrix.sum(axis=0)/count_vectorizer_matrix.sum(axis=0))[0]
        self.word2tfidf = {k: words_tfidf[v] for k, v in count_vectorizer.vocabulary_.items()}
        np.save(f'{vect_folder}token2tfidf-max_df_{max_df}-min_df_{min_df}', self.word2tfidf)
        
        return count_vectorizer, count_vectorizer_matrix
    
    def add_faiss_vectors(self, w2vect_model, tfidf=True):
        ### Si la carpeta no existe, la creo
        faiss_folder = f'{self.dst_folder}faiss/'
        if not os.path.exists(faiss_folder):
            os.makedirs(faiss_folder)
        ###
        if w2vect_model is None:
            w2v_dst_folder = f'{self.dst_folder}w2vect/'
            w2vect_file = glob.glob(w2v_dst_folder+'*.wv')[0]
        else:
            w2vect_file = w2vect_model

        faiss_filename = f'{faiss_folder}indexes' # Indeces de faiss w2v
        faiss_tfidf_filename = f'{faiss_folder}indexes_tfidf' # Indeces de faiss  TFIDF
        faiss_ids_filename = f'{faiss_folder}ids.npy' # Ids de mongo
        
        if os.path.exists(faiss_filename) and os.path.exists(faiss_ids_filename):
            # Si ya existe data de faiss la cargo
            faiss_articles_ids = np.load(faiss_ids_filename) # ids mongo
            faiss_index2 = faiss.read_index(faiss_filename) # indices de faiss w2v
            # Si ya existe el de tfidf
            if os.path.exists(faiss_tfidf_filename):
                faiss_index2_tfidf = faiss.read_index(faiss_tfidf_filename) # indices de faiss tfidf
                if not tfidf:
                    print('tfidf file exists but tfidf is set to False')
            else:
                if tfidf:
                    print('tfidf file not found while flag is True')
        else:
            # No existen datos de faiss. Inicializo todo vacio
            faiss_articles_ids = []
            faiss_index2 = None
            faiss_index2_tfidf = None
        
        
        vect_folder = f'{self.dst_folder}vectorizers/'
        token2tfidf_file = glob.glob(vect_folder+'token2tfidf*.npy')[0]
        # word_vect_dim = self.w2v_model.wv.vector_size

        related_articles = RelatedArticles(
            spacy_model_path=self.spacy_model_path, 
            gensim_model_path=w2vect_file, 
            token2tfidf_path=token2tfidf_file
        )
        print(f'using: {w2vect_file}')
        xb = []
        xb_tfidf = []
        new_article_ids = []
        sentence_iterator = SentenceIterator(self.get_training_folder(), ids=True, debug=False)
        for i, (article_tokens, art_id) in enumerate(sentence_iterator):
            print(f'\rArticulo: {i}', end='')
            if art_id not in faiss_articles_ids:
                new_article_ids.append(art_id)
                vect, vect_tfidf = related_articles.tokens2vect(article_tokens)
                xb.append(vect)
                xb_tfidf.append(vect_tfidf)
        
        xb = np.array(xb, dtype='float32')
        xb_tfidf = np.array(xb_tfidf, dtype='float32')

        # Update articles ids file
        all_articles_ids = list(faiss_articles_ids) + new_article_ids
        np.save(faiss_ids_filename, all_articles_ids)
        #####
        N_vects = len(new_article_ids)
        if len(faiss_articles_ids) == 0:
            # No había nada guardado
            ids = np.arange(N_vects).astype('int64')
        else:
            # Habia ya datos guardados
            ids = np.arange(N_vects).astype('int64') + faiss_index2.ntotal

        word_vect_dim = xb.shape[1]
        if len(faiss_articles_ids) == 0:
            index = faiss.IndexFlatIP(word_vect_dim) 
            faiss_index2 = faiss.IndexIDMap(index)
            if tfidf:
                index_tfidf = faiss.IndexFlatIP(word_vect_dim) 
                faiss_index2_tfidf = faiss.IndexIDMap(index_tfidf)
                
        faiss_index2.add_with_ids(xb, ids)
        faiss.write_index(faiss_index2, faiss_filename)
        
        if tfidf:
            faiss_index2_tfidf.add_with_ids(xb_tfidf, ids)
            faiss.write_index(faiss_index2_tfidf, faiss_tfidf_filename)

    def add_faiss_vectors_db(self, w2vect_model, vectorizers_folder='vectorizers', tfidf=True):
        ### Si la carpeta no existe, la creo
        faiss_folder = f'{self.dst_folder}{self.faiss_folder}/'
        if not os.path.exists(faiss_folder):
            os.makedirs(faiss_folder)
        ###

        if w2vect_model is None:
            # Usa el de la clase
            w2vect_file = self.w2v_model
        else:
            # Usa el que se le pasa como parámetro
            w2vect_file = w2vect_model
        
        vect_folder = f'{self.dst_folder}{vectorizers_folder}/'
        token2tfidf_file = glob.glob(vect_folder+'token2tfidf*.npy')[0]

        related_articles = RelatedArticles(
            spacy_model_path=self.spacy_model_path, 
            gensim_model_path=w2vect_file, 
            token2tfidf_path=token2tfidf_file
        )
        
        total_vectors = 0
        vector_size = related_articles.w2v_model.wv.vector_size

        faiss_filename = f'{faiss_folder}indexes' # Indeces de faiss w2v
        faiss_tfidf_filename = f'{faiss_folder}indexes_tfidf' # Indeces de faiss  TFIDF
        
        if os.path.exists(faiss_filename):
            # Si ya existe data de faiss la cargo
            faiss_indexes = faiss.read_index(faiss_filename) # indices de faiss w2v
            # Si ya existe el de tfidf
            if os.path.exists(faiss_tfidf_filename):
                faiss_indexes_tfidf = faiss.read_index(faiss_tfidf_filename) # indices de faiss tfidf
                if not tfidf:
                    print('tfidf file exists but tfidf is set to False')
            else:
                if tfidf:
                    print('tfidf file not found while flag is True')
        else:
            # No existen datos de faiss. Creo archivos
            index = faiss.IndexFlatIP(vector_size) 
            faiss_indexes = faiss.IndexIDMap(index)
            if tfidf:
                index_tfidf = faiss.IndexFlatIP(vector_size) 
                faiss_indexes_tfidf = faiss.IndexIDMap(index_tfidf)
        
        print(f'using: {w2vect_file}')
        total_vectors = faiss_indexes.ntotal
        total_vectors_tfidf = faiss_indexes_tfidf.ntotal

        xb = []
        xb_tfidf = []
        faiss_count = total_vectors
        faiss_count_tfidf = total_vectors_tfidf
        ids = []
        ids_tfidf = []
        already_got_faiss_in_db = 0
        sentence_iterator = SentenceIterator(self.get_training_folder(), ids=True, debug=True)
        for i, (article_tokens, art_id) in enumerate(sentence_iterator):
            print(f'\rArticulo: {i}', end='')
            article = Article.objects(id=art_id).get()
            if article['faiss_index'] is None:
                vect, vect_tfidf = related_articles.tokens2vect(article_tokens)
                xb.append(vect)
                xb_tfidf.append(vect_tfidf)
                article['faiss_index'] = faiss_count
                article['faiss_index_tfidf'] = faiss_count_tfidf
                ids.append(faiss_count)
                ids_tfidf.append(faiss_count_tfidf)
                article.save()
                faiss_count = faiss_count + 1
                faiss_count_tfidf = faiss_count_tfidf + 1
            else:
                already_got_faiss_in_db = already_got_faiss_in_db + 1
        
        if len(ids) == 0:
            # No se agrego nada por que ya estaba
            return total_vectors, len(ids), already_got_faiss_in_db

        xb = np.array(xb, dtype='float32')
        xb_tfidf = np.array(xb_tfidf, dtype='float32')

        ids = np.array(ids, dtype='int64')
        ids_tfidf = np.array(ids_tfidf, dtype='int64')

        faiss_indexes.add_with_ids(xb, ids)
        faiss.write_index(faiss_indexes, faiss_filename)
        
        faiss_indexes_tfidf.add_with_ids(xb_tfidf, ids_tfidf)
        faiss.write_index(faiss_indexes_tfidf, faiss_tfidf_filename)

        return total_vectors, len(ids), already_got_faiss_in_db