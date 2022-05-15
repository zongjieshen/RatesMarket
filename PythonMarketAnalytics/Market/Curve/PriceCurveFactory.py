from Market.Curve import *

class PriceCurveFactory:
    """Factory to add rates to the price curve class"""

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
        return PriceCurveFactory._pcCreate(data, label, ccy, valueDate, itemToBuild.params)

    def _pcCreate(df, key, ccy, valueDate, params):
        pillars = []
        try:
            for index, row in df.iterrows():
                pillars.append(Spread.fromRow(row, valueDate))
        except Exception as exp:
            raise Exception(exp)

        return PriceCurve(key,valueDate,ccy,pillars,**params)


