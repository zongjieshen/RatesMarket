import Market as mkt
import numpy as np
import datetime

class YieldCurveFactory:
    """description of class"""

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
        interType = itemToBuild.interType
        return YieldCurveFactory._ycCreate(data, label, ccy, interType, valueDate)

    def _ycCreate(df, key, ccy, interType, valueDate):
        pillars = []
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
            elif pillarType == 'BondYield':
                pillar = mkt.BondYield.fromRow(row, 'Fixed', valueDate)
                if pillar.maturityDate - pillar.startDate > datetime.timedelta(days=15):
                    pillars.append(pillar)
            elif pillarType == 'BondPrice':
                pass
        #Remove overdue pillars
        for pillar in pillars:
            if pillar.maturityDate < valueDate:
                pillars.remove(pillar)

        return mkt.YieldCurve(key,valueDate,ccy,interType,pillars)


