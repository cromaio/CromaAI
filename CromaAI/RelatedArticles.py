import numpy as np
import faiss
from CromaGNI import CromaGNI
from datetime import datetime
from dateutil.relativedelta import relativedelta
import spacy
from gensim.models import Word2Vec, KeyedVectors
import faiss
from models import Article, Publication
from fast_autocomplete import AutoComplete
import os


        
class RelatedArticles():    
    @staticmethod
    def get_filtered_by_date(articles, distances, days=0, months=0, years=1):
        filter_date = (datetime.now() - relativedelta(days=days, months=months, years=years)).date()
        filtered_articles= []
        filtered_distances = []
        for i, article in enumerate(articles):
            if article.publish_date>filter_date: 
                filtered_articles.append(article)
                filtered_distances.append(distances[i])
        return filtered_articles, np.array(filtered_distances)

    @staticmethod
    def article2text(article):
        title = CromaGNI.preprocess_aws_data(article['title'])
        text = CromaGNI.preprocess_aws_data(article['text'])
        text = title + '\n' + text
        return text
    
    @staticmethod
    def doc2tokens(doc):
        tokens = []
        i = 0
        while i<len(doc):
            t = doc[i]
            tx = t.text
#             print(tx, t.ent_type_, t.ent_iob_, t.pos_, t.ent_kb_id_)
            if t.ent_iob_=='O':
                ent_tex = tx
                i+=1
                if (not t.is_space and '@' not in t.text) or '\n' in t.text: # and t.text != '\n'):
                    if t.is_digit:
                        tokens.append('__DIGIT__')
                    elif '$' in tx:
                        tokens.append('__CURRENCY__')
                    else:
                        tokens.append(ent_tex)
            else:
                ent_tex = ''
                while t.ent_iob_!='O':
                    if t.pos_ == 'DET' and t.ent_iob_=='B':
                        # It is an article
                        tokens.append(tx)
                    else:
                        ent_tex = ent_tex + ' ' + tx
                    i+=1
                    if i<len(doc):
                        t = doc[i]
                        tx = t.text
                    else:
                        break
                ent_tex = ent_tex.strip().replace(' - ', '-')
                tokens.append(ent_tex)
        return tokens
    
    def __init__(self, spacy_model_path=None, gensim_model_path=None, faiss_indexes_path=None, faiss_article_ids_path=None, token2tfidf_path=None):
        if spacy_model_path is not None:
            self.nlp = spacy.load(spacy_model_path)
        if gensim_model_path is not None:
            self.w2v_model = KeyedVectors.load(gensim_model_path, mmap='r')
            model_words, self.model_synonyms = self.prepare_autocomplete()
            self.autocomplete_model = AutoComplete(words=model_words)
        if faiss_indexes_path is not None:
            self.faiss_indexes = faiss.read_index(faiss_indexes_path)
        if faiss_article_ids_path is not None:
            # print(faiss_article_ids_path)
            self.faiss_article_ids = np.load(faiss_article_ids_path)
        if token2tfidf_path is not None:
            self.token2tfidf = np.load(token2tfidf_path, allow_pickle=True).item()
        else:
            self.token2tfidf = None
            
        
        
    def save_training_tokens(self, publication_name, chunk_size = 50_000):
        dst_folder = f'training_data_{publication_name}_{chunk_size}/'
        if not os.path.exists(dst_folder):
            os.makedirs(dst_folder)
        articles = Article.objects(publication=Publication.objects(name=publication_name).get()).order_by('-publish_date')
        N = articles.count()
        N_chunks = np.ceil(N/chunk_size)
        sentences = []
        ids = []
        chunk = 0
        for i, article in enumerate(articles):
            if i%chunk_size == 0 and i!=0:
                chunk+=1
                file_name = f'{dst_folder}tokens_{publication_name}_{chunk}.npy'
                np.save(file_name, sentences)
                sentences = []
                print()
                print(f'{file_name} saved!')
                file_name_ids = f'{dst_folder}tokens_{publication_name}_{chunk}_ids.npy'
                np.save(file_name_ids, ids)
                ids = []

            text = RelatedArticles.article2text(article)
            print(f'\r{i}/{N}', end=' ')
            doc = self.nlp(text)
            sentences.append(RelatedArticles.doc2tokens(doc))
            ids.append(str(article['id']))
        chunk+=1
        file_name = f'{dst_folder}tokens_{publication_name}_{chunk}.npy'
        np.save(file_name, sentences)
        sentences = []
        print()
        print(f'{file_name} saved!')
        file_name_ids = f'{dst_folder}tokens_{publication_name}_{chunk}_ids.npy'
        np.save(file_name_ids, ids)
        ids = []

    def get_autocomplete_words_list(self, text):
        autocomplets = self.autocomplete_model.search(text, size=10)
        near_words = []
        for word in autocomplets:
            near_words = near_words + self.model_synonyms[word[0]]
        
        return near_words
    
    def get_similar(self, word, topn=10):
        words = []
        distances = []
        for word, distance in self.w2v_model.wv.most_similar(word, topn=topn):
            words.append(word)
            distances.append(distance)
        return words, distances
            
    def get_related_articles(self, article, years=1, months=0, days=0, radius=0.89):
        chossen_id = str(article.id)
        id_form_article_id = np.where(self.faiss_article_ids==chossen_id)[0]
        if len(id_form_article_id) == 0:
            # Not in faiss db already
            vector = self.article2vect(article) # np.array([article_to_faiss_vect(article, nlp_custom, w2v_model)])
        else:
            vector = np.array([self.faiss_indexes.index.reconstruct(int(id_form_article_id[0]))])
        articles, distances = self.get_related_articles_from_vector(vector, years=years, months=months, days=days, radius=radius)
        
        if len(id_form_article_id) == 0:
            articles = list(articles)
            articles.insert(0, article)
            distances = list(distances)
            distances.insert(0, 1.0)
        return articles, distances
    
    def tokens2vect(self, art_arry, tfidf=True):
        if self.token2tfidf is None:
            tfidf=False
        word_vect_dim=self.w2v_model.wv.vector_size
        v = np.zeros(word_vect_dim)
        if tfidf:
            v_tfidf = np.zeros(word_vect_dim)
        for word in art_arry:
            if word in self.w2v_model.wv.vocab:
                if tfidf:
                    wordtfidf = self.token2tfidf.get(word, 0)
                    v_tfidf = v_tfidf + self.w2v_model.wv.get_vector(word)*wordtfidf
                v = v + self.w2v_model.wv.get_vector(word)
            else:
                words = word.split(' ')
                if len(words)>1:
                    for word in words:
                        if word in self.w2v_model.wv.vocab:
                            v = v + self.w2v_model.wv.get_vector(word)
                            if tfidf:
                                wordtfidf = self.token2tfidf.get(word, 0)
                                v_tfidf = v_tfidf + self.w2v_model.wv.get_vector(word)*wordtfidf
        norm = np.linalg.norm(v)
        
        
        if norm==0:
            v = np.zeros(word_vect_dim)
        else:
            v = v/norm
        
        if tfidf:
            norm_tfidf = np.linalg.norm(v_tfidf)
            if norm_tfidf==0:
                v_tfidf = np.zeros(word_vect_dim)
            else:
                v_tfidf = v_tfidf/norm_tfidf
            
            return v.astype('float32'), v_tfidf.astype('float32')
        else:
            return v.astype('float32')
        
        
    
    def doc2vect(self, doc):
        tokens = RelatedArticles.doc2tokens(doc)
        return self.tokens2vect(tokens)
    
    def text2doc(self, text):
        return self.nlp(text)
    
    def text2vect(self, text):
        doc = self.text2doc(text)
        return self.doc2vect(doc)
    
    def article2vect(self, article):
        text = RelatedArticles.article2text(article)
        return self.text2vect(text)
    
    def get_related_articles_from_vector(self, vector, radius=0.89, k=None, fr = 0, filter_by_date=True, years=1, months=0, days=0):
        if len(vector.shape) == 1:
            vector = np.array([vector])
        if k is None:
            lims, D, I = self.faiss_indexes.range_search(vector, radius)
            j = 0
            distances = D[lims[j]:lims[j+1]][fr:]
            sorted_idx = np.argsort(distances)[::-1]
            distances = distances[sorted_idx]
            indexes = I[lims[j]:lims[j+1]][fr:][sorted_idx]
        else:
            D, I = self.faiss_indexes.search(vector, k)
            distances = D[0][fr:]
            indexes = I[0][fr:]

        articles = []
        for idx in indexes:
            articles.append(Article.objects(id=self.faiss_article_ids[idx]).first())

        if filter_by_date:
            articles, distances = RelatedArticles.get_filtered_by_date(articles, distances, years=years, months=months, days=days)

        return articles, distances
    
    def add_faiss_vectors(self, articles, old_faiss_ids_f, old_faiss_indexes_f, old_faiss_indexes_tfidf_f, new_faiss_ids_f, new_faiss_indexes_f, new_faiss_indexes_tfidf_f):
        if new_faiss_indexes_tfidf_f is not None:
            tfidf=True
        else:
            tfidf=False
        # Read faiss indexes and mongoids
        if old_faiss_ids_f is None or old_faiss_indexes_f is None:
            faiss_articles_ids = []
            faiss_index2 = None
            faiss_index2_tfidf = None
        else:
            faiss_articles_ids = np.load(old_faiss_ids_f)
            faiss_index2 = faiss.read_index(old_faiss_indexes_f)
            faiss_index2_tfidf = faiss.read_index(old_faiss_indexes_tfidf_f)

        N_vects = len(articles)
        # Get wordvectors
        word_vect_dim = self.w2v_model.wv.vector_size
        xb = np.zeros((N_vects, word_vect_dim), dtype='float32')
        if tfidf:
            xb_tfidf = np.zeros((N_vects, word_vect_dim), dtype='float32')
        new_article_ids = []
        i=0
        j=0
        while j<N_vects:
            article = articles[i]
            if str(article.id) not in faiss_articles_ids:
                new_article_ids.append(str(article.id))
                if tfidf:
                    xb[j, :], xb_tfidf[j, :] = self.article2vect(article)
                else:
                    xb[j, :] = self.article2vect(article)
                j+=1
            i+=1
            print(f'\r{i}, {j} / {N_vects}', end='')

        # Update articles ids
        all_articles_ids = list(faiss_articles_ids) + new_article_ids
        np.save(new_faiss_ids_f, all_articles_ids)
        if len(faiss_articles_ids) == 0:
            ids = np.arange(N_vects).astype('int64')  # + faiss_index2.ntotal
        else:
            ids = np.arange(N_vects).astype('int64') + faiss_index2.ntotal

        if len(faiss_articles_ids) == 0:
            index = faiss.IndexFlatIP(word_vect_dim) 
            faiss_index2 = faiss.IndexIDMap(index)
            if tfidf:
                index_tfidf = faiss.IndexFlatIP(word_vect_dim) 
                faiss_index2_tfidf = faiss.IndexIDMap(index_tfidf)
                
        faiss_index2.add_with_ids(xb, ids)
        faiss.write_index(faiss_index2, new_faiss_indexes_f)
        
        if tfidf:
            faiss_index2_tfidf.add_with_ids(xb_tfidf, ids)
            faiss.write_index(faiss_index2_tfidf, new_faiss_indexes_tfidf_f)
            
    def prepare_autocomplete(self):
        words = {}
        for word, g in self.w2v_model.wv.vocab.items():
            lower = word.lower()
            if lower in words:
                if g.count > words[lower]['count']:
                    words[lower] = {'count': g.count}
            else:
                words[lower] = {'count': g.count}

        synonyms = {}
        for word, g in self.w2v_model.wv.vocab.items():
            lower = word.lower()
            if lower not in synonyms:
                synonyms[lower] = []
            synonyms[lower].append(word)
        return words, synonyms

# def article_to_faiss_vect(article, nlp, w2v_model):
#     # article2vect
#     title = CromaGNI.preprocess_aws_data(article['title'])
#     text = CromaGNI.preprocess_aws_data(article['text'])
#     text = title + '\n' + text
#     doc = nlp(text)
#     return get_sentence_vect(doc, w2v_model)



# def get_related_aticles(vector, faiss_indexes, faiss_article_ids, Article, radius=0.89, k=None, fr = 0, filter_by_date=True, years=1, months=0, days=0):
#     if k is None:
#         lims, D, I = faiss_indexes.range_search(vector, radius)
#         j = 0
#         distances = D[lims[j]:lims[j+1]][fr:]
#         sorted_idx = np.argsort(distances)[::-1]
#         distances = distances[sorted_idx]
#         indexes = I[lims[j]:lims[j+1]][fr:][sorted_idx]
#     else:
#         D, I = faiss_indexes.search(vector, k)
#         distances = D[0][fr:]
#         indexes = I[0][fr:]
    
#     articles = []
    
#     for idx in indexes:
#         articles.append(Article.objects(id=faiss_article_ids[idx]).first())
    
#     if filter_by_date:
#         articles, distances = get_filtered_by_date(articles, distances, years=years, months=months, days=days)

#     return articles, distances

# def add_faiss_vectors(old_faiss_ids_f, old_faiss_indexes_f, new_faiss_ids_f, new_faiss_indexes_f, articles, w2v_model, nlp_ner, N_vects=10000):
#     # Read faiss indexes and mongoids
#     if old_faiss_ids_f is None or old_faiss_indexes_f is None:
#         faiss_articles_ids = []
#         faiss_index2 = None
#     else:
#         faiss_articles_ids = np.load(old_faiss_ids_f)
#         faiss_index2 = faiss.read_index(old_faiss_indexes_f)
    
#     # Get wordvectors
#     word_vect_dim = w2v_model.wv.vector_size
#     xb = np.zeros((N_vects, word_vect_dim), dtype='float32')
#     new_article_ids = []
#     i=0
#     j=0
#     while j<N_vects:
#         article = articles[i]
#         if str(article.id) not in faiss_articles_ids:
#             new_article_ids.append(str(article.id))
#             xb[j, :] = article_to_faiss_vect(article, nlp_ner, w2v_model)
#             j+=1
#         i+=1
#         print(f'\r{i}, {j}', end='')
        
#     # Update articles ids
#     all_articles_ids = list(faiss_articles_ids) + new_article_ids
#     np.save(new_faiss_ids_f, all_articles_ids)
#     if len(faiss_articles_ids) == 0:
#         ids = np.arange(N_vects).astype('int64')  # + faiss_index2.ntotal
#     else:
#         ids = np.arange(N_vects).astype('int64') + faiss_index2.ntotal
        
#     if len(faiss_articles_ids) == 0:
#         index = faiss.IndexFlatIP(word_vect_dim) 
#         faiss_index2 = faiss.IndexIDMap(index)
#     faiss_index2.add_with_ids(xb, ids)
#     faiss.write_index(faiss_index2, new_faiss_indexes_f)

# def array_to_sentence_vect(art_arry, w2v_model):
#     word_vect_dim=w2v_model.wv.vector_size
#     v = np.zeros(word_vect_dim)
#     for word in art_arry:
#         if word in w2v_model.wv.vocab:
#             v = v + w2v_model.wv.get_vector(word)
#         else:
#             words = word.split(' ')
#             if len(words)>1:
#                 for word in words:
#                     if word in w2v_model.wv.vocab:
#                         v = v + w2v_model.wv.get_vector(word)
#     norm = np.linalg.norm(v)
#     if norm==0:
#         return np.zeros(word_vect_dim)
#     else:
#         return v/np.linalg.norm(v)

# def word2vect_encode(doc):
#     tokens = []
#     i = 0
#     while i<len(doc):
#         t = doc[i]
#         tx = t.text
#         # print(tx, t.ent_type_, t.ent_iob_, t.pos_, t.ent_kb_id_)
#         if t.ent_iob_=='O':
#             ent_tex = tx
#             i+=1
#             if (not t.is_space and '@' not in t.text):
#                 if t.is_digit:
#                     tokens.append('__DIGIT__')
#                 elif '$' in tx:
#                     tokens.append('__CURRENCY__')
#                 else:
#                     tokens.append(ent_tex)
#         else:
#             ent_tex = ''
#             while t.ent_iob_!='O':
#                 if t.pos_ == 'DET' and t.ent_iob_=='B':
#                     # It is an article
#                     tokens.append(tx)
#                 else:
#                     ent_tex = ent_tex + ' ' + tx
#                 i+=1
#                 if i<len(doc):
#                     t = doc[i]
#                     tx = t.text
#                 else:
#                     break
            
#             ent_tex = ent_tex.strip().replace(' - ', '-')
#             tokens.append(ent_tex)
        
        
#     return tokens

# def get_sentence_vect(doc, w2v_model):
#     tokens = word2vect_encode(doc)
#     return array_to_sentence_vect(tokens, w2v_model).astype('float32')