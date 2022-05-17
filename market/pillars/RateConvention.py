import numpy as np
import math
from market.util import Constants, OneOf

#RateConvention class
class RateConvention():
    rateConvention = OneOf(Constants.RateConvention)

    def __init__(self, rateConvention, yearFraction):
        self.rateConvention = rateConvention
        #Call accrued period method to convert year fraction
        self.yearFraction = yearFraction

    def DfToRate(self,dfs):
        if isinstance(dfs, (list,np.ndarray)) == False:
            dfs = [dfs]
            yearFraction = [self.yearFraction]
        else:
            yearFraction = self.yearFraction
        rate = np.empty_like(dfs, dtype=np.float64)
        for idx, (df, t) in enumerate(zip(dfs,yearFraction)):
            if t == 0:
                rate[idx] = 0
            elif self.rateConvention.lower() == 'zero':
                rate[idx]= - math.log(df) / t
            elif self.rateConvention.lower() == 'linear':
                rate[idx]= (1/df - 1)/t
            elif self.rateConvention.lower() == 'annual':
                rate[idx]= pow(df, -1/t) -1
            elif self.rateConvention.lower() == 'semiAnnual':
                rate[idx]= 2 * pow(df, -1/(2*t)) -1
            elif self.rateConvention.lower() == 'monthly':
                rate[idx]= 12 * pow(df, -1/(12*t)) -1
            elif self.rateConvention.lower() == 'quarterly':
                rate[idx]= 4 * pow(df, -1/(4*t)) -1
            else:
                raise Exception('RateConvention not Implemented')
        return rate

    def RateToDf(self, rates):
        if isinstance(rates, (list,np.ndarray)) == False:
            rates = [rates]
            yearFraction = [self.yearFraction]
        dfs = np.empty_like(rates, dtype=np.float64)
        for idx, (rate, t) in enumerate(zip(rates,yearFraction)):
            if t == 0: 
                dfs[idx] =1
            elif self.rateConvention.lower() == 'zero':
                dfs[idx]= - pow(-rate * t)
            elif self.rateConvention.lower() == 'linear':
                dfs[idx]= 1 / (1 + rate * t)
            elif self.rateConvention.lower() == 'annual':
                dfs[idx]= pow(1 + rate, -t)
            elif self.rateConvention.lower() == 'semiAnnual':
                dfs[idx]= 2 * pow(1 + rate/2, -t)
            elif self.rateConvention.lower() == 'monthly':
                dfs[idx]= 12 * pow(1 + rate/12, -t)
            elif self.rateConvention.lower() == 'quarterly':
                dfs[idx]= 4 * pow(1 + rate/4, -t)
            else:
                raise Exception('RateConvention not Implemented')
        return dfs


    
