from market.dates import *
from market.instruments import Bond, IndexedBond, CreditDefaultSwap, Deposit, Instrument, Swap, DiscountFactor, BasisSwap
from market.util import Constants, OneOf
from market.pillars import RateConvention
import pandas as pd
import numpy as np
import scipy.interpolate
import copy

class Curve():
    interpMethod = OneOf(Constants.InterpMethod)

    def __init__(self, key, ccy, valueDate, **kwargs):
        self.key= key
        self.ccy = ccy
        self.valueDate = valueDate
        #Add property to check if discountCurve exists in market
        self.discountCurve = kwargs.get('discountcurve',self.key)
        self.interpMethod = kwargs.get('interpmethod','linear')
        self.initialFactor = kwargs.get('initialFactor',1)

        self._built = False

    def __repr__(self):
        return f"{self.key}; {self.ccy}; {self.valueDate.strftime('%Y-%m-%d')}; status:{self._built}"

    def DiscountFactor(self, dates, returndf = False):
        '''Returns the interpolated discount factor for an arbitrary date
        '''
        if isinstance(dates,list) is True:
            dates = np.asarray(dates)
        if isinstance(dates,np.ndarray) is False:
            dates = np.asarray([dates])
        interpolator = scipy.interpolate.interp1d(self.points['timestamp'],
                                                  self.points['discount_factor'],
                                                  kind=self.interpMethod,
                                                  fill_value='extrapolate') 
        values = np.exp(interpolator(ScheduleDefinition.DateOffset(dates)))

        if returndf is True:
            dt = pd.DataFrame(list(zip(dates,values)),columns =['Dates', f'{self.key}.DiscountFactor'])
            dt.set_index('Dates',inplace=True)
            return dt
        else:
            return values
    

    def view(self, ret=False):
        '''Prints the discount factor curve
        Optionally return tuple of the maturities and discount factors
        '''
        if not self._built:
            self.Build()

        maturities = self.points['maturity']
        discount_factors = np.exp(self.points['discount_factor'])
        print(self.key)
        for i in range(len(self.points)):
            date = maturities[i].astype(object).strftime('%Y-%m-%d')
            print('{0} {1:.10f}'.format(date, discount_factors[i]))

        if ret:
            return maturities, discount_factors

    def _addinstruments(self, market):
        """Add instruments for bootstrapping

        Args:
            market (_type_): _description_

        Yields:
            _type_: returns a generator of instruments for performance
        """        
        for pillar in self.pillars:
            if pillar.quoteType == 'BondYield' and pillar.bondType.lower() == 'fixed':
                yield (Bond(pillar, self, market))
            elif pillar.quoteType == 'BondYield' and pillar.bondType.lower() == 'capitalindexed':
                 yield (IndexedBond(pillar, self, market))
            elif pillar.quoteType == 'DiscountFactor':
                yield (DiscountFactor(pillar))
            elif pillar.quoteType == 'DepositRate':
                yield (Deposit(pillar, self, market))
            elif pillar.quoteType == 'SwapRate':
                yield (Swap(pillar, self, market))
            elif pillar.quoteType == 'BasisSwapRate':
                yield (BasisSwap(pillar, self, market))
            elif pillar.quoteType == 'CreditDefaultSwapRate':
                yield (CreditDefaultSwap(pillar, self, market))

    def ItemInfo(self):
        if hasattr(self, 'pillars') is False:
            return f'Curve {self.key} has no pillars'
        pillars = [pd.DataFrame([pillar.__dict__]) for pillar in self.pillars]
        dt = pd.concat(pillars)
        dt = dt.drop(columns = ['dateAdjuster'])
        dt['startDate'] = dt['startDate'].dt.strftime('%d/%m/%Y')
        dt['maturityDate'] = dt['maturityDate'].dt.strftime('%d/%m/%Y')
        dt.columns = dt.columns.str.strip('_').str.capitalize()
        return dt
