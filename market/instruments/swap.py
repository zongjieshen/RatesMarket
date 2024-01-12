from market.instruments import *

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

class XccyBasisSwap(Swap):
    def __init__(self, quote, curve, market = None, notional =1):
        super(XccyBasisSwap, self).__init__(quote, curve, market, notional)
        self.subType = 'xccyBasis'
        self.collDiscount = self.market[self.curve.collDiscount]
        self.collProject = self.market[self.curve.collProject]
        self.forProject = self.market[self.curve.forProject]

        self.yearBasis2 = quote.yearBasis2
        self.rateConvention2 = quote.rateConvention2
        self.dateAdjuster2 = quote.dateAdjuster2

        self.schedule2 = Schedule(self.startDate,self.maturity,
                                 quote.paymentFrequency2,self.dateAdjuster2)
        self.schedule2._create_schedule()
        self.ccy2 = quote.ccy2
        self.compoundFrequency2 = quote.compoundFrequency2


    def SolveDf(self):
        discountCurve = self.market[self.curve.discountCurve]
        guess = np.log(discountCurve.DiscountFactor(self.maturity))
        return scipy.optimize.newton(self._objectiveFunction, guess)

    def _objectiveFunction(self,guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve, discountCurve = self._copy(guess)
        return self.Valuation(discountCurve)

    def Valuation(self, discountCurve):
        basisLeg = DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'basis',self.yearBasis,self.forProject, discountCurve).pv()

        indexType2 = 'ois' if self.compoundFrequency2.lower() == 'daily' else 'floating'
        collLegPv = DiscountCashFlow(self.ccy,self.schedule2,self.notional,self.rate,
                              indexType2,self.yearBasis2,self.collProject, self.collDiscount).pv()

        return basisLeg - collLegPv
