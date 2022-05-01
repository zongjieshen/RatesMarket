from Market.Pillars import *
import Market.Dates as Dates


#Deposit Rate
class DepositRate(Rate):
    def __init__(self, *args, **kwargs):
        super(DepositRate, self).__init__(*args, **kwargs)
        self.quoteType = 'DepositRate'

    @classmethod
    def fromRow(cls, row, valueDate):
        calendar = row["Calendar"]
        startDate = Dates.ScheduleDefinition.DateConvert(row["StartDate"], valueDate,calendar)
        maturityDate = Dates.ScheduleDefinition.DateConvert(row["Maturity"], valueDate,calendar)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency, calendar)

