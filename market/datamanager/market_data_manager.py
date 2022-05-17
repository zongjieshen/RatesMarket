import pandas as pd
from pathlib import Path
from market.util import *
from dataclasses import dataclass, field
from market.util import Constants



class marketDataManager():
    def basemarket():
        bondfilters = "ValueType == 'BondYield' and Currency == 'AUD'"
        audswapFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or (ValueType == 'SwapRate' and Label.str.contains ('AUDSwap').values)"
        gbpOisFilters = "Currency == 'GBP' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'SwapRate' and CompoundingFrequency == 'Daily'"
        jpyOisFilters = "Currency == 'JPY' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'SwapRate' and CompoundingFrequency == 'Daily'"
        usdOisFilters = "Currency == 'USD' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'SwapRate' and CompoundingFrequency == 'Daily'"
        audSwap3mFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or ValueType == 'SwapRate' and PaymentFrequency == 'Quarterly' and Label.str.startswith('AUDSwap').values or ValueType == 'BasisSwap' and PaymentFrequency == 'SemiAnnual' and Label.str.startswith('AUDBasis6m3m').values"
        audSwap6mFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or ValueType == 'SwapRate' and PaymentFrequency == 'SemiAnnual' and Label.str.startswith('AUDSwap').values or ValueType == 'BasisSwap' and PaymentFrequency == 'Quarterly' and Label.str.startswith('AUDBasis6m3m').values"
        audSwap1mFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or ValueType == 'BasisSwap' and Label.str.startswith('AUDBasis3m1m').values"
        beiCurveFilters = "Currency =='AUD' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'BondYield'"
        aucpiFilter = "Currency =='AUD'"
        iaaSpreadFilter = "Label == 'RBABondA'"
        usdCreditCurveFilter = "ValueType == 'CreditDefaultSwap' and Currency == 'USD'"

        #Params
        audSwapDiscount = XString("discountCurve=AUDSwap")
        aud3mDiscount = XString("discountCurve=AUDSwap3m")
        iaaSpreadParams = XString("InterpMethod = previous")
        iaaCurveParams = XString("spreadCurve=IaaSpread;periods=3m;yearBasis=acton365f;discountCurve=AUDBondGov")
        beiCurveParams = XString("discountCurve=AUDBondGov;IndexFixing=AUCPI")
        usdCreditCurveParams = XString("discountCurve=USDOIS")

        bondCurveItem = ItemToBuild(True,'yieldCurve','AUDBondGov',bondfilters,'AUD')
        audSwapItem = ItemToBuild(True,'yieldCurve','AUDSwap',audswapFilters,'AUD')
        gbpOisItem = ItemToBuild(True,'yieldCurve','GBPOIS',gbpOisFilters,'GBP')
        jpyOisItem = ItemToBuild(True,'yieldCurve','JPYOIS',jpyOisFilters,'JPY')
        usdOisItem = ItemToBuild(True,'yieldCurve','USDOIS',usdOisFilters,'USD')
        audSwap3mItem = ItemToBuild(True,'yieldCurve','AUDSwap3m',audSwap3mFilters,'AUD',audSwapDiscount._toDictionary('=',';'))
        audSwap6mItem = ItemToBuild(True,'yieldCurve','AUDSwap6m',audSwap6mFilters,'AUD',audSwapDiscount._toDictionary('=',';'))
        audSwap1mItem = ItemToBuild(True,'yieldCurve','AUDSwap1m',audSwap1mFilters,'AUD',aud3mDiscount._toDictionary('=',';'))
        usdCreditCurveItem = ItemToBuild(True,'creditCurve','USDCreditSwap',usdCreditCurveFilter,'USD',usdCreditCurveParams._toDictionary('=',';'))

        auCPI = ItemToBuild(True,'indexfixing','AUCPI',aucpiFilter,'AUD')
        beiCurve = ItemToBuild(True,'InflationCurve','AUD.Bond.Gov.BEI',beiCurveFilters,'AUD',beiCurveParams._toDictionary('=',';'))
        iaaSpread = ItemToBuild(True,'PriceCurve','IaaSpread',iaaSpreadFilter,'AUD',iaaSpreadParams._toDictionary('=',';'))
        iaaCurve = ItemToBuild(True,'SpreadYieldCurve','IaaCurve', '','AUD', iaaCurveParams._toDictionary('=',';'))

        itemsToBuild = [audSwap3mItem,audSwap6mItem,audSwap1mItem,iaaCurve,audSwapItem,gbpOisItem,jpyOisItem,usdOisItem,bondCurveItem,auCPI,usdCreditCurveItem,beiCurve,iaaSpread]
        
        #itemsToBuild = [bondCurveItem,auCPI,beiCurve]
        return itemsToBuild

    def FromExcelArray(dt):
        buildItems =[]
        for index, row in dt.iterrows():
            params = XString(row['Params'])._toDictionary('=',';') if row['Params'] is not None else {}
            item = ItemToBuild(row['Build'],row['CurveType'],
                               row['Label'],row['Filter'],row['Ccy'],
                               params)
            buildItems.append(item)
        return buildItems




@dataclass
class ItemToBuild():
    build: bool
    itemType: str
    label: str
    filters: str
    ccy: str
    params: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.itemType is not None and self.itemType.lower() not in Constants.ItemType:
            raise ValueError(f'Expected {self.itemType!r} to be one of {Constants.ItemType!r}')
