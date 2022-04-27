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

        def _sortMarket(marketItemList, newList):
            if len(marketItemList) ==0:
                return
            
            for item in marketItemList:
                if item.key == item.discountCurve and item not in newList:
                   newList.append(item)
                   marketItemList.remove(item)
                elif item.key != item.discountCurve and next((x for x in newList if x.key == item.discountCurve), None) is not None:
                   newList.append(item)
                   marketItemList.remove(item)
                else:
                    marketItemList.append(marketItemList.pop(0))
                    break
            _sortMarket(marketItemList, newList)

        sortedMarketList =[]
        _sortMarket(list(self.marketItems.values()),sortedMarketList)
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
                itemList.append((item.ccy, key))
        return pd.DataFrame(itemList,columns = ['Currency','Items'])

    def AddorUpdateItem(self,marketItem):
        if marketItem.key in self.marketItems:
            self.marketItems.pop(marketItem.key)
            self.marketItems[marketItem.key] = marketItem
        else:
            self.marketItems[marketItem.key] = marketItem

    def GetMarketItem(self,curveKey):
        if curveKey in self.marketItems:
            return self.marketItems[curveKey]
        else:
            return Exception (f'{curveKey} does not exist in the Market {self.handlename}')

    def YcShock(self,ycKey,shockType,shockAmount,pillarToShock=-1):
        shockedYc = self.marketItems[ycKey].CreateShockedCurve(shockType,shockAmount,pillarToShock)
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
            market._itemsToBuild = MarketDataManager.baseMarket()
        else:
            market._itemsToBuild = MarketDataManager.FromExcelArray(buildItems)

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
            else:
                return NotImplementedError

            if marketItem:
                market.marketItems[marketItem.key] = marketItem

        market._build()
        return market

class MarketDataManager():
    def baseMarket():
        bondfilters = "ValueType == 'BondYield' and Currency == 'AUD'"
        audswapFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or (ValueType == 'SwapRate' and Label.str.contains ('AUDSwap').values)"
        gbpOisFilters = "Currency == 'GBP' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'SwapRate' and CompoundingFrequency == 'Daily'"
        jpyOisFilters = "Currency == 'JPY' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'SwapRate' and CompoundingFrequency == 'Daily'"
        audSwap3mFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or ValueType == 'SwapRate' and PaymentFrequency == 'Quarterly' and Label.str.startswith('AUDSwap').values or ValueType == 'BasisSwap' and PaymentFrequency == 'SemiAnnual' and Label.str.startswith('AUDBasis6m3m').values"
        audSwap6mFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or ValueType == 'SwapRate' and PaymentFrequency == 'SemiAnnual' and Label.str.startswith('AUDSwap').values or ValueType == 'BasisSwap' and PaymentFrequency == 'Quarterly' and Label.str.startswith('AUDBasis6m3m').values"
        audSwap1mFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or ValueType == 'BasisSwap' and Label.str.startswith('AUDBasis3m1m').values"
        beiCurveFilters = "Currency =='AUD' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'BondYield'"
        aucpiFilter = "Currency =='AUD'"

        bondCurveItem = ItemToBuild(True,'yieldCurve','AUDBondGov',bondfilters,'AUD')
        audSwapItem = ItemToBuild(True,'yieldCurve','AUDSwap',audswapFilters,'AUD')
        gbpOisItem = ItemToBuild(True,'yieldCurve','GBPOIS',gbpOisFilters,'GBP')
        jpyOisItem = ItemToBuild(True,'yieldCurve','JPYOIS',jpyOisFilters,'JPY')
        audSwap3mItem = ItemToBuild(True,'yieldCurve','AUDSwap3m',audSwap3mFilters,'AUD','AUDSwap')
        audSwap6mItem = ItemToBuild(True,'yieldCurve','AUDSwap6m',audSwap6mFilters,'AUD','AUDSwap')
        audSwap1mItem = ItemToBuild(True,'yieldCurve','AUDSwap1m',audSwap1mFilters,'AUD','AUDSwap3m')

        auCPI = ItemToBuild(True,'indexfixing','AUCPI',aucpiFilter,'AUD')
        beiCurve = ItemToBuild(True,'InflationCurve','AUD.Bond.Gov.BEI',beiCurveFilters,'AUD','AUDBondGov','AUCPI')

        itemsToBuild = [audSwap3mItem,audSwap6mItem,audSwap1mItem,audSwapItem,gbpOisItem,jpyOisItem,bondCurveItem,auCPI,beiCurve]

        return itemsToBuild

    def FromExcelArray(dt):
        buildItems =[]
        for index, row in dt.iterrows():
            item = ItemToBuild(row['Build'],row['CurveType'],
                               row['Label'],row['Filter'],row['Ccy'],
                               row['DiscountCurve'],row['IndexFixingKey'])
            buildItems.append(item)
        return buildItems


class ItemToBuild():
    def __init__(self, build: bool, itemType: str, label: str, filters: str, ccy: str, discountCurve = '', indexFixing = ''):
        self.build = build
        self.itemType = itemType
        self.label = label
        self.filters = filters
        self.ccy = ccy
        self.discountCurve = discountCurve
        self.indexFixing = indexFixing