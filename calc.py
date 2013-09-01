from __future__ import division
from collections import Counter
import re

si_prefixes = {
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

si_units = [
    'gram',
    'second',
    'byte',
    'bit',
    'meter',
]

si_prefix_abbreviations = {
    'm': 'milli',
    'n': 'nano',
    'k': 'kilo',
}

si_units_abbreviations = {
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

def to_unit(name):
    return Unit((name,), ())

def pattern(text):
    number = r'(\d+(?:\.\d*)?)'
    word = r'([a-zA-Z]+)'
    beginning = r'(?:^|\W)'
    return beginning + text.format(number=number, word=word)

def parse(text):
    text = re.sub(pattern('{number}%'), r'Percentage(\1 / 100)', text)
    text = re.sub(pattern('{number}\s*{word}'), r'Measure(\1, to_unit("\2"))', text)
    return eval(text)

def print_page(value):
    if isinstance(value, Measure):
        return str(value)
    elif isinstance(value, Percentage):
        complement = Percentage(1 - value)
        inverse = 1 / value
        return '{value}<br><br>Complement: <a href="?q=100%-{value}">{complement}</a><br>Inverse: <a href="?q=1/{value}">{inverse}</a>'.format(value=value, complement=complement, inverse=inverse)
    elif isinstance(value, float) or isinstance(value, int):
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
