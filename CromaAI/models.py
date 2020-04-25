from mongoengine import connect, IntField, Document, StringField, DateField, URLField, ListField, ReferenceField, disconnect, LongField
import SchemaValidation
import enum

"""
AWS_types = ['EVENT', 'PERSON', 'ORGANIZATION', 'COMMERCIAL_ITEM', 'QUANTITY', 'TITLE', 'OTHER', 'LOCATION', 'DATE']

azure_types = ['DateTime', 'Location', 'Organization', 'Person', 'IP_Address', 'Email', 'Other', 'Quantity', 'URL', 'Phone_Number']

azure_subtypes = ['Date', 'Ordinal', 'Age', 'Number', 'Percentage', 'Currency', 'TimeRange', 'Time', 'Duration', 'Set', 'DateTimeRange', 'DateRange', 'Temperature', 'Dimension']


google_types = [UNKNOWN: 0, PERSON: 1, LOCATION: 2, ORGANIZATION: 3, EVENT: 4, WORK_OF_ART: 5, CONSUMER_GOOD: 6, OTHER: 7, PHONE_NUMBER: 9, ADDRESS: 10, DATE: 11, NUMBER: 12, PRICE: 13]

google_mentions_type = [TYPE_UNKNOWN: 0, PROPER: 1, COMMON: 2]

"""

class NerAzure(Document):
    text = StringField(required=True)
    entities = ListField()
    language = StringField(required=True)
    meta = {
        'indexes': [
            '#text',  # hashed index
        ]
    }
    
class NerAws(Document):
    text = StringField(required=True)
    entities = ListField()
    language = StringField(required=True)
    meta = {
        'indexes': [
            '#text',  # hashed index
        ]
    }
    
class NerGoogle(Document):
    text = StringField(required=True)
    entities = ListField()
    language = StringField(required=True)
    meta = {
        'indexes': [
            '#text',  # hashed index
        ]
    }

class Publication(Document):
    name = StringField(required=True, unique=True)
    url = URLField(required=True, unique=True)
    location = StringField(required=True)
    fetch_method = StringField(required=True)
    api_url = URLField()
    
class Article(Document):
    title = StringField(required=True)
    summary = StringField()
    text = StringField(required=True)
    publish_date = DateField(required=True)
    url = URLField(required=True, unique=True)
    author = ListField()
    keywords = ListField()
    categories = ListField()
    publication = ReferenceField(Publication, required=True)
    pub_art_id = StringField(required=True)
    ner_azure_id = ReferenceField(NerAzure, required=False)
    ner_google_id = ReferenceField(NerGoogle, required=False)
    ner_aws_id = ReferenceField(NerAws, required=False)
    faiss_index = IntField()
    faiss_index_tfidf = IntField()
    meta = {
        'indexes': [
            {'fields': ['faiss_index']},
            {'fields': ['publication']},
            {'fields': ['pub_art_id']},
            {'fields': ['publish_date']},
            {'fields': ['#text']}, #, 'sparse': True, 'unique': True
            {'fields': ['pub_art_id', 'publication'], 'unique': True}
        ]
    }
    # faiss_index = LongField(required=False)
    

class EntitySubtype(enum.Enum):
    NoSubtype = 0
    Date = 1
    Ordinal = 2
    Age = 3
    Number = 4
    Percentage = 5
    Currency = 6
    TimeRange = 7
    Time = 8
    Duration = 9
    Set = 10
    DateTimeRange = 11
    DateRange = 12
    Temperature = 13
    Dimension = 14

class EntityPOS(enum.Enum):
    UNKNOWN = 0 # Google
    PROPER = 1 # Google
    PROPN = PROPER # Spacy
    COMMON = 2 # Google
    NOUN = COMMON # Spacy

class EntityType(enum.Enum):
    PERSON = 1 # Google and AWS
    PER = PERSON # Spacy
    Person = PERSON # Azure

    LOCATION = 2 # Google and AWS
    LOC = LOCATION # Spacy
    Location = LOCATION # Azure

    ORGANIZATION = 3 # Google and AWS
    ORG = ORGANIZATION # Spacy
    Organization = ORGANIZATION # Azure

    EVENT = 4 # Google and AWS

    WORK_OF_ART = 5

    CONSUMER_GOOD = 6 # Google
    COMMERCIAL_ITEM = CONSUMER_GOOD # AWS

    OTHER =  7 # Google and AWS
    Other = OTHER # Azure
    MISC = OTHER # Spacy

    PHONE_NUMBER = 9 # Google
    Phone_Number = PHONE_NUMBER # Azure

    ADDRESS = 10

    DATE = 11 # Google and AWS
    DateTime = DATE # Azure

    NUMBER = 12 # AWS

    PRICE = 13 # AWS

    TITLE = 14 # AWS

    QUANTITY = 15 # AWS
    Quantity = QUANTITY # Azure

    IP_Address = 16 # Azure

    Email = 17 # Azure

    URL = 18 # Azure
    
class EntityLink(Document):
    name = StringField(required=True)
    mid = StringField()
    wikipedia_url = URLField(unique=True)
    wikipedia_id = StringField()
    bing_id = StringField()
    wikipedia_language = StringField()
    
class EntityMention(SchemaValidation.Validation):
    name = SchemaValidation.StringField(required=True)
    text = SchemaValidation.StringField(required=True)
    start = SchemaValidation.IntField(required=True)
    end = SchemaValidation.IntField(required=True)
    ent_type = SchemaValidation.EnumFiled(EntityType, required=True)
    ent_subtype = SchemaValidation.EnumFiled(EntitySubtype) #Azure subtype
    pos_type = SchemaValidation.EnumFiled(EntityPOS) #Google POS tag
    score = SchemaValidation.FloatField(max_value=1, min_value=0)
    salience = SchemaValidation.FloatField(max_value=1, min_value=0)
    entity_link = SchemaValidation.DictField(EntityLink)
    
