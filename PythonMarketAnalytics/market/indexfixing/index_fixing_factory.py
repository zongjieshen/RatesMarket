import numpy as np
import datetime
from market.indexfixing.index_fixing import *
from market.pillars import *

class IndexFixingFactory:
    """Factory to add cpi factor to the index fixing class"""

    @staticmethod
    def Creat(dataFrame, itemToBuild, valueDate, build: bool):
        label = itemToBuild.label
        if dataFrame.empty:
            raise Exception('DataFrame is empty')
        ccy = itemToBuild.ccy
        filters = itemToBuild.filters
        data = dataFrame.query(filters)
        if data.empty:
            raise Exception('Failed to retrieve curve date')
        return IndexFixingFactory._ifCreate(data, label, ccy)

    def _ifCreate(df, key, ccy):
        pillars = []
        for index, row in df.iterrows():
            pillar = FixingRate.fromRow(row)
            pillars.append(pillar)
            #Throw error if duplicate maturity pillars
            for pillar in pillars:
                if sum(p.maturityDate == pillar.maturityDate for p in pillars) > 1:
                    raise Exception(f'{pillar.label} {pillar.maturityDate} has another pillar having the same maturity')

        return IndexFixing(key,ccy,pillars)



