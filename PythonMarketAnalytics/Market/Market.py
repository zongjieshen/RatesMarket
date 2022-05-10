import pandas as pd
import Market as mkt
import multiprocessing as mp   
from pathlib import Path


class Market():
    def __init__(self, handleName, valueDate, filePath):
        self.handleName = handleName
        self.valueDate = mkt.ScheduleDefinition.DateConvert(valueDate)
        
        self.marketItems = {}
    def worker(arg):
        obj, market = arg
        obj.Build(market)
        return obj
    def _build(self):
        #Check if all dependencies exist before passing into the recursive sorting function
        for item in self.marketItems.values():
            if next((x for x in self.marketItems.values() if x.key == item.discountCurve), None) is None:
                raise Exception(f'{item.discountCurve} curve doesnt exist in the market list')

        def _sortMarket(marketItemList, dependency, newList = None):
            marketItemList.sort(key=lambda r: hasattr(r,dependency) is False or r.key == getattr(r,dependency), reverse = True)
            if newList is None:
                newList =[]
            if len(marketItemList) ==0:
                return newList
            
            for item in marketItemList:
                if hasattr(item,dependency) is False or item.key == getattr(item,dependency) and item not in newList:
                   newList.append(item)
                   marketItemList.remove(item)
                   break
                elif item.key != getattr(item,dependency) and next((x for x in newList if x.key == getattr(item,dependency)), None) is not None:
                   newList.append(item)
                   marketItemList.remove(item)
                   break
                else:
                    marketItemList.append(marketItemList.pop(0))
                    break
            return _sortMarket(marketItemList, dependency, newList)

        sortedMarketList = _sortMarket(list(self.marketItems.values()), 'discountCurve')
        sortedMarketList = _sortMarket(sortedMarketList, 'spreadCurve')
        #TODO MultiProcessing

        #marketItems = sorted(self.marketItems.values(), key=lambda x: (x.key != x.discountCurve))
        #with mp.Pool(processes=4) as pool:
            #listtest = pool.map(Market.worker, ((obj,self) for obj in marketItems))

        for marketItem in sortedMarketList:
           marketItem.Build(self)
           print(f'{marketItem.key} build status is {marketItem._built}')

        


    def GetItems(self):
        if len(self.marketItems)  < 1:
            return Exception(f'market {self.handlename} hasnt been built')
        else:
            itemList =[]
            for key, item in self.marketItems.items():
                itemList.append((item.ccy + '|'+ item.__class__.__name__, item.key))
        return pd.DataFrame(itemList,columns = ['Currency|ItemType','Items'])

    def AddorUpdateItem(self,marketItem):
        if marketItem.key in self.marketItems:
            self.marketItems.pop(marketItem.key)
            self.marketItems[marketItem.key] = marketItem
        else:
            self.marketItems[marketItem.key] = marketItem

    def GetMarketItem(self,curveKey):
        if curveKey.lower() in self.marketItems:
            return self.marketItems[curveKey.lower()]
        else:
            return Exception (f'{curveKey} does not exist in the Market {self.handleName}')

    def YcShock(self,ycKey,shockType,shockAmount,pillarToShock=-1):
        shockedYc = self.marketItems[ycKey].CreateShockedCurve(shockType,shockAmount,pillarToShock,self)
        self.AddorUpdateItem(shockedYc)

            
class MarketFactory():
    @staticmethod
    def Create(handleName, valueDate, filePath = None, buildItems = None):
        if filePath is None:
            filePath = Path(__file__).parent/"MarketData.xlsx"
        ycDf=pd.read_excel(filePath,sheet_name='YieldCurve')
        icDf=pd.read_excel(filePath,sheet_name='InflationCurve')
        ifDf = pd.read_excel(filePath,sheet_name='IndexFixing')
        market = Market(handleName, valueDate, filePath)
        if buildItems is None:
            market._itemsToBuild = mkt.MarketDataManager.baseMarket()
        else:
            market._itemsToBuild = mkt.MarketDataManager.FromExcelArray(buildItems)

        for item in market._itemsToBuild:
            itemType = item.itemType
            if item.build == False or not item.label:
                continue
            elif itemType.lower() == 'yieldcurve':
                marketItem = mkt.YieldCurveFactory.Creat(ycDf,item,market.valueDate,item.build)
            elif itemType.lower() == 'inflationcurve':
                marketItem = mkt.InflationCurveFactory.Creat(icDf,item,market.valueDate,item.build)
            elif itemType.lower() == 'indexfixing':
                marketItem = mkt.IndexFixingFactory.Creat(ifDf,item,market.valueDate,item.build)
            elif itemType.lower() == 'pricecurve':
                marketItem = mkt.PriceCurveFactory.Creat(ycDf,item,market.valueDate,item.build)
            elif itemType.lower() == 'spreadyieldcurve':
                marketItem = mkt.SpreadYieldCurveFactory.Creat(item,market.valueDate,item.build)
            else:
                return NotImplementedError

            if marketItem:
                market.marketItems[marketItem.key.lower()] = marketItem

        market._build()
        return market
