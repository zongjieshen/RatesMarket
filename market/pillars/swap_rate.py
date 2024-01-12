from market.pillars import *
from market.util import Constants, OneOf

#SwapRate
class SwapRate(Rate):
    def __init__(self, **kwargs):
        super(SwapRate, self).__init__(**kwargs)
        self.compoundFrequency = kwargs['compoundFrequency']
        self.paymentDelay = kwargs['paymentDelay']
        self.quoteType = 'SwapRate'

    def __repr__(self):
        return (f"SwapRate('{self.startDate.strftime('%Y-%m-%d')}', '{self.maturityDate.strftime('%Y-%m-%d')}', '{self.ccy}', '{self.label}', "
                f"'{self.rateConvention}', '{self.yearBasis}', {self.rate}, '{self.paymentFrequency}', '{self.calendar}', '{self.compoundFrequency}', '{self.paymentDelay}')")
    
    @classmethod
    def fromRow(cls, row, valueDate):
        calendar = row["Calendar"]
        dateAdjuster = DateAdjuster('modified following', calendar)
        startDate = ScheduleDefinition.DateConvert(row["StartDate"], valueDate, dateAdjuster)
        maturityDate = ScheduleDefinition.DateConvert(row["Maturity"], valueDate, dateAdjuster)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        compoundFrequency = row['CompoundingFrequency']
        paymentDelay = row["PaymentDelay"]
        ccy2 = row["Currency2"]
        calendar2 = row['Calendar2']
        rateConvention2 = row["RateConvention2"]
        yearBasis2 = row["YearBasis2"]
        paymentFrequency2 = row["PaymentFrequency2"]
        compoundFrequency2 = row['CompoundingFrequency2']
        paymentDelay2 = row["PaymentDelay2"]
        return cls(startDate = startDate, maturityDate = maturityDate, ccy = ccy, label = label, rateConvention = rateConvention, 
                   yearBasis = yearBasis, rate = rate, paymentFrequency = paymentFrequency, calendar = calendar,
                       compoundFrequency = compoundFrequency,paymentDelay = paymentDelay, ccy2 = ccy2, rateConvention2 = rateConvention2, yearBasis2 = yearBasis2, 
                   paymentFrequency2 = paymentFrequency2, compoundFrequency2 = compoundFrequency2,paymentDelay2 = paymentDelay2, calendar2 = calendar2)

class BasisSwapRate(SwapRate):
    def __init__(self, **kwargs):
        super(BasisSwapRate, self).__init__(**kwargs)
        self.quoteType = 'BasisSwapRate'

class XccyBasisSwapRate(SwapRate):
    yearBasis2 = OneOf(Constants.YearBasis)
    paymentFrequency2 = OneOf(Constants.RateConvention)
    rateConvention2 = OneOf(Constants.RateConvention)

    def __init__(self, **kwargs):
        super(XccyBasisSwapRate, self).__init__(**kwargs)
        self.quoteType = 'XccyBasisSwapRate'
        self.ccy2 = kwargs['ccy2']
        self.rateConvention2 = kwargs['rateConvention2']
        self.yearBasis2 = kwargs['yearBasis2']
        self.paymentFrequency2 =kwargs['paymentFrequency2']
        self.compoundFrequency2 = kwargs['compoundFrequency2']
        self.paymentDelay2 = kwargs['paymentDelay2']
        self.calendar2 = kwargs.get('calendar2', None)
        self.dateAdjuster2 = DateAdjuster('modified following', self.calendar2)
