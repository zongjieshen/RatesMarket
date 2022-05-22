import pytest
import numpy as np
import pandas as pd
import market as mkt
valueDate = pd.to_datetime('31/12/2021',format = '%d/%m/%Y')

def test_schedule():
   expected = np.rec.array([('2021-12-31', '2022-06-30', '2022-06-30', 0., 0.),
           ('2022-06-30', '2022-12-30', '2022-12-30', 0., 0.),
           ('2022-12-30', '2023-06-30', '2023-06-30', 0., 0.),
           ('2023-06-30', '2023-12-29', '2023-12-29', 0., 0.),
           ('2023-12-29', '2024-06-28', '2024-06-28', 0., 0.),
           ('2024-06-28', '2024-12-30', '2024-12-30', 0., 0.),
           ('2024-12-30', '2025-06-30', '2025-06-30', 0., 0.),
           ('2025-06-30', '2025-12-31', '2025-12-31', 0., 0.)],
          dtype=[('accrual_start', '<M8[D]'), ('accrual_end', '<M8[D]'), 
                 ('payment_date', '<M8[D]'), ('cashflow', '<f8'), ('PV', '<f8')])
   
   maturity = pd.to_datetime('31/12/2025',format = '%d/%m/%Y')
   period = '6m'
   dateAdj = mkt.DateAdjuster('modified following','SYD') 
   schedule = mkt.Schedule(valueDate,maturity,period,dateAdj)
   schedule._create_schedule()
   np.testing.assert_array_equal(schedule.periods,expected)

@pytest.mark.parametrize("test_input,expected", [(np.datetime64(valueDate), valueDate), 
                                                 (44561, valueDate), 
                                                 ('t+2b', pd.to_datetime('2022-01-04')),
                                                 ('t+12y+2b', pd.to_datetime('2034-01-03')),
                                                 (['t+12y+2b','t+13y+3b'], [pd.to_datetime('2034-01-03'),pd.to_datetime('2035-01-03')])
                                                 ])
def test_date_convert(test_input,expected):
   assert mkt.ScheduleDefinition.DateConvert(test_input, valueDate) == expected