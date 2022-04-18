import Market.Dates as Dates
import pandas as pd
import numpy as np
import math

class Rate():
    def __init__(self, startDate, maturityDate, ccy, label, rateConvention, 
                 yearBasis, rate, paymentFrequency):
        self.startDate = startDate
        self.maturityDate = maturityDate
        self.ccy = ccy
        self.label = label
        self.rateConvention = rateConvention
        self.yearBasis = yearBasis
        self.rate = rate
        self.paymentFrequency = paymentFrequency



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
                   yearBasis, rate, paymentFrequency,coupon):
        super(BondYield, self).__init__(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency)
        self.quoteType='BondYield'
        self.coupon = coupon

    @classmethod
    def fromRow(cls, row, bondType, valueDate):
        startDate = Dates.ScheduleDefinition.DateConvert(row["StartDate"], valueDate)
        maturityDate = Dates.ScheduleDefinition.DateConvert(row["Maturity"], valueDate)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        coupon = row["Coupon"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency,coupon)


#Deposit Rate
class DepositRate(Rate):
    def __init__(self, *args, **kwargs):
        super(DepositRate, self).__init__(*args, **kwargs)
        self.quoteType = 'DepositRate'

    @classmethod
    def fromRow(cls, row, valueDate):
        startDate = Dates.ScheduleDefinition.DateConvert(row["StartDate"], valueDate)
        maturityDate = Dates.ScheduleDefinition.DateConvert(row["Maturity"], valueDate)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency)


#Discount Factor
class DiscountFactorRate():
    def __init__(self, maturityDate, value):
        self.quoteType = 'DiscountFactor'
        self.maturityDate = maturityDate
        self.value = value

#SwapRate
class SwapRate(Rate):
    def __init__(self, *args, **kwargs):
        super(SwapRate, self).__init__(*args, **kwargs)


    @classmethod
    def fromRow(cls, row, valueDate):
        startDate = Dates.ScheduleDefinition.DateConvert(row["StartDate"], valueDate)
        maturityDate = Dates.ScheduleDefinition.DateConvert(row["Maturity"], valueDate)
        ccy = row["Currency"]
        label = row["Label"]
        rateConvention = row["RateConvention"]
        yearBasis = row["YearBasis"]
        rate = row["Value"]
        paymentFrequency = row["PaymentFrequency"]
        cls.compoundFrequency = row['CompoundingFrequency']
        cls.paymentDelay = row["PaymentDelay"]
        return cls(startDate, maturityDate, ccy, label, rateConvention, 
                   yearBasis, rate, paymentFrequency)













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
        for idx, df, t in enumerate(zip(dfs,self.yearFraction)):
            if t == 0:
                rate[idx] = 0
            elif self._rateConvention == 'Zero':
                rate[idx]= - math.log(df) / t
            elif self._rateConvention == 'Linear':
                rate[idx]= (1/df - 1)/t
            elif self._rateConvention == 'Annual':
                rate[idx]= pow(df, -1/t) -1
            elif self._rateConvention == 'SemiAnnual':
                rate[idx]= 2 * pow(df, -1/(2*t)) -1
            elif self._rateConvention == 'Monthly':
                rate[idx]= 12 * pow(df, -1/(12*t)) -1
            elif self._rateConvention == 'Quarterly':
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
            elif self._rateConvention == 'Zero':
                dfs[idx]= - pow(-rate * t)
            elif self._rateConvention == 'Linear':
                dfs[idx]= 1 / (1 + rate * t)
            elif self._rateConvention == 'Annual':
                dfs[idx]= pow(1 + rate, -t)
            elif self._rateConvention == 'SemiAnnual':
                dfs[idx]= 2 * pow(1 + rate/2, -t)
            elif self._rateConvention == 'Monthly':
                dfs[idx]= 12 * pow(1 + rate/12, -t)
            elif self._rateConvention == 'Quarterly':
                dfs[idx]= 4 * pow(1 + rate/4, -t)
            else:
                raise Exception('RateConvention not Implemented')
        return dfs


    
