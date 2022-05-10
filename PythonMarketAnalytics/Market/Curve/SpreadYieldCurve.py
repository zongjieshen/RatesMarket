from Market.Pillars import *
from Market.Curve.YieldCurve import *
from Market.Curve.Curve import *
from Market.Curve.PriceCurve import *


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


    def Build(self,market):
        yc = market.GetMarketItem(self.discountCurve)
        spreads = market.GetMarketItem(self.spreadCurve)

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




