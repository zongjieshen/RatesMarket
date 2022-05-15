from Market.Curve import *

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
            raise Exception('Failed to retrieve curve data')
        return YieldCurveFactory._ycCreate(data, label, ccy, valueDate, itemToBuild.params )

    def _ycCreate(df, key, ccy, valueDate, params):
        pillars = []
        try:
            for index, row in df.iterrows():
                pillarType = row['ValueType']
                if pillarType in ['Df',np.nan,'DiscountFactor']:
                    pass
                elif pillarType == 'DepositRate':
                    pillar = DepositRate.fromRow(row, valueDate)
                    pillars.append(pillar)
                elif pillarType == 'SwapRate':
                    pillar = SwapRate.fromRow(row, valueDate)
                    pillars.append(pillar)
                elif pillarType == 'BasisSwap':
                    pillar = BasisSwapRate.fromRow(row, valueDate)
                    pillars.append(pillar)
                elif pillarType == 'BondYield':
                    pillar = BondYield.fromRow(row, 'Fixed', valueDate)
                    if pillar.maturityDate - pillar.startDate > datetime.timedelta(days=15):
                        pillars.append(pillar)
                elif pillarType == 'BondPrice':
                    pass
            #Remove overdue pillars and check pillars falling on same maturity date causing convergence error
            for pillar in pillars:
                if pillar.maturityDate < valueDate:
                    pillars.remove(pillar)
                if sum(p.maturityDate == pillar.maturityDate for p in pillars) > 1:
                    print(f"{pillar.label} {pillar.maturityDate.strftime('%Y-%m-%d')} has another pillar having the same maturity")
        except Exception as exp:
            raise Exception(exp)

        return YieldCurve(key,valueDate,ccy,pillars,**params)

    @staticmethod
    def ToAssets(pillar,curve, notional):
        if isinstance(pillar,DepositRate):
            return Deposit(pillar,curve, None,notional)
        elif isinstance(pillar,BondQuote):
            return Bond(pillar,curve, None,notional)
        elif isinstance(pillar,SwapRate):
            return Swap(pillar,curve, None,notional)
        else:
            raise Exception(f'{typeof(pillar)} cannot be converted to asset')


