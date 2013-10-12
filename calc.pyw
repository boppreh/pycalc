from __future__ import division
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import re
from math import *

from units import Unit
from numeric import Measure, Percentage


def to_measure(value, unit):
    """
    Converts a numeric value and a unit into a normalized measure.
    """
    multiplier, new_unit = unit.normalize()
    return Measure(value * multiplier, new_unit)

def to_unit(text):
    """
    Converts the textual description of a unit into its Unit instance.
    No support yet for multiple parts in the numerator or denominator.
    """
    text = text.replace(' ', '')
    if '/' in text:
        numerator, denominator = text.split('/')
        return Unit([numerator], [denominator])
    else:
        return Unit([text])


def pattern(text):
    """
    Expands a regex pattern, expanding references to "number", "word" and
    "unit" to their respective regexes.
    """
    number = r'(\d+(?:\.\d*)?)'
    word = r'([a-zA-Z]+)'
    unit = r'([a-zA-Z]+(?:\s*/\s*[a-zA-Z]+)?)'
    return r'\b' + text.format(number=number, word=word, unit=unit)

def parse(text):
    """
    Parses and eval an expression that uses measures and percentages.
    """
    text = re.sub(pattern(r'{number}%'), r'Percentage(\1 / 100)', text)

    text = re.sub(pattern(r'(.+)\s+in\s+({unit})$'),
                  r'(\1).convert(to_unit("\2"))',
                  text)

    text = re.sub(pattern(r'{number}\s*{unit}'),
                  r'to_measure(\1, to_unit("\2"))',
                  text)

    return eval(text)


if __name__ == "__main__":
    page_templates = {
        Percentage: """
    {{result}}
    Complement: {{100% - result}}
    Inverse: {{1 / result}} """,

        tuple: """
    {{result}}
    {{100 * result[1] / result[0]}}% / {{100 * result[0] / result[1]}}%
    {{10 * log10(result[1] / result[0])}} dB"""
    }

    def apply_template(value, template):
        """
        Given a value and a template, replace all sub-expressions in the
        template with their results linked to the formula.
        """
        template = template.replace('\n', '<br>').replace('result', str(value))
        for expression in re.findall('{{(.+?)}}', template):
            exp_result = parse(expression)
            uri = urlencode({'q': expression})
            link = '<a href="/?{}">{}</a>'.format(uri, exp_result)
            template = template.replace('{{' + expression + '}}', link)

        return template

    def print_page(value):
        """
        Returns the HTML page body for a given value.
        """
        for type, template in page_templates.items():
            if isinstance(value, type):
                return apply_template(value, template)

        return str(value)

    from background import tray
    import webbrowser
    tray('Calculator', 'calculator.png',
         on_click=lambda: webbrowser.open('http://localhost:5000'))


    from simpleserver import serve
    last_queries = []
    serve(last_queries, port=2346)

    from flask import Flask, request
    app = Flask(__name__)

    @app.route('/')
    def hello():
        if len(request.args):
            query = request.args['q']
            result = parse(query)
            body = print_page(result)
            last_queries.append(query + ' = ' + str(result))
            if len(last_queries) > 10:
                last_queries.pop(0)
        else:
            query = ''
            body = ''
        return '<html><body><form action="/" method="GET"><input name="q" value="{}" style="width: 500" autofocus/></form>{}</body></html>'.format(query, body)

    app.run(debug=True, use_reloader=False)
