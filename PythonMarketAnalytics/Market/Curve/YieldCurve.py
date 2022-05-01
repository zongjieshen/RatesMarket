from Market.Pillars import *
from Market.Instruments import *
from Market.Curve.YieldCurveFactory import *
from Market.Curve.Curve import *
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

        for instrument in self._addInstruments(market):
            df = instrument.SolveDf()

            #Add the solved df to the curve
            array = np.array([(np.datetime64(instrument.maturity.strftime('%Y-%m-%d')),
                              time.mktime(instrument.maturity.timetuple()),
                              df)], dtype=self.points.dtype)
            self.points = np.append(self.points, array)

        self._built = True

    #Dv01 wrapper 
    def Dv01AtEachPillar(self,shockType, market = None, shockAmount= -0.0001, notional= 1e6):
        baseYc = self
        shockedYc = self.CreateShockedCurve(shockType, shockAmount, market)
        result = {}
        for pillar in baseYc.pillars:
            baseNpv = YieldCurveFactory.ToAssets(pillar,baseYc,notional).Valuation(baseYc,baseYc)
            shockedNpv = YieldCurveFactory.ToAssets(pillar,shockedYc,notional).Valuation(shockedYc,shockedYc)
            result[pillar.label] = (shockedNpv-baseNpv)/(shockAmount * 10000)
        return pd.DataFrame(list(result.items()),columns= ['Pillar','Delta'])

    def Dv01MatrixAtEachPillar(self, shockType, market = None, shockAmount= -0.0001, notional= 1e6):
        baseNpv = {}
        result = {}
        discountCurve = self if self.key == self.discountCurve else market.GetMarketItem(self.discountCurve)
        for pillar in self.pillars:
            shockedCurve = self.CreateShockedCurve(shockType, shockAmount, market)
            perRow = []
            for instrument in self._addInstruments(market):
                baseNpv = instrument.Valuation(self, discountCurve)
                shockedNpv = instrument.Valuation(shockedCurve, shockedCurve)
                perRow.append((shockedNpv-baseNpv)/(shockAmount * 10000))
            result[pillar.label] = perRow
        return pd.DataFrame(result)


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
    def ShiftPillar(self, shockAmount, pillarToShock = -1, discountCurve = None):
        dC = self.key if discountCurve is None else discountCurve
        shiftedKey = self.key + '.PillarShocked'
        shiftedPillars = copy.deepcopy(self.pillars)
        for idx, pillar in enumerate(shiftedPillars):
            if pillarToShock == -1 or idx == pillarToShock:
                pillar.Shock(shockAmount)
        return YieldCurve(shiftedKey,self.valueDate,self.ccy, shiftedPillars,dC)


    #Shock Curve wrapper
    def CreateShockedCurve(self, shockType, shockAmount, market = None, pillarToShock =-1):
        if shockType.lower() == 'zero':
            shockedYc = self.ShiftZero(shockAmount,pillarToShock)
        elif shockType.lower() == 'pillar' and self.key == self.discountCurve:
            shockedYc = self.ShiftPillar(shockAmount,pillarToShock)
        elif shockType.lower() == 'pillar' and self.key != self.discountCurve:
            discountCurve = market.GetMarketItem(self.discountCurve)
            shockedDc = discountCurve.ShiftPillar(shockAmount,pillarToShock)
            shockedDc.Build()
            market.AddorUpdateItem(shockedDc)
            shockedYc = self.ShiftPillar(shockAmount,pillarToShock,shockedDc.key)
        elif shockType.lower() == 'basis' and self.key != self.discountCurve:
            shockedYc = self.ShiftPillar(shockAmount,pillarToShock)
        else:
            raise Exception(f'{shockType} is not supported')

        shockedYc.Build(market)
        return shockedYc

