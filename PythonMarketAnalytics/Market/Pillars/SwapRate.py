from Market.Pillars import *
import Market.Dates as Dates

#SwapRate
class SwapRate(Rate):
    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,calendar,compoundFrequency,paymentDelay):
        super(SwapRate, self).__init__(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,calendar)
        self.compoundFrequency = compoundFrequency
        self.paymentDelay = paymentDelay
        self.quoteType = 'SwapRate'

    @classmethod
    def fromRow(cls, row, valueDate):
        calendar = row["Calendar"]
        startDate = Dates.ScheduleDefinition.DateConvert(row["StartDate"], valueDate, calendar)
        maturityDate = Dates.ScheduleDefinition.DateConvert(row["Maturity"], valueDate, calendar)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        compoundFrequency = row['CompoundingFrequency']
        paymentDelay = row["PaymentDelay"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,calendar,compoundFrequency,paymentDelay)

class BasisSwapRate(SwapRate):
    def __init__(self, *args, **kwargs):
        super(BasisSwapRate, self).__init__(*args, **kwargs)
        self.quoteType = 'BasisSwapRate'



    
