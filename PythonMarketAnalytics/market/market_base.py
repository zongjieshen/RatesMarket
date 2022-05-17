import pandas as pd
from market.datamanager import *
from market.curves import *
from market.indexfixing import *
from market.factory import *
from market.dates import *
from multiprocessing import Process, Manager
from pathlib import Path
import time

class Market():
    def __init__(self, handleName, valueDate):
        self.handleName = handleName
        self.valueDate = ScheduleDefinition.DateConvert(valueDate)
        
        self.marketItems = {}

    def __getitem__(self, key):
        if isinstance(key, str):
            if key.lower() in ['all',':']:
                return list(self.marketItems.values())
            elif key.lower() in self.marketItems:
                return self.marketItems[key.lower()]
            else:
                raise Exception (f'{key} is not in the market {self.handleName}')
        else:
            raise TypeError (f'{key} has to be a string')

    def __len__(self):
        return len(self.marketItems)
    
    def __repr__(self):
        return f'Name: {self.handleName}; Date: {self.valueDate}; NumOfItems: {len(self)}'

    def __contains__(self, marketItem):
        if isinstance(marketItem, str):
            return True if marketItem.lower() in self.marketItems else False
        else:
            raise Exception(f'Only item key can be used to check')

    def __add__(self, marketItem):
        if isinstance(marketItem, (Curve, IndexFixing)):
            self.marketItems[marketItem.key.lower()] = marketItem
        else:
            raise TypeError(f'type of {marketItem} is incorrect')


    def _worker(itemList,dic, market):
        '''Internal worker function for multi-processing'''
        def _checkDep(item, dic, dependencies = ['discountCurve','spreadCurve']):
            flags = [False] * len(dependencies)
            for idx, dep in enumerate(dependencies):
                dependencyValue = getattr(item, dep, item.key)
                if dependencyValue == item.key:
                    flags[idx] = True
                elif dependencyValue != item.key and dependencyValue.lower() in dic and dic[dependencyValue.lower()]._built:
                    flags[idx] = True
            return all(flag is True for flag in flags)

        while len(itemList) != 0:
            item = itemList.pop(0)
            if item.key not in dic and _checkDep(item, market.marketItems) is True:
                item.Build(market)
                print(f'{item.key} build status is {item._built}')
                dic[item.key.lower()] = item
                market + item
            else:
                itemList.append(item)
    

    def _build(self):
        #Check if all dependencies exist before passing into the recursive sorting function
        for item in self.marketItems.values():
            if next((x for x in self.marketItems.values() if x.key == item.discountCurve), None) is None:
                raise Exception(f'{item.discountCurve} curve doesnt exist in the market list')

        marketList = list(self.marketItems.values())

        #market._worker(marketList, {},self)

        tic = time.time()
        with Manager() as manager:
            dic = manager.dict()

            p = Process(target=Market._worker, args=(marketList,dic, self))
            p.start()
            p.join()

            self.marketItems = dict(dic)
        toc = time.time()
        print('Done in {:.4f} seconds'.format(toc-tic))

        #tic = time.time()
        #Market._worker(marketList, {},self)
        #toc = time.time()
        #print('Done in {:.4f} seconds'.format(toc-tic))

    def GetItems(self):
        if len(self.marketItems)  < 1:
            return Exception(f'market {self.handlename} hasnt been built')
        else:
            itemList =[]
            for key, item in self.marketItems.items():
                itemList.append((item.ccy + '|'+ item.__class__.__name__, item.key))
        return pd.DataFrame(itemList,columns = ['Currency|ItemType','Items'])

    def YcShock(self,ycKey,shockType,shockAmount,pillarToShock=-1):
        shockedYc = self.marketItems[ycKey].CreateShockedCurve(shockType,shockAmount,pillarToShock,self)
        self + shockedYc


def Charts(curves, returnType, dates, tenor = '+3m',yearBasis = 'acton365f', rateConvention = 'linear'):
    '''Stand Alone function to plot the curve charts'''
    if isinstance(curves, (list,np.ndarray)) == False:
        curves =[curves]
    charts = []

    for curve in curves:
        if isinstance(curve, YieldCurve):
            if returnType.lower().startswith ('zero'):
                charts.append(curve.ZeroRates(dates, yearBasis, rateConvention))
            elif returnType.lower().startswith('fwd'):
                charts.append(curve.FwdRates(dates, tenor, yearBasis, rateConvention))
            elif returnType.lower().startswith ('swaprate'):
                charts.append(curve.SwapRates(dates, tenor, yearBasis, rateConvention))
            elif returnType.lower().startswith ('discount') or returnType.lower() == 'df':
                charts.append(curve.DiscountFactor(dates,returndf = True))
        elif isinstance(curve, CreditCurve):
            if returnType.lower().startswith ('survival'):
                charts.append(curve.SurvivalProbability(dates, True))
            elif returnType.lower().startswith('hazard'):
                charts.append(curve.HazardRates(dates, yearBasis, rateConvention))
        elif isinstance(curve, InflationCurve):
            if returnType.lower() == 'cpi':
                charts.append(curve.CPI(dates, True))
            elif returnType.lower().startswith('cpirate'):
                charts.append(curve.CPIRates(dates, yearBasis, rateConvention))
        elif isinstance(curve, IndexFixing):
            print('IndexFixing is embedded in Inflation, Use InflationCurve instead')
            continue
        elif isinstance(curve, PriceCurve):
            if returnType.lower() == 'price':
                charts.append(curve.Price(dates, True))
        else:
            raise Exception('Please select the right rate Type to return')
    return pd.concat(charts,axis=1)


            

def Create(handleName, valueDate, filePath = None, buildItems = None):
    '''Main function to create a market'''
    if filePath is None:
        filePath = Path(__file__).parent/"marketData.xlsx"
    ycDf=pd.read_excel(filePath,sheet_name='YieldCurve')
    icDf=pd.read_excel(filePath,sheet_name='InflationCurve')
    ifDf = pd.read_excel(filePath,sheet_name='IndexFixing')
    ccDf = pd.read_excel(filePath,sheet_name='CreditCurve')
    market = Market(handleName, valueDate)
    if buildItems is None:
        market._itemsToBuild = marketDataManager.basemarket()
    else:
        market._itemsToBuild = marketDataManager.FromExcelArray(buildItems)

    for item in market._itemsToBuild:
        itemType = item.itemType
        if item.build == False or not item.label:
            continue
        elif itemType.lower() == 'yieldcurve':
            marketItem = YieldCurveFactory.Creat(ycDf,item,market.valueDate,item.build)
        elif itemType.lower() == 'inflationcurve':
            marketItem = InflationCurveFactory.Creat(icDf,item,market.valueDate,item.build)
        elif itemType.lower() == 'indexfixing':
            marketItem = IndexFixingFactory.Creat(ifDf,item,market.valueDate,item.build)
        elif itemType.lower() == 'pricecurve':
            marketItem = PriceCurveFactory.Creat(ycDf,item,market.valueDate,item.build)
        elif itemType.lower() == 'spreadyieldcurve':
            marketItem = SpreadYieldCurveFactory.Creat(item,market.valueDate,item.build)
        elif itemType.lower() == 'creditcurve':
            marketItem = CreditCurveFactory.Creat(ccDf, item,market.valueDate,item.build)
        else:
            return NotImplementedError

        market + marketItem

    market._build()
    return market
