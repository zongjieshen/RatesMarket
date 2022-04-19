#! /usr/bin/env python
# vim: set fileencoding=utf-8
import calendar
import datetime
import dateutil.relativedelta
import numpy as np
import pandas as pd
from enum import Enum
import holidays

class EFrequency(Enum):
        Annual = 'Annual'
        SemiAnnual = 'SemiAnnual'
        Quarterly = 'Quarterly'
        Monthly = 'Monthly'
        Zero = 'Zero'
       
class Schedule:
    '''Swap fixing, accrual, and payment dates
    '''
    def __init__(self, valueDate, maturity,frequency,
                 period_adjustment='unadjusted',
                 payment_adjustment='unadjusted'
                 ):

        # variable assignment
        self.valueDate = valueDate
        self.maturity = maturity
        self.period_delta = self._couponPerAnnum(frequency)[1]
        self.couponPerAnnum = self._couponPerAnnum(frequency)[0]
        self.period_adjustment = period_adjustment
        self.payment_adjustment = payment_adjustment

        # date generation routine
        self._gen_periods()
        self._create_schedule()

    def _gen_periods(self):
        '''Private method to generate the date series
        '''
        self._period_ends = self._gen_dates(self.valueDate,
                                                self.maturity,
                                                self.period_delta,
                                                self.period_adjustment)
        self._adjusted_period_ends = self._gen_dates(self.valueDate,
                                                     self.maturity,
                                                     self.period_delta,
                                                     self.period_adjustment)
        self._period_starts = [self.valueDate] + self._adjusted_period_ends[:-1]
        self._fixing_dates = self._gen_date_adjustments(self._adjusted_period_ends,
                                                            self.period_adjustment)
        self._payment_dates = self._gen_date_adjustments(self._period_ends,
                                                         0,
                                                         adjustment=self.payment_adjustment)

    def _create_schedule(self):
        '''Private function to merge the lists of periods to a np recarray
        '''
        arrays = self._np_dtarrays(self._fixing_dates, self._period_starts,
                                   self._adjusted_period_ends,
                                   self._payment_dates)
        arrays = (arrays + (np.zeros(len(self._fixing_dates), dtype=np.float64),) +
                  (np.zeros(len(self._fixing_dates), dtype=np.float64),))
        self.periods = np.rec.fromarrays((arrays),
                                         dtype=[('fixing_date', 'datetime64[D]'),
                                                ('accrual_start', 'datetime64[D]'),
                                                ('accrual_end', 'datetime64[D]'),
                                                ('payment_date', 'datetime64[D]'),
                                                ('cashflow', np.float64), 
                                                ('PV', np.float64)])




    def _gen_dates(self, valueDate, maturity, delta, adjustment):
        '''Private function to backward generate a series of dates starting
        from the maturity to the valueDate.

        Note that the valueDate date is not returned.
        '''
        dates = []
        current = maturity
        counter = 0
        while current > valueDate:
            dates.append(ScheduleDefinition._date_adjust(current, adjustment))
            counter += 1
            current = maturity - (delta * counter)
        return dates[::-1]


    def _gen_date_adjustments(self, dates, delta, adjustment='unadjusted'):
        '''Private function to take a list of dates and adjust each for a number
        of days. It will also adjust each date for a business day adjustment if
        requested.
        '''
        adjusted_dates = []
        for date in dates:
            adjusted_date = ScheduleDefinition._date_adjust(date, adjustment)
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

    def _couponPerAnnum(self,frequency):
        if EFrequency(frequency) is EFrequency.Annual:
            return (1, dateutil.relativedelta.relativedelta(years=1))
        elif EFrequency(frequency) is EFrequency.Monthly:
            return (12, dateutil.relativedelta.relativedelta(months=1))
        elif EFrequency(frequency) is EFrequency.Quarterly:
            return (4, dateutil.relativedelta.relativedelta(months=3))
        elif EFrequency(frequency) is EFrequency.SemiAnnual:
            return (2, dateutil.relativedelta.relativedelta(months=6))
        elif EFrequency(frequency) is EFrequency.Zero:
            return (0, self.maturity - self.valueDate)
        else:
            return (0, dateutil.relativedelta.relativedelta(months=0))


class ScheduleDefinition():

    @staticmethod
    def _date_adjust(date, adjustment, calendar = holidays.AU()):
        '''Method to return a date that is adjusted according to the
        adjustment convention method defined

        Arguments:
            date (datetime)     : Date to be adjusted
            adjustment (str)    : Adjustment type
                                  available: unadjusted,
                                             following,
                                             preceding,
                                             modified following
        '''
        if adjustment == 'unadjusted':
            return date
        elif adjustment == 'following':
            if date.weekday() < 5:
                return ScheduleDefinition._holidayAdj(date,adjustment,calendar)
            else:
                return date + ScheduleDefinition._timedelta(7 - date.weekday(), 'days')
        elif adjustment == 'preceding':
            if date.weekday() < 5:
                return ScheduleDefinition._holidayAdj(date,adjustment,calendar)
            else:
                date = date - ScheduleDefinition._timedelta(max(0, date.weekday() - 5), 'days')
                return ScheduleDefinition._holidayAdj(date,adjustment,calendar)
        elif adjustment == 'modified following':
            if date.month == ScheduleDefinition._date_adjust(date, 'following').month:
                date = ScheduleDefinition._date_adjust(date, 'following')
                return ScheduleDefinition._holidayAdj(date,adjustment,calendar)
            else:
                date = date - ScheduleDefinition._timedelta(7 - date.weekday(), 'days')
                return ScheduleDefinition._holidayAdj(date,adjustment,calendar)
        else:
            raise Exception('Adjustment period not recognized')

    @staticmethod
    def _holidayAdj(date,adjustment, calendar):
        if date not in calendar or adjustment == 'unadjusted':
            return date
        else:
            while date in calendar:
                if adjustment == 'following':
                    date = pd.to_datetime(date) + pd.offsets.DateOffset(1)
                elif adjustment == 'preceding':
                    date = pd.to_datetime(date) - pd.offsets.DateOffset(1)
                else:
                    date = pd.to_datetime(date) + pd.offsets.DateOffset(1)
        return date.to_pydatetime()
            

    
    @staticmethod
    def _timedelta(delta, period_length):
        '''Private function to convert a number and string (eg -- 3, 'months') to
        a dateutil relativedelta object
        '''
        if period_length == 'months':
            return dateutil.relativedelta.relativedelta(months=delta)
        elif period_length == 'weeks':
            return dateutil.relativedelta.relativedelta(weeks=delta)
        elif period_length == 'days':
            return dateutil.relativedelta.relativedelta(days=delta)
        else:
            raise Exception('Period length "{period_length}" not '
                            'recognized'.format(**locals()))

    @staticmethod
    def YearFraction(startDate, maturity, basis):
        '''Static method to return the accrual length, as a decimal,
        between an effective and a maturity subject to a basis convention

        Arguments:
            effective (datetime)    : First day of the accrual period
            maturity (datetime)     : Last day of the accrual period
            basis (str)             : Basis convention
                                      available: Act360,
                                                 Act365,
                                                 30360,
                                                 30E360

        '''
        startDate = ScheduleDefinition.DateConvert(startDate)
        maturity = ScheduleDefinition.DateConvert(maturity)
        if basis.lower() == 'act360':
            accrual_period = (maturity - startDate).days / 360
        elif basis.lower() == 'acton365f':
            accrual_period = (maturity - startDate).days / 365
        elif basis.lower() == '30360':
            start, end = min(startDate.day, 30), min(maturity.day, 30)
            months = (30 * (maturity.month - startDate.month) +
                      360 * (maturity.year - startDate.year))
            accrual_period = (end - start + months) / 360
        elif basis.lower() == '30e360':
            start, end = max(0, 30 - startDate.day), min(30, maturity.day)
            months = 30 * (maturity.month - startDate.month - 1)
            years = 360 * (maturity.year - startDate.year)
            accrual_period = (years + months + start + end) / 360
        elif basis.lower() == 'equalcoupons':
            accrual_period = maturity.year - startDate.year + (maturity.month - startDate.month)/12
        else:
            raise Exception('Accrual basis "{basis}" '
                            'not recognized'.format(**locals()))
        return accrual_period
    
    @staticmethod
    def YearFractionList(periodStarts, periodEnds, basis):
        periods = np.empty_like(periodStarts, dtype=np.float64)
        for idx, (start, maturity) in enumerate(zip(periodStarts,periodEnds)):
            periods[idx] = ScheduleDefinition.YearFraction(start, maturity, basis)
        return periods

    @staticmethod
    def DateConvert(date,valueDate=None):
        if type(date) == datetime.datetime:
            return date
        elif type(date) == np.datetime64:
            timestamp = date.astype('<M8[s]').astype(np.uint64)
            return datetime.datetime.fromtimestamp(timestamp).replace(hour=0, minute=0, second=0, microsecond=0)
        elif type(date) == int:
            return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + date - 2)
        elif type(date) == str:
            return ScheduleDefinition.ShiftDays(valueDate, date)
        else:
            return pd.to_datetime(date).to_pydatetime()


    @staticmethod
    def ShiftDays(valueDate, tenors):
        tenors = [x.strip() for x in tenors.split("+")[1:]]
        date = valueDate
        if not tenors:
            return valueDate
        for tenor in tenors:
            if tenor.endswith('y'):
                offset = int(tenor.replace('y',''))
                date = pd.to_datetime(date) + dateutil.relativedelta.relativedelta(years=offset)
            elif tenor.endswith('m'):
                offset = int(tenor.replace('m',''))
                date = pd.to_datetime(date) + dateutil.relativedelta.relativedelta(months=offset)
            elif tenor.endswith('b'):
                offset = int(tenor.replace('b',''))
                date = pd.to_datetime(date) + pd.offsets.BusinessDay(offset)
            elif tenor.endswith('d'):
                offset = int(tenor.replace('d',''))
                date = pd.to_datetime(date) + pd.offsets.DateOffset(offset)
            else:
                raise Exception('Cannot parse the date')
        return date.to_pydatetime()

