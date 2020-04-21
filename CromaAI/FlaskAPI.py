from flask_mongoengine import MongoEngine
from IPython.display import HTML
import spacy
import faiss
import numpy as np
from gensim.models import Word2Vec

from datetime import datetime
import config

import sys
import os
sys.path.append('../')
import flask
from CromaDisplacy import return_HTML_from_db, return_HTML
from models import Publication, NerAzure, NerGoogle, NerAws
from CromaGNI import CromaGNI
from RelatedArticles import RelatedArticles #get_sentence_vect, article_to_faiss_vect, get_related_aticles
# from CromaGNILib.models import Publication

from flask_mongoengine import MongoEngine
# from flask_debugtoolbar import DebugToolbarExtension
# sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../../')))

def url_for_other_page(page):
    args = flask.request.args.copy()
    args['page'] = page
    return flask.url_for(flask.request.endpoint, **args)

app = flask.Flask(__name__)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page
    

app.config.from_object(__name__)
app.config['MONGODB_SETTINGS'] = {
    'db': config.database['db_name'],
    'host': config.database['host'],
    'port': config.database['port']
    }
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'flask+mongoengine=<3'
app.config['JSON_AS_ASCII'] = False
app.debug = True
app.config['DEBUG_TB_PANELS'] = (
    'flask_debugtoolbar.panels.versions.VersionDebugPanel',
    'flask_debugtoolbar.panels.timer.TimerDebugPanel',
    'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask_debugtoolbar.panels.template.TemplateDebugPanel',
    'flask_debugtoolbar.panels.logger.LoggingPanel',
    'flask_mongoengine.panels.MongoDebugPanel'
)

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

db = MongoEngine()
db.init_app(app)

# DebugToolbarExtension(app)
# Load models and data
print('Loading models ...')
# print(config.models.faiss_ids)
related_articles = RelatedArticles(
    config.models.spacy,
    config.models.gensim_w2v,
    config.models.faiss_indexes,
    config.models.faiss_ids,
    config.models.token2tfidf
)

print('Finished loading models')

class Article(db.Document):
    title = db.StringField()
    summary = db.StringField()
    text = db.StringField()
    publish_date = db.DateField()
    url = db.URLField()
    author = db.ListField()
    keywords = db.ListField()
    categories = db.ListField()
    publication = db.ReferenceField(Publication)
    pub_art_id = db.StringField()
    ner_azure_id = db.ReferenceField(NerAzure, required=False)
    ner_google_id = db.ReferenceField(NerGoogle, required=False)
    ner_aws_id = db.ReferenceField(NerAws, required=False)
    meta = {'strict': False}

# Get article
@app.route('/api/v1/article')
def get_article_api():
    article_id = flask.request.args.get('id')
    return {"article": Article.objects(id=article_id).first()}

# Get related articles
@app.route('/related')
def get_related():
    years = int(flask.request.args.get('years') or '0')
    months = int(flask.request.args.get('months') or '0')
    days = int(flask.request.args.get('days') or '0')
    chossen_id = flask.request.args.get('id')
    radius = float((flask.request.args.get('radius')) or 0.85)
    article = Article.objects(id=chossen_id).get()
    
    articles, similarities = related_articles.get_related_articles(article, years=years, months=months, days=days, radius=radius)
        
    return flask.render_template('related.html', articles=zip(articles, similarities))

@app.route('/api/v1/related')
def get_related_api():
    years = int(flask.request.args.get('years') or '0')
    months = int(flask.request.args.get('months') or '0')
    days = int(flask.request.args.get('days') or '0')
    chossen_id = flask.request.args.get('id')
    radius = float((flask.request.args.get('radius')) or 0.85)
    article = Article.objects(id=chossen_id).get()
    
    articles, similarities = related_articles.get_related_articles(article, years=years, months=months, days=days, radius=radius)
        
    return {'related_articles': [{'article_id': str(a['id']), 'similarity':float(s)} for a, s in zip(articles, similarities)]}


# Get highlighted article
@app.route('/api/v1/article_entities')
def get_highlighted_article_api():
    article_id = flask.request.args.get('id')
    cloud = (flask.request.args.get('cloud') or 'spacy')
    detail = (flask.request.args.get('detail') or False)
    
    article = Article.objects(id=article_id).first()
    title = article.title
    html = None
    ner = None
    json_data_doc = None
    json_data_title = None
    # text = article['text']
    if cloud == 'aws':
        ner = article.ner_aws_id
    elif cloud == 'azure':
        ner = article.ner_azure_id
    elif cloud == 'google':
        ner = article.ner_google_id
    if ner is not None:
        html = return_HTML_from_db(ner)
        json_data_doc = ner.to_json()
    
    if cloud == 'spacy':
        text = CromaGNI.preprocess_aws_data(article.text)
        doc = related_articles.text2doc(text) 
        json_data_doc = doc.to_json()
        html = return_HTML(json_data_doc)
        json_data_title = related_articles.text2doc(title).to_json()
        title = return_HTML(json_data_title)
    
    if cloud == 'raw':
        html = CromaGNI.preprocess_aws_data(article.text)
        
    if html is None:
        return {'error': 'Cloud API results not in db'}
    if detail:
        return {"article": article, 'title': title, 'html': html, 'json_data_doc': json_data_doc, 'json_data_title': json_data_title}
    else:
        return {'NER_content': json_data_doc, 'NER_title': json_data_title}

@app.route('/highlighted_article')
def get_highlighted_article():
    article_id = flask.request.args.get('id')
    cloud = (flask.request.args.get('cloud') or 'spacy')
    
    article = Article.objects(id=article_id).first()
    title = article.title
    html = None
    ner = None
    # text = article['text']
    if cloud == 'aws':
        ner = article.ner_aws_id
    elif cloud == 'azure':
        ner = article.ner_azure_id
    elif cloud == 'google':
        ner = article.ner_google_id
    if ner is not None:
        html = return_HTML_from_db(ner)
    
    if cloud == 'spacy':
        text = CromaGNI.preprocess_aws_data(article.text)
        doc = related_articles.text2doc(text) 
        html = return_HTML(doc.to_json())
        title = return_HTML(related_articles.text2doc(title).to_json())
    
    if cloud == 'raw':
        html = CromaGNI.preprocess_aws_data(article.text)
        
    if html is None:
        return 'Cloud API results not in db'
    
    cloudoptions=[{'value': 'google', 'string': 'Google', 'selected': ''},
                  {'value': 'azure', 'string': 'Azure', 'selected': ''},
                  {'value': 'aws', 'string': 'AWS', 'selected': ''},
                  {'value': 'spacy', 'string': 'Custom', 'selected': ''},
                  {'value': 'raw', 'string': 'Raw', 'selected': ''},
                 ]
    for cloud_item in cloudoptions:
        if cloud == cloud_item['value']:
            cloud_item['selected'] = 'selected'
    
    return flask.render_template('article.html', article=article, title=title, html=html, cloudoptions=cloudoptions)

def get_articles():
    google = int(flask.request.args.get('google') or 0)
    aws = int(flask.request.args.get('aws') or 0)
    azure = int(flask.request.args.get('azure') or 0)
    selected_pub = (flask.request.args.get('pub') or Publication.objects(name=config.active_publication).first().id)
    page_num = int(flask.request.args.get('page') or 1)
    per_page = int(flask.request.args.get('count') or 10)
    from_date = flask.request.args.get('from') or '2000-01-01'
    to_date = flask.request.args.get('to') or datetime.now().strftime("%Y-%m-%d")
    
#     if to_date is None:
#         to_date = datetime.now().strftime("%Y-%m-%d")
    
#     if from_date is None:
#         from_date = '2000-01-01'
    
    cloud_args = {
    }
    if google==1:
        cloud_args['ner_google_id__ne'] = None
    if aws==1:
        cloud_args['ner_aws_id__ne'] = None
    if azure==1:
        cloud_args['ner_azure_id__ne'] = None
    
    print(datetime.strptime(from_date, "%Y-%m-%d").date())
    
    articles_page = Article.objects(publication=selected_pub, 
                                    **cloud_args, 
                                    publish_date__gte=datetime.strptime(from_date, "%Y-%m-%d").date(), 
                                    publish_date__lte=datetime.strptime(to_date, "%Y-%m-%d").date()
                                   ).order_by('-publish_date').paginate(page=page_num, per_page=per_page)
    
    pubs = []
    for pub in Publication.objects():
        if selected_pub == str(pub.id):
            selected='selected'
        else:
            selected=''
        pubs.append([pub, selected])
    return articles_page, pubs, cloud_args, from_date, to_date

@app.route('/api/v1/articles')
def pagination_api():
    articles_page, pubs, cloud_args, from_date, to_date = get_articles()    
    return {'articles_page': articles_page.items, 'fromDate':from_date, 'toDate':to_date}

@app.route('/articles')
def pagination():
    articles_page, pubs, cloud_args, from_date, to_date = get_articles()
    
    return flask.render_template('pagination.html', articles_page=articles_page, publications=pubs, cloud_args=cloud_args, fromDate=from_date, toDate=to_date)


@app.route('/analyzer')
def get_analyzer():
    return flask.render_template('analyzer.html', analysed_text=None)

@app.route('/w2v')
def get_w2v():
    return flask.render_template('w2v.html')

@app.route('/w2v/autocomplete', methods=['POST'])
def get_autocomplete():
    text = flask.request.json
    return {'words': related_articles.get_autocomplete_words_list(text)}

@app.route('/api/v1/w2v/autocomplete', methods=['POST'])
def get_autocomplete_api():
    text = flask.request.json
    return {'words': related_articles.get_autocomplete_words_list(text)}


### Get similar words
@app.route('/api/v1/w2v/similar', methods=['POST'])
def get_similar_api():
    response = flask.request.json
    words, similarities = related_articles.get_similar(response['word'], topn=10)
    return {'similar_words': [{'word':w, 'similarity':d} for w, d in zip(words, similarities)]}

@app.route('/w2v/similar', methods=['POST'])
def get_similar():
    response = flask.request.json
    words, distances = related_articles.get_similar(response['word'], topn=10)
    return {'html': flask.render_template('similar_terms_list.html', data=zip(words, distances))}
    
@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/analyzer/text', methods=['POST'])
def post_text():
    # Receives text, converts it to DOC, gets NERs, gets vector and return articles and NER HTML
    text = flask.request.json
    doc = related_articles.text2doc(text)
    html = return_HTML(doc.to_json())
    
    vector = related_articles.doc2vect(doc)
    if type(vector) == tuple:
        vector = vector[1]
    articles, distances = related_articles.get_related_articles_from_vector(vector, k=10, filter_by_date=False)
    
    return {'html': html, 'related_html': flask.render_template('related_articles.html', articles=zip(articles, distances))}

@app.route('/api/v1/analyzer/text', methods=['POST'])
def post_text_api():
    # Receives text, converts it to DOC, gets NERs, gets vector and return articles and NER HTML
    text = flask.request.json
    print(flask.request.data)
    print(text)
    doc = related_articles.text2doc(text)
    html = return_HTML(doc.to_json())
    
    vector = related_articles.doc2vect(doc)
    if type(vector) == tuple:
        vector = vector[1]
    articles, similarities = related_articles.get_related_articles_from_vector(vector, k=10, filter_by_date=False)
    
    if len(articles) == 0:
        related_and_similarities = []
    else:
        related_and_similarities = [{'article_id': str(a['id']), 'similarity':float(s)} for a, s in zip(articles, similarities)]

    return {'html': html, 'related_articles': related_and_similarities, 'doc': doc.to_json()}

app.add_url_rule('/pagination', view_func=pagination)


    
if __name__ == "__main__":
    port = 5000
    host = "0.0.0.0"
    for i, a in enumerate(sys.argv):
        if a == '-p':
            port = sys.argv[i+1]
        if a == '-h':
            host = sys.argv[i+1]

    app.run(host=host, port=port)