from Market.Dates import *
from Market.Pillars import *
import scipy.interpolate
import scipy.optimize
import sys
import time
import copy

class Instrument(object):
    def __init__(self, quote):
        self.key = quote.label
        self.ccy = quote.ccy
        self.yearBasis = quote.yearBasis
        self.rateConvention = quote.rateConvention
        self.startDate = quote.startDate
        self.maturity = quote.maturityDate
        self.rate = quote.rate
        

    def SolveDf():
        return NotImplementedError

    def Valuation():
        return NotImplementedError

    def _copy(self,guess):
        temp_curve = None
        temp_curve = copy.deepcopy(self.curve)
        temp_curve.points = np.append(self.curve.points,
                               np.array([(np.datetime64(self.maturity.strftime('%Y-%m-%d')),
                                          time.mktime(self.maturity.timetuple()),
                                          guess)],
                                        dtype=self.curve.points.dtype))
        return temp_curve

#Discount Factor
class DiscountFactor(Instrument):
    def __init__(self, quote):
        self.maturity = quote.maturityDate
        self.df = quote.value

    def SolveDf(self):
        return np.log(self.df)
#Deposit
class Deposit(Instrument):
    def __init__(self, quote, curve, notional =1):
        super(Deposit, self).__init__(quote)
        self.curve = curve
        self.notional = notional
        self.schedule = Schedule(self.startDate,self.maturity,
                                 quote.paymentFrequency,'modified following','modified following')

    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate,self.maturity,self.yearBasis)
        df = RateConvention(self.rateConvention,yearFraction).RateToDf(self.rate)
        lastTenor = ScheduleDefinition.DateConvert(self.curve.points['maturity'])
        if isinstance(lastTenor, datetime.datetime) and self.curve.points.size == 1:
            yfSettle = ScheduleDefinition.YearFraction(lastTenor,self.startDate,self.yearBasis)
            factor = pow(df,yfSettle / yearFraction)
            return np.log(df * factor)
        else:
            interpolator = scipy.interpolate.interp1d(self.curve.points['timestamp'],
                                                  self.curve.points['discount_factor'],
                                                  kind='linear',
                                                  fill_value='extrapolate')
            factor = np.exp(interpolator(time.mktime(self.startDate.timetuple())))
            return np.log(df * factor)

    def Valuation(self,projectCurve, discountCurve):
        return DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'fixed',self.yearBasis,projectCurve,discountCurve).pv()

class Bond(Instrument):
    def __init__(self, quote, curve, notional =1):
        super(Bond, self).__init__(quote)
        self.portfolio = 'curve'
        self.subType = 'Fixed'
        self.coupon = quote.coupon
        self.notional = notional
        self.exDivDays = 7
        self.schedule = Schedule(self.startDate,self.maturity,
                                 quote.paymentFrequency,'modified following','modified following')
        self.curve = curve
        #overwrite the bond start date with last coupon date
        prevCoupnDate = self._prevCouponDate(self.schedule.periods[0]['accrual_end'])
        self.schedule.periods[0]['accrual_start'] = np.datetime64(prevCoupnDate.strftime('%Y-%m-%d'))

    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate,self.maturity,self.yearBasis)
        rateConvention = RateConvention(self.rateConvention,yearFraction)
        guess = np.log(rateConvention.RateToDf(self.rate))
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve = self._copy(guess)
        discount_curve = self.curve.discountCurve if self.curve.discountCurve is not False else temp_curve

        pv = self.Valuation(temp_curve,discount_curve)
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
        return ScheduleDefinition.DateConvert(thisCouponDate) - self.schedule.period_delta

    def isExDiv(self,nextCouponDate, startDate,exDivDays):
        exDiv = dateutil.relativedelta.relativedelta(days=exDivDays)
        return nextCouponDate + exDiv <= startDate


class Swap(Instrument):
    def __init__(self, quote, curve, notional =1):
        super(Swap, self).__init__(quote)
        self.portfolio = 'curve'
        self.subType = 'vanilla'
        self.notional = notional
        self.paymentDelay = quote.paymentDelay
        self.schedule = Schedule(self.startDate,self.maturity,
                                 quote.paymentFrequency,'modified following','modified following')
        self.curve = curve

    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate,self.maturity,self.yearBasis)
        rateConvention = RateConvention(self.rateConvention,yearFraction)
        guess = np.log(rateConvention.RateToDf(self.rate))
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve = self._copy(guess)
        discount_curve = self.curve.discountCurve if self.curve.discountCurve is not False else temp_curve

        return self.Valuation(temp_curve, discount_curve)

    def Valuation(self, projectCurve, discountCurve):
        fixedLegPv = DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'fixed',self.yearBasis,projectCurve,discountCurve).pv()

        floatingLegPv = DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'floating',self.yearBasis,projectCurve,discountCurve).pv()

        return fixedLegPv - floatingLegPv

#Leg modelling
class DiscountCashFlow():
    def __init__(self, ccy, schedule, notional, fixedRate, indexKey, yearBasis, projectCurve, discountCurve):
        self.ccy = ccy
        self.schedule = schedule
        self.notional = notional
        self.fixedRate = fixedRate
        self.indexKey = indexKey
        self.yearBasis = yearBasis
        self.projectCurve = projectCurve
        self.discount_curve = discountCurve

    def pv(self):
        def _getPeriods():
            periodStart = self.schedule.periods['accrual_start']
            periodEnd = self.schedule.periods['accrual_end']
            accural_periods = ScheduleDefinition.YearFractionList(periodStart, periodEnd, self.yearBasis)
            return periodStart, periodEnd, accural_periods

        if self.indexKey.lower() == 'fixed':
            periodStart, periodEnd, accural_periods = _getPeriods()

            cashflows = self.fixedRate * accural_periods * self.notional
            cashflows[-1] += self.notional
            self.schedule.periods['cashflow'] = cashflows

            payment_dates = self.schedule.periods['payment_date']
            self.schedule.periods['PV'] = cashflows * self.discount_curve.DiscountFactor(payment_dates)
            return self.schedule.periods['PV'].sum()
        elif self.indexKey.lower() == 'floating':
            periodStart, periodEnd, accural_periods = _getPeriods()

            dfStart = self.projectCurve.DiscountFactor(periodStart)
            dfEnd = self.projectCurve.DiscountFactor(periodEnd)
            fwd = (dfStart / dfEnd - 1) / accural_periods

            cashflows = fwd * accural_periods * self.notional
            cashflows[-1] += self.notional
            self.schedule.periods['cashflow'] = cashflows

            payment_dates = self.schedule.periods['payment_date']
            self.schedule.periods['PV'] = cashflows * self.discount_curve.DiscountFactor(payment_dates)
            return self.schedule.periods['PV'].sum()
        else:
            return NotImplementedError





        

