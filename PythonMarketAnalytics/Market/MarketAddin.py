import xlwings as xw
import pandas as pd
import Market as mkt
import numpy as np
import Market.Dates as Dates

@xw.func
def MarketCreate(handlename, valueDate):
    import Market as mkt
    """Creates a market in memory, given set of market items"""
    filepath = r'C:\Users\sheny\source\repos\zongjieshen\PythonMarketAnalytics\PythonMarketAnalytics\Market\BondYield.xlsx'
    valueDate = mkt.ScheduleDefinition.DateConvert(valueDate)
    market = mkt.MarketFactory.Create(handlename, valueDate,filepath)
    return market


@xw.func
@xw.arg('df', pd.DataFrame, index=True, header=True)
def describe(df):
    return df.describe()


