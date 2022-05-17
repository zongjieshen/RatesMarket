from market.pillars import *

#SwapRate
class CreditDefaultSwapRate(Rate):
    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,dateAdjuster,couponRate, recoveryRate):
        super(CreditDefaultSwapRate, self).__init__(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,dateAdjuster)
        self.couponRate = couponRate
        self.recoveryRate = recoveryRate
        self.quoteType = 'CreditDefaultSwapRate'

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
        couponRate = row["Coupon"]
        paymentFrequency = row["PaymentFrequency"]
        recoveryRate = row["RecoveryRate"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,dateAdjuster,couponRate, recoveryRate)




    
