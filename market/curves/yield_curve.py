from market.curves.curve_base import *
from market.curves.price_curve import *
from market.pillars import DepositRate, DiscountFactor
from market.instruments import xinstrument
from market.market_base import *


class YieldCurve(Curve):
    def __init__(self, key, valueDate, ccy, pillars, **kwargs):
        super(YieldCurve, self).__init__(key, ccy, valueDate, **kwargs)

        pillars.sort(key=lambda r: r.maturityDate)
        self.pillars = pillars
        self.points = np.array([(np.datetime64(self.valueDate.strftime('%Y-%m-%d')),
                                 ScheduleDefinition.DateOffset(self.valueDate),
                                 np.log(self.initialFactor))],
                               dtype=[('maturity', 'datetime64[D]'),
                                      ('timestamp', np.float64),
                                      ('discount_factor', np.float64)])

        self.points = self.points[0]

    def __len__(self):
        if hasattr(self, 'pillars'):
            return len(self.pillars)
        else:
            return 0

    def __repr__(self):
        return f"{self.key}; {self.ccy}; {self.valueDate.strftime('%Y-%m-%d')}; NumOfpillars:{len(self)} status:{self._built}"

    def Build(self, market=None):
        for instrument in self._addinstruments(market):
            df = instrument.SolveDf()
            # Add the solved df to the curve
            array = np.array([(np.datetime64(instrument.maturity.strftime('%Y-%m-%d')),
                               ScheduleDefinition.DateOffset(
                                   instrument.maturity),
                              df)], dtype=self.points.dtype)
            self.points = np.append(self.points, array)

        self._built = True

    def ZeroRates(self, dates, yearBasis='acton365f', rateConvention='linear'):
        if isinstance(dates, list) == False:
            dates = [dates]
        startDates = [self.valueDate] * len(dates)
        yearFractions = ScheduleDefinition.YearFractionList(
            startDates, dates, yearBasis)
        dfs = self.DiscountFactor(dates)
        values = RateConvention(rateConvention, yearFractions).DfToRate(dfs)
        dt = pd.DataFrame(list(zip(dates, values)), columns=[
                          'Dates', f'{self.key}.ZeroRates'])
        dt.set_index('Dates', inplace=True)
        return dt

    def FwdRates(self, startDates, tenor, yearBasis='acton365f', rateConvention='linear'):
        if isinstance(startDates, list) == False:
            startDates = [startDates]
        endDates = [
            x + ScheduleDefinition._parseDate(tenor) for x in startDates]
        yearFractions = ScheduleDefinition.YearFractionList(
            startDates, endDates, yearBasis)
        df1 = self.DiscountFactor(startDates)
        df2 = self.DiscountFactor(endDates)
        dfs = df2/df1
        fwd = RateConvention(rateConvention, yearFractions).DfToRate(dfs)
        dt = pd.DataFrame(list(zip(startDates, fwd)), columns=[
                          'Dates', f'{self.key}.FwdRates'])
        dt.set_index('Dates', inplace=True)
        return dt

    def SwapRates(self, dates, tenor, yearBasis='acton365f', rateConvention='linear', adjustment='modified following', calendar='SYD'):
        def _sumproduct(date):
            dateAdjuster = DateAdjuster(adjustment, calendar)
            schedule = Schedule(self.valueDate, date, tenor, dateAdjuster)
            schedule._create_schedule()
            periodStart = schedule.periods['accrual_start']
            periodEnd = schedule.periods['accrual_end']
            yearFractions = ScheduleDefinition.YearFractionList(
                periodStart, periodEnd, yearBasis)
            dfs = self.DiscountFactor(periodStart)
            return np.sum(np.multiply(dfs, yearFractions))

        if isinstance(dates, list) == False:
            dates = [dates]
        swapRates = []
        for date in dates:
            if date == self.valueDate:
                continue
            dcf = self.DiscountFactor(
                self.valueDate) - self.DiscountFactor(date)
            sumProduct = _sumproduct(date)
            swapRate = np.divide(dcf, sumProduct)
            swapRates.append(swapRate.flat[0])
        dt = pd.DataFrame(list(zip(dates, swapRates)), columns=[
                          'Dates', f'{self.key}.SwapRates'])
        dt.set_index('Dates', inplace=True)
        return dt

    # Dv01 wrapper
    def Dv01AtEachpillar(self, shockType, market=None, shockAmount=-0.0001, notional=1e6):
        baseYc = self
        shockedYc = self.CreateShockedCurve(shockType, shockAmount, market)
        result = {}
        for pillar in baseYc.pillars:
            baseNpv = xinstrument.ToAssets(
                pillar, baseYc, notional).Valuation(baseYc, baseYc)
            shockedNpv = xinstrument.ToAssets(
                pillar, shockedYc, notional).Valuation(shockedYc, shockedYc)
            result[pillar.label] = (shockedNpv-baseNpv)/(shockAmount * 10000)
        return pd.DataFrame(list(result.items()), columns=['Pillar', 'Delta'])

    # Zero Shock
    def ShiftZero(self, shockAmount, pillarToShock=-1):
        shiftedKey = self.key + '.ZeroShocked'
        shiftedpillars = []
        maturityDateList = self.points['maturity']
        df = np.exp(self.points['discount_factor'])

        for idx, (maturityDate, df) in enumerate(zip(maturityDateList, df)):
            maturityDate = ScheduleDefinition.DateConvert(maturityDate)
            if maturityDate > self.valueDate and (pillarToShock == -1 or idx == pillarToShock):
                yearFraction = ScheduleDefinition.YearFraction(
                    self.valueDate, maturityDate, 'ActOn365f')
                dfShifted = RateConvention(
                    'Linear', yearFraction).RateToDf(shockAmount)[0] * df
                pillar = DiscountFactor(maturityDate, dfShifted)
                shiftedpillars.append(pillar)
        return YieldCurve(shiftedKey, self.valueDate, self.ccy, shiftedpillars, **{'discountCurve': self.discountCurve})
    # pillarShock

    def Shiftpillar(self, shockAmount, pillarToShock=-1, discountCurve=None):
        dC = self.key if discountCurve is None else discountCurve
        shiftedKey = self.key + '.pillarShocked'
        shiftedpillars = copy.deepcopy(self.pillars)
        for idx, pillar in enumerate(shiftedpillars):
            if pillarToShock == -1 or idx == pillarToShock:
                pillar.Shock(shockAmount)
        return YieldCurve(shiftedKey, self.valueDate, self.ccy, shiftedpillars, **{'discountCurve': dC})

    # Shock Curve wrapper
    def CreateShockedCurve(self, shockType, shockAmount, market=None, pillarToShock=-1, period='3m', yearBasis='acton365f'):
        '''Wrapper function to call the underlying shock method.
        Currently supported shockType: zero, pillar, basis, forward
        '''
        if shockType.lower() == 'zero':
            shockedYc = self.ShiftZero(shockAmount, pillarToShock)
        elif shockType.lower() == 'pillar' and self.key == self.discountCurve:
            shockedYc = self.Shiftpillar(shockAmount, pillarToShock)
        elif shockType.lower() == 'pillar' and self.key != self.discountCurve:
            discountCurve = market[self.discountCurve]
            shockedDc = discountCurve.Shiftpillar(shockAmount, pillarToShock)
            shockedDc.Build()
            market + shockedDc
            shockedYc = self.Shiftpillar(
                shockAmount, pillarToShock, shockedDc.key)
        elif shockType.lower() == 'basis' and self.key != self.discountCurve:
            shockedYc = self.Shiftpillar(shockAmount, pillarToShock)
        elif shockType.lower() == 'foward':
            shockedYc = self.ShiftForward(
                shockAmount, period, yearBasis, pillarToShock)
        else:
            raise Exception(f'{shockType} is not supported')

        shockedYc.Build(market)
        return shockedYc

    # fwd curve
    def ToFowardRateCurve(self, period='3m', yearBasis='acton365f'):
        '''Converting a yield curve to fwd rate curve using Deposit Rate
        The discount factor results before and after should be the same'''
        fwdpillars = []
        dateAdjuster = DateAdjuster('unadjusted')
        maturity = ScheduleDefinition.DateConvert(self.points['maturity'][-1])
        schedule = Schedule(self.valueDate, maturity, period, dateAdjuster)
        schedule._create_schedule()
        startDates = schedule.periods['accrual_start']
        endDates = schedule.periods['accrual_end']
        yfs = ScheduleDefinition.YearFractionList(
            startDates, endDates, yearBasis)
        df = self.DiscountFactor(endDates) / self.DiscountFactor(startDates)
        fwds = RateConvention('Linear', yfs).DfToRate(df)

        # Construct new fwd curve using deposit rate
        for startDate, endDate, fwd in zip(startDates, endDates, fwds):
            startDate = ScheduleDefinition.DateConvert(startDate)
            endDate = ScheduleDefinition.DateConvert(endDate)
            fwdpillars.append(DepositRate(startDate, endDate, self.ccy,
                                          startDate.strftime('%Y-%m-%d'),
                                          'Linear', yearBasis, fwd, 'Zero', 'DEFAULT'))

        fwdRateCurve = YieldCurve(
            self.key, self.valueDate, self.ccy, fwdpillars)
        fwdRateCurve.Build()

        return fwdRateCurve

    def ShiftForward(self, shockAmount, period='3m', yearBasis='acton365f', pillarToShock=-1):
        yc = self.ToFowardRateCurve(period, yearBasis)
        shiftedKey = self.key + '.fowradShifted'
        shiftedpillars = copy.deepcopy(yc.pillars)
        for idx, pillar in enumerate(shiftedpillars):
            if pillarToShock == -1 or idx == pillarToShock:
                pillar.Shock(shockAmount)
        return YieldCurve(shiftedKey, self.valueDate, self.ccy, shiftedpillars, **{'discountCurve': yc})


class SpreadYieldCurve(YieldCurve):
    '''Extension of the YieldCurve class'''

    def __init__(self, key, ccy, valueDate, **kwargs):
        # Initialise the base Curve class to get initial df, but don't initialise YieldCurve as we dont have pillars yet
        super(YieldCurve, self).__init__(key, ccy, valueDate, **kwargs)
        self.key = key
        self.valueDate = valueDate
        self.ccy = ccy
        # Need to guard the below
        self.periods = kwargs.get('periods', None)
        self.yearBasis = kwargs.get('yearbasis', None)
        self.spreadCurve = kwargs.get('spreadcurve', None)
        self.points = np.array([(np.datetime64(self.valueDate.strftime('%Y-%m-%d')),
                                 ScheduleDefinition.DateOffset(self.valueDate),
                                 np.log(self.initialFactor))],
                               dtype=[('maturity', 'datetime64[D]'),
                                      ('timestamp', np.float64),
                                      ('discount_factor', np.float64)])

        self.points = self.points[0]

    def Build(self, market):
        yc = market[self.discountCurve.lower()]
        spreads = market[self.spreadCurve.lower()]

        fwdCurve = yc.ToFowardRateCurve(self.periods, self.yearBasis)
        self.pillars = copy.deepcopy(fwdCurve.pillars)
        for pillar in self.pillars:
            if isinstance(spreads, PriceCurve):
                spread = spreads.Price(pillar.startDate, spreads.interpMethod)
                pillar.Shock(spread)
            elif isinstance(spreads, float):
                pillar.Shock(spreads)
            else:
                raise Exception(f'{spreads} type is not supported')

        super(SpreadYieldCurve, self).Build()

        self._built = True

class XccyBasisCurve(YieldCurve):
    '''Extension of the YieldCurve class'''

    def __init__(self, *args, **kwargs):
        # Initialise the base Curve class to get initial df, but don't initialise YieldCurve as we dont have pillars yet
        super(XccyBasisCurve, self).__init__(*args, **kwargs)
        self.ccy2 = kwargs.get('ccy2', None)
        self.collDiscount = kwargs.get('colldiscount', None)
        self.collProject = kwargs.get('collproject', None)
        self.forProject = kwargs.get('forproject', None)
