from Market.Curve import *

class SpreadYieldCurveFactory:
    """Factory to add rates initialise spread yield curve class"""

    @staticmethod
    def Creat(itemToBuild, valueDate, build: bool):
        return SpreadYieldCurve(itemToBuild.label,itemToBuild.ccy, valueDate, **itemToBuild.params)


