import holidays
import datetime
import numpy as np
import pandas as pd
from enum import Enum
from market.util import Constants, OneOf

class EFrequency(Enum):
        annual = 1
        semiannual = 2
        quarterly = 4
        monthly = 12
        zero = 0

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


class DateAdjuster():
    adjustment = OneOf(Constants.Adjustments)

    def __init__(self, adjustment = 'modified following', calendar = 'DEFAULT'):
        self.calendar = calendar
        self.adjustment = adjustment

    def __str__(self):
        return f'{self.calendar}'
    def __repr__(self):
        return f'{self.calendar}'

class ScheduleDefinition():
    @staticmethod
    def EndOfMonthAdj(dates, lag):
        def _endOfMonthAdj(date, lag):
            date = date + pd.offsets.QuarterEnd(0) + pd.offsets.DateOffset(months = lag)
            return date + pd.offsets.QuarterEnd(0)

        if isinstance(dates,(list,np.ndarray)):
            datesList =[]
            for date in dates:
                datesList.append(_endOfMonthAdj(date,lag))
            return datesList
        else:
            return _endOfMonthAdj(dates, lag)


    @staticmethod
    def _date_adjust(date, dateAdjuster: DateAdjuster):
        '''Method to return a date that is adjusted according to the
        adjustment convention method defined
        '''
        calendar = dateAdjuster.calendar
        adjustment = dateAdjuster.adjustment

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
                    dateAdjuster = DateAdjuster('following',calendar)
                    if date.month == ScheduleDefinition._date_adjust(date, dateAdjuster).month:
                        newDateAdjuster = DateAdjuster('following',calendar)
                        date = ScheduleDefinition._date_adjust(date, newDateAdjuster)
                    else:
                        newDateAdjuster = DateAdjuster('preceding',calendar)
                        date = ScheduleDefinition._date_adjust(date, newDateAdjuster)
            return date
        
    @staticmethod
    def YearFraction(startDate, maturity, basis, calendar = None):
        '''Static method to return the accrual length, as a decimal,
        between an effective and a maturity subject to a basis convention
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
        elif basis.lower() == 'actonact':
            accrual_period = (maturity - startDate).days / (365 + calendar.isleap(startDate.year))
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
    def DateConvert(dates,valueDate = None, dateAdjuster = None):
        if dateAdjuster is None:
            dateAdjuster = DateAdjuster()

        #Internal function
        def _dateConvert(date, valueDate,dateAdjuster):
            if type(date) == np.datetime64:
                timestamp = date.astype('<M8[s]').astype(np.uint64)
                return pd.to_datetime(datetime.datetime.fromtimestamp(timestamp).replace(hour=0, minute=0, second=0, microsecond=0))
            elif type(date) == int or type(date) == float:
                return datetime.datetime.fromtimestamp((date - 25569) * 86400).replace(hour=0, minute=0, second=0, microsecond=0)
            elif type(date) == str and 't' in date:
                return ScheduleDefinition.ShiftDays(valueDate, date, dateAdjuster)
            else:
                return pd.to_datetime(date).replace(hour=0, minute=0, second=0, microsecond=0)

        if isinstance(dates,(list,np.ndarray)):
            datesList =[]
            for date in dates:
                datesList.append(_dateConvert(date,valueDate,dateAdjuster))
            return datesList
        else:
            return _dateConvert(dates,valueDate, dateAdjuster)


    @staticmethod
    def ShiftDays(valueDate, tenors, dateAdjuster = None):
        if dateAdjuster is None:
            dateAdjuster = DateAdjuster()

        tenors = [x.strip() for x in tenors.split("+")[1:]]
        date = valueDate
        if not tenors:
            return valueDate
        for tenor in tenors:
            date = pd.to_datetime(date) + ScheduleDefinition._parseDate(tenor)
            date = ScheduleDefinition._date_adjust(date,dateAdjuster)
        return date.replace(hour=0, minute=0, second=0, microsecond=0)

    def _parseDate(period, valueDate = None, maturity = None):
        if period is None:
            raise Exception(f'{period} cannot be None')

        if (period in EFrequency._member_names_):
            if EFrequency[period] is EFrequency.annual:
                return pd.offsets.DateOffset(years=1)
            elif EFrequency[period] is EFrequency.monthly:
                return pd.offsets.DateOffset(months=1)
            elif EFrequency[period] is EFrequency.quarterly:
                return pd.offsets.DateOffset(months=3)
            elif EFrequency[period] is EFrequency.semiannual:
                return pd.offsets.DateOffset(months=6)
            elif EFrequency[period] is EFrequency.zero and valueDate is not None and maturity is not None:
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

    @staticmethod
    def DateOffset(date):
        if isinstance(date, np.ndarray) is True:
            return (date.astype('<M8[s]') - np.datetime64('1970-01-01')) / np.timedelta64(1, 's')
        else:
            return (np.asarray(date).astype('<M8[s]') - np.datetime64('1970-01-01')) / np.timedelta64(1, 's')