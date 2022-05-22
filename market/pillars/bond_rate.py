from market.pillars import *


#Bond Quote
class BondQuote(Rate):
    def __init__(self, *args, **kwargs):
        super(BondQuote, self).__init__(*args, **kwargs)
        self.quoteType = 'BondQuote'


class BondYield(BondQuote):
    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,calendar, coupon, bondType, notionalIndexation):
        super(BondYield, self).__init__(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency, calendar)
        self.quoteType='BondYield'
        self.coupon = coupon
        self.bondType = bondType
        self.notionalIndexation = notionalIndexation

    @classmethod
    def fromRow(cls, row, bondType, valueDate):
        calendar = row["Calendar"]
        dateAdjuster = DateAdjuster('modified following',calendar)
        startDate = ScheduleDefinition.DateConvert(row["StartDate"], valueDate,dateAdjuster)
        maturityDate = ScheduleDefinition.DateConvert(row["Maturity"], valueDate,dateAdjuster)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        coupon = row["Coupon"]
        notionalIndexation = row['NotionalIndexation'] if 'NotionalIndexation' in row else ''

        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency, calendar, coupon, bondType, notionalIndexation)
