from market.pillars import *

#SwapRate
class CreditDefaultSwapRate(Rate):
    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,calendar,couponRate, recoveryRate):
        super(CreditDefaultSwapRate, self).__init__(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,calendar)
        self.couponRate = couponRate
        self.recoveryRate = recoveryRate
        self.quoteType = 'CreditDefaultSwapRate'
        
    def __repr__(self):
        return (f"SwapRate('{self.startDate.strftime('%Y-%m-%d')}', '{self.maturityDate.strftime('%Y-%m-%d')}', '{self.ccy}', '{self.label}', "
                f"'{self.rateConvention}', '{self.yearBasis}', {self.rate}, '{self.paymentFrequency}', '{self.calendar}', '{self.couponRate}', '{self.recoveryRate}')")
        
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
                   yearBasis, rate, paymentFrequency,calendar,couponRate, recoveryRate)




    
