from market.instruments import *
import numpy as np
import abc

class Option(Instrument):
    def __init__(self, quote, curve, market=None, notional=1):
        super(Option, self).__init__(quote)
        self.portfolio = 'option'
        self.notional = notional
        self.curve = curve
        self.market = market
        self.strike = quote.strike
        self.optionType = quote.optionType  # 'call' or 'put'
        self.expiryDate = quote.expiryDate
        self.volatility = quote.volatility
        
    @abc.abstractmethod
    def SolveDf(self):
        return NotImplementedError
        
    @abc.abstractmethod
    def Valuation(self):
        return NotImplementedError
        
    def _copy(self, guess):
        temp_curve = None
        temp_curve = copy.deepcopy(self.curve)
        temp_curve.points = np.append(self.curve.points,
                               np.array([(np.datetime64(self.maturity.strftime('%Y-%m-%d')),
                                          ScheduleDefinition.DateOffset(self.maturity),
                                          guess)],
                                        dtype=self.curve.points.dtype))

        if isinstance(self.market, market_base.Market) and self.curve.discountCurve != self.curve.key and self.market[self.curve.discountCurve]._built == True:
            discountCurve = self.market[self.curve.discountCurve]
        else:
            discountCurve = temp_curve

        return temp_curve, discountCurve