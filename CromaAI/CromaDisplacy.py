import numpy as np
from models import EntityType

DEFAULT_LANG = "en"
DEFAULT_DIR = "ltr"

TPL_ENTS = """
<div class="entities" style="line-height: 2.5; direction: {dir}">{content}</div>
"""


TPL_ENT = """
<mark class="entity" style="background: {bg}; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em;">
    {text}
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">{label}</span>
</mark>
"""

TPL_ENT_RTL = """
<mark class="entity" style="background: {bg}; padding: 0.45em 0.6em; margin: 0 0.25em; line-height: 1; border-radius: 0.35em">
    {text}
    <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-right: 0.5rem">{label}</span>
</mark>
"""

TPL_FIGURE = """
<figure style="margin-bottom: 6rem">{content}</figure>
"""

TPL_PAGE = """
<!DOCTYPE html>
<html lang="{lang}">
    <head>
        <title>displaCy</title>
    </head>
    <body style="font-size: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'; padding: 4rem 2rem; direction: {dir}">{content}</body>
</html>
"""

TPL_TITLE = """
<h2 style="margin: 0">{title}</h2>
"""

def escape_html(text):
    """Replace <, >, &, " with their HTML encoded representation. Intended to
    prevent HTML errors in rendered displaCy markup.
    text (unicode): The original text.
    RETURNS (unicode): Equivalent text to be safely used within HTML.
    """
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text

def minify_html(html):
    """Perform a template-specific, rudimentary HTML minification for displaCy.
    Disclaimer: NOT a general-purpose solution, only removes indentation and
    newlines.
    html (unicode): Markup to minify.
    RETURNS (unicode): "Minified" HTML.
    """
    return html.strip().replace("    ", "").replace("\n", "")

class EntityRenderer(object):
    """Render named entities as HTML."""

    style = "ent"

    def __init__(self, options={}):
        """Initialise dependency renderer.
        options (dict): Visualiser-specific options (colors, ents)
        """
        colors = {
            "ORG": "#7aecec",
            "PRODUCT": "#bfeeb7",
            "GPE": "#feca74",
            "LOC": "#ff9561",
            "PERSON": "#aa9cfc",
            "NORP": "#c887fb",
            "FACILITY": "#9cc9cc",
            "EVENT": "#ffeb80",
            "LAW": "#ff8197",
            "LANGUAGE": "#ff8197",
            "WORK_OF_ART": "#f0d0ff",
            "DATE": "#bfe1d9",
            "TIME": "#bfe1d9",
            "MONEY": "#e4e7d2",
            "QUANTITY": "#e4e7d2",
            "ORDINAL": "#e4e7d2",
            "CARDINAL": "#e4e7d2",
            "PERCENT": "#e4e7d2",
            "MISC": "#bfe1d9",
        }
        
        self.default_color = "#ddd"
        self.colors = colors
        self.ents = options.get("ents", None)
        self.direction = DEFAULT_DIR
        self.lang = DEFAULT_LANG

        template = options.get("template")
        if template:
            self.ent_template = template
        else:
            if self.direction == "rtl":
                self.ent_template = TPL_ENT_RTL
            else:
                self.ent_template = TPL_ENT

    def render(self, parsed, page=False, minify=False):
        """Render complete markup.
        parsed (list): Dependency parses to render.
        page (bool): Render parses wrapped as full HTML page.
        minify (bool): Minify HTML markup.
        RETURNS (unicode): Rendered HTML markup.
        """
        rendered = []
        for i, p in enumerate(parsed):
            if i == 0:
                settings = p.get("settings", {})
                self.direction = settings.get("direction", DEFAULT_DIR)
                self.lang = settings.get("lang", DEFAULT_LANG)
            if "ents" in p:
                rendered.append(self.render_ents(p["text"], p["ents"], p.get("title")))
            else:
                rendered.append(self.render_ents(p["text"], p["entities"], p.get("title")))
        if page:
            docs = "".join([TPL_FIGURE.format(content=doc) for doc in rendered])
            markup = TPL_PAGE.format(content=docs, lang=self.lang, dir=self.direction)
        else:
            markup = "".join(rendered)
        if minify:
            return minify_html(markup)
        return markup

    def render_ents(self, text, spans, title, html_esc=False):
        """Render entities in text.
        text (unicode): Original text.
        spans (list): Individual entity spans and their start, end and label.
        title (unicode or None): Document title set in Doc.user_data['title'].
        """
        markup = ""
        offset = 0
        for span in spans:
            if 'ent_type' in span:
                label = EntityType(span["ent_type"]).name
            else:
                label = span["label"]
            start = span["start"]
            end = span["end"]
            additional_params = span.get("params", {})
            if html_esc:
                entity = escape_html(text[start:end])
            else:
                entity = text[start:end]
            fragments = text[offset:start].split("\n")
            for i, fragment in enumerate(fragments):
                if html_esc:
                    markup += escape_html(fragment)
                else:
                    markup += fragment
                if len(fragments) > 1 and i != len(fragments) - 1:
                    markup += "</br>"
            if self.ents is None or label.upper() in self.ents:
                color = self.colors.get(label.upper(), self.default_color)
                ent_settings = {"label": label, "text": entity, "bg": color}
                ent_settings.update(additional_params)
                markup += self.ent_template.format(**ent_settings)
            else:
                markup += entity
            offset = end
        if html_esc:
            markup += escape_html(text[offset:])
        else:
            markup += text[offset:]
        markup = TPL_ENTS.format(content=markup, dir=self.direction)
        if title:
            markup = TPL_TITLE.format(title=title) + markup
        return markup
    
    
def return_HTML(parsed_doc):
    renderer = EntityRenderer()
    return renderer.render([parsed_doc], minify=True)

def return_HTML_from_db(dbdata):
    renderer = EntityRenderer()
    return renderer.render([{'text': dbdata['text'], 'ents':  dbdata['entities']}], minify=True)