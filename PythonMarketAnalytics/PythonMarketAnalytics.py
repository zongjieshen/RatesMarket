import pandas as pd
import Market as mkt
import xlwings as xw
import numpy as np
from datetime import datetime, timedelta

valueDate = datetime(2021, 12, 31)


#t = baseMarket.GetItems()

#pillarShok = curve.CreateShockedCurve('pillar',0.0001,-1)
#zeroShock = curve.CreateShockedCurve('zero',0.0001,-1)
#dv01 = curve.Dv01AtEachPillar('pillar',-0.0001)
#pillarShok.view()
#curve = baseMarket.marketItems['AUDSwap']
#curve.view()

#testDate = [datetime(2040, 12, 26),datetime(2050, 12, 26)]
#print(curve.FwdRates(testDate,'+3m'))

#mkt.YieldCurve.Charts(baseMarket.marketItems['AUDSwap'], 'SwapRates',testDate,'6m')
#gbpois = baseMarket.GetMarketItem('GBPOIS')
#t = mkt.ScheduleDefinition.DateConvert(44561)
#baseMarket.YcShock('AUDSwap','pillar',0.0001,-1)
#print(baseMarket.GetItems())
#schedule = mkt.Schedule(valueDate,testDate,'3m','modified following')
#schedule._gen_dates('modified following')
#global Handles
Handles ={}

@xw.func
def RemoveHandle(handleName):
    if handleName in Handles:
        del Handles[handleName]
        return True
    else:
        return (f'{handleName} handle does not exist')

@xw.func
def GetHandle():
    if len(Handles) == 0:
        return (f'No handles in the dictionary')
    else:
        return list(Handles.keys())

@xw.func
@xw.ret(index=False, header=True, expand='table')
def ScheduleCreate(valueDate, maturity, period,adjustments = 'unadjusted',calendar=None):
    valueDate = pd.to_datetime(valueDate)
    maturity = pd.to_datetime(maturity)
    schedule = mkt.Schedule(valueDate,maturity,period,'modified following','modified following',calendar)
    df = pd.DataFrame(schedule._gen_dates(adjustments),columns = ['Dates'])
    df['Dates'] = df['Dates'].dt.strftime('%m/%d/%Y')
    return df

@xw.func
def MarketCreate(handlename, valueDate,useCache = True):
    """Creates a market in memory, given set of market items"""
    if handlename in Handles and useCache is True:
        return handlename
    else:
        filepath = r'C:\Users\sheny\source\repos\zongjieshen\PythonMarketAnalytics\PythonMarketAnalytics\Market\BondYield.xlsx'
        print(type(valueDate))
        valueDate = mkt.ScheduleDefinition.DateConvert(valueDate)
        print(valueDate)
        market = mkt.MarketFactory.Create(handlename, valueDate,filepath)
        Handles[handlename] = market
        return handlename

@xw.func
@xw.ret(index=False, header=True, expand='table')
def MarketChartPoints(marketHandle,curveName, ratesType, dates ,tenor):
    dates = mkt.ScheduleDefinition.DateConvert(dates)
    market = Handles[marketHandle]
    curves = market.GetMarketItem(curveName)
    df = mkt.YieldCurve.Charts(curves,ratesType, dates ,tenor)
    return df

@xw.func
@xw.ret(index=False, header=True, expand='table')
def MarketItems(marketHandle):
    market = Handles[marketHandle]
    return market.GetItems()

@xw.func
@xw.ret(index=False, header=True, expand='table')
def MarketItemPillars(marketHandle, curveName):
    market = Handles[marketHandle]
    curve = market.GetMarketItem(curveName)
    pillars = [pd.DataFrame([pillar.__dict__]) for pillar in curve.pillars]
    dt = pd.concat(pillars)
    dt['startDate'] = dt['startDate'].dt.strftime('%m/%d/%Y')
    dt['maturityDate'] = dt['maturityDate'].dt.strftime('%m/%d/%Y')
    return dt

@xw.func
@xw.ret(index=False, header=True, expand='table')
def MarketDv01AtEachPillar(marketHandle, curveName, shockType, shockAmount= -0.0001, notional= 1e6):
    market = Handles[marketHandle]
    curve = market.GetMarketItem(curveName)
    return curve.Dv01AtEachPillar(shockType, shockAmount, notional)
    

from multiprocessing import freeze_support, set_start_method
if __name__ == '__main__':
    set_start_method('spawn', True)
    freeze_support()
    filepath = r'C:\Users\Zongjie\source\repos\zongjieshen\PythonMarketAnalytics\PythonMarketAnalytics\Market\BondYield.xlsx'
    baseMarket = mkt.MarketFactory.Create('baseMarket',valueDate,filepath)
    curve = baseMarket.marketItems['AUDSwap']
    aud3mcurve = baseMarket.marketItems['AUDSwap3m']
    curve.view()
    aud3mcurve.view()
    xw.serve()







