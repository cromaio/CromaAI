from bs4 import BeautifulSoup
import textacy
import textacy.preprocessing
import enum

class CromaGNI:
    @staticmethod
    def html_to_text(html):
        # pueden ser otros parsers 
        # https://stackoverflow.com/questions/33511544/how-to-get-rid-of-beautifulsoup-user-warning
        soup = BeautifulSoup(html, "html.parser") 

        # kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()    # rip it out
#             print('entro:')
#             print(script)

        # get text
        text = soup.get_text(separator=' ')

        # break into lines and remove leading and trailing space on each
        # lines = (line.strip() for line in text.splitlines())
        # break multi-headlines into a line each
        # chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
    #     text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    
    @staticmethod
    def preprocess_data_for_word2vect(html):
        preprocessed_text = CromaGNI.html_to_text(html)
        preprocessed_text = textacy.preprocessing.normalize_unicode(preprocessed_text)
    #     preprocessed_text = textacy.preprocessing.normalize_hyphenated_words(preprocessed_text)
        preprocessed_text = textacy.preprocessing.replace_currency_symbols(preprocessed_text)
        
        preprocessed_text = textacy.preprocessing.replace_emails(preprocessed_text, replace_with='')
        preprocessed_text = textacy.preprocessing.replace_phone_numbers(preprocessed_text, replace_with='')
        preprocessed_text = textacy.preprocessing.replace_urls(preprocessed_text, replace_with='')
        
        preprocessed_text = textacy.preprocessing.normalize_quotation_marks(preprocessed_text)
        preprocessed_text = textacy.preprocessing.normalize_whitespace(preprocessed_text)
        preprocessed_text = preprocessed_text.replace('ʼ', "'")
        
        preprocessed_text = preprocessed_text.replace('\u200d♂️', '')
        preprocessed_text = textacy.preprocessing.normalize_unicode(preprocessed_text)
        preprocessed_text = preprocessed_text.replace('????????', '')
        
        preprocessed_text = '\n'.join([line.strip() for line in preprocessed_text.split('\n') if line.strip() != ''])
        return preprocessed_text
    
    @staticmethod
    def preprocess_data(html, rem_email_phone_url=True, replace_single_quote=False, rem_emojis=False, replace_zero_width_joiner=False, strip_sentences=False, remove_twitter_question_marks=False):
        preprocessed_text = CromaGNI.html_to_text(html)
        preprocessed_text = textacy.preprocessing.normalize_unicode(preprocessed_text)
    #     preprocessed_text = textacy.preprocessing.normalize_hyphenated_words(preprocessed_text)
    #     preprocessed_text = textacy.preprocessing.replace_currency_symbols(preprocessed_text)
        if rem_email_phone_url:
            preprocessed_text = textacy.preprocessing.replace_emails(preprocessed_text, replace_with='')
            preprocessed_text = textacy.preprocessing.replace_phone_numbers(preprocessed_text, replace_with='')
            preprocessed_text = textacy.preprocessing.replace_urls(preprocessed_text, replace_with='')
        if rem_emojis:
            preprocessed_text = textacy.preprocessing.replace_emojis(preprocessed_text, replace_with='')
        
        preprocessed_text = textacy.preprocessing.normalize_quotation_marks(preprocessed_text)
        preprocessed_text = textacy.preprocessing.normalize_whitespace(preprocessed_text)
        if replace_single_quote:
            preprocessed_text = preprocessed_text.replace('ʼ', "'")
        if replace_zero_width_joiner:
            # Azure hace cosas raras con esto. Esta presente en los tweets de azure
            preprocessed_text = preprocessed_text.replace('\u200d♂️', '')
        preprocessed_text = textacy.preprocessing.normalize_unicode(preprocessed_text)
        if remove_twitter_question_marks:
            preprocessed_text = preprocessed_text.replace('????????', '')
        # Remove multiple enters and spaces
        if strip_sentences:
            preprocessed_text = '\n'.join([line.strip() for line in preprocessed_text.split('\n') if line.strip() != ''])
        return preprocessed_text
    
    @staticmethod
    def preprocess_aws_data(html, rem_email_phone_url=False):
        preprocessed_text = CromaGNI.html_to_text(html)
        preprocessed_text = textacy.preprocessing.normalize_unicode(preprocessed_text)
    #     preprocessed_text = textacy.preprocessing.normalize_hyphenated_words(preprocessed_text)
    #     preprocessed_text = textacy.preprocessing.replace_currency_symbols(preprocessed_text)
        if rem_email_phone_url:
            preprocessed_text = textacy.preprocessing.replace_emails(preprocessed_text)
            preprocessed_text = textacy.preprocessing.replace_phone_numbers(preprocessed_text)
            preprocessed_text = textacy.preprocessing.replace_urls(preprocessed_text)
        preprocessed_text = textacy.preprocessing.replace_emojis(preprocessed_text)
        preprocessed_text = textacy.preprocessing.normalize_quotation_marks(preprocessed_text)
        preprocessed_text = textacy.preprocessing.normalize_whitespace(preprocessed_text)
        return preprocessed_text
    
    @staticmethod
    def get_article_entities(doc):
        entities = {}
        for ent in doc.ents:
            pos = []
            for t in ent.as_doc():
                pos.append(t.pos_)

            if 'PROPN' in pos:
                pos_ = 'PROPN'
            elif 'NOUN' in pos:
                pos_ = 'NOUN'
            else:
                pos_ = 'UNKNOWN'

            if ent.text not in entities:
                entities[ent.text] = {'length': len(ent.text), 'mentions': [{'idx': ent.start_char, 
                                                                             'POS': CromaGNI.EntityMention.Type[pos_].value, 
                                                                            'type': CromaGNI.Entity.Type[ent.label_].value, }]}
            else:
                entities[ent.text]['mentions'].append({'idx': ent.start_char, 
                                                       'POS': CromaGNI.EntityMention.Type[pos_].value, 
                                                             'type': CromaGNI.Entity.Type[ent.label_].value, })
        entities_list = []
        for k,v in entities.items():
            v['name'] =  k
            entities_list.append(v)
        return entities_list
    
    class EntityMention:
        class Type(enum.Enum):
            UNKNOWN = 0
            PROPER = 1
            PROPN = PROPER # Spacy
            COMMON = 2
            NOUN = COMMON # Spacy
    class Entity:
        class Type(enum.Enum):
            PERSON = 1
            PER = PERSON # Spacy
            LOCATION = 2
            LOC = LOCATION # Spacy
            ORGANIZATION = 3
            ORG = ORGANIZATION # Spacy
            EVENT = 4
            WORK_OF_ART = 5
            CONSUMER_GOOD = 6
            OTHER =  7
            MISC = OTHER # Spacy
            PHONE_NUMBER = 9
            ADDRESS = 10
            DATE = 11
            NUMBER = 12
            PRICE = 13