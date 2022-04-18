from Market.Pillars import *
from Market.Instruments import *
import scipy.interpolate
import time

class Curve(object):
    def __init__(self, key, ccy, valueDate, interpType, discount_curve):
        self.key= key
        self.ccy = ccy
        self.valueDate = valueDate
        self._interpType = interpType
        self.discount_curve = discount_curve
        self._built = False

    def discount_factor(self, date):
        '''Returns the interpolated discount factor for an arbitrary date
        '''
        if type(date) is not datetime.datetime and type(date) is not np.datetime64:
            raise TypeError('Date must be a datetime.datetime or np.datetime64')
        if type(date) == datetime.datetime:
            date = time.mktime(date.timetuple())

        return np.exp(self.log_discount_factor(date))    
    
    def view(self, ret=False):
        '''Prints the discount factor curve
        Optionally return tuple of the maturities and discount factors
        '''
        if not self._built:
            self.Build()

        maturities = self.points['maturity']
        discount_factors = np.exp(self.points['discount_factor'])
        print(self.key)
        for i in range(len(self.points)):
            date = maturities[i].astype(object).strftime('%Y-%m-%d')
            print('{0} {1:.10f}'.format(date, discount_factors[i]))

        if ret:
            return maturities, discount_factors

    def _addInstruments(self,pillars):
        instruments =[]
        for pillar in pillars:
            if isinstance(pillar,BondYield):
                instruments.append(Bond(pillar,self))
            elif isinstance(pillar,BondYield):
                pass
            elif isinstance(pillar,DiscountFactorRate):
                instruments.append(DiscountFactor(pillar))
            elif isinstance(pillar,DepositRate):
                instruments.append(Deposit(pillar,self))
            elif isinstance(pillar,SwapRate):
                instruments.append(Swap(pillar,self))
        return instruments



class YieldCurve(Curve):
    def __init__(self, key,valueDate, ccy, interpType, pillars, discount_curve=False):
        super(YieldCurve, self).__init__(key, ccy, valueDate,interpType, discount_curve)

        pillars.sort(key=lambda r:r.maturityDate)
        self.pillars = pillars
        

    def Build(self):
        instruments = self._addInstruments(self.pillars)
        if not isinstance(self.discount_curve, Curve) and self.discount_curve is not False:
            raise TypeError('Discount curve must of of type Curve')
        self.points = np.array([(np.datetime64(self.valueDate.strftime('%Y-%m-%d')),
                                time.mktime(self.valueDate.timetuple()),
                                np.log(1))],
                              dtype=[('maturity', 'datetime64[D]'),
                                     ('timestamp', np.float64),
                                     ('discount_factor', np.float64)])

        self.points = self.points[0]
        for instrument in instruments:
            df = instrument.SolveDf()

            #Add the solved df to the curve
            array = np.array([(np.datetime64(instrument.maturity.strftime('%Y-%m-%d')),
                              time.mktime(instrument.maturity.timetuple()),
                              df)], dtype=self.points.dtype)
            self.points = np.append(self.points, array)

        self._built = True

    def Dv01AtEachPillar(self,shockType, shockAmount, notional):
        pass

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
        return YieldCurve(shiftedKey,self.valueDate,self.ccy,self._interpType,
                          shiftedPillars,self.discount_curve)


    def CreateShockedCurve(self, shockType, shockAmount, pillarToShock =-1):
        if shockType.lower() == 'zero':
            shockedYc = self.ShiftZero(shockAmount,pillarToShock)
        else:
            shiftedKey = self.key + '.PillarShocked'
            shiftedPillars = self.pillars
            for idx, pillar in enumerate(shiftedPillars):
                if pillarToShock == -1 or idx == pillarToShock:
                    pillar.Shock(shockAmount)
            shockedYc = YieldCurve(shiftedKey,self.valueDate,self.ccy,self._interpType,
                          shiftedPillars,self.discount_curve)
        shockedYc.Build()

        return shockedYc

