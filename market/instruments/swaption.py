from market.instruments import *
from market.instruments.options import Option
import numpy as np
from scipy.stats import norm

class Swaption(Option):
    def __init__(self, quote, curve, market=None, notional=1):
        super(Swaption, self).__init__(quote, curve, market, notional)
        self.subType = 'vanilla'
        self.underlyingSwap = quote.underlyingSwap
        self.exerciseType = quote.exerciseType  # 'european' or 'bermudan'
        
        # Create the underlying swap schedule
        self.swapSchedule = Schedule(self.expiryDate, self.maturity,
                                    quote.paymentFrequency, self.dateAdjuster)
        self.swapSchedule._create_schedule()
        
        # Model parameters
        self.model_type = quote.model_type if hasattr(quote, 'model_type') else 'black'
        self.model = self._create_model()
        
    def _create_model(self):
        """Create the appropriate pricing model based on model_type."""
        if self.model_type.lower() == 'g2pp':
            return G2ppSwaptionModel(self)
        else:  # Default to Black model
            return BlackSwaptionModel(self)
        
    def SolveDf(self):
        yearFraction = ScheduleDefinition.YearFraction(self.startDate, self.maturity, self.yearBasis)
        rateConvention = RateConvention(self.rateConvention, yearFraction)
        guess = rateConvention.RateToDf(self.rate)
        return scipy.optimize.newton(self._objectiveFunction, guess)
    
    def _objectiveFunction(self, guess):
        if not isinstance(guess, (int, float, complex)):
            guess = guess[0]

        temp_curve, discountCurve = self._copy(guess)
        return self.Valuation(temp_curve, discountCurve)
    
    def Valuation(self, projectCurve, discountCurve):
        return self.model.price(projectCurve, discountCurve)


class SwaptionModel:
    """Base class for swaption pricing models."""
    def __init__(self, swaption):
        self.swaption = swaption
    
    @abc.abstractmethod
    def price(self, projectCurve, discountCurve):
        """Price the swaption using the model."""
        return NotImplementedError
    
    def _create_underlying_swap(self, projectCurve, discountCurve):
        """Create a swap object that represents the underlying swap."""
        return {
            'rate': self.swaption.strike,
            'schedule': self.swaption.swapSchedule,
            'notional': self.swaption.notional,
            'ccy': self.swaption.ccy,
            'yearBasis': self.swaption.yearBasis
        }
    
    def _get_periods(self, swap):
        """Get the period information from the swap schedule."""
        periodStart = swap['schedule'].periods['accrual_start']
        periodEnd = swap['schedule'].periods['accrual_end']
        accural_periods = ScheduleDefinition.YearFractionList(periodStart, periodEnd, swap['yearBasis'])
        return periodStart, periodEnd, accural_periods
    
    def _calculate_forward_rate(self, swap, projectCurve, discountCurve):
        """Calculate the forward swap rate."""
        periodStart, periodEnd, accural_periods = self._get_periods(swap)
        
        # Calculate PV01 of the fixed leg
        pv01 = 0
        for i in range(len(periodStart)):
            df = discountCurve.DiscountFactor(periodEnd[i])
            pv01 += df * accural_periods[i]
        
        # Calculate the floating leg PV
        floating_pv = 0
        for i in range(len(periodStart)):
            df_start = projectCurve.DiscountFactor(periodStart[i])
            df_end = projectCurve.DiscountFactor(periodEnd[i])
            fwd = (df_start / df_end - 1)
            df_payment = discountCurve.DiscountFactor(periodEnd[i])
            floating_pv += fwd * df_payment * self.swaption.notional
        
        # Forward rate = floating leg PV / PV01
        return floating_pv / (pv01 * self.swaption.notional)


class BlackSwaptionModel(SwaptionModel):
    """Black model for swaption pricing."""
    
    def price(self, projectCurve, discountCurve):
        # Get the forward swap rate
        swap = self._create_underlying_swap(projectCurve, discountCurve)
        forward_rate = self._calculate_forward_rate(swap, projectCurve, discountCurve)
        
        # Calculate the option value using Black's formula
        if self.swaption.exerciseType.lower() == 'european':
            return self._black_formula(forward_rate, projectCurve, discountCurve)
        elif self.swaption.exerciseType.lower() == 'bermudan':
            # For Bermudan swaptions, a more complex model would be needed
            # This is a simplified placeholder
            return self._black_formula(forward_rate, projectCurve, discountCurve) * 1.1
        else:
            raise ValueError(f"Unknown exercise type: {self.swaption.exerciseType}")
    
    def _black_formula(self, forward_rate, projectCurve, discountCurve):
        """Implement Black's formula for swaption pricing."""
        strike = self.swaption.strike
        vol = self.swaption.volatility
        expiry = self.swaption.expiryDate
        
        # Calculate time to expiry in years
        today = self.swaption.startDate
        t = ScheduleDefinition.YearFraction(today, expiry, self.swaption.yearBasis)
        
        # Calculate d1 and d2
        if vol * np.sqrt(t) > 0:
            d1 = (np.log(forward_rate / strike) + 0.5 * vol**2 * t) / (vol * np.sqrt(t))
            d2 = d1 - vol * np.sqrt(t)
        else:
            # Handle the case where vol or t is zero
            if forward_rate > strike:
                d1 = float('inf')
                d2 = float('inf')
            else:
                d1 = float('-inf')
                d2 = float('-inf')
        
        # Get the discount factor to the expiry date
        df = discountCurve.DiscountFactor(expiry)
        
        # Calculate the underlying swap's annuity
        swap = self._create_underlying_swap(projectCurve, discountCurve)
        _, _, accural_periods = self._get_periods(swap)
        annuity = sum(accural_periods) * self.swaption.notional
        
        # Calculate the option price based on option type
        if self.swaption.optionType.lower() == 'call':
            return df * annuity * (forward_rate * norm.cdf(d1) - strike * norm.cdf(d2))
        elif self.swaption.optionType.lower() == 'put':
            return df * annuity * (strike * norm.cdf(-d2) - forward_rate * norm.cdf(-d1))
        else:
            raise ValueError(f"Unknown option type: {self.swaption.optionType}")


class G2ppSwaptionModel(SwaptionModel):
    """G2++ model for swaption pricing using Monte Carlo simulation."""
    
    def price(self, projectCurve, discountCurve):
        # Check if we have a G2++ model in the market
        if not hasattr(self.swaption.market, 'g2pp_model'):
            raise ValueError("G2++ model not found in market. Please add a G2++ model before pricing with this model.")
        
        g2pp_model = self.swaption.market.g2pp_model
        
        # Ensure the G2++ model is built
        if not g2pp_model._built:
            g2pp_model.Build(self.swaption.market)
        
        # Get the expiry time in years
        expiry_time = ScheduleDefinition.YearFraction(
            self.swaption.startDate, self.swaption.expiryDate, self.swaption.yearBasis)
        
        # Get the swap schedule times
        swap = self._create_underlying_swap(projectCurve, discountCurve)
        periodStart, periodEnd, accural_periods = self._get_periods(swap)
        
        # Convert dates to simulation times (years from valuation date)
        sim_times = [0.0]  # Start with t=0
        sim_times.append(expiry_time)  # Add expiry time
        
        # Add all payment dates of the underlying swap
        for date in periodEnd:
            time = ScheduleDefinition.YearFraction(
                self.swaption.startDate, date, self.swaption.yearBasis)
            if time > expiry_time and time not in sim_times:
                sim_times.append(time)
        
        # Sort the simulation times
        sim_times.sort()
        
        # Simulate paths
        n_paths = 1000  # Number of simulation paths
        paths = g2pp_model.simulate_paths(np.array(sim_times), n_paths)
        
        # Find the index of the expiry time
        expiry_idx = sim_times.index(expiry_time)
        
        # Price the swaption using Monte Carlo
        return self._monte_carlo_price(paths, expiry_idx, projectCurve, discountCurve)
    
    def _monte_carlo_price(self, paths, expiry_idx, projectCurve, discountCurve):
        """Price the swaption using Monte Carlo simulation."""
        # Get the underlying swap details
        swap = self._create_underlying_swap(projectCurve, discountCurve)
        strike = self.swaption.strike
        
        # Get the swap schedule
        periodStart, periodEnd, accural_periods = self._get_periods(swap)
        
        # Calculate the swap value at expiry for each path
        n_paths = paths['r'].shape[0]
        swap_values = np.zeros(n_paths)
        
        for i in range(len(periodStart)):
            # Skip periods that start before expiry
            if periodStart[i] <= self.swaption.expiryDate:
                continue
            
            # Find the indices in the simulation times
            start_time = ScheduleDefinition.YearFraction(
                self.swaption.startDate, periodStart[i], self.swaption.yearBasis)
            end_time = ScheduleDefinition.YearFraction(
                self.swaption.startDate, periodEnd[i], self.swaption.yearBasis)
            
            start_idx = np.searchsorted(paths['times'], start_time)
            end_idx = np.searchsorted(paths['times'], end_time)
            
            # Calculate discount factors for this period
            df_start = self.swaption.market.g2pp_model.discount_factor_simulation(
                paths, expiry_idx, start_idx)
            df_end = self.swaption.market.g2pp_model.discount_factor_simulation(
                paths, expiry_idx, end_idx)
            
            # Calculate forward rate for this period
            fwd_rate = (df_start / df_end - 1) / accural_periods[i]
            
            # Fixed leg contribution
            fixed_cf = strike * accural_periods[i] * self.swaption.notional
            swap_values -= fixed_cf * df_end
            
            # Floating leg contribution
            float_cf = fwd_rate * accural_periods[i] * self.swaption.notional
            swap_values += float_cf * df_end
        
        # Add the notional exchange at maturity if applicable
        if self.swaption.notional != 0:
            maturity_time = ScheduleDefinition.YearFraction(
                self.swaption.startDate, self.swaption.maturity, self.swaption.yearBasis)
            maturity_idx = np.searchsorted(paths['times'], maturity_time)
            
            df_maturity = self.swaption.market.g2pp_model.discount_factor_simulation(
                paths, expiry_idx, maturity_idx)
            
            # No net notional exchange for standard swaps, but included for completeness
            swap_values += 0 * df_maturity
        
        # Apply the option payoff
        if self.swaption.optionType.lower() == 'call':
            payoffs = np.maximum(swap_values, 0)
        elif self.swaption.optionType.lower() == 'put':
            payoffs = np.maximum(-swap_values, 0)
        else:
            raise ValueError(f"Unknown option type: {self.swaption.optionType}")
        
        # Discount the payoffs to the valuation date
        df_expiry = discountCurve.DiscountFactor(self.swaption.expiryDate)
        present_value = df_expiry * np.mean(payoffs)
        
        return present_value