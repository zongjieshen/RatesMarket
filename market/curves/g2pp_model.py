from market.curves.curve_base import *
import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

class G2ppModel(Curve):
    """G2++ (Two-Factor Gaussian) interest rate model implementation.
    
    The G2++ model is a two-factor short-rate model where the short rate is given by:
    r(t) = x(t) + y(t) + phi(t)
    
    where x and y follow the SDEs:
    dx(t) = -a*x(t)*dt + sigma*dW1(t)
    dy(t) = -b*y(t)*dt + eta*dW2(t)
    
    with dW1(t) and dW2(t) being Brownian motions with correlation rho.
    
    phi(t) is a deterministic function chosen to fit the initial yield curve.
    """
    
    def __init__(self, key, valueDate, ccy, yieldCurve, **kwargs):
        super(G2ppModel, self).__init__(key, ccy, valueDate, **kwargs)
        
        # Reference to the yield curve for calibration
        self.yieldCurve = yieldCurve
        
        # Model parameters
        self.a = kwargs.get('a', 0.1)  # Mean reversion speed for first factor
        self.b = kwargs.get('b', 0.3)  # Mean reversion speed for second factor
        self.sigma = kwargs.get('sigma', 0.01)  # Volatility of first factor
        self.eta = kwargs.get('eta', 0.01)  # Volatility of second factor
        self.rho = kwargs.get('rho', -0.5)  # Correlation between factors
        
        # Calibration targets
        self.calibration_expiries = []  # List of expiry dates for calibration
        self.calibration_tenors = []    # List of underlying swap tenors
        self.calibration_vols = []      # List of market volatilities
        
        # Phi(t) function values - will be populated during calibration
        self.phi_times = []
        self.phi_values = []
        
        self._built = False
    
    def Build(self, market=None):
        """Build the G2++ model by calibrating to market data."""
        # First ensure the yield curve is built
        if not self.yieldCurve._built:
            self.yieldCurve.Build(market)
        
        # Fit the phi function to match the initial yield curve
        self._fit_phi_function()
        
        # If we have calibration targets, calibrate the model parameters
        if len(self.calibration_expiries) > 0:
            self._calibrate_to_swaption_vols(market)
        
        self._built = True
    
    def _fit_phi_function(self):
        """Fit the phi function to match the initial yield curve."""
        # Get a set of times to fit phi at
        times = np.linspace(0, 30, 61)  # 0 to 30 years in 0.5 year steps
        
        # Calculate phi values to match the yield curve
        phi_values = []
        for t in times:
            if t == 0:
                phi_values.append(self.yieldCurve.ZeroRates([self.valueDate]).iloc[0, 0])
            else:
                date = self.valueDate + datetime.timedelta(days=int(t*365))
                zero_rate = self.yieldCurve.ZeroRates([date]).iloc[0, 0]
                
                # Calculate the model-implied zero rate without phi
                model_rate = self._zero_rate_without_phi(t)
                
                # Phi is the difference
                phi_values.append(zero_rate - model_rate)
        
        self.phi_times = times
        self.phi_values = phi_values
    
    def _zero_rate_without_phi(self, t):
        """Calculate the zero rate at time t without the phi adjustment."""
        # In the G2++ model, this is the contribution from the x and y processes
        # For t=0, this is 0 since x(0) = y(0) = 0
        return 0.0
    
    def _calibrate_to_swaption_vols(self, market):
        """Calibrate the model parameters to match market swaption volatilities."""
        # Define the objective function for calibration
        def objective(params):
            # Unpack parameters
            self.a, self.b, self.sigma, self.eta, self.rho = params
            
            # Ensure parameters are within valid ranges
            if self.a <= 0 or self.b <= 0 or self.sigma <= 0 or self.eta <= 0 or self.rho <= -1 or self.rho >= 1:
                return 1e10  # Return a large value for invalid parameters
            
            # Calculate model-implied volatilities
            model_vols = []
            for i in range(len(self.calibration_expiries)):
                expiry = self.calibration_expiries[i]
                tenor = self.calibration_tenors[i]
                
                # Calculate time to expiry in years
                t_expiry = ScheduleDefinition.YearFraction(self.valueDate, expiry, 'act/365')
                
                # Calculate tenor in years
                end_date = expiry + ScheduleDefinition._parseDate(tenor)
                t_tenor = ScheduleDefinition.YearFraction(expiry, end_date, 'act/365')
                
                # Get the model-implied volatility
                model_vol = self._swaption_implied_vol(t_expiry, t_tenor)
                model_vols.append(model_vol)
            
            # Calculate the sum of squared errors
            errors = np.array(model_vols) - np.array(self.calibration_vols)
            return np.sum(errors**2)
        
        # Initial parameters [a, b, sigma, eta, rho]
        initial_params = [self.a, self.b, self.sigma, self.eta, self.rho]
        
        # Parameter bounds
        bounds = [(0.001, 1.0), (0.001, 1.0), (0.0001, 0.1), (0.0001, 0.1), (-0.999, 0.999)]
        
        # Run the optimization
        result = minimize(objective, initial_params, bounds=bounds, method='L-BFGS-B')
        
        # Update the model parameters with the calibrated values
        self.a, self.b, self.sigma, self.eta, self.rho = result.x
    
    def _swaption_implied_vol(self, t_expiry, t_tenor):
        """Calculate the model-implied Black volatility for a swaption."""
        # Calculate the G2++ model variance for the given expiry and tenor
        variance = self._calculate_swap_rate_variance(t_expiry, t_tenor)
        
        # Convert to Black volatility
        return np.sqrt(variance / t_expiry)
    
    def _calculate_swap_rate_variance(self, t_expiry, t_tenor):
        """Calculate the variance of the swap rate under the G2++ model."""
        # This is a simplified implementation
        # In a full implementation, we would need to calculate the impact of
        # the G2++ model on the swap rate distribution
        
        # For now, use a simplified formula based on the model parameters
        # This is an approximation and should be replaced with the actual formula
        # from the G2++ model literature
        
        # Simplified variance calculation
        var_x = (self.sigma**2 / (2 * self.a)) * (1 - np.exp(-2 * self.a * t_expiry))
        var_y = (self.eta**2 / (2 * self.b)) * (1 - np.exp(-2 * self.b * t_expiry))
        cov_xy = (self.rho * self.sigma * self.eta / (self.a + self.b)) * (1 - np.exp(-(self.a + self.b) * t_expiry))
        
        # Apply a tenor adjustment (simplified)
        tenor_factor = 1 - np.exp(-0.05 * t_tenor)
        
        return (var_x + var_y + 2 * cov_xy) * tenor_factor
    
    def simulate_paths(self, times, n_paths, seed=None):
        """Simulate paths of the short rate under the G2++ model.
        
        Args:
            times: Array of times at which to simulate the paths
            n_paths: Number of paths to simulate
            seed: Random seed for reproducibility
            
        Returns:
            Dictionary containing the simulated paths for r, x, and y
        """
        if seed is not None:
            np.random.seed(seed)
        
        dt = times[1] - times[0]  # Assuming uniform time steps
        n_steps = len(times)
        
        # Initialize arrays for the factors and short rate
        x = np.zeros((n_paths, n_steps))
        y = np.zeros((n_paths, n_steps))
        r = np.zeros((n_paths, n_steps))
        
        # Generate correlated Brownian motions
        dW1 = np.random.normal(0, np.sqrt(dt), (n_paths, n_steps-1))
        dW2 = self.rho * dW1 + np.sqrt(1 - self.rho**2) * np.random.normal(0, np.sqrt(dt), (n_paths, n_steps-1))
        
        # Simulate the paths
        for i in range(1, n_steps):
            t = times[i]
            
            # Update x and y using the Euler-Maruyama method
            x[:, i] = x[:, i-1] * np.exp(-self.a * dt) + self.sigma * np.sqrt((1 - np.exp(-2 * self.a * dt)) / (2 * self.a)) * dW1[:, i-1]
            y[:, i] = y[:, i-1] * np.exp(-self.b * dt) + self.eta * np.sqrt((1 - np.exp(-2 * self.b * dt)) / (2 * self.b)) * dW2[:, i-1]
            
            # Get phi(t) by interpolation
            phi_t = np.interp(t, self.phi_times, self.phi_values)
            
            # Calculate r(t) = x(t) + y(t) + phi(t)
            r[:, i] = x[:, i] + y[:, i] + phi_t
        
        return {
            'times': times,
            'r': r,
            'x': x,
            'y': y
        }
    
    def discount_factor_t0(self, t):
        """Calculate the discount factor P(0,t) from the yield curve."""
        if isinstance(t, (int, float)):
            date = self.valueDate + datetime.timedelta(days=int(t*365))
            return self.yieldCurve.DiscountFactor(date)[0]
        else:
            dates = [self.valueDate + datetime.timedelta(days=int(ti*365)) for ti in t]
            return self.yieldCurve.DiscountFactor(dates)
    
    def discount_factor_simulation(self, paths, s, t):
        """Calculate discount factors P(s,t) for all simulated paths.
        
        Args:
            paths: Dictionary of simulated paths from simulate_paths
            s: Start time index
            t: End time index
            
        Returns:
            Array of discount factors for each path
        """
        times = paths['times']
        r = paths['r']
        
        # Calculate the integral of r from s to t for each path
        # Using trapezoidal rule for integration
        dt = times[1] - times[0]
        integral = np.zeros(r.shape[0])
        
        for i in range(s, t):
            integral += 0.5 * (r[:, i] + r[:, i+1]) * dt
        
        # Return the discount factors
        return np.exp(-integral)
    
    def add_calibration_target(self, expiry, tenor, volatility):
        """Add a swaption volatility as a calibration target.
        
        Args:
            expiry: Expiry date of the swaption
            tenor: Tenor of the underlying swap (e.g., '5Y')
            volatility: Market Black volatility
        """
        self.calibration_expiries.append(expiry)
        self.calibration_tenors.append(tenor)
        self.calibration_vols.append(volatility)