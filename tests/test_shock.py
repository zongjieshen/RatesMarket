import pytest
import numpy as np
import pandas as pd
import market as mkt

valueDate = pd.to_datetime('31/12/2021',format = '%d/%m/%Y')

def test_zero_shock():
    expected = np.array([1.     , 0.99998, 0.99994, 0.99981, 0.99889, 0.99598, 0.98177,
       0.96178, 0.93936, 0.91924, 0.89872, 0.87777, 0.85734, 0.83734,
       0.81743, 0.77872, 0.72407, 0.64743, 0.58883, 0.54279, 0.36065])
    
    audSwap = mkt.YieldCurve('AUDSwap',valueDate, 'AUD',[])
    audSwap.points = np.array([('2021-12-31', 1.6409088e+09,  0.00000000e+00),
       ('2022-02-04', 1.6439328e+09, -1.43834700e-05),
       ('2022-03-04', 1.6463520e+09, -4.31854280e-05),
       ('2022-04-04', 1.6490304e+09, -1.68561400e-04),
       ('2022-07-04', 1.6568928e+09, -1.05980980e-03),
       ('2023-01-04', 1.6727904e+09, -3.92280107e-03),
       ('2024-01-04', 1.7043264e+09, -1.82009611e-02),
       ('2025-01-06', 1.7361216e+09, -3.86632868e-02),
       ('2026-01-05', 1.7675712e+09, -6.21591602e-02),
       ('2027-01-04', 1.7990208e+09, -8.37090091e-02),
       ('2028-01-04', 1.8305568e+09, -1.06185209e-01),
       ('2029-01-04', 1.8621792e+09, -1.29672580e-01),
       ('2030-01-04', 1.8937152e+09, -1.53121889e-01),
       ('2031-01-06', 1.9254240e+09, -1.76619195e-01),
       ('2032-01-05', 1.9568736e+09, -2.00593032e-01),
       ('2034-01-04', 2.0199456e+09, -2.48904132e-01),
       ('2037-01-05', 2.1147264e+09, -3.21366318e-01),
       ('2042-01-06', 2.2725792e+09, -4.32741024e-01),
       ('2047-01-04', 2.4301728e+09, -5.27113098e-01),
       ('2052-01-04', 2.5879392e+09, -6.08042546e-01),
       ('2072-01-04', 3.2190912e+09, -1.01484653e+00)],
      dtype=[('maturity', '<M8[D]'), ('timestamp', '<f8'), ('discount_factor', '<f8')])

    audswapZeroShocked = audSwap.CreateShockedCurve('zero',shockAmount = 0.0001)
    df = np.exp(audswapZeroShocked.points['discount_factor']).round(5)
    np.testing.assert_array_equal(df,expected)

def test_fwd_shock():
    expected = np.array([0.37764, 0.3757 , 0.37381, 0.37191, 0.37   , 0.3681 , 0.36625,
       0.36439, 0.36252, 0.36066])
    
    audSwap = mkt.YieldCurve('AUDSwap',valueDate, 'AUD',[])
    audSwap.points = np.array([('2021-12-31', 1.6409088e+09,  0.00000000e+00),
       ('2022-02-04', 1.6439328e+09, -1.43834700e-05),
       ('2022-03-04', 1.6463520e+09, -4.31854280e-05),
       ('2022-04-04', 1.6490304e+09, -1.68561400e-04),
       ('2022-07-04', 1.6568928e+09, -1.05980980e-03),
       ('2023-01-04', 1.6727904e+09, -3.92280107e-03),
       ('2024-01-04', 1.7043264e+09, -1.82009611e-02),
       ('2025-01-06', 1.7361216e+09, -3.86632868e-02),
       ('2026-01-05', 1.7675712e+09, -6.21591602e-02),
       ('2027-01-04', 1.7990208e+09, -8.37090091e-02),
       ('2028-01-04', 1.8305568e+09, -1.06185209e-01),
       ('2029-01-04', 1.8621792e+09, -1.29672580e-01),
       ('2030-01-04', 1.8937152e+09, -1.53121889e-01),
       ('2031-01-06', 1.9254240e+09, -1.76619195e-01),
       ('2032-01-05', 1.9568736e+09, -2.00593032e-01),
       ('2034-01-04', 2.0199456e+09, -2.48904132e-01),
       ('2037-01-05', 2.1147264e+09, -3.21366318e-01),
       ('2042-01-06', 2.2725792e+09, -4.32741024e-01),
       ('2047-01-04', 2.4301728e+09, -5.27113098e-01),
       ('2052-01-04', 2.5879392e+09, -6.08042546e-01),
       ('2072-01-04', 3.2190912e+09, -1.01484653e+00)],
      dtype=[('maturity', '<M8[D]'), ('timestamp', '<f8'), ('discount_factor', '<f8')])

    audswapFwdShocked = audSwap.CreateShockedCurve('foward',shockAmount = 0.0001, period = '3m', yearBasis = 'acton365f')
    df = np.exp(audswapFwdShocked.points['discount_factor']).round(5)[-10:]
    np.testing.assert_array_equal(df,expected)

def test_pillar_shock():
   expected = np.array([1.     , 0.99998, 0.99994, 0.99981, 0.99889, 0.99598, 0.98177,
       0.96178, 0.93936, 0.91924, 0.89872, 0.87777, 0.85734, 0.83734,
       0.81742, 0.77871, 0.72406, 0.64742, 0.58884, 0.54281, 0.36067])

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
            mkt.SwapRate('2022-01-04', '2030-01-04', 'AUD', 'AUDSwap8Y', 'linear', 'acton365f', 0.01899, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2031-01-06', 'AUD', 'AUDSwap9Y', 'linear', 'acton365f', 0.01945, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2032-01-05', 'AUD', 'AUDSwap10Y', 'linear', 'acton365f', 0.019875, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2034-01-04', 'AUD', 'AUDSwap12Y', 'linear', 'acton365f', 0.02053, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2037-01-05', 'AUD', 'AUDSwap15Y', 'linear', 'acton365f', 0.021175, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2042-01-06', 'AUD', 'AUDSwap20Y', 'linear', 'acton365f', 0.021425, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2047-01-04', 'AUD', 'AUDSwap25Y', 'linear', 'acton365f', 0.0210375, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2052-01-04', 'AUD', 'AUDSwap30Y', 'linear', 'acton365f', 0.02043, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2072-01-04', 'AUD', 'AUDSwap50Y', 'linear', 'acton365f', 0.02043, 'semiannual', 'SYD', 'Zero', '0d')]

   audSwap = mkt.YieldCurve('AUDSwap',valueDate, 'AUD',pillars)
   audswapPillarShocked = audSwap.CreateShockedCurve('pillar',shockAmount = 0.0001)
   df = np.exp(audswapPillarShocked.points['discount_factor']).round(5)
   np.testing.assert_array_equal(df,expected)

def test_Dv01AtEachpillar():
   expected = np.array([['AUDBILL1M', -9.58899],['AUDBILL2M', -17.25984],['AUDBILL3M', -25.74989],['AUDBILL6M', -50.6349],
                     ['AUDSwap1Y', -99.81438],['AUDSwap2Y', -198.55485],['AUDSwap3Y', -296.32769],['AUDSwap4Y', -390.15254],
                     ['AUDSwap5Y', -482.41084],['AUDSwap6Y', -572.89699],['AUDSwap7Y', -661.55625],['AUDSwap8Y', -747.93193],
                     ['AUDSwap9Y', -832.77359],['AUDSwap10Y', -914.94653],['AUDSwap12Y', -1073.92223],['AUDSwap15Y', -1298.90635],
                     ['AUDSwap20Y', -1641.09904],['AUDSwap25Y', -1949.7023],['AUDSwap30Y', -2233.01378],['AUDSwap50Y', -3127.13758]], dtype=object)

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
            mkt.SwapRate('2022-01-04', '2030-01-04', 'AUD', 'AUDSwap8Y', 'linear', 'acton365f', 0.01899, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2031-01-06', 'AUD', 'AUDSwap9Y', 'linear', 'acton365f', 0.01945, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2032-01-05', 'AUD', 'AUDSwap10Y', 'linear', 'acton365f', 0.019875, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2034-01-04', 'AUD', 'AUDSwap12Y', 'linear', 'acton365f', 0.02053, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2037-01-05', 'AUD', 'AUDSwap15Y', 'linear', 'acton365f', 0.021175, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2042-01-06', 'AUD', 'AUDSwap20Y', 'linear', 'acton365f', 0.021425, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2047-01-04', 'AUD', 'AUDSwap25Y', 'linear', 'acton365f', 0.0210375, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2052-01-04', 'AUD', 'AUDSwap30Y', 'linear', 'acton365f', 0.02043, 'semiannual', 'SYD', 'Zero', '0d'),
            mkt.SwapRate('2022-01-04', '2072-01-04', 'AUD', 'AUDSwap50Y', 'linear', 'acton365f', 0.02043, 'semiannual', 'SYD', 'Zero', '0d')]

   audSwap = mkt.YieldCurve('AUDSwap',valueDate, 'AUD',pillars)
   audSwap.Build()
   dv01 = audSwap.Dv01AtEachpillar('pillar').round(5).to_numpy()
   np.testing.assert_array_equal(dv01,expected)


