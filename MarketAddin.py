import pandas as pd
import market as mkt
import xlwings as xw
import dateutil.relativedelta 

Handles ={}
if __name__ == '__main__':
    valueDate = pd.to_datetime('31/12/2021')
    baseMarket = mkt.Create('basemarket',valueDate)
    date_list = [valueDate + dateutil.relativedelta.relativedelta(months=3*x) for x in range(100)] 
    df = mkt.Charts(list(baseMarket.marketItems.values()), 'zero', date_list,'3m')
    audSwap = baseMarket['AUDSwap']
    dv01 = audSwap.Dv01AtEachpillar('pillar')
    iaaSpread = baseMarket['iaaspread']
    fwdShockedCurve = audSwap.CreateShockedCurve('zero',shockAmount = 0.0001, period = '3m', yearBasis = 'acton365f')
    df = mkt.Charts([audSwap,fwdShockedCurve], 'fwd', date_list,'3m')
    fwdShockedCurve = mkt.ToFowardSpreadCurve(audSwap,iaaSpread, 'IaaCurve')
    #aud3mcurve = basemarket.marketItems['AUDSwap3m']
   # basemarket.YcShock('AUDSwap3m','pillar',0.0001)
    #fwdCurve.view()
    #aud3mcurve.view()
    xw.serve()

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
def ScheduleCreate(valueDate, maturity, period, adjustment = 'unadjusted',calendar=None):
    dateAdjuster = mkt.DateAdjuster(adjustment, calendar)
    valueDate = pd.to_datetime(valueDate)
    maturity = pd.to_datetime(maturity)
    schedule = mkt.Schedule(valueDate,maturity,period,dateAdjuster)
    df = pd.DataFrame(schedule._gen_dates(),columns = ['Dates'])
    df['Dates'] = df['Dates'].dt.strftime('%d/%m/%Y')
    return df

@xw.func
@xw.arg('buildItems', pd.DataFrame, index=False, header=True)
def marketCreate(handlename, valueDate, filepath = None, buildItems = None, useCache = True):
    '''Creates a market in memory, given set of market it
    ems'''
    if handlename in Handles and useCache is True:
        return handlename
    else:
        valueDate = mkt.ScheduleDefinition.DateConvert(valueDate)
        market = mkt.Create(handlename, valueDate,filepath,buildItems)
        Handles[handlename] = market
        return handlename

@xw.func
@xw.ret(index=False, header=True, expand='table')
def marketChartPoints(marketHandle,curveName, ratesType, dates ,tenor):
    '''Returns DF, ZeroRates, SwapRates in the chart based on a schedule created'''
    dates = mkt.ScheduleDefinition.DateConvert(dates)
    market = Handles[marketHandle]
    curve = market[curveName]
    df = mkt.Charts(curve,ratesType, dates ,tenor)
    return df

@xw.func
@xw.ret(index=False, header=True, expand='table')
def marketItems(marketHandle):
    market = Handles[marketHandle]
    return market.GetItems()

@xw.func
@xw.ret(index=False, header=True, expand='table')
def marketItemInfo(marketHandle, curveName):
    market = Handles[marketHandle]
    curve = market[curveName]
    return curve.ItemInfo()

@xw.func
@xw.ret(index=False, header=True, expand='table')
def marketDv01AtEachpillar(marketHandle, curveName, shockType, shockAmount= -0.0001, notional= 1e6):
    market = Handles[marketHandle]
    curve = market[curveName]
    return curve.Dv01AtEachpillar(shockType, market, shockAmount, notional)
    









