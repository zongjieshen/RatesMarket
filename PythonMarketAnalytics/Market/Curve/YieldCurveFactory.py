import Market as mkt
import numpy as np
import datetime

class YieldCurveFactory:
    """Factory to add rates to the yield curve class"""

    @staticmethod
    def Creat(dataFrame, itemToBuild, valueDate, build: bool):
        label = itemToBuild.label
        if dataFrame.empty:
            raise Exception('DataFrame is empty')
        ccy = itemToBuild.ccy
        filters = itemToBuild.filters
        data = dataFrame.query(filters)
        if data.empty:
            raise Exception('Failed to retrieve curve date')
        return YieldCurveFactory._ycCreate(data, label, ccy, itemToBuild.discountCurve, valueDate)

    def _ycCreate(df, key, ccy, discountCurve, valueDate):
        pillars = []
        try:
            for index, row in df.iterrows():
                pillarType = row['ValueType']
                if pillarType in ['Df',np.nan,'DiscountFactor']:
                    pass
                elif pillarType == 'DepositRate':
                    pillar = mkt.DepositRate.fromRow(row, valueDate)
                    pillars.append(pillar)
                elif pillarType == 'SwapRate':
                    pillar = mkt.SwapRate.fromRow(row, valueDate)
                    pillars.append(pillar)
                elif pillarType == 'BasisSwap':
                    pillar = mkt.BasisSwapRate.fromRow(row, valueDate)
                    pillars.append(pillar)
                elif pillarType == 'BondYield':
                    pillar = mkt.BondYield.fromRow(row, 'Fixed', valueDate)
                    if pillar.maturityDate - pillar.startDate > datetime.timedelta(days=15):
                        pillars.append(pillar)
                elif pillarType == 'BondPrice':
                    pass
            #Remove overdue pillars and check pillars falling on same maturity date causing convergence error
            for pillar in pillars:
                if pillar.maturityDate < valueDate:
                    pillars.remove(pillar)
                if sum(p.maturityDate == pillar.maturityDate for p in pillars) > 1:
                    print(f'{pillar.label} {pillar.maturityDate} has another pillar having the same maturity')
        except Exception as exp:
            raise Exception(exp)

        return mkt.YieldCurve(key,valueDate,ccy,pillars,discountCurve)

    @staticmethod
    def ToAssets(pillar,curve, notional):
        if isinstance(pillar,mkt.DepositRate):
            return mkt.Deposit(pillar,curve,notional)
        elif isinstance(pillar,mkt.BondQuote):
            return mkt.Bond(pillar,curve, None,notional)
        elif isinstance(pillar,mkt.SwapRate):
            return mkt.Swap(pillar,curve, None,notional)
        else:
            raise Exception(f'{typeof(pillar)} cannot be converted to asset')


