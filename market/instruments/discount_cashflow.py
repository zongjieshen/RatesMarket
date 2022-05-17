from market.instruments import *
import numpy as np

#Leg modelling
class DiscountCashFlow():
    def __init__(self, ccy: str, schedule: dates.Schedule, notional: float, rate: float, indexType: str, yearBasis: str, projectCurve, discountCurve):
        self.ccy = ccy
        self.schedule = schedule
        self.notional = notional
        self.rate = rate
        self.indexType = indexType
        self.yearBasis = yearBasis
        self.projectCurve = projectCurve
        self.discount_curve = discountCurve

    def _getPeriods(self):
        periodStart = self.schedule.periods['accrual_start']
        periodEnd = self.schedule.periods['accrual_end']
        accural_periods = ScheduleDefinition.YearFractionList(periodStart, periodEnd, self.yearBasis)
        return periodStart, periodEnd, accural_periods
    def _discount(self, cashflows):
        self.schedule.periods['cashflow'] = cashflows
        payment_dates = self.schedule.periods['payment_date']
        self.schedule.periods['PV'] = cashflows * self.discount_curve.DiscountFactor(payment_dates)
        return self.schedule.periods['PV'].sum()

    def pv(self):
        periodStart, periodEnd, accural_periods = self._getPeriods()
        if self.indexType.lower() == 'fixed':
            cashflows = self.rate * accural_periods * self.notional            
        elif self.indexType.lower() == 'floating':
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
            dfStart = self.projectCurve.DiscountFactor(periodStart)
            dfEnd = self.projectCurve.DiscountFactor(periodEnd)
            fwd = (dfStart / dfEnd - 1) + self.rate * accural_periods
            cashflows = fwd * self.notional
        else:
            return NotImplementedError

        cashflows[-1] += self.notional

        return self._discount(cashflows)



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

    def pv(self):
        periodStart, periodEnd, accural_periods = self._getPeriods()

        indexPeriodEnd = ScheduleDefinition.EndOfMonthAdj(periodEnd,self.indexLag)
        indexPeriodStart = ScheduleDefinition.EndOfMonthAdj(indexPeriodEnd,self.indexLag)
        yf = ScheduleDefinition.YearFractionList(indexPeriodStart, indexPeriodEnd, self.yearBasis)
        cpiS = self.projectCurve.DiscountFactor(indexPeriodStart)
        cpiE = self.projectCurve.DiscountFactor(indexPeriodEnd)
        p = 1 + yf * (cpiE / cpiS - 1)
        #KtFactor = previous KtFactor * pvalue, hence, cumulative product below
        pCum = np.cumprod(p)
        kt = self.notionalIndexFactor * pCum
        notional = self.notional * kt
        cashflows = notional * self.rate * accural_periods
        cashflows[-1] += notional[-1]

        return self._discount(cashflows)


class CDSFlow(DiscountCashFlow):
    '''private class to calculate the premium and default leg of a CDS
        premiumLeg = Notional * CouponRate * yearFrac * SurvivalProbability
        defaultLeg = - Notional * (1 - RecoveryRate) * Incremental DefaultProbability
        accruedInterest = Notional * YearFrac * CouponRate
        NPV = premiumLeg + defaultLeg - accuredInterest'''

    def __init__(self, ccy, schedule, notional, rate, indexType, yearBasis, projectCurve, 
                discountCurve, recoveryRate, couponRate):
        super(CDSFlow, self).__init__(ccy, schedule, notional, rate, indexType, yearBasis, projectCurve, discountCurve)
        self.recoveryRate = recoveryRate
        self.couponRate = couponRate
        self.prevSurvivalProb = 1

    def pv(self):
        periodStart, periodEnd, accural_periods = self._getPeriods()
        def _prevCouponDate(period,thisCouponDate):
            return ScheduleDefinition.DateConvert(thisCouponDate) - ScheduleDefinition._parseDate(period)
        
        if self.indexType.lower() == 'premium':
            survivalProb = self.projectCurve.SurvivalProbability(periodEnd)
            cashflows = self.couponRate * accural_periods * self.notional * survivalProb
            return self._discount(cashflows)
        elif self.indexType.lower() == 'default':
            survivalProbEnd = self.projectCurve.SurvivalProbability(periodEnd)
            #Compute the default probability per period
            survivalProbStart = np.insert(survivalProbEnd,0, 1)[:-1]
            defaultProb = survivalProbStart - survivalProbEnd
            cashflows = - self.notional * (1 - self.recoveryRate) * defaultProb
            return self._discount(cashflows)
        elif self.indexType.lower() == 'accruedinterest':
            thisCouponDate = self.schedule.periods[0]['accrual_end']
            prevCoupnDate = _prevCouponDate(self.schedule.period,thisCouponDate)
            yearFrac = ScheduleDefinition.YearFraction(prevCoupnDate, self.schedule.valueDate, self.yearBasis)
            accuredInterest = self.notional * yearFrac * self.couponRate
            return accuredInterest
        


