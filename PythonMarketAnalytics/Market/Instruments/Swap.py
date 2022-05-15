from Market.Instruments import *

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
        discountCurve = self.market[self.curve.discountCurve]
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
