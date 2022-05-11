from abc import ABC, abstractmethod

class Constants:
    Adjustments = {'unadjusted','following','modified following','preceding'}
    YearBasis = {'acton360','acton365f','30360','30e360','equalcoupons','actonact'}
    ItemType = {'yieldcurve','pricecurve','indexfixing','spreadyieldcurve','inflationcurve'}
    InterpMethod = {'linear', 'nearest', 'nearest-up', 'zero', 'slinear', 'quadratic', 'cubic', 'previous', 'next', 'zero', 'slinear', 'quadratic', 'cubic'}
    RateConvention = {'zero','linear','annual','semiannual','monthly','quarterly'}


class Validator(ABC):

    def __set_name__(self, owner, name):
        self.private_name = '_' + name

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self.private_name, value.lower())

    @abstractmethod
    def validate(self, value):
        pass

class OneOf(Validator):
    def __init__(self, options):
        self.options = options

    def validate(self, value):
        if value.lower() not in self.options:
            raise ValueError(f'Expected {value!r} to be one of {self.options!r}')