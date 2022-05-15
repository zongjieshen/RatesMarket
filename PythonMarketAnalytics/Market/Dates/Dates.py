import holidays
import numpy as np
import pandas as pd
from Market.Dates.ScheduleDefinition import *

class Schedule:
    '''Schedule fixing, accrual, and payment dates
    '''
    def __init__(self, valueDate, maturity,frequency,
                 dateAdjuster = None):

        # variable assignment
        self.valueDate = valueDate
        self.maturity = maturity
        self.period = frequency
        self.dateAdjuster = dateAdjuster if dateAdjuster is not None else DateAdjuster()


        if frequency in EFrequency._member_names_:
            self.couponPerAnnum = EFrequency[frequency].value
    


    def _create_schedule(self):
        '''Private function to merge the lists of periods to a np recarray
        '''
        self._period_starts = [self.valueDate] + self._gen_dates()[:-1]
        self._adjusted_period_ends = self._gen_dates()
        self._payment_dates = self._gen_dates()

        arrays = self._np_dtarrays(self._period_starts,
                                   self._adjusted_period_ends,
                                   self._payment_dates)
        arrays = (arrays + (np.zeros(len(self._period_starts), dtype=np.float64),) +
                  (np.zeros(len(self._period_starts), dtype=np.float64),))
        self.periods = np.rec.fromarrays((arrays),
                                         dtype=[('accrual_start', 'datetime64[D]'),
                                                ('accrual_end', 'datetime64[D]'),
                                                ('payment_date', 'datetime64[D]'),
                                                ('cashflow', np.float64), 
                                                ('PV', np.float64)])


    def _gen_dates(self):
        '''Private function to backward generate a series of dates starting
        from the maturity to the valueDate.

        Note that the valueDate date is not returned.
        '''
        delta = ScheduleDefinition._parseDate(self.period, self.valueDate, self.maturity)

        dates = []
        current = self.maturity
        counter = 0
        while current > self.valueDate:
            dates.append(current)
            counter += 1
            current = self.maturity - (delta * counter)

        adjustedDates = self._gen_date_adjustments(dates[::-1])

        return adjustedDates


    def _gen_date_adjustments(self, dates):
        '''Private function to take a list of dates and adjust each for a number
        of days. It will also adjust each date for a business day adjustment if
        requested.
        '''
        adjusted_dates = []
        for date in dates:
            adjusted_date = ScheduleDefinition._date_adjust(date, self.dateAdjuster)
            adjusted_dates.append(adjusted_date)
        return adjusted_dates

    def _np_dtarrays(self, *args):
        '''Converts a series of lists of dates to a tuple of np arrays of
        np.datetimes
        '''
        fmt = '%Y-%m-%d'
        arrays = []
        for arg in args:
            arrays.append(np.asarray([np.datetime64(date.strftime(fmt)) for date in arg]))
        return tuple(arrays)
