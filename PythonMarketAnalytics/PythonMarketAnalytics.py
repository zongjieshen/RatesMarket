import pandas as pd
import Market as mkt

import numpy as np
from datetime import datetime, timedelta

valueDate = datetime(2021, 12, 31)

filepath = r'C:\Users\sheny\source\repos\zongjieshen\PythonMarketAnalytics\PythonMarketAnalytics\Market\BondYield.xlsx'

baseMarket = mkt.MarketFactory.Create('baseMarket',valueDate,filepath)
t = baseMarket.GetItems()
curve = baseMarket.marketItems['AUDSwap']
pillarShok = curve.CreateShockedCurve('pillar',0.0001,-1)
zeroShock = curve.CreateShockedCurve('zero',0.0001,-1)
dv01 = curve.Dv01AtEachPillar('pillar',-0.0001)
pillarShok.view()
zeroShock.view()
curve.view()

testDate = datetime(2025, 12, 31)
print(curve.FwdRates(testDate,'+3m'))

gbpois = baseMarket.GetMarketItem('GBPOIS')
gbpois.view()
#baseMarket.YcShock('AUDSwap','pillar',0.0001,-1)
#print(baseMarket.GetItems())







