import abc
from Market.Util import Constants, OneOf

class Rate():
    yearBasis = OneOf(Constants.YearBasis)
    paymentFrequency = OneOf(Constants.RateConvention)
    rateConvention = OneOf(Constants.RateConvention)

    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                 yearBasis, rate, paymentFrequency, dateAdjuster):
        self.startDate = startDate
        self.maturityDate = maturityDate
        self.ccy = ccy
        self.label = label
        self.rateConvention = rateConvention
        self.yearBasis = yearBasis
        self.rate = rate
        self.paymentFrequency = paymentFrequency
        self.dateAdjuster = dateAdjuster


    @abc.abstractmethod
    def fromRow():
        return NotImplementedError

    def Shock(self,amount):
        self.rate += amount




    
