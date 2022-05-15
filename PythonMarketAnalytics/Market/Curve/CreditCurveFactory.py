from Market.Curve import *

class CreditCurveFactory:
    """Factory to add rates to the credit curve class"""

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
        return CreditCurveFactory._ccCreate(data, label, ccy, valueDate, itemToBuild.params)

    def _ccCreate(df, key, ccy, valueDate, params):
        pillars = []
        try:
            for index, row in df.iterrows():
                pillarType = row['ValueType']
                if pillarType == 'CreditDefaultSwap':
                    pillars.append(CreditDefaultSwapRate.fromRow(row, valueDate))
                elif pillarType == 'DefaultProbability':
                    pass
                else:
                    raise Exception(f'{pillarType} is not supported')
        except Exception as exp:
            raise Exception(exp)

        return CreditCurve(key,valueDate,ccy,pillars,**params)


