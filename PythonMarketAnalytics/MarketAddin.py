import pandas as pd
import Market as mkt
import xlwings as xw
import dateutil.relativedelta 

Handles ={}
if __name__ == '__main__':
    valueDate = pd.to_datetime('31/12/2021')
    baseMarket = mkt.MarketFactory.Create('baseMarket',valueDate)
    curve = baseMarket.marketItems['AUDBondGov']
    iaaCurve = baseMarket.GetMarketItem('IaaSpread')
    fwdCurve = curve.ToFowardSpreadCurve(iaaCurve, 'IaaCurve')
    #aud3mcurve = baseMarket.marketItems['AUDSwap3m']
   # baseMarket.YcShock('AUDSwap3m','pillar',0.0001)
    #swapdate = pd.to_datetime('31/12/2021')
    #date_list = [swapdate + dateutil.relativedelta.relativedelta(months=3*x) for x in range(10)] 
    #test =  mkt.Curve.Charts(curve, 'swaprates', date_list,'3m')
    fwdCurve.view()
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
def MarketCreate(handlename, valueDate, filepath = None, buildItems = None, useCache = True):
    """Creates a market in memory, given set of market items"""
    if handlename in Handles and useCache is True:
        return handlename
    else:
        valueDate = mkt.ScheduleDefinition.DateConvert(valueDate)
        market = mkt.MarketFactory.Create(handlename, valueDate,filepath,buildItems)
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
    dt['startDate'] = dt['startDate'].dt.strftime('%d/%m/%Y')
    dt['maturityDate'] = dt['maturityDate'].dt.strftime('%d/%m/%Y')
    return dt

@xw.func
@xw.ret(index=False, header=True, expand='table')
def MarketDv01AtEachPillar(marketHandle, curveName, shockType, shockAmount= -0.0001, notional= 1e6):
    market = Handles[marketHandle]
    curve = market.GetMarketItem(curveName)
    return curve.Dv01AtEachPillar(shockType, market, shockAmount, notional)
    









