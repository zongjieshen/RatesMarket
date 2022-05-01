from Market.Dates import *
from Market.Pillars import *
import pandas as pd
import time
import copy
import abc

class Instrument():
    def __init__(self, quote, adjustment = 'modified following'):
        self.key = quote.label
        self.ccy = quote.ccy
        self.yearBasis = quote.yearBasis
        self.rateConvention = quote.rateConvention
        self.startDate = quote.startDate
        self.maturity = quote.maturityDate
        self.rate = quote.rate
        self.calendar = quote.calendar

        self.schedule = Schedule(self.startDate,self.maturity,
                                 quote.paymentFrequency,adjustment,self.calendar)
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

