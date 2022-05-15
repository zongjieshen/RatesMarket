from Market.Dates import *
from Market.Pillars import *
from Market import Market
import scipy.optimize
import copy
import abc

class Instrument():
    def __init__(self, quote):
        self.key = quote.label
        self.ccy = quote.ccy
        self.yearBasis = quote.yearBasis
        self.rateConvention = quote.rateConvention
        self.startDate = quote.startDate
        self.maturity = quote.maturityDate
        self.rate = quote.rate
        self.dateAdjuster = quote.dateAdjuster

        self.schedule = Schedule(self.startDate,self.maturity,
                                 quote.paymentFrequency,self.dateAdjuster)
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
                                          ScheduleDefinition.DateOffset(self.maturity),
                                          guess)],
                                        dtype=self.curve.points.dtype))

        if isinstance(self.market, Market.Market) and self.curve.discountCurve != self.curve.key and self.market[self.curve.discountCurve]._built == True:
            discountCurve = self.market[self.curve.discountCurve]
        else:
            discountCurve = temp_curve

        return temp_curve, discountCurve

