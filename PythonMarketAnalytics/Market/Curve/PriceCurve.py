from Market.Curve import *

class PriceCurve(Curve):
    def __init__(self, key,valueDate, ccy, pillars, **kwargs):
        super(PriceCurve, self).__init__(key, ccy, valueDate, **kwargs)

        pillars.sort(key=lambda r:r.maturityDate)
        self.pillars = pillars
        
    def Build(self,market=None):

        for pillar in self.pillars:
            #Re-construct points
            if hasattr(self,'points'):
                array = np.array([(np.datetime64(pillar.maturityDate.strftime('%Y-%m-%d')),
                                  ScheduleDefinition.DateOffset(pillar.maturityDate),
                                  pillar.rate)], dtype=self.points.dtype)
                self.points = np.append(self.points, array)
            else:
                self.points = np.array([(np.datetime64(pillar.maturityDate.strftime('%Y-%m-%d')),
                                ScheduleDefinition.DateOffset(pillar.maturityDate),
                                pillar.rate)],
                              dtype=[('maturity', 'datetime64[D]'),
                                     ('timestamp', np.float64),
                                     ('price', np.float64)])

        self._built = True

    
    def Price(self, dates, InterpMethod):
        if self.points.size == 1:
            return self.points[0]['price']
        else:
            interpolator = scipy.interpolate.interp1d(self.points['timestamp'],
                                                self.points['price'],
                                                kind=InterpMethod,
                                                fill_value='extrapolate') 
            return interpolator(dates.astype('<M8[s]'))

