from Market.Curve import *

class InflationCurveFactory:
    """Factory to add rates to the inflation curve class"""

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
        return InflationCurveFactory._icCreate(data, label, ccy, valueDate, itemToBuild.params)

    def _icCreate(df, key, ccy,valueDate, params):
        pillars = []
        try:
            for index, row in df.iterrows():
                pillarType = row['ValueType']
                if pillarType in ['Df',np.nan,'DiscountFactor']:
                    pass
                elif pillarType == 'InflationSwapRate':
                    pass
                elif pillarType == 'BondYield':
                    pillar = BondYield.fromRow(row, 'CapitalIndexed', valueDate)
                    pillar.indexFixingKey = params['indexfixing']
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

        return InflationCurve(key,valueDate,ccy,pillars,**params)



