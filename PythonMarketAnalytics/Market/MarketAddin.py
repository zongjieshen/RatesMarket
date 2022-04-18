import xlwings as xw
import pandas as pd
import Market as mkt

@xw.func
def MarketCreate(handlename, valueDate):
    """Creates a market in memory, given set of market items"""
    filepath = r'C:\Users\Zongjie\source\repos\MarketBuilding\PythonApplication1\MarketData\BondYield.xlsx'
    #valueDate = mkt.Dates.ScheduleDefinition.DateConvert(valueDate)
    x = pd.get_versions
    market = mkt.MarketFactory.Create(handlename, valueDate,filepath)
    return market


