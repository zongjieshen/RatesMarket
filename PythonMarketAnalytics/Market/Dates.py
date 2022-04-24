#! /usr/bin/env python
# vim: set fileencoding=utf-8
from calendar import calendar
import holidays
import datetime

from pandas.core.algorithms import value_counts
import numpy as np
import pandas as pd
from enum import Enum

class EFrequency(Enum):
        Annual = 1
        SemiAnnual = 2
        Quarterly = 4
        Monthly = 12
        Zero = 0

class ECalendar(Enum):
        SYD = holidays.AU()
        CAN = holidays.CA()
        SWI = holidays.CH()
        DEN = holidays.DK()
        EUR = holidays.TAR()
        UKG = holidays.UK()
        HKG = holidays.HK()
        JAP = holidays.JP()
        NOR = holidays.NO()
        NZL = holidays.NZ()
        SWE = holidays.SE()
        SIN = holidays.SG()
        USA = holidays.US()
        TOKYO = holidays.JP()
        LONDON = holidays.England()
        DEFAULT = holidays.AU()


class Schedule:
    '''Schedule fixing, accrual, and payment dates
    '''
    adjustments ={'unadjusted','following','modified following','preceding'}

    def __init__(self, valueDate, maturity,frequency,
                 period_adjustment='unadjusted',
                 payment_adjustment='unadjusted',
                 calendar = 'SYD'):

        # variable assignment
        self.valueDate = valueDate
        self.maturity = maturity
        self.period = frequency
        self.period_adjustment = period_adjustment
        self.payment_adjustment = payment_adjustment
        self.calendar = calendar

        if frequency in EFrequency._member_names_:
            self.couponPerAnnum = EFrequency[frequency].value
    
    @property
    def period_adjustment(self):
        return self._period_adjustment
    @period_adjustment.setter
    def period_adjustment(self,period_adjustment):
        if period_adjustment not in self.adjustments:
            raise ValueError(f"Invalid adjustment {period_adjustment} defined")
        self._period_adjustment = period_adjustment

    @property
    def payment_adjustment(self):
        return self._payment_adjustment
    @payment_adjustment.setter
    def payment_adjustment(self,payment_adjustment):
        if payment_adjustment not in self.adjustments:
            raise ValueError(f"Invalid adjustment {payment_adjustment} defined")
        self._payment_adjustment = payment_adjustment



    def _create_schedule(self):
        '''Private function to merge the lists of periods to a np recarray
        '''
        self._period_starts = [self.valueDate] + self._gen_dates(self.period_adjustment,self.calendar)[:-1]
        self._adjusted_period_ends = self._gen_dates(self.period_adjustment,self.calendar)
        self._fixing_dates = self._gen_date_adjustments(self._adjusted_period_ends,self.period_adjustment,self.calendar)
        self._payment_dates = self._gen_dates(self.payment_adjustment,self.calendar)

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




    def _gen_dates(self, adjustment, calendar):
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

        adjustedDates = self._gen_date_adjustments(dates[::-1],adjustment,calendar)

        return adjustedDates


    def _gen_date_adjustments(self, dates, adjustment, calendar):
        '''Private function to take a list of dates and adjust each for a number
        of days. It will also adjust each date for a business day adjustment if
        requested.
        '''
        adjusted_dates = []
        for date in dates:
            adjusted_date = ScheduleDefinition._date_adjust(date, adjustment,calendar)
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

class ScheduleDefinition():

    @staticmethod
    def _date_adjust(date, adjustment,calendar):
        '''Method to return a date that is adjusted according to the
        adjustment convention method defined
        '''
        calendar = 'DEFAULT' if calendar == None else calendar
        if adjustment == 'unadjusted':
            return date
        else:
            while date.weekday() > 4 or date in ECalendar[calendar].value:
                if adjustment == 'following':
                    date = date + pd.offsets.DateOffset(1)
                elif adjustment == 'preceding':
                    date = date - pd.offsets.DateOffset(1)
                else:
                    if date.month == ScheduleDefinition._date_adjust(date, 'following',calendar).month:
                        date = ScheduleDefinition._date_adjust(date, 'following',calendar)
                    else:
                        date = ScheduleDefinition._date_adjust(date, 'preceding',calendar)
            return date
        
    @staticmethod
    def YearFraction(startDate, maturity, basis, calendar = None):
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
        startDate = ScheduleDefinition.DateConvert(startDate,calendar)
        maturity = ScheduleDefinition.DateConvert(maturity,)
        if basis.lower() == 'acton360':
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
    def DateConvert(dates,valueDate = None,calendar = None, adjustment = 'modified following'):
        def _dateConvert(date, valueDate,adjustment,calendar):
            if type(date) == datetime.datetime:
                return date
            elif type(date) == np.datetime64:
                timestamp = date.astype('<M8[s]').astype(np.uint64)
                return datetime.datetime.fromtimestamp(timestamp).replace(hour=0, minute=0, second=0, microsecond=0)
            elif type(date) == int or type(date) == float:
                return datetime.datetime.fromtimestamp((date - 25569) * 86400)
            elif type(date) == str and 't' in date:
                return ScheduleDefinition.ShiftDays(valueDate, date, adjustment, calendar)
            else:
                return pd.to_datetime(date)

        if isinstance(dates,list) == True:
            datesList =[]
            for date in dates:
                datesList.append(_dateConvert(date,valueDate,adjustment,calendar))
            return datesList
        else:
            return _dateConvert(dates,valueDate,adjustment,calendar)


    @staticmethod
    def ShiftDays(valueDate, tenors,adjustment,calendar):
        tenors = [x.strip() for x in tenors.split("+")[1:]]
        date = valueDate
        if not tenors:
            return valueDate
        for tenor in tenors:
            date = pd.to_datetime(date) + ScheduleDefinition._parseDate(tenor)
            date = ScheduleDefinition._date_adjust(date,adjustment,calendar)
        return date

    def _parseDate(period, valueDate = None, maturity = None):
        if period is None:
            raise Exception(f'{period} cannot be None')

        if (period in EFrequency._member_names_):
            if EFrequency[period] is EFrequency.Annual:
                return pd.offsets.DateOffset(years=1)
            elif EFrequency[period] is EFrequency.Monthly:
                return pd.offsets.DateOffset(months=1)
            elif EFrequency[period] is EFrequency.Quarterly:
                return pd.offsets.DateOffset(months=3)
            elif EFrequency[period] is EFrequency.SemiAnnual:
                return pd.offsets.DateOffset(months=6)
            elif EFrequency[period] is EFrequency.Zero and valueDate is not None and maturity is not None:
                return maturity - valueDate
            else:
                return pd.offsets.DateOffset(months=0)

        if isinstance(period,str):
            period = period.lower();
            period = period.replace(" ", "");
            period = period.replace("\t", "");
            period = period.replace("years", "y");
            period = period.replace("year", "y");
            period = period.replace("months", "m");
            period = period.replace("month", "m");
            period = period.replace("businessdays", "b");
            period = period.replace("businessday", "b");
            period = period.replace("bd", "b");
            period = period.replace("days", "d");
            period = period.replace("day", "d");

        if period.endswith('y'):
            offset = int(period.replace('y',''))
            return pd.offsets.DateOffset(years=offset)
        elif period.endswith('m'):
            offset = int(period.replace('m',''))
            return pd.offsets.DateOffset(months=offset)
        elif period.endswith('b'):
            offset = int(period.replace('b',''))
            return pd.offsets.BusinessDay(offset)
        elif period.endswith('d'):
            offset = int(period.replace('d',''))
            return pd.offsets.DateOffset(offset)
        else:
            raise Exception (f'{period} date type is not defined')

