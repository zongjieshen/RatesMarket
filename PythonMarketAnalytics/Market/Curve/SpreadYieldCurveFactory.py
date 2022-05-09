import Market as mkt
import numpy as np
import datetime

class SpreadYieldCurveFactory:
    """Factory to add rates initialise spread yield curve class"""

    @staticmethod
    def Creat(itemToBuild, valueDate, build: bool):
        return mkt.SpreadYieldCurve(itemToBuild.label, valueDate, itemToBuild.ccy, itemToBuild.periods, 
                                    itemToBuild.yearBasis, itemToBuild.discountCurve, itemToBuild.spreadCurve)


