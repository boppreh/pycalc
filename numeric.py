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

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        assert not hasattr(other, 'unit') or self.unit == other.unit
        return Measure(float(self) - other, self.unit)

    def __rsub__(self, other):
        return self.__sub__(-other)

    def __mul__(self, other):
        if hasattr(other, 'unit'):
            return Measure(float(self) * other, self.unit * other.unit)
        else:
            return Measure(float(self) * other, self.unit)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        if hasattr(other, 'unit'):
            return Measure(float(self) / other, self.unit / other.unit)
        else:
            return Measure(float(self) / other, self.unit)

    def __rtruediv__(self, other):
        if hasattr(other, 'unit'):
            return Measure(other / float(self), self.unit / other.unit)
        else:
            return Measure(other / float(self), self.unit)

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
