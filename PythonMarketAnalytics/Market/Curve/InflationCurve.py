import Market as mkt
from Market.Curve.Curve import *
import pandas as pd
import scipy.interpolate
import time


class InflationCurve(Curve):
    def __init__(self, key,valueDate, ccy, pillars, discount_curve, indexFixingKey):
        super(InflationCurve, self).__init__(key, ccy, valueDate, discount_curve)

        pillars.sort(key=lambda r:r.maturityDate)
        self.pillars = pillars
        self.indexFixingKey = indexFixingKey
        

    def Build(self,market=None):
        indexFixing = market.GetMarketItem(self.indexFixingKey)
        self.initialCPI = indexFixing.LastFixing()
        #Remove the instrument if the indexation period of maturity is already known
        for idx, instrument in enumerate(self._addInstruments(market)):
            if ScheduleDefinition.EndOfMonthAdj(instrument.maturity,instrument.indexLag) <= self.initialCPI.maturityDate:
                print(f'{instrument.key} maturity date {instrument.maturity} + indexlag {instrument.indexLag} is before the IndexFixing last known date {self.initialCPI.maturityDate}')
                self.pillars.pop(idx)

        del self.points

        fixings = []
        #Add past index fixings to the curve
        for pillar in indexFixing.pillars:
            fixings.append((np.datetime64(pillar.maturityDate.strftime('%Y-%m-%d')),
                            ScheduleDefinition.DateOffset(pillar.maturityDate),
                            np.log(pillar.value)
                            ))
        self.points = np.array(fixings,dtype=[('maturity', 'datetime64[D]'),
                                                ('timestamp', np.float64),
                                                ('discount_factor', np.float64)])

        #self.points = self.points[-1]
        for instrument in self._addInstruments(market):
            df = instrument.SolveDf()

            #Add the solved df to the curve
            array = np.array([(np.datetime64(instrument.maturity.strftime('%Y-%m-%d')),
                              ScheduleDefinition.DateOffset(instrument.maturity),
                              df)], dtype=self.points.dtype)
            self.points = np.append(self.points, array)

        self._built = True

    def GetFixingOrInterpolate(self, indexFixing, date):
        if date <= indexFixing.pillars[-1].Date:
            return indexFixing.Fixing(date)
        else:
            return self.DiscountFactor(date)

    def ZeroRates(self, dates, yearBasis = 'acton365f', rateConvention = 'linear'):
        if isinstance(dates, list) == False:
            dates =[dates]
        startDates = [self.valueDate] * len(dates)
        yearFractions = ScheduleDefinition.YearFractionList(startDates,dates,yearBasis)
        dfs = self.initialCPI.value / self.DiscountFactor(dates)
        values = RateConvention(rateConvention,yearFractions).DfToRate(dfs)
        dt = pd.DataFrame(list(zip(dates,values)),columns =['Dates', f'{self.key}.ZeroRates'])
        dt.set_index('Dates',inplace=True)
        return dt
        
    def CPI(self, dates):
        return self.DiscountFactor(dates)
