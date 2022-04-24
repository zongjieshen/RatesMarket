from Market.Pillars import *
from Market.Instruments import *
from Market.YieldCurveFactory import *
import Market as mkt
import pandas as pd
import scipy.interpolate
import time
import copy

class Curve():
    def __init__(self, key, ccy, valueDate, discountCurve):
        self.key= key
        self.ccy = ccy
        self.valueDate = valueDate
        #Add property to check if discountCurve exists in Market
        self.discountCurve = discountCurve if discountCurve !='' else key
        self._built = False
        self.points = np.array([(np.datetime64(self.valueDate.strftime('%Y-%m-%d')),
                                time.mktime(self.valueDate.timetuple()),
                                np.log(1))],
                              dtype=[('maturity', 'datetime64[D]'),
                                     ('timestamp', np.float64),
                                     ('discount_factor', np.float64)])

        self.points = self.points[0]
    def Build(self):
        return NotImplementedError

    def DiscountFactor(self, dates, returndf = False):
        '''Returns the interpolated discount factor for an arbitrary date
        '''
        
        if isinstance(dates,list) is True:
            dates = np.asarray(dates)
        if isinstance(dates,np.ndarray) is False:
            dates = np.asarray([dates])
        if all(isinstance(item, (datetime.datetime, np.datetime64)) for item in dates):
            dates = np.array(pd.to_datetime(dates))

        interpolator = scipy.interpolate.interp1d(self.points['timestamp'],
                                                  self.points['discount_factor'],
                                                  kind='linear',
                                                  fill_value='extrapolate') 
        values = np.exp(interpolator(dates.astype('<M8[s]')))
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

    def SwapRates(self,dates, tenor, yearBasis = 'acton365f', rateConvention = 'linear'):

        if isinstance(dates, list) == False:
            dates =[dates]
        endDates = [x + ScheduleDefinition._parseDate(tenor) for x in dates]
        startDates = [self.valueDate] * len(dates)
        dcf = self.DiscountFactor(startDates) - self.DiscountFactor(dates)
        yearFractions = ScheduleDefinition.YearFractionList(dates,endDates,yearBasis)
        schedules = [mkt.Schedule(self.valueDate,date,tenor,'modified following','modified following')._gen_dates('modified following') for date in dates]
        cumDcf = [self.DiscountFactor(schedule) for schedule in schedules]
        sumProducts = np.asarray([np.sum(date) for date in np.multiply(cumDcf, yearFractions)])
        swapRates = np.divide(dcf, sumProducts)
        dt = pd.DataFrame(list(zip(dates,swapRates)),columns =['Dates', f'{self.key}.SwapRates'])
        dt.set_index('Dates',inplace=True)
        return dt

    
    @staticmethod
    def Charts(curves, returnType, dates, tenor = '+3m',yearBasis = 'acton365f', rateConvention = 'linear'):
        if isinstance(curves, list) == False:
            curves =[curves]
        charts = []
        
        for curve in curves:
            if returnType.lower() == 'zero':
                charts.append(curve.ZeroRates(dates, yearBasis, rateConvention))
            elif returnType.lower() == 'fwd':
                charts.append(curve.FwdRates(dates, tenor, yearBasis, rateConvention))
            elif returnType.lower() == 'swaprates':
                charts.append(curve.SwapRates(dates, tenor, yearBasis, rateConvention))
            else:
                charts.append(curve.DiscountFactor(dates,True))
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
        instruments =[]
        for pillar in self.pillars:
            if pillar.quoteType == 'BondYield':
                instruments.append(Bond(pillar, self, market))
            elif pillar.quoteType == 'BondQuote':
                pass
            elif pillar.quoteType == 'DiscountFactor':
                instruments.append(DiscountFactor(pillar))
            elif pillar.quoteType == 'DepositRate':
                instruments.append(Deposit(pillar, self, market))
            elif pillar.quoteType == 'SwapRate':
                instruments.append(Swap(pillar, self, market))
            elif pillar.quoteType == 'BasisSwapRate':
                instruments.append(BasisSwap(pillar, self, market))
        return instruments



class YieldCurve(Curve):
    def __init__(self, key,valueDate, ccy, pillars, discount_curve=''):
        super(YieldCurve, self).__init__(key, ccy, valueDate, discount_curve)

        pillars.sort(key=lambda r:r.maturityDate)
        self.pillars = pillars
        
    def Build(self,market=None):
        instruments = self._addInstruments(market)

        for instrument in instruments:
            df = instrument.SolveDf()

            #Add the solved df to the curve
            array = np.array([(np.datetime64(instrument.maturity.strftime('%Y-%m-%d')),
                              time.mktime(instrument.maturity.timetuple()),
                              df)], dtype=self.points.dtype)
            self.points = np.append(self.points, array)

        self._built = True

    #Dv01 wrapper 
    def Dv01AtEachPillar(self,shockType, shockAmount= -0.0001, notional= 1e6):
        baseYc = self
        shockedYc = self.CreateShockedCurve(shockType, shockAmount)
        result = {}
        for pillar in baseYc.pillars:
            baseNpv = YieldCurveFactory.ToAssets(pillar,baseYc,notional).Valuation(baseYc,baseYc)
            shockedNpv = YieldCurveFactory.ToAssets(pillar,shockedYc,notional).Valuation(shockedYc,shockedYc)
            result[pillar.label] = (shockedNpv-baseNpv)/(shockAmount * 10000)
        return pd.DataFrame(list(result.items()),columns= ['Pillar','Amount'])

    #Zero Shock
    def ShiftZero(self,shockAmount, pillarToShock = -1):
        shiftedKey = self.key + '.ZeroShocked'
        shiftedPillars =[]
        maturityDateList = self.points['maturity']
        df = np.exp(self.points['discount_factor'])

        for idx, (maturityDate, df) in enumerate(zip(maturityDateList, df)):
            maturityDate = ScheduleDefinition.DateConvert(maturityDate)
            if maturityDate > self.valueDate and (pillarToShock == -1 or idx == pillarToShock):
                yearFraction = ScheduleDefinition.YearFraction(self.valueDate,maturityDate,'ActOn365f')
                dfShifted = RateConvention('Linear',yearFraction).RateToDf(shockAmount)[0] * df
                pillar = DiscountFactorRate(maturityDate,dfShifted)
                shiftedPillars.append(pillar)
        return YieldCurve(shiftedKey,self.valueDate,self.ccy,shiftedPillars,self.discountCurve)

    #PillarShock
    def CreateShockedCurve(self, shockType, shockAmount, pillarToShock =-1):
        if shockType.lower() == 'zero':
            shockedYc = self.ShiftZero(shockAmount,pillarToShock)
        else:
            shiftedKey = self.key + '.PillarShocked'
            shiftedPillars = copy.deepcopy(self.pillars)
            for idx, pillar in enumerate(shiftedPillars):
                if pillarToShock == -1 or idx == pillarToShock:
                    pillar.Shock(shockAmount)
            shockedYc = YieldCurve(shiftedKey,self.valueDate,self.ccy,
                          shiftedPillars,self.discountCurve)
        shockedYc.Build()

        return shockedYc

