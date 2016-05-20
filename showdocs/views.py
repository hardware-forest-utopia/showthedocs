import os
import logging
import markupsafe, markdown

from flask import render_template, request, redirect
from showdocs import app, html, annotate, structs, docs, errors, config

from showdocs.structs import Annotation

logger = logging.getLogger(__name__)

def _safedocs(docs):
    for path, externaldoc in docs.withcontents():
        yield path, markupsafe.Markup(externaldoc.contents)

def _csspaths(docs):
    css = set()
    for _, externaldoc in docs.withcontents():
        for path in externaldoc.css:
            css.add('/static/external/' + path)
    return css

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contribute')
def contribute():
    contents = markupsafe.Markup(markdown.markdown(open(os.path.join(
        config.ROOT, 'contributing.md')).read()))
    return render_template('contribute.html', contents=contents)

@app.route('/query')
def query():
    try:
        q = request.args.get('q', '')
        if not q:
            return redirect('/')

        lang = request.args.get('lang', 'guess')
        formatquery = bool(request.args.get('format', True))

        annotated, docs = annotate.annotate(q, lang, formatquery)

        return render_template('query.html',
                               lang=lang,
                               query=markupsafe.Markup(annotated),
                               docs=_safedocs(docs),
                               additionalcss=_csspaths(docs))
    except errors.NoAnnotatorFound, e:
        message = "lang '%s' isn't supported"
        return render_template('error.html',
                               title='oops',
                               message=message % e.args[0])
    except errors.ParsingError, e:
        formattederror = html.formaterror(q, e)
        return render_template('queryerror.html',
                               lang=lang,
                               query=markupsafe.Markup(formattederror[0]),
                               message=markupsafe.Markup(formattederror[1]))
    except:
        if config.TEST:
            raise
        logger.error('uncaught exception: lang=%r formatquery=%r query=%r',
                     lang,
                     formatquery,
                     q,
                     exc_info=True)
        message = 'something went wrong... this was logged and will be checked'
        return render_template('error.html', title='oops', message=message)
