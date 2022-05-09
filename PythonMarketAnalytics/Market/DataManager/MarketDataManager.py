import pandas as pd
from pathlib import Path
from dataclasses import dataclass


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
        iaaSpreadFilter = "Label == 'RBABondA'"

        #Params
        audSwapDiscount = "discountCurve=AUDSwap"
        aud3mDiscount = "discountCurve=AUDSwap3m"
        iaaSpreadParams = "InterpMethod = previous"
        iaaCurveParams = "spreadCurve=IaaSpread;periods=3m;yearBasis=acton365f;discountCurve=AUDBondGov"
        beiCurveParams = "discountCurve=AUDBondGov;IndexFixing=AUCPI"

        bondCurveItem = ItemToBuild(True,'yieldCurve','AUDBondGov',bondfilters,'AUD')
        audSwapItem = ItemToBuild(True,'yieldCurve','AUDSwap',audswapFilters,'AUD')
        gbpOisItem = ItemToBuild(True,'yieldCurve','GBPOIS',gbpOisFilters,'GBP')
        jpyOisItem = ItemToBuild(True,'yieldCurve','JPYOIS',jpyOisFilters,'JPY')
        audSwap3mItem = ItemToBuild(True,'yieldCurve','AUDSwap3m',audSwap3mFilters,'AUD',**MarketDataManager._toDictionary(audSwapDiscount,'=',';'))
        audSwap6mItem = ItemToBuild(True,'yieldCurve','AUDSwap6m',audSwap6mFilters,'AUD',**MarketDataManager._toDictionary(audSwapDiscount,'=',';'))
        audSwap1mItem = ItemToBuild(True,'yieldCurve','AUDSwap1m',audSwap1mFilters,'AUD',**MarketDataManager._toDictionary(aud3mDiscount,'=',';'))

        auCPI = ItemToBuild(True,'indexfixing','AUCPI',aucpiFilter,'AUD')
        beiCurve = ItemToBuild(True,'InflationCurve','AUD.Bond.Gov.BEI',beiCurveFilters,'AUD',**MarketDataManager._toDictionary(beiCurveParams,'=',';'))
        iaaSpread = ItemToBuild(True,'PriceCurve','IaaSpread',iaaSpreadFilter,'AUD',**MarketDataManager._toDictionary(iaaSpreadParams,'=',';'))
        iaaCurve = ItemToBuild(True,'SpreadYieldCurve','IaaCurve', '','AUD', **MarketDataManager._toDictionary(iaaCurveParams,'=',';'))


        itemsToBuild = [audSwap3mItem,audSwap6mItem,audSwap1mItem,iaaCurve,audSwapItem,gbpOisItem,jpyOisItem,bondCurveItem,auCPI,beiCurve,iaaSpread]
        #itemsToBuild = [bondCurveItem, iaaSpread, iaaCurve]
        return itemsToBuild

    def FromExcelArray(dt):
        buildItems =[]
        for index, row in dt.iterrows():
            params = row['Params'] if row['Params'] is not None else ''
            item = ItemToBuild(row['Build'],row['CurveType'],
                               row['Label'],row['Filter'],row['Ccy'],
                               **MarketDataManager._toDictionary(params,'=',';'))
            buildItems.append(item)
        return buildItems

    @staticmethod
    def _toDictionary(str, rowSplit, colSplit):
        if rowSplit not in str and colSplit not in str:
            return {}
        d = dict(x.split(rowSplit) for x in str.split(colSplit))
        return {k.lower():v for k,v in d.items()}


class ItemToBuild():
    def __init__(self, build, itemType, label, filters, ccy, **kwargs):
        self.build = build
        self.itemType = itemType
        self.label = label
        self.filters = filters
        self.ccy = ccy
        self.discountCurve = kwargs.get('discountcurve','')
        self.indexFixing = kwargs.get('indexfixing','')
        self.interpMethod = kwargs.get('interpmethod','')
        self.periods = kwargs.get('periods',None)
        self.yearBasis = kwargs.get('yearbasis',None)
        self.spreadCurve = kwargs.get('spreadcurve',None)

