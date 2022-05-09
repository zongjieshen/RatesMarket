from Market.Pillars import *
from Market.Instruments import *
from Market.Curve.YieldCurveFactory import *
from Market.Curve.Curve import *
from Market.Curve.PriceCurve import *
import pandas as pd


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
                               ScheduleDefinition.DateOffset(instrument.maturity),
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
                pillar = DiscountFactor(maturityDate,dfShifted)
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

    
    def ToFowardRateCurve(self, period = '3m', yearBasis = 'acton365f'):
        '''Converting a yield curve to fwd rate curve using Deposit Rate
        The discount factor results before and after should be the same'''
        fwdPillars =[]
        dateAdjuster = DateAdjuster('unadjusted')
        maturity = self.pillars[-1].maturityDate
        schedule = mkt.Schedule(self.valueDate,maturity,period,dateAdjuster)
        schedule._create_schedule()
        startDates = schedule.periods['accrual_start']
        endDates = schedule.periods['accrual_end']
        yfs = ScheduleDefinition.YearFractionList(startDates, endDates, yearBasis)
        df = self.DiscountFactor(endDates) / self.DiscountFactor(startDates)
        fwds = RateConvention('Linear',yfs).DfToRate(df)

        #Construct new fwd curve using deposit rate
        for startDate, endDate, fwd in zip(startDates, endDates, fwds):
            startDate = ScheduleDefinition.DateConvert(startDate)
            endDate = ScheduleDefinition.DateConvert(endDate)
            fwdPillars.append(DepositRate(startDate, endDate, self.ccy, 
                                          startDate.strftime('%Y-%m-%d'),
                                          'Linear',yearBasis, fwd, 'Zero', dateAdjuster))

        fwdRateCurve = YieldCurve(self.key,self.valueDate,self.ccy, fwdPillars)
        fwdRateCurve.Build()

        return fwdRateCurve

    #Shock curve on forward rates
    def ToFowardSpreadCurve(self, spreads, curveName, period = '3m', yearBasis = 'acton365f'):
        '''Adding a spread curve on yield curve on the fwd basis'''
        fwdCurve = self.ToFowardRateCurve(period,yearBasis)
        shiftedPillars = copy.deepcopy(fwdCurve.pillars)
        for pillar in shiftedPillars:
            if isinstance(spreads, PriceCurve):
                spread = spreads.Price(pillar.startDate,spreads.interpMethod)
                pillar.Shock(spread)
            elif isinstance(spreads, float):
                pillar.Shock(spreads)
            else:
                raise Exception (f'{spreads} type is not supported')

        fwdSpreadCurve = YieldCurve(curveName,self.valueDate,self.ccy, shiftedPillars)
        fwdSpreadCurve.Build()

        return fwdSpreadCurve




