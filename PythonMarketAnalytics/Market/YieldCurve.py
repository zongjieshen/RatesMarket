from Market.Pillars import *
from Market.Instruments import *
from Market.YieldCurveFactory import *
from Market.Curve import *
import Market as mkt
import pandas as pd
import scipy.interpolate
import time
import copy
import abc


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

