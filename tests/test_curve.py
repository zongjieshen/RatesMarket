import pytest
import numpy as np
import pandas as pd
import market as mkt

valueDate = pd.to_datetime('31/12/2021',format = '%d/%m/%Y')

def test_single_curve():
    expected = np.array([1.     , 0.99999, 0.99996, 0.99983, 0.99894, 0.99608, 0.98196,
       0.96207, 0.93973, 0.9197 , 0.89926, 0.87838, 0.85803])
    
    #Add pillars here so that unit test is independent from the factory method
    pillars = [mkt.DepositRate('2022-01-04', '2022-02-04', 'AUD', 'AUDBILL1M', 'linear', 'acton365f', 0.00015, 'zero', 'SYD'),
            mkt.DepositRate('2022-01-04', '2022-03-04', 'AUD', 'AUDBILL2M', 'linear', 'acton365f', 0.000257, 'zero', 'SYD'),
            mkt.DepositRate('2022-01-04', '2022-04-04', 'AUD', 'AUDBILL3M', 'linear', 'acton365f', 0.000677, 'zero', 'SYD'),
            mkt.DepositRate('2022-01-04', '2022-07-04', 'AUD', 'AUDBILL6M', 'linear', 'acton365f', 0.002135, 'zero', 'SYD'),
            mkt.SwapRate('2022-01-04', '2023-01-04', 'AUD', 'AUDSwap1Y', 'linear', 'acton365f', 0.003921, 'quarterly', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2024-01-04', 'AUD', 'AUDSwap2Y', 'linear', 'acton365f', 0.009084, 'quarterly', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2025-01-06', 'AUD', 'AUDSwap3Y', 'linear', 'acton365f', 0.0128, 'quarterly', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2026-01-05', 'AUD', 'AUDSwap4Y', 'linear', 'acton365f', 0.01545, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2027-01-04', 'AUD', 'AUDSwap5Y', 'linear', 'acton365f', 0.01665, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2028-01-04', 'AUD', 'AUDSwap6Y', 'linear', 'acton365f', 0.01759, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2029-01-04', 'AUD', 'AUDSwap7Y', 'linear', 'acton365f', 0.01839, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2030-01-04', 'AUD', 'AUDSwap8Y', 'linear', 'acton365f', 0.01899, 'semiannual', 'SYD', 'Zero', '0d')]
            
    curve = mkt.YieldCurve('CurveTest',valueDate, 'AUD',pillars)
    curve.Build()
    df = np.exp(curve.points['discount_factor']).round(5)
    np.testing.assert_array_equal(df,expected)

def test_basis_curve():
    expected = np.array([1.     , 0.99999, 0.99996, 0.99983, 0.99932, 0.99894, 0.99608,
       0.98196, 0.96207, 0.94237, 0.92291, 0.90287, 0.88241, 0.86251,
       0.84292, 0.82325, 0.7855 , 0.73242, 0.65816, 0.60195, 0.55862])

    audswapFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or (ValueType == 'SwapRate' and Label.str.contains ('AUDSwap').values)"
    audSwapItem = mkt.ItemToBuild(True,'yieldCurve','AUDSwap',audswapFilters,'AUD')
    audSwap3mFilters = "(ValueType == 'DepositRate' and Label.str.contains ('AUDBILL').values) or ValueType == 'SwapRate' and PaymentFrequency == 'Quarterly' and Label.str.startswith('AUDSwap').values or ValueType == 'BasisSwap' and PaymentFrequency == 'SemiAnnual' and Label.str.startswith('AUDBasis6m3m').values"
    audSwapDiscount = mkt.XString("discountCurve=AUDSwap")
    audSwap3mItem = mkt.ItemToBuild(True,'yieldCurve','AUDSwap3m',audSwap3mFilters,'AUD',audSwapDiscount._toDictionary('=',';'))

    market = mkt.Create('AudSwap',valueDate,None,[audSwap3mItem,audSwapItem])
    aud3mSwap = market['AUDSwap3m']
    df = np.exp(aud3mSwap.points['discount_factor']).round(5)
    np.testing.assert_array_equal(df,expected)

def test_cpi_curve():
   expected = np.array([117.9    , 118.8    , 119.7    , 130.38333, 137.58721, 145.53125,
       152.70172, 163.33236, 186.9011 , 231.66816])

   bondfilters = "ValueType == 'BondYield' and Currency == 'AUD'"
   beiCurveFilters = "Currency =='AUD' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'BondYield'"
   aucpiFilter = "Currency =='AUD'"
   beiCurveParams = mkt.XString("discountCurve=AUDBondGov;IndexFixing=AUCPI")
   auCPI = mkt.ItemToBuild(True,'indexfixing','AUCPI',aucpiFilter,'AUD')
   beiCurve = mkt.ItemToBuild(True,'InflationCurve','AUD.Bond.Gov.BEI',beiCurveFilters,'AUD',beiCurveParams._toDictionary('=',';'))
   bondCurveItem = mkt.ItemToBuild(True,'yieldCurve','AUDBondGov',bondfilters,'AUD')
   market = mkt.Create('BEI',valueDate,None,[beiCurve,bondCurveItem, auCPI])

   beiCurve = market['AUD.Bond.Gov.BEI']
   df = np.exp(beiCurve.points['discount_factor'][-10:]).round(5)
   np.testing.assert_array_equal(df,expected)

def test_spread_yield_curve():
   expected = np.array([0.40937, 0.40646, 0.40357, 0.40073, 0.39795, 0.39512, 0.39231,
       0.38956, 0.38685, 0.3841 ])

   bondfilters = "ValueType == 'BondYield' and Currency == 'AUD'"
   bondCurveItem = mkt.ItemToBuild(True,'yieldCurve','AUDBondGov',bondfilters,'AUD')
   iaaSpreadFilter = "Label == 'RBABondA'"
   iaaSpreadParams = mkt.XString("InterpMethod = previous")
   iaaCurveParams = mkt.XString("spreadCurve=IaaSpread;periods=3m;yearBasis=acton365f;discountCurve=AUDBondGov")
   iaaSpread = mkt.ItemToBuild(True,'PriceCurve','IaaSpread',iaaSpreadFilter,'AUD',iaaSpreadParams._toDictionary('=',';'))
   iaaCurve = mkt.ItemToBuild(True,'SpreadYieldCurve','IaaCurve', '','AUD', iaaCurveParams._toDictionary('=',';'))
   market = mkt.Create('IAA',valueDate,None,[iaaCurve,bondCurveItem,iaaSpread])

   iaaCurve = market['IaaCurve']
   df = np.exp(iaaCurve.points['discount_factor'][-10:]).round(5)
   np.testing.assert_array_equal(df,expected)

def test_credit_curve():
    expected = np.array([1.     , 0.91977, 0.7966 , 0.65404, 0.60155, 0.50857, 0.48967, 0.35932])
    
    usdOisFilters = "Currency == 'USD' and Context == 'Valuation' and Source == 'BBG' and ValueType == 'SwapRate' and CompoundingFrequency == 'Daily'"
    usdCreditCurveFilter = "ValueType == 'CreditDefaultSwap' and Currency == 'USD'"
    
    usdCreditCurveParams = mkt.XString("discountCurve=USDOIS")
    usdOisItem = mkt.ItemToBuild(True,'yieldCurve','USDOIS',usdOisFilters,'USD')
    usdCreditCurveItem = mkt.ItemToBuild(True,'creditCurve','USDCreditSwap',usdCreditCurveFilter,'USD',usdCreditCurveParams._toDictionary('=',';'))
    market = mkt.Create('CDS',valueDate,None,[usdOisItem,usdCreditCurveItem])
    creditCurve = market['USDCreditSwap']
    df = creditCurve.points['survival_probability'].round(5)
    np.testing.assert_array_equal(df,expected)



