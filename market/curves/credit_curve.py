from market.curves.curve_base import *

class CreditCurve(Curve):
    def __init__(self, key,valueDate, ccy, pillars, **kwargs):
        super(CreditCurve, self).__init__(key, ccy, valueDate, **kwargs)

        pillars.sort(key=lambda r:r.maturityDate)
        self.pillars = pillars
        self.points = np.array([(np.datetime64(self.valueDate.strftime('%Y-%m-%d')),
                        ScheduleDefinition.DateOffset(self.valueDate),
                        self.initialFactor)],
                        dtype=[('maturity', 'datetime64[D]'),
                                ('timestamp', np.float64),
                                ('survival_probability', np.float64)])

        self.points = self.points[0]

    def __len__(self):
        if hasattr(self, 'pillars'):
            return len(self.pillars)
        else:
            return 0

    def __repr__(self):
        return f"{self.key}; {self.ccy}; {self.valueDate.strftime('%Y-%m-%d')}; NumOfpillars:{len(self)} status:{self._built}"
        
    def Build(self,market=None):

        for instrument in self._addinstruments(market):
            df = instrument.SolveDf()
            #Add the solved df to the curve
            array = np.array([(np.datetime64(instrument.maturity.strftime('%Y-%m-%d')),
                               ScheduleDefinition.DateOffset(instrument.maturity),
                              df)], dtype=self.points.dtype)
            self.points = np.append(self.points, array)

        self._built = True

    def SurvivalProbability(self, dates,returnSp=False):
        if isinstance(dates,list) is True:
            dates = np.asarray(dates)
        if isinstance(dates,np.ndarray) is False:
            dates = np.asarray([dates])
        lastTenor = self.points['survival_probability'][-1]
        interpolator = scipy.interpolate.interp1d(self.points['timestamp'],
                                                  self.points['survival_probability'],
                                                  kind=self.interpMethod,
                                                  fill_value=lastTenor,
                                                  bounds_error=False) 
        values = interpolator(ScheduleDefinition.DateOffset(dates))

        if returnSp is True:
            dt = pd.DataFrame(list(zip(dates,values)),columns =['Dates', f'{self.key}.SurvivalProb'])
            dt.set_index('Dates',inplace=True)
            return dt
        else:
            return values

    def HazardRates(self, dates, yearBasis = 'acton365f', rateConvention = 'linear'):
        if isinstance(dates, list) == False:
            dates =[dates]
        startDates = [self.valueDate] * len(dates)
        yearFractions = ScheduleDefinition.YearFractionList(startDates,dates,yearBasis)
        sp = self.SurvivalProbability(dates)
        values = RateConvention(rateConvention,yearFractions).DfToRate(sp)
        dt = pd.DataFrame(list(zip(dates,values)),columns =['Dates', f'{self.key}.HazardRates'])
        dt.set_index('Dates',inplace=True)
        return dt
