import pandas as pd
import Market as mkt
import operator
import multiprocessing as mp

from Market.YieldCurve import *                                                    


class Market():
    def __init__(self, handleName, valueDate, filePath):
        self.handleName = handleName
        self.valueDate = mkt.ScheduleDefinition.DateConvert(valueDate)
        self._itemsToBuild = MarketDataManager.baseMarket()
        self.marketItems = {}
    def worker(arg):
        obj, market = arg
        obj.Build(market)
        return obj
    def _build(self):
        marketItems = sorted(self.marketItems.values(), key=lambda x: (x.key != x.discountCurve))
        #with mp.Pool(processes=4) as pool:
            #listtest = pool.map(Market.worker, ((obj,self) for obj in marketItems))

        for marketItem in marketItems:
           marketItem.Build(self)

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
    def Create(handleName, valueDate, filePath):
        #TODO: Change file path
        df=pd.read_excel(filePath)
        market = Market(handleName, valueDate, filePath)
        for item in market._itemsToBuild:
            itemType = item.itemType
            if item.build == False or not item.label:
                continue
            elif itemType.lower() == 'yieldcurve':
                marketItem = mkt.YieldCurveFactory.Creat(df,item,market.valueDate,item.build)
            else:
                return NotImplementedError

            if marketItem:
                market.marketItems[marketItem.key] = marketItem

        market._build()
        return market

class MarketDataManager():
    def baseMarket():
        bondfilters = "ValueType.str.startswith('BondYield').values and Currency == 'AUD'"
        audswapFilters = "(ValueType.str.startswith('DepositRate').values and Label.str.contains ('AUDBILL').values) or (ValueType.str.startswith('SwapRate').values and Label.str.contains ('AUDSwap').values)"
        gbpOisFilters = "Currency.str.startswith('GBP').values and Context.str.startswith('Valuation').values and Source == 'BBG' and ValueType.str.startswith('SwapRate').values and CompoundingFrequency.str.startswith('Daily').values"
        jpyOisFilters = "Currency.str.startswith('JPY').values and Context.str.startswith('Valuation').values and Source == 'BBG' and ValueType.str.startswith('SwapRate').values and CompoundingFrequency.str.startswith('Daily').values"
        audSwap3mFilters = "(ValueType.str.startswith('DepositRate').values and Label.str.contains ('AUDBILL').values) or ValueType.str.startswith('SwapRate').values and PaymentFrequency == 'Quarterly' and Label.str.startswith('AUDSwap').values or ValueType.str.startswith('BasisSwap').values and PaymentFrequency == 'SemiAnnual' and Label.str.startswith('AUDBasis6m3m').values"
        audSwap6mFilters = "(ValueType.str.startswith('DepositRate').values and Label.str.contains ('AUDBILL').values) or ValueType.str.startswith('SwapRate').values and PaymentFrequency == 'SemiAnnual' and Label.str.startswith('AUDSwap').values or ValueType.str.startswith('BasisSwap').values and PaymentFrequency == 'Quarterly' and Label.str.startswith('AUDBasis6m3m').values"

        bondCurveItem = ItemToBuild(True,'yieldCurve','AUDBondGov',bondfilters,'AUD')
        audSwapItem = ItemToBuild(True,'yieldCurve','AUDSwap',audswapFilters,'AUD')
        gbpOisItem = ItemToBuild(True,'yieldCurve','GBPOIS',gbpOisFilters,'GBP')
        jpyOisItem = ItemToBuild(True,'yieldCurve','JPYOIS',jpyOisFilters,'JPY')
        audSwap3mItem = ItemToBuild(True,'yieldCurve','AUDSwap3m',audSwap3mFilters,'AUD','AUDSwap')
        audSwap6mItem = ItemToBuild(True,'yieldCurve','AUDSwap6m',audSwap6mFilters,'AUD','AUDSwap')



        itemsToBuild = [audSwap3mItem,audSwap6mItem,bondCurveItem,gbpOisItem,jpyOisItem,audSwapItem]

        return itemsToBuild


class ItemToBuild():
    def __init__(self, build: bool, itemType: str, label: str, filters: str, ccy: str, discountCurve = ''):
        self.build = build
        self.itemType = itemType
        self.label = label
        self.filters = filters
        self.ccy = ccy
        self.discountCurve = discountCurve