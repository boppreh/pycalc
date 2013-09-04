from __future__ import division
import re
from math import *
from urllib import urlencode
from units import Unit

class Measure(float):
    """
    Number with associated unit. Behaves as a float for arithmetic operations,
    but asserts and updates units as necessary.
    """
    # Required to extend primitive types.
    def __new__(cls, value, unit):
        return float.__new__(cls, value)

    # Values has already been incorporated, nothing to set.
    def __init__(self, value, unit):
        self.unit = unit

    def __add__(self, other):
        assert not hasattr(other, 'unit') or self.unit == other.unit
        return Measure(float(self) + other, self.unit)

    def __sub__(self, other):
        assert not hasattr(other, 'unit') or self.unit == other.unit
        return Measure(float(self) - other, self.unit)

    def __mul__(self, other):
        if hasattr(other, 'unit'):
            return Measure(float(self) * other, self.unit * other.unit)
        else:
            return Measure(float(self) * other, self.unit)

    def __truediv__(self, other):
        if hasattr(other, 'unit'):
            return Measure(float(self) / other, self.unit / other.unit)
        else:
            return Measure(float(self) / other, self.unit)

    def __pow__(self, other):
        assert not other.unit
        return Measure(float(self) ** other, self.unit * self.unit)

    def __str__(self):
        if self.unit:
            return '{} {}'.format(float(self), self.unit)
        else:
            return str(float(self))

    def convert(self, other_unit):
        """
        Converts a measure into a different unit.
        """
        multiplier, normalized = other_unit.normalize()
        assert self.unit == normalized
        return Measure(float(self) / multiplier, other_unit)

class Percentage(float):
    """
    Class for representing percentages of measures. Implements non-obvious
    arithmetic, such as "100 + 15% = 115" and "100 * 15% = 15". For most
    operations behave as a float, where 100% is 1.0.
    """
    def __radd__(self, other):
        if isinstance(other, Percentage):
            return Percentage(float(other) + float(self))
        return other * (1 + float(self))

    def __rsub__(self, other):
        if isinstance(other, Percentage):
            return Percentage(float(other) - float(self))
        return other * (1 - float(self))

    def __str__(self):
        return str(float(self) * 100) + '%'

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

    text = re.sub(pattern(r'^(.+) in ({unit})$'),
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


    from flask import Flask, request
    app = Flask(__name__)

    @app.route('/')
    def hello():
        if len(request.args):
            query = request.args['q']
            body = print_page(parse(query))
        else:
            query = ''
            body = ''
        return '<html><body><form action="/" method="GET"><input name="q" value="{}" style="width: 500" autofocus/></form>{}</body></html>'.format(query, body)

    app.debug = True
    app.run()
