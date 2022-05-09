from Market.Pillars import *
from Market.Curve.YieldCurve import *
from Market.Curve.Curve import *
from Market.Curve.PriceCurve import *


class SpreadYieldCurve(YieldCurve):
    def __init__(self, key,valueDate, ccy,periods, yearBasis, discountCurve: str, priceCurve: str):
        #Initialise the base Curve class to get initial df, but don't initialise YieldCurve as we dont have pillars yet
        super(YieldCurve, self).__init__(key, ccy, valueDate, discountCurve)
        self.key= key
        self.valueDate = valueDate
        self.ccy = ccy
        self.periods = periods
        self.yearBasis = yearBasis
        self.discountCurve  = discountCurve
        self.spreadCurve = priceCurve


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




