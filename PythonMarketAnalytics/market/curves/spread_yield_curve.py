from market.curves.curve_base import *
from market.curves.yield_curve import *
from market.curves.price_curve import *

class SpreadYieldCurve(YieldCurve):
    def __init__(self, key, ccy,valueDate, **kwargs):
        #Initialise the base Curve class to get initial df, but don't initialise YieldCurve as we dont have pillars yet
        super(YieldCurve, self).__init__(key, ccy, valueDate, **kwargs)
        self.key= key
        self.valueDate = valueDate
        self.ccy = ccy
        #Need to guard the below
        self.periods = kwargs.get('periods',None)
        self.yearBasis = kwargs.get('yearbasis',None)
        self.spreadCurve = kwargs.get('spreadcurve',None)
        self.points = np.array([(np.datetime64(self.valueDate.strftime('%Y-%m-%d')),
                        ScheduleDefinition.DateOffset(self.valueDate),
                        np.log(self.initialFactor))],
                        dtype=[('maturity', 'datetime64[D]'),
                                ('timestamp', np.float64),
                                ('discount_factor', np.float64)])

        self.points = self.points[0]


    def Build(self,market):
        yc = market[self.discountCurve.lower()]
        spreads = market[self.spreadCurve.lower()]

        fwdCurve = yc.ToFowardRateCurve(self.periods, self.yearBasis)
        self.pillars = copy.deepcopy(fwdCurve.pillars)
        for pillar in self.pillars:
            if isinstance(spreads, PriceCurve):
                spread = spreads.Price(pillar.startDate,spreads.interpMethod)
                pillar.Shock(spread)
            elif isinstance(spreads, float):
                pillar.Shock(spreads)
            else:
                raise Exception (f'{spreads} type is not supported')

        super(SpreadYieldCurve, self).Build()

        self._built = True




