import pandas as pd
import Market as mkt

class Market(object):
    def __init__(self, handleName, valueDate, filePath):
        self.handleName = handleName
        self.valueDate = valueDate
        self._itemsToBuild = MarketDataManager.baseMarket()
        self.marketItems = {}

    def _build(self):
        for key, marketItem in self.marketItems.items():
            marketItem.Build()

    def GetItems(self):
        if len(self.marketItems)  < 1:
            return Exception('market "{self.handlename}" hasnt been built')
        else:
            itemList =[]
            for key, item in self.marketItems.items():
                itemList.append((item.ccy, key))
        return itemList

    def AddorUpdateItem(self,marketItem):
        if marketItem.key in self.marketItems:
            self.marketItems.pop(curveKey)
            self.marketItems[marketItem.key] = marketItem
        else:
            self.marketItems[marketItem.key] = marketItem

    def GetMarketItem(self,curveKey):
        if curveKey in self.marketItems:
            return self.marketItems[curveKey]
        else:
            return Exception ('"{curveKey} does not exist in the Market "{self.handlename}"')

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
        audswapFilters = "(ValueType.str.startswith('DepositRate').values and Label.str.contains ('AUDBILL')) or (ValueType.str.startswith('SwapRate').values and Label.str.contains ('AUDSwap'))"
        gbpOisFilters = "Currency.str.startswith('GBP') and Context.str.startswith('Valuation') and Source == 'BBG' and ValueType.str.startswith('SwapRate') and CompoundingFrequency.str.startswith('Daily')"
        jpyOisFilters = "Currency.str.startswith('JPY') and Context.str.startswith('Valuation') and Source == 'BBG' and ValueType.str.startswith('SwapRate') and CompoundingFrequency.str.startswith('Daily')"

        bondCurveItem = ItemToBuild(True,'yieldCurve','AUDBondGov',bondfilters,'AUD',False)
        audSwapItem = ItemToBuild(True,'yieldCurve','AUDSwap',audswapFilters,'AUD',False)
        gbpOisItem = ItemToBuild(True,'yieldCurve','GBPOIS',gbpOisFilters,'GBP',False)
        jpyOisItem = ItemToBuild(True,'yieldCurve','JPYOIS',gbpOisFilters,'JPY',False)



        itemsToBuild = [gbpOisItem,bondCurveItem,audSwapItem,jpyOisItem]

        return itemsToBuild


class ItemToBuild():
    def __init__(self, build: bool, itemType: str, label: str, filters: str, ccy: str, discountCurve = False):
        self.build = build
        self.itemType = itemType
        self.label = label
        self.filters = filters
        self.ccy = ccy
        self.discountCurve = discountCurve