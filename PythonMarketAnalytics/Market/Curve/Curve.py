import Market.Dates as Dates
from Market.Pillars import *
from Market.Instruments import *
from Market.IndexFixing import *
import pandas as pd
import numpy as np
import abc
import copy

class Curve():
    def __init__(self, key, ccy, valueDate, **kwargs):
        self.key= key
        self.ccy = ccy
        self.valueDate = valueDate
        #Add property to check if discountCurve exists in Market
        self.discountCurve = kwargs.get('discountcurve',self.key)
        self.interpMethod = kwargs.get('interpmethod','linear')
        self.initialFactor = kwargs.get('initialFactor',1)

        self._built = False
        self.points = np.array([(np.datetime64(self.valueDate.strftime('%Y-%m-%d')),
                                ScheduleDefinition.DateOffset(self.valueDate),
                                np.log(self.initialFactor))],
                              dtype=[('maturity', 'datetime64[D]'),
                                     ('timestamp', np.float64),
                                     ('discount_factor', np.float64)])

        self.points = self.points[0]


    @abc.abstractmethod
    def Build(self):
        return NotImplementedError

    def DiscountFactor(self, dates, returndf = False):
        '''Returns the interpolated discount factor for an arbitrary date
        '''
        
        if isinstance(dates,list) is True:
            dates = np.asarray(dates)
        if isinstance(dates,np.ndarray) is False:
            dates = np.asarray([dates])
        #if all(isinstance(item, (datetime.datetime, np.datetime64)) for item in dates):
        #    dates = np.array(pd.to_datetime(dates))
        interpolator = scipy.interpolate.interp1d(self.points['timestamp'],
                                                  self.points['discount_factor'],
                                                  kind=self.InterpMethod,
                                                  fill_value='extrapolate') 
        values = np.exp(interpolator(ScheduleDefinition.DateOffset(dates)))

        if returndf is True:
            dt = pd.DataFrame(list(zip(dates,values)),columns =['Dates', f'{self.key}.DiscountFactor'])
            dt.set_index('Dates',inplace=True)
            return dt
        else:
            return np.exp(interpolator(dates.astype('<M8[s]')))
    
    def ZeroRates(self, dates, yearBasis = 'acton365f', rateConvention = 'linear'):
        if isinstance(dates, list) == False:
            dates =[dates]
        startDates = [self.valueDate] * len(dates)
        yearFractions = ScheduleDefinition.YearFractionList(startDates,dates,yearBasis)
        dfs = self.DiscountFactor(dates)
        values = RateConvention(rateConvention,yearFractions).DfToRate(dfs)
        dt = pd.DataFrame(list(zip(dates,values)),columns =['Dates', f'{self.key}.ZeroRates'])
        dt.set_index('Dates',inplace=True)
        return dt
    
    def FwdRates(self, startDates, tenor, yearBasis = 'acton365f', rateConvention = 'linear'):
        if isinstance(startDates, list) == False:
            startDates =[startDates]
        endDates = [x + ScheduleDefinition._parseDate(tenor) for x in startDates] 
        yearFractions = ScheduleDefinition.YearFractionList(startDates,endDates,yearBasis)
        df1 = self.DiscountFactor(startDates)
        df2 = self.DiscountFactor(endDates)
        dfs = df2/df1
        fwd = RateConvention(rateConvention,yearFractions).DfToRate(dfs)
        dt = pd.DataFrame(list(zip(startDates,fwd)),columns =['Dates', f'{self.key}.FwdRates'])
        dt.set_index('Dates',inplace=True)
        return dt

    def SwapRates(self,dates, tenor, yearBasis = 'acton365f', rateConvention = 'linear', adjustment = 'modified following', calendar = 'SYD'):
        def _sumproduct(date):
                dateAdjuster = DateAdjuster(adjustment, calendar)
                schedule = mkt.Schedule(self.valueDate,date,tenor,dateAdjuster)
                schedule._create_schedule()
                periodStart = schedule.periods['accrual_start']
                periodEnd  = schedule.periods['accrual_end']
                yearFractions = ScheduleDefinition.YearFractionList(periodStart,periodEnd,yearBasis)
                dfs = self.DiscountFactor(periodStart)
                return np.sum(np.multiply(dfs, yearFractions))

        if isinstance(dates, list) == False:
            dates =[dates]
        swapRates = []
        for date in dates:
            if date == self.valueDate:
                continue
            dcf = self.DiscountFactor(self.valueDate) - self.DiscountFactor(date)
            sumProduct = _sumproduct(date)
            swapRate = np.divide(dcf, sumProduct)
            swapRates.append(swapRate.flat[0])
        dt = pd.DataFrame(list(zip(dates,swapRates)),columns =['Dates', f'{self.key}.SwapRates'])
        dt.set_index('Dates',inplace=True)
        return dt

    @staticmethod
    def Charts(curves, returnType, dates, tenor = '+3m',yearBasis = 'acton365f', rateConvention = 'linear'):
        if isinstance(curves, list) == False:
            curves =[curves]
        charts = []

        for curve in curves:
            if isinstance(curve, IndexFixing) == True:
                continue
            if returnType.lower().startswith ('zero'):
                charts.append(curve.ZeroRates(dates, yearBasis, rateConvention))
            elif returnType.lower().startswith('fwd'):
                charts.append(curve.FwdRates(dates, tenor, yearBasis, rateConvention))
            elif returnType.lower().startswith ('swaprate'):
                charts.append(curve.SwapRates(dates, tenor, yearBasis, rateConvention))
            else:
                charts.append(curve.DiscountFactor(dates,returndf = True))
        return pd.concat(charts,axis=1)

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

    def _addInstruments(self, market):
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