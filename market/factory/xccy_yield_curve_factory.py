from market.curves import *
from market.pillars import *

class XccyBasisCurveFactory:
    """Factory to add rates initialise spread yield curve class"""

    @staticmethod
    def Creat(itemToBuild, valueDate, build: bool):
        return XccyBasisCurve(itemToBuild.label,itemToBuild.ccy, valueDate, **itemToBuild.params)


