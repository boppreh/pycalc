from __future__ import division
from collections import Counter
import re
from math import *
from urllib import urlencode

si_prefixes_multipliers = {
    'centi': 1 / 100,
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
    'u': 'micro',
    'n': 'nano',
    'k': 'kilo',
    'c': 'centi',
}

unit_abbreviations = {
    'g': 'gram',
    's': 'second',
    'm': 'meter',

    'h': 'hour',
    'min': 'minute',

    'in': 'inch',
    'ft': 'foot',

    'b': 'bit',
    'B': 'byte',
}

alternative_units = {
    'inch': (2.54, 'centimeter'),
    'foot': (30.48, 'centimeter'),
    'yard': (0.9144, 'meter'),
    'mile': (1.60934, 'kilometer'),

    'minute': (60, 'second'),
    'hour': (60, 'minute'),
    'day': (24, 'hour'),
    'week': (7, 'day'),
    'month': (30, 'day'),
    'year': (12, 'month'),
    'century': (100, 'year'),
    'millennium': (1000, 'year'),

    'kb': (1000, 'bit'),
    'mb': (1000 ** 2, 'bit'),
    'gb': (1000 ** 3, 'bit'),
    'tb': (1000 ** 3, 'bit'),

    'byte': (8, 'bit'),
    'KB': (1000, 'byte'),
    'MB': (1000 ** 2, 'byte'),
    'GB': (1000 ** 3, 'byte'),
    'TB': (1000 ** 3, 'byte'),
}

class Unit(object):
    def __init__(self, numerator=(), denominator=()):
        self.numerator = tuple(numerator)
        self.denominator = tuple(denominator)

    def __bool__(self):
        return bool(self.numerator or self.denominator)

    def __mul__(self, other):
        return Unit(self.numerator + other.numerator, self.denominator + self.denominator)

    def __truediv__(self, other):
        return Unit(self.numerator + other.denominator, self.denominator + other.numerator)

    def __eq__(self, other):
        return self.numerator == other.numerator and self.denominator == other.denominator

    def group_powers(self, units):
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

        if not any(den.values()):
            return self.group_powers(num)
        else:
            return self.group_powers(num) + ' / ' + self.group_powers(den)

    @staticmethod
    def normalize_single(name):
        old_name = name
        total_multiplier = 1.0

        if name in unit_abbreviations:
            name = unit_abbreviations[name]

        if name in alternative_units:
            multiplier, name = alternative_units[name] 
            total_multiplier *= multiplier

        for prefix in si_prefix_abbreviations:
            unit = name[len(prefix):]
            if unit in unit_abbreviations:
                long_prefix = si_prefix_abbreviations[prefix]
                long_unit = unit_abbreviations[unit]
                name = long_prefix + long_unit 

        for prefix, multiplier in si_prefixes_multipliers.items():
            if name.startswith(prefix) and len(name) > len(prefix):
                total_multiplier *= multiplier
                name = name[len(prefix):]

        if name  == old_name:
            return (total_multiplier, name)
        else:
            new_multiplier, new_name = Unit.normalize_single(name)
            return new_multiplier * total_multiplier, new_name

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

    def convert(self, other_unit):
        multiplier, normalized = other_unit.normalize()
        assert self.unit == normalized
        return Measure(float(self) / multiplier, other_unit)

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

def to_measure(value, unit):
    multiplier, new_unit = unit.normalize()
    return Measure(value * multiplier, new_unit)

def to_unit(text):
    text = text.replace(' ', '')
    if '/' in text:
        numerator, denominator = text.split('/')
        return Unit([numerator], [denominator])
    else:
        return Unit([text])


def pattern(text):
    number = r'(\d+(?:\.\d*)?)'
    word = r'([a-zA-Z]+)'
    unit = r'([a-zA-Z]+(?:\s*/\s*[a-zA-Z]+)?)'
    beginning = r'(?:(?<=\W)|^)'
    return beginning + text.format(number=number, word=word, unit=unit)

def parse(text):
    text = re.sub(pattern(r'{number}%'), r'Percentage(\1 / 100)', text)

    text = re.sub(pattern(r'^(.+) in ({unit})$'),
                  r'(\1).convert(to_unit("\2"))',
                  text)

    text = re.sub(pattern(r'{number}\s*{unit}'),
                  r'to_measure(\1, to_unit("\2"))',
                  text)

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
        return '<html><body><form action="/" method="GET"><input name="q" value="{}" style="width: 500" autofocus/></form>{}</body></html>'.format(query, body)

    app.debug = True
    app.run()
