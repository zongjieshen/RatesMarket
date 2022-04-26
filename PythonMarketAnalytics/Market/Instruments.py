from Market.Dates import *
from Market.Pillars import *
import scipy.interpolate
import scipy.optimize
import pandas as pd
import time
import copy
import abc

class Instrument(object):
    def __init__(self, quote,periodAdjustment = 'modified following',paymentAdjustment = 'modified following'):
        self.key = quote.label
        self.ccy = quote.ccy
        self.yearBasis = quote.yearBasis
        self.rateConvention = quote.rateConvention
        self.startDate = quote.startDate
        self.maturity = quote.maturityDate
        self.rate = quote.rate
        self.calendar = quote.calendar

        self.schedule = Schedule(self.startDate,self.maturity,
                                 quote.paymentFrequency,periodAdjustment,paymentAdjustment,self.calendar)
        self.schedule._create_schedule()
        
    @abc.abstractmethod
    def SolveDf():
        return NotImplementedError
    @abc.abstractmethod
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

        if self.market is not None and self.curve.discountCurve != '' and self.market.GetMarketItem(self.curve.discountCurve)._built == True:
            discountCurve = self.market.GetMarketItem(self.curve.discountCurve)
        else:
            discountCurve = temp_curve

        return temp_curve, discountCurve

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
                                          time.mktime(maturity.timetuple()),
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



class Swap(Instrument):
    def __init__(self, quote, curve, market = None, notional =1):
        super(Swap, self).__init__(quote)
        self.portfolio = 'curve'
        self.subType = 'vanilla'
        self.notional = notional
        self.paymentDelay = quote.paymentDelay
        #TODO add paymentDelay to schedule
        self.curve = curve
        self.market = market
        self.compoundFrequency = quote.compoundFrequency

    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate,self.maturity,self.yearBasis)
        rateConvention = RateConvention(self.rateConvention,yearFraction)
        guess = np.log(rateConvention.RateToDf(self.rate))
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve, discountCurve = self._copy(guess)
        return self.Valuation(temp_curve, discountCurve)

    def Valuation(self, projectCurve, discountCurve):
        fixedLegPv = DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'fixed',self.yearBasis,projectCurve,discountCurve).pv()

        indexType = 'ois' if self.compoundFrequency.lower() == 'daily' else 'floating'
        floatingLegPv = DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              indexType,self.yearBasis,projectCurve,discountCurve).pv()

        return fixedLegPv - floatingLegPv

class BasisSwap(Swap):
    def __init__(self, *args, **kwargs):
        super(BasisSwap, self).__init__(*args, **kwargs)
        self.subType = 'basis'

    def SolveDf(self):
        discountCurve = self.market.GetMarketItem(self.curve.discountCurve)
        guess = np.log(discountCurve.DiscountFactor(self.maturity))
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve, discountCurve = self._copy(guess)
        return self.Valuation(temp_curve, discountCurve)

    def Valuation(self, projectCurve, discountCurve):
        basisLeg = DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'basis',self.yearBasis,projectCurve,discountCurve).pv()

        indexType = 'ois' if self.compoundFrequency.lower() == 'daily' else 'floating'
        floatingLegPv = DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              indexType,self.yearBasis,discountCurve,discountCurve).pv()

        return basisLeg - floatingLegPv

#Leg modelling
class DiscountCashFlow():
    def __init__(self, ccy, schedule, notional, rate, indexType, yearBasis, projectCurve, discountCurve):
        self.ccy = ccy
        self.schedule = schedule
        self.notional = notional
        self.rate = rate
        self.indexType = indexType
        self.yearBasis = yearBasis
        self.projectCurve = projectCurve
        self.discount_curve = discountCurve

    def pv(self):
        def _getPeriods():
            periodStart = self.schedule.periods['accrual_start']
            periodEnd = self.schedule.periods['accrual_end']
            accural_periods = ScheduleDefinition.YearFractionList(periodStart, periodEnd, self.yearBasis)
            return periodStart, periodEnd, accural_periods

        if self.indexType.lower() == 'fixed':
            periodStart, periodEnd, accural_periods = _getPeriods()

            cashflows = self.rate * accural_periods * self.notional            
        elif self.indexType.lower() == 'floating':
            periodStart, periodEnd, accural_periods = _getPeriods()

            dfStart = self.projectCurve.DiscountFactor(periodStart)
            dfEnd = self.projectCurve.DiscountFactor(periodEnd)
            fwd = (dfStart / dfEnd - 1)
            cashflows = fwd * self.notional
        elif self.indexType.lower() == 'ois':
            cashflows =[]
            for period in self.schedule.periods:
                fwd = self.__ois_fwd_rate(self.projectCurve, period)
                cashflows.append(fwd * self.notional)
        elif self.indexType.lower() == 'basis':
            periodStart, periodEnd, accural_periods = _getPeriods()
            dfStart = self.projectCurve.DiscountFactor(periodStart)
            dfEnd = self.projectCurve.DiscountFactor(periodEnd)
            fwd = (dfStart / dfEnd - 1) + self.rate * accural_periods
            cashflows = fwd * self.notional
        else:
            return NotImplementedError

        cashflows[-1] += self.notional
        self.schedule.periods['cashflow'] = cashflows
        payment_dates = self.schedule.periods['payment_date']
        self.schedule.periods['PV'] = cashflows * self.discount_curve.DiscountFactor(payment_dates)
        return self.schedule.periods['PV'].sum()



    def __ois_fwd_rate(self, projectCurve, period):
        '''Private method for calculating the compounded forward rate for an OIS
        swap.

        The compounded forward rate is calculated as the

                                     DF[i]
                                Π [ ------- ] - 1
                                i   DF[i+1]

        Note that it achieves very speedily by calculating each forward
        rate (+ 1) for the entire date array, and then calculating the product
        of the array. Additionally, there are 3 entries for every Friday, as
        each friday should compound 3 times (no new rates on weekends).
        '''
        start_date = period['accrual_start'].astype('<M8[s]')
        end_date = period['accrual_end'].astype('<M8[s]')
        one_day = np.timedelta64(1, 'D')
        start_day = start_date.astype(object).weekday()
        rate = 1
        first_dates = np.arange(start_date, end_date, one_day)
        # replace all Saturdays and Sundays with Fridays
        fridays = first_dates[4 - start_day::7]
        first_dates[5 - start_day::7] = fridays[:len(first_dates[5 - start_day::7])]
        first_dates[6 - start_day::7] = fridays[:len(first_dates[6 - start_day::7])]
        second_dates = first_dates + one_day
        initial_dfs = projectCurve.DiscountFactor(first_dates)
        end_dfs = projectCurve.DiscountFactor(second_dates)
        rates = (initial_dfs / end_dfs)
        rate = rates.prod() - 1
        return rate


class CPIIndexationFlow(DiscountCashFlow):
    def __init__(self, ccy, schedule, notional, rate, indexType, yearBasis, projectCurve, discountCurve,notionalIndexFactor, indexLag):
        super(CPIIndexationFlow, self).__init__(ccy, schedule, notional, rate, indexType, yearBasis, projectCurve, discountCurve)
        self.notionalIndexFactor = notionalIndexFactor
        self.indexLag = indexLag
        prevNotional = notional

    def pv(self):
        periodStart = self.schedule.periods['accrual_start']
        periodEnd = self.schedule.periods['accrual_end']
        accural_periods = ScheduleDefinition.YearFractionList(periodStart, periodEnd, self.yearBasis)

        prevKtFactor = self.notionalIndexFactor
        cashflows =[]
        for period, accYf in zip(periodEnd,accural_periods):
            indexationPeriodEnd = ScheduleDefinition.EndOfMonthAdj(period,self.indexLag)
            indexationPeriodStart = ScheduleDefinition.EndOfMonthAdj(indexationPeriodEnd,self.indexLag)
            yf = ScheduleDefinition.YearFraction(indexationPeriodStart, indexationPeriodEnd, self.yearBasis)
            cpiStart = self.projectCurve.DiscountFactor(indexationPeriodStart)[0]
            cpiEnd = self.projectCurve.DiscountFactor(indexationPeriodEnd)[0]
            pValue = 1 + yf * (cpiEnd / cpiStart - 1)
            ktFactor = prevKtFactor * pValue

            notional = self.notional * ktFactor
            coupon = notional * self.rate * accYf 
            if period == periodEnd[-1]:
                cashflows.append(notional + coupon)
            else:
                cashflows.append(coupon)

            prevKtFactor = ktFactor

        self.schedule.periods['cashflow'] = cashflows
        payment_dates = self.schedule.periods['payment_date']
        self.schedule.periods['PV'] = cashflows * self.discount_curve.DiscountFactor(payment_dates)
        return self.schedule.periods['PV'].sum()