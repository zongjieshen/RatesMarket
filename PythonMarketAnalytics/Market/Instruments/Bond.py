from Market.Dates import *
from Market.Pillars import *
from Market.Instruments import *
import scipy.interpolate
import scipy.optimize
import pandas as pd

class Bond(Instrument):
    def __init__(self, quote, curve, market = None, notional =1):
        super(Bond, self).__init__(quote)
        self.portfolio = 'curve'
        self.subType = quote.bondType
        self.coupon = quote.coupon
        self.notional = notional
        self.exDivDays = 7
        self.market = market
        #overwrite the bond start date with last coupon date
        prevCoupnDate = self._prevCouponDate(self.schedule.periods[0]['accrual_end'])
        self.schedule.periods[0]['accrual_start'] = np.datetime64(prevCoupnDate.strftime('%Y-%m-%d'))
        self.curve = curve

    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate,self.maturity,self.yearBasis)
        rateConvention = RateConvention(self.rateConvention,yearFraction)
        guess = np.log(rateConvention.RateToDf(self.rate))
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve, discountCurve = self._copy(guess)

        pv = self.Valuation(temp_curve,discountCurve)
        targetPv = self.DirtyPrice()
        return pv - targetPv

    def Valuation(self, projectCurve, discountCurve):
        return DiscountCashFlow(self.ccy,self.schedule,self.notional,self.coupon,
                              self.subType,self.yearBasis,projectCurve,discountCurve).pv()


    def DirtyPrice(self):
        nextCouponDate = ScheduleDefinition.DateConvert(self.schedule.periods[0]['accrual_end'])
        prevCoupnDate = ScheduleDefinition.DateConvert(self.schedule.periods[0]['accrual_start'])
        i = self.rate/self.schedule.couponPerAnnum
        f= (nextCouponDate - self.startDate).days
        d =(nextCouponDate - prevCoupnDate).days
        g = self.coupon/self.schedule.couponPerAnnum

        if nextCouponDate == self.maturity:
            price = (1+g)/(1+f/365 * i) * 100
        else:
            v = 1 / (1+i)
            n = len(self.schedule.periods) - 1
            vPowN = pow(v, n)
            aSubN = (1 - vPowN) / i
            c=0 if self.isExDiv(nextCouponDate,self.startDate,self.exDivDays) else 1
            price = pow(v, f/d) * (g * (c+aSubN) + vPowN) * 100
        return price / 100 * self.notional

    def _prevCouponDate(self,thisCouponDate):
        return ScheduleDefinition.DateConvert(thisCouponDate) - ScheduleDefinition._parseDate(self.schedule.period)

    def isExDiv(self,nextCouponDate, startDate,exDivDays):
        exDiv = pd.offsets.DateOffset(exDivDays)
        return nextCouponDate + exDiv <= startDate


#CIB Bonds for BEI Curve
class IndexedBond(Bond):
    def __init__(self, quote, curve, market, notional =1):
        super(IndexedBond, self).__init__(quote, curve, market, notional =1)
        self.indexLag = -6
        self.notionalIndexation = quote.notionalIndexation
        self.indexFixingKey = quote.indexFixingKey
        

    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate,self.maturity,self.yearBasis)
        rateConvention = RateConvention(self.rateConvention,yearFraction)
        guess = np.log(self.curve.initialCPI.value / rateConvention.RateToDf(self.rate))
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]
        #Adjust maturity date to CPI Publication date
        maturity= ScheduleDefinition.EndOfMonthAdj(self.maturity,self.indexLag)
        temp_curve = copy.deepcopy(self.curve)


        temp_curve.points = np.append(self.curve.points,
                               np.array([(np.datetime64(maturity.strftime('%Y-%m-%d')),
                                          ScheduleDefinition.DateOffset(maturity),
                                          guess)],
                                        dtype=self.curve.points.dtype))

        discountCurve = self.market.GetMarketItem(self.curve.discountCurve)

        pv = self.Valuation(temp_curve,discountCurve)
        targetPv = self.DirtyPrice()
        return pv - targetPv

    def Valuation(self, projectCurve, discountCurve):
        return CPIIndexationFlow(self.ccy,self.schedule,self.notional,self.coupon,
                              self.subType,self.yearBasis,projectCurve,discountCurve, 
                              self.notionalIndexation, self.indexLag).pv()
    
    #p-value
    def _pValue(valueDate,indexFixing, indexLag, yearBasis):
        indexationPeriodEnd = ScheduleDefinition.EndOfMonthAdj(valueDate,indexLag)
        indexationPeriodStart = ScheduleDefinition.EndOfMonthAdj(indexationPeriodEnd,indexLag)
        cpiEnd = indexFixing.Fixing(indexationPeriodEnd)
        cpiStart = indexFixing.Fixing(indexationPeriodStart)
        yf = ScheduleDefinition.YearFraction(indexationPeriodStart,indexationPeriodEnd,yearBasis)
        if cpiEnd == 0 or cpiStart == 0:
            raise ZeroDivisionError
        return yf * (cpiEnd / cpiStart -1) * 100

    #ktFactor
    def _ktFactor(pValue, notionalIndexation):
        return notionalIndexation * (1 + pValue / 100)

    def DirtyPrice(self):
        
        indexFixing = self.market.GetMarketItem(self.indexFixingKey)

        nextCouponDate = ScheduleDefinition.DateConvert(self.schedule.periods[0]['accrual_end'])
        prevCoupnDate = ScheduleDefinition.DateConvert(self.schedule.periods[0]['accrual_start'])
        i = self.rate/self.schedule.couponPerAnnum
        f= (nextCouponDate - self.startDate).days
        d =(nextCouponDate - prevCoupnDate).days
        g = self.coupon/self.schedule.couponPerAnnum

        v = 1 / (1+i)
        n = len(self.schedule.periods) - 1
        vPowN = pow(v, n)
        aSubN = (1 - vPowN) / i
        c=0 if self.isExDiv(nextCouponDate,self.startDate,self.exDivDays) else 1
        p = IndexedBond._pValue(nextCouponDate,indexFixing,self.indexLag, self.yearBasis)
        ktFactor = IndexedBond._ktFactor(p, self.notionalIndexation)

        price = pow(v, f/d) * (g * (c+aSubN) + vPowN) * 100 * ktFactor * pow(1 + p / 100, -f / d)
        return price / 100 * self.notional
