import Market as mkt
import pandas as pd

class IndexFixing():
    def __init__(self, key, ccy, pillars):
        self.key = key
        self.ccy = ccy
        self.discountCurve = self.key #Add this to ensure the market check doesnt fail
        self.spreadCurve = self.key

        pillars.sort(key=lambda r:r.maturityDate)
        self.pillars = pillars
        
    def Build(self,market=None):
        # No boostrap required
        self._built = True

    def LastFixing(self):
        return self.pillars[-1]

    def Fixing(self,date):
        #Ensure we are comparing timestamp with timestamp
        date = pd.to_datetime(date)
        fixing =  next((x for x in self.pillars if x.maturityDate == date), None)
        if fixing is not None:
            return fixing.value
        else:
            raise Exception(f'Could not find the fixing for index {self.key} at date {date}')