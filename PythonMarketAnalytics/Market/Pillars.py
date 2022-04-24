import Market.Dates as Dates
import pandas as pd
import numpy as np
import math

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


    @classmethod
    def fromRow():
        return NotImplementedError

    def Shock(self,amount):
        self.rate += amount


#Bond Quote
class BondQuote(Rate):
    def __init__(self, *args, **kwargs):
        super(BondQuote, self).__init__(*args, **kwargs)
        self.quoteType = 'BondQuote'


class BondYield(BondQuote):
    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,calendar, coupon):
        super(BondYield, self).__init__(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency, calendar)
        self.quoteType='BondYield'
        self.coupon = coupon

    @classmethod
    def fromRow(cls, row, bondType, valueDate):
        calendar = row["Calendar"]
        startDate = Dates.ScheduleDefinition.DateConvert(row["StartDate"], valueDate,calendar)
        maturityDate = Dates.ScheduleDefinition.DateConvert(row["Maturity"], valueDate,calendar)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        coupon = row["Coupon"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency, calendar,coupon)


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


#Discount Factor
class DiscountFactorRate():
    def __init__(self, maturityDate, value):
        self.quoteType = 'DiscountFactor'
        self.maturityDate = maturityDate
        self.value = value

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









#RateConvention class
class RateConvention():
    def __init__(self, rateConvention, yearFraction):
        self._rateConvention = rateConvention
        #Call accrued period method to convert year fraction
        self.yearFraction = yearFraction

    def DfToRate(self,dfs):
        if isinstance(dfs, list) == False:
            rates = [dfs]
            yearFraction = [self.yearFraction]
        rate = np.empty_like(dfs, dtype=np.float64)
        for idx, (df, t) in enumerate(zip(dfs,self.yearFraction)):
            if t == 0:
                rate[idx] = 0
            elif self._rateConvention.lower() == 'zero':
                rate[idx]= - math.log(df) / t
            elif self._rateConvention.lower() == 'linear':
                rate[idx]= (1/df - 1)/t
            elif self._rateConvention.lower() == 'annual':
                rate[idx]= pow(df, -1/t) -1
            elif self._rateConvention.lower() == 'semiAnnual':
                rate[idx]= 2 * pow(df, -1/(2*t)) -1
            elif self._rateConvention.lower() == 'monthly':
                rate[idx]= 12 * pow(df, -1/(12*t)) -1
            elif self._rateConvention.lower() == 'quarterly':
                rate[idx]= 4 * pow(df, -1/(4*t)) -1
            else:
                raise Exception('RateConvention not Implemented')
        return rate

    def RateToDf(self, rates):
        if isinstance(rates, list) == False:
            rates = [rates]
            yearFraction = [self.yearFraction]
        dfs = np.empty_like(rates, dtype=np.float64)
        for idx, (rate, t) in enumerate(zip(rates,yearFraction)):
            if t == 0: 
                dfs[idx] =1
            elif self._rateConvention.lower() == 'zero':
                dfs[idx]= - pow(-rate * t)
            elif self._rateConvention.lower() == 'linear':
                dfs[idx]= 1 / (1 + rate * t)
            elif self._rateConvention.lower() == 'annual':
                dfs[idx]= pow(1 + rate, -t)
            elif self._rateConvention.lower() == 'semiAnnual':
                dfs[idx]= 2 * pow(1 + rate/2, -t)
            elif self._rateConvention.lower() == 'monthly':
                dfs[idx]= 12 * pow(1 + rate/12, -t)
            elif self._rateConvention.lower() == 'quarterly':
                dfs[idx]= 4 * pow(1 + rate/4, -t)
            else:
                raise Exception('RateConvention not Implemented')
        return dfs


    
