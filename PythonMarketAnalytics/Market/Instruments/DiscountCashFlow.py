from Market.Instruments import *
import scipy.interpolate
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