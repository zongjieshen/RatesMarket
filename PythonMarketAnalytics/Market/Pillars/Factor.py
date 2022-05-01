import Market.Dates as Dates
#base class
class Factor():
    def __init__(self, maturityDate, value):
        self.maturityDate = maturityDate
        self.value = value
#Discount Factor
class DiscountFactorRate(Factor):
    def __init__(self, *args, **kwargs):
        super(DiscountFactorRate, self).__init__(*args, **kwargs)
        self.quoteType = 'DiscountFactor'

class FixingRate(Factor):
    def __init__(self, *args, **kwargs):
        super(FixingRate, self).__init__(*args, **kwargs)
        self.quoteType = 'IndexFixing'

    @classmethod
    def fromRow(cls, row):
        Date = Dates.ScheduleDefinition.DateConvert(row["Date"])
        value = row["Value"]
        return cls(Date, value)

