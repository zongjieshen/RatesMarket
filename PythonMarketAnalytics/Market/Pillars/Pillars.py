import abc

class Rate():
    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                 yearBasis, rate, paymentFrequency, calendar):
        self.startDate = startDate
        self.maturityDate = maturityDate
        self.ccy = ccy
        self.label = label
        self.rateConvention = rateConvention
        self.yearBasis = yearBasis
        self.rate = rate
        self.paymentFrequency = paymentFrequency
        self.calendar = calendar


    @abc.abstractmethod
    def fromRow():
        return NotImplementedError

    def Shock(self,amount):
        self.rate += amount




    
