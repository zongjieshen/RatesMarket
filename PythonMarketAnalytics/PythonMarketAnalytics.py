import pandas as pd
import datetime
import Market as mkt

import numpy as np
from datetime import datetime, timedelta

valueDate = datetime(2021, 12, 31)

filepath = r'C:\Users\Zongjie\source\repos\MarketBuilding\PythonApplication1\MarketData\BondYield.xlsx'

baseMarket = mkt.MarketFactory.Create('baseMarket',valueDate,filepath)
t = baseMarket.GetItems();
curve = baseMarket.marketItems['AUDSwap']
pillarShok = curve.CreateShockedCurve('pillar',0.0001,-1)
zeroShock = curve.CreateShockedCurve('zero',0.0001,-1)
pillarShok.view()
zeroShock.view()

baseMarket.YcShock('AUDSwap','pillar',0.0001,-1)
print(baseMarket.GetItems())







