from __future__ import division
from collections import Counter
import re
from math import *
from urllib import urlencode

si_prefixes_multipliers = {
    'milli': 1 / 1000,
    'micro': 1 / 1000 ** 2,
    'nano': 1 / 1000 ** 3,
    'kilo': 1000,

    'mega': 1000 ** 2,
    'giga': 1000 ** 3,
    'tera': 1000 ** 4,
    'peta': 1000 ** 5,
    'exa': 1000 ** 6,
}

si_prefix_abbreviations = {
    'm': 'milli',
    'n': 'nano',
    'k': 'kilo',
}

si_unit_abbreviations = {
    'g': 'gram',
    's': 'second',
    'b': 'bit',
    'B': 'byte',
    'm': 'meter',
}

class Unit(object):
    def __init__(self, numerator=(), denominator=()):
        self.numerator = numerator
        self.denominator = denominator

    def __bool__(self):
        return bool(self.numerator or self.denominator)

    def __mul__(self, other):
        return Unit(self.numerator + other.numerator, self.denominator + self.denominator)

    def __truediv__(self, other):
        return Unit(self.numerator + other.denominator, self.denominator + other.numerator)

    def __eq__(self, other):
        return self.numerator == other.numerator and self.denominator == other.denominator

    def simplify(self, units):
        str_numerators = []
        for unit, count in units.items():
            if count == 0:
                continue
            elif count == 1:
                str_numerators.append(str(unit))
            else:
                str_numerators.append(str(unit) + '^' + str(count))

        return ' '.join(str_numerators)

    def __str__(self):
        num = Counter(self.numerator)
        den = Counter(self.denominator)
        for unit, count in num.items():
            num[unit] -= min(count, den[unit])
            den[unit] -= min(count, den[unit])

        if not all(den.values()):
            return self.simplify(num)
        else:
            return self.simplify(num) + ' / ' + self.simplify(den)

    @staticmethod
    def normalize_single(name):
        if len(name) == 1 and name in si_unit_abbreviations:
            name = si_unit_abbreviations[name]
        elif len(name) == 2:
            prefix, unit = name[0], name[1]

            if (prefix in si_prefix_abbreviations and
                unit in si_unit_abbreviations):

                long_prefix = si_prefix_abbreviations[prefix]
                long_unit = si_unit_abbreviations[unit]
                name = long_prefix + long_unit 

        for prefix, multiplier in si_prefixes_multipliers.items():
            if name.startswith(prefix) and len(name) > len(prefix):
                return (multiplier, name[len(prefix):])

        return (1, name)

    def normalize(self):
        total_multiplier = 1.0
        new_numerator = []
        new_denominator = []

        for name in self.numerator:
            multiplier, new_name = self.normalize_single(name)
            total_multiplier *= multiplier
            new_numerator.append(new_name)

        for name in self.denominator:
            multiplier, new_name = self.normalize_single(name)
            total_multiplier /= multiplier
            new_denominator.append(new_name)

        return (total_multiplier, Unit(new_numerator, new_denominator))

class Measure(float):
    def __new__(cls, value, unit):
        return float.__new__(cls, value)

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

class Percentage(float):
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

def to_measure(value, name):
    multiplier, name = Unit.normalize_single(name)
    return Measure(value * multiplier, Unit((name,), ()))

def pattern(text):
    number = r'(\d+(?:\.\d*)?)'
    word = r'([a-zA-Z]+)'
    beginning = r'(?:^|\W)'
    return beginning + text.format(number=number, word=word)

def parse(text):
    text = re.sub(pattern('{number}%'), r'Percentage(\1 / 100)', text)
    text = re.sub(pattern('{number}\s*{word}'), r'to_measure(\1, "\2")', text)
    return eval(text)


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
    template = template.replace('\n', '<br>').replace('result', str(value))
    for expression in re.findall('{{(.+?)}}', template):
        exp_result = parse(expression)
        uri = urlencode({'q': expression})
        link = '<a href="/?{}">{}</a>'.format(uri, exp_result)
        template = template.replace('{{' + expression + '}}', link)

    return template

def print_page(value):
    for type, template in page_templates.items():
        if isinstance(value, type):
            return apply_template(value, template)

    return str(value)


if __name__ == "__main__":
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
        return '<html><body><form action="/" method="GET"><input name="q" value="{}" autofocus/></form>{}</body></html>'.format(query, body)

    app.debug = True
    app.run()
