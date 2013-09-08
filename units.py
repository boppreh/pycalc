from __future__ import division
from collections import Counter

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

    'pound': (0.453592, 'kilogram'),
    'stone': (6.35029, 'kilogram'),

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
    'pb': (1000 ** 4, 'bit'),

    'byte': (8, 'bit'),
    'KB': (1000, 'byte'),
    'MB': (1000 ** 2, 'byte'),
    'GB': (1000 ** 3, 'byte'),
    'TB': (1000 ** 3, 'byte'),
    'PB': (1000 ** 4, 'byte'),
}

class Unit(object):
    """
    Class for representing a rational unit, such as "kilometer/second" or
    "newton/m^2".

    Each unit part is a string that is handled in a normalized form (usually SI
    unit).
    """
    def __init__(self, numerator=(), denominator=()):
        """
        Creates a new unit with numerator and denominator, automatically
        simplifying the fraction as necessary.
        """
        numerator, denominator = list(numerator), list(denominator)
        for name in numerator:
            if name in denominator:
                numerator.remove(name)
                denominator.remove(name)
        self.numerator = numerator
        self.denominator = denominator

    def __nonzero__(self):
        return bool(len(self.numerator) or len(self.denominator))

    def __bool__(self):
        return self.__nonzero__()

    def __mul__(self, other):
        return Unit(self.numerator + other.numerator, self.denominator + other.denominator)

    def __truediv__(self, other):
        return Unit(self.numerator + other.denominator, self.denominator + other.numerator)

    def __eq__(self, other):
        return (isinstance(other, Unit) and 
                sorted(self.numerator) == sorted(other.numerator) and
                sorted(self.denominator) == sorted(other.denominator))

    def _group_powers(self, units):
        """
        Converts a list of units into a nice string grouping their powers.
        Ex: "m m m s" -> "m^3 s".
        """
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

        if not self.denominator:
            return self._group_powers(num)
        else:
            den = Counter(self.denominator)
            return self._group_powers(num) + ' / ' + self._group_powers(den)

    @staticmethod
    def _normalize_single(name):
        """
        Normalizes a single unit part, expanding abbreviations and converting
        to SI units as necessary. Automatically normalizes until reaching a
        stable name.

        Return the multiplier and the new name. Ex: "km" -> (1000, "meter").
        """
        old_name = name
        total_multiplier = 1.0

        # Expand direct abbreviations.
        if name in unit_abbreviations:
            name = unit_abbreviations[name]

        # Convert alternative units to SI.
        if name in alternative_units:
            multiplier, name = alternative_units[name] 
            total_multiplier *= multiplier

        # Expand abbreviated SI prefixes if unit is also abbreviated.
        for prefix in si_prefix_abbreviations:
            unit = name[len(prefix):]
            if name.startswith(prefix) and unit in unit_abbreviations:
                long_prefix = si_prefix_abbreviations[prefix]
                long_unit = unit_abbreviations[unit]
                name = long_prefix + long_unit 

        # Remove SI prefixes.
        for prefix, multiplier in si_prefixes_multipliers.items():
            if name.startswith(prefix) and len(name) > len(prefix):
                total_multiplier *= multiplier
                name = name[len(prefix):]

        if name  == old_name:
            assert total_multiplier == 1.0
            return (1.0, name)
        else:
            # Repeat until no changes.
            new_multiplier, new_name = Unit._normalize_single(name)
            return new_multiplier * total_multiplier, new_name

    def normalize(self):
        """
        Returns a normalized Unit instance and its multiplier in relation to
        the current instance.
        """
        total_multiplier = 1.0
        new_numerator = []
        new_denominator = []

        for name in self.numerator:
            multiplier, new_name = self._normalize_single(name)
            total_multiplier *= multiplier
            new_numerator.append(new_name)

        for name in self.denominator:
            multiplier, new_name = self._normalize_single(name)
            total_multiplier /= multiplier
            new_denominator.append(new_name)

        return (total_multiplier, Unit(new_numerator, new_denominator))
