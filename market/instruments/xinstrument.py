from market.instruments import Deposit, Bond, Swap
from market.pillars import DepositRate, BondQuote, SwapRate

def ToAssets(pillar,curve, notional):
    if isinstance(pillar,DepositRate):
        return Deposit(pillar,curve, None,notional)
    elif isinstance(pillar,BondQuote):
        return Bond(pillar,curve, None,notional)
    elif isinstance(pillar,SwapRate):
        return Swap(pillar,curve, None,notional)
    else:
        raise Exception(f'{typeof(pillar)} cannot be converted to asset')