from Market.Instruments import *
import scipy.interpolate

#Discount Factor
class DiscountFactor(Instrument):
    def __init__(self, quote):
        self.maturity = quote.maturityDate
        self.df = quote.value

    def SolveDf(self):
        return np.log(self.df)
#Deposit
class Deposit(Instrument):
    def __init__(self, quote, curve, market = None, notional =1):
        super(Deposit, self).__init__(quote)
        self.curve = curve
        self.notional = notional
        self.market = market

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
            factor = np.exp(interpolator(ScheduleDefinition.DateOffset(self.startDate)))
            return np.log(df * factor)

    def Valuation(self,projectCurve, discountCurve):
        return DiscountCashFlow(self.ccy,self.schedule,self.notional,self.rate,
                              'fixed',self.yearBasis,projectCurve,discountCurve).pv()