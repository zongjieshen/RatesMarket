from market.curves.curve_base import *

class InflationCurve(Curve):
    def __init__(self, key,valueDate, ccy, pillars, **kwargs):
        super(InflationCurve, self).__init__(key, ccy, valueDate, **kwargs)

        pillars.sort(key=lambda r:r.maturityDate)
        self.pillars = pillars
        self.indexFixingKey = kwargs.get('indexfixing','AUCPI')
        

    def Build(self,market=None):
        indexFixing = market[self.indexFixingKey]
        self.initialCPI = indexFixing.LastFixing()
        #Remove the instrument if the indexation period of maturity is already known
        for idx, instrument in enumerate(self._addinstruments(market)):
            if ScheduleDefinition.EndOfMonthAdj(instrument.maturity,instrument.indexLag) <= self.initialCPI.maturityDate:
                print(f"{instrument.key} maturity date {instrument.maturity.strftime('%Y-%m-%d')} {instrument.indexLag} (indexlag) is before the IndexFixing last known date {self.initialCPI.maturityDate.strftime('%Y-%m-%d')}")
                self.pillars.pop(idx)

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
        for instrument in self._addinstruments(market):
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

    def CPIRates(self, dates, yearBasis = 'acton365f', rateConvention = 'linear'):
        if isinstance(dates, (list, np.ndarray)) == False:
            dates =[dates]
        startDates = [self.valueDate] * len(dates)
        yearFractions = ScheduleDefinition.YearFractionList(startDates,dates,yearBasis)
        dfs = self.initialCPI.value / self.DiscountFactor(dates)
        values = RateConvention(rateConvention,yearFractions).DfToRate(dfs)
        dt = pd.DataFrame(list(zip(dates,values)),columns =['Dates', f'{self.key}.CPIRates'])
        dt.set_index('Dates',inplace=True)
        return dt
        
    def CPI(self, dates, returndf = False):
        return self.DiscountFactor(dates,returndf)
