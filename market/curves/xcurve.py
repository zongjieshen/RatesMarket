from market.curves import *
from market.util import *
import market as mkt
#Shock curve on forward rates
def ToFowardSpreadCurve(yc: YieldCurve, spreads: PriceCurve, curveName: str, period = '3m', yearBasis = 'acton365f'):
    '''Adding a spread curve on yield curve on the fwd basis'''
    label = yc.key + 'fwdShifted'
    params = XString(f'spreadCurve={spreads.key};periods={period};yearBasis={yearBasis};discountCurve={yc.key}')
    syc = SpreadYieldCurve(label,yc.ccy, yc.valueDate, **params._toDictionary('=',';'))
    market = mkt.Market('SpreadYcMarket',yc.valueDate)
    market + yc
    market + spreads
    syc.Build(market)

    return syc


