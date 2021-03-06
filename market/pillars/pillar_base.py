import abc
from market.dates import *
from market.util import Constants, OneOf

class Rate():
    yearBasis = OneOf(Constants.YearBasis)
    paymentFrequency = OneOf(Constants.RateConvention)
    rateConvention = OneOf(Constants.RateConvention)

    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                 yearBasis, rate, paymentFrequency, calendar, adjustment = 'modified following'):
        self.startDate = startDate if isinstance(startDate, datetime.datetime) is True else ScheduleDefinition.DateConvert(startDate)
        self.maturityDate = maturityDate if isinstance(maturityDate, datetime.datetime) is True else ScheduleDefinition.DateConvert(maturityDate)
        self.ccy = ccy
        self.label = label
        self.rateConvention = rateConvention
        self.yearBasis = yearBasis
        self.rate = rate
        self.paymentFrequency = paymentFrequency
        self.calendar = calendar
        self.dateAdjuster = DateAdjuster(adjustment,calendar)

    def __repr__(self):
        return (f"Label:{self.label}; StartDate:{self.startDate.strftime('%Y-%m-%d')}; MaturityDate:{self.maturityDate.strftime('%Y-%m-%d')}; Ccy:{self.ccy}; "
                f"Rate:{self.rate}; PaymentFrequency: {self.paymentFrequency}; YearBasis:{self.yearBasis}; Calendar:{self.dateAdjuster}")

    @abc.abstractmethod
    def fromRow():
        return NotImplementedError

    def Shock(self,amount):
        self.rate += amount




    
