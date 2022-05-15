from Market.Instruments import *

class CreditDefaultSwap(Instrument):
    def __init__(self, quote, curve, market = None, notional =1):
        super(CreditDefaultSwap, self).__init__(quote)
        self.portfolio = 'curve'
        self.subType = 'vanilla'
        self.notional = notional
        self.curve = curve
        self.market = market
        self.recoveryRate = quote.recoveryRate
        self.couponRate = quote.couponRate

    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate,self.maturity,self.yearBasis)
        rateConvention = RateConvention(self.rateConvention,yearFraction)
        guess = rateConvention.RateToDf(self.rate)
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve, discountCurve = self._copy(guess)
        return self.Valuation(temp_curve, discountCurve)

    def Valuation(self, projectCurve, discountCurve):
        premiumLegPV = CDSFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'premium',self.yearBasis,projectCurve,
                              discountCurve,self.recoveryRate,self.couponRate).pv()

        defaultLegPV = CDSFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'default',self.yearBasis,projectCurve,discountCurve,
                              self.recoveryRate,self.couponRate).pv()
        accuredInterest = CDSFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'accruedinterest',self.yearBasis,projectCurve,discountCurve,
                              self.recoveryRate,self.couponRate).pv()

        return premiumLegPV + defaultLegPV - accuredInterest
