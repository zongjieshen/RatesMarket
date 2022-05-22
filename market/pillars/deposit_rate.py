from market.pillars import *


#Deposit Rate
class DepositRate(Rate):
    def __init__(self, *args, **kwargs):
        super(DepositRate, self).__init__(*args, **kwargs)
        self.quoteType = 'DepositRate'

    def __repr__(self):
        return (f"DepositRate('{self.startDate.strftime('%Y-%m-%d')}', '{self.maturityDate.strftime('%Y-%m-%d')}', '{self.ccy}', '{self.label}', "
                f"'{self.rateConvention}', '{self.yearBasis}', {self.rate}, '{self.paymentFrequency}', '{self.calendar}')")

    @classmethod
    def fromRow(cls, row, valueDate):
        calendar = row["Calendar"]
        dateAdjuster = DateAdjuster('modified following', calendar)
        startDate = ScheduleDefinition.DateConvert(row["StartDate"], valueDate,dateAdjuster)
        maturityDate = ScheduleDefinition.DateConvert(row["Maturity"], valueDate,dateAdjuster)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency, calendar)

