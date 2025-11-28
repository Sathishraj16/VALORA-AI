"""
VALORA Economic Simulation Engine
Differential equation-based macroeconomic dynamics with real-world modeling

Mathematical Foundation:
- IS-LM-AS/AD Framework with Dynamic Extensions
- Phillips Curve with Expectations
- Solow Growth Model Components
- Financial Accelerator Mechanisms
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from enum import Enum
import math
from scipy.integrate import odeint
from scipy.optimize import fsolve
import logging

logger = logging.getLogger(__name__)


class BusinessCyclePhase(Enum):
    """Economic cycle phases"""
    EXPANSION = "expansion"
    PEAK = "peak"
    RECESSION = "recession"
    TROUGH = "trough"


class Sector(Enum):
    """Economic sectors for GDP decomposition"""
    AGRICULTURE = "agriculture"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    GOVERNMENT = "government"
    CONSTRUCTION = "construction"
    ENERGY = "energy"


@dataclass
class MacroState:
    """Complete macroeconomic state vector"""
    # Core indicators
    gdp: float = 1_000_000.0
    gdp_growth: float = 0.025
    potential_gdp: float = 1_000_000.0
    output_gap: float = 0.0
    
    # Prices
    inflation: float = 0.02
    expected_inflation: float = 0.02
    core_inflation: float = 0.02
    price_level: float = 100.0
    
    # Labor market
    unemployment: float = 0.05
    natural_unemployment: float = 0.045
    labor_force: float = 100_000.0
    employment: float = 95_000.0
    wage_growth: float = 0.03
    
    # Monetary
    interest_rate: float = 0.05
    real_interest_rate: float = 0.03
    money_supply: float = 500_000.0
    velocity_of_money: float = 2.0
    
    # Fiscal
    government_spending: float = 200_000.0
    tax_revenue: float = 180_000.0
    tax_rate: float = 0.25
    fiscal_deficit: float = 20_000.0
    public_debt: float = 500_000.0
    debt_to_gdp: float = 0.5
    
    # Financial sector
    credit_supply: float = 400_000.0
    credit_demand: float = 380_000.0
    bank_reserves: float = 50_000.0
    reserve_ratio: float = 0.1
    loan_default_rate: float = 0.02
    
    # Consumer/Business
    consumer_confidence: float = 100.0
    business_confidence: float = 100.0
    consumption: float = 600_000.0
    investment: float = 200_000.0
    savings_rate: float = 0.15
    
    # External
    exports: float = 100_000.0
    imports: float = 100_000.0
    trade_balance: float = 0.0
    exchange_rate: float = 1.0
    
    # Sectoral GDP
    sector_gdp: Dict[str, float] = field(default_factory=lambda: {
        Sector.AGRICULTURE.value: 50_000.0,
        Sector.MANUFACTURING.value: 200_000.0,
        Sector.SERVICES.value: 400_000.0,
        Sector.TECHNOLOGY.value: 150_000.0,
        Sector.FINANCE.value: 100_000.0,
        Sector.GOVERNMENT.value: 50_000.0,
        Sector.CONSTRUCTION.value: 30_000.0,
        Sector.ENERGY.value: 20_000.0,
    })
    
    # Cycle tracking
    cycle_phase: BusinessCyclePhase = BusinessCyclePhase.EXPANSION
    cycle_duration: int = 0
    
    # Time
    tick: int = 0
    timestamp: float = 0.0


@dataclass
class PolicyAction:
    """Government/Central Bank policy intervention"""
    policy_type: str  # "monetary", "fiscal", "regulatory"
    parameter: str
    old_value: float
    new_value: float
    timestamp: float
    duration: Optional[int] = None  # ticks for temporary policies
    decay_rate: float = 0.0


@dataclass
class EconomicShock:
    """External or internal economic shock"""
    shock_type: str  # "supply", "demand", "financial", "policy", "external"
    name: str
    magnitude: float  # -1.0 to 1.0, negative = adverse
    affected_sectors: List[str] = field(default_factory=list)
    duration: int = 1
    decay_rate: float = 0.1
    current_intensity: float = 1.0
    tick_applied: int = 0


class EconomicParameters:
    """Model calibration parameters based on empirical research"""
    
    # Phillips Curve parameters
    PHILLIPS_SLOPE: float = 0.3  # Inflation sensitivity to output gap
    INFLATION_PERSISTENCE: float = 0.7  # Autoregressive component
    EXPECTATIONS_WEIGHT: float = 0.5  # Forward-looking weight
    
    # Okun's Law
    OKUN_COEFFICIENT: float = 2.0  # % GDP change per 1% unemployment change
    
    # IS Curve (Demand)
    IS_INTEREST_SENSITIVITY: float = 0.5  # Output gap sensitivity to real rate
    IS_FISCAL_MULTIPLIER: float = 1.5  # Government spending multiplier
    IS_CONFIDENCE_WEIGHT: float = 0.2  # Consumer confidence impact
    
    # Taylor Rule
    TAYLOR_INFLATION_WEIGHT: float = 1.5
    TAYLOR_OUTPUT_WEIGHT: float = 0.5
    NEUTRAL_RATE: float = 0.03
    
    # Consumption function (Keynesian)
    MPC: float = 0.75  # Marginal propensity to consume
    AUTONOMOUS_CONSUMPTION: float = 50_000.0
    WEALTH_EFFECT: float = 0.05
    
    # Investment function
    INVESTMENT_INTEREST_SENSITIVITY: float = 0.8
    INVESTMENT_CONFIDENCE_WEIGHT: float = 0.3
    ACCELERATOR_COEFFICIENT: float = 0.4
    
    # Money demand (LM)
    MONEY_INCOME_ELASTICITY: float = 1.0
    MONEY_INTEREST_ELASTICITY: float = 0.5
    
    # Credit market
    CREDIT_MULTIPLIER: float = 5.0
    DEFAULT_SENSITIVITY_TO_RATES: float = 0.3
    DEFAULT_SENSITIVITY_TO_UNEMPLOYMENT: float = 0.5
    
    # Confidence dynamics
    CONFIDENCE_PERSISTENCE: float = 0.8
    CONFIDENCE_GDP_SENSITIVITY: float = 0.3
    CONFIDENCE_UNEMPLOYMENT_SENSITIVITY: float = -0.4
    CONFIDENCE_INFLATION_SENSITIVITY: float = -0.2
    
    # Sector elasticities
    SECTOR_CYCLE_SENSITIVITY: Dict[str, float] = {
        Sector.AGRICULTURE.value: 0.3,
        Sector.MANUFACTURING.value: 1.2,
        Sector.SERVICES.value: 0.8,
        Sector.TECHNOLOGY.value: 1.5,
        Sector.FINANCE.value: 1.8,
        Sector.GOVERNMENT.value: 0.1,
        Sector.CONSTRUCTION.value: 2.0,
        Sector.ENERGY.value: 0.5,
    }
    
    # Shock decay
    SHOCK_DECAY_RATE: float = 0.15
    SHOCK_PROPAGATION_LAG: int = 2


class MacroeconomicEngine:
    """
    Core simulation engine implementing continuous-time economic dynamics
    using Euler method discretization of differential equations
    """
    
    def __init__(self, initial_state: Optional[MacroState] = None, dt: float = 1.0):
        self.state = initial_state or MacroState()
        self.dt = dt  # Time step (1 = 1 quarter)
        self.params = EconomicParameters()
        self.history: List[MacroState] = []
        self.active_shocks: List[EconomicShock] = []
        self.active_policies: List[PolicyAction] = []
        self.shock_queue: List[EconomicShock] = []
        
    def step(self) -> MacroState:
        """
        Execute one simulation step using Euler integration
        
        Economic dynamics follow the system:
        dY/dt = f(Y, π, i, G, T, shocks)
        dπ/dt = g(Y, π^e, unemployment)
        du/dt = h(Y, Y_potential)
        """
        # Save current state to history
        self.history.append(self._copy_state(self.state))
        
        # Process shock decay
        self._process_shocks()
        
        # Calculate aggregate shock impact
        shock_impact = self._calculate_shock_impact()
        
        # Step 1: Update expectations (adaptive + rational mix)
        self._update_expectations()
        
        # Step 2: Solve goods market equilibrium (IS curve)
        self._update_output(shock_impact)
        
        # Step 3: Update labor market (Okun's Law + Phillips)
        self._update_labor_market()
        
        # Step 4: Update prices (Phillips Curve)
        self._update_inflation(shock_impact)
        
        # Step 5: Update monetary sector
        self._update_monetary_sector()
        
        # Step 6: Update financial sector (credit, banking)
        self._update_financial_sector()
        
        # Step 7: Update confidence indices
        self._update_confidence()
        
        # Step 8: Update sectoral decomposition
        self._update_sectors(shock_impact)
        
        # Step 9: Update fiscal accounts
        self._update_fiscal()
        
        # Step 10: Detect business cycle phase
        self._detect_cycle_phase()
        
        # Step 11: Process temporary policy expirations
        self._process_policy_expiration()
        
        # Advance time
        self.state.tick += 1
        self.state.timestamp += self.dt
        
        return self._copy_state(self.state)
    
    def _update_expectations(self):
        """Update inflation expectations using adaptive-rational hybrid"""
        # Adaptive component: based on past inflation
        adaptive = self.state.inflation
        
        # Rational component: converge to target
        target = 0.02  # Central bank target
        rational = target
        
        # Weighted average
        alpha = self.params.EXPECTATIONS_WEIGHT
        self.state.expected_inflation = (
            alpha * rational + (1 - alpha) * adaptive
        )
    
    def _update_output(self, shock_impact: Dict):
        """
        IS Curve: Y = C + I + G + NX
        
        dY/dt = α[C(Y,i) + I(Y,i,conf) + G - T + NX] - Y
        
        With:
        - C = c₀ + MPC * (Y - T)
        - I = I₀ - b*r + accelerator*dY/dt + conf_weight*business_conf
        """
        Y = self.state.gdp
        r = self.state.real_interest_rate
        G = self.state.government_spending
        T = self.state.tax_revenue
        
        # Consumption function
        disposable_income = Y * (1 - self.state.tax_rate)
        consumption = (
            self.params.AUTONOMOUS_CONSUMPTION +
            self.params.MPC * disposable_income +
            self.params.WEALTH_EFFECT * self.state.consumer_confidence * 1000
        )
        
        # Investment function
        base_investment = 0.2 * self.state.potential_gdp
        interest_effect = -self.params.INVESTMENT_INTEREST_SENSITIVITY * r * base_investment
        confidence_effect = self.params.INVESTMENT_CONFIDENCE_WEIGHT * (
            self.state.business_confidence - 100
        ) / 100 * base_investment
        
        # Accelerator effect (investment responds to growth)
        if len(self.history) > 1:
            gdp_change = (Y - self.history[-1].gdp) / self.history[-1].gdp if self.history[-1].gdp > 0 else 0
            accelerator_effect = self.params.ACCELERATOR_COEFFICIENT * gdp_change * Y
        else:
            accelerator_effect = 0
            
        investment = max(0, base_investment + interest_effect + confidence_effect + accelerator_effect)
        
        # Net exports (simplified)
        net_exports = self.state.exports - self.state.imports
        
        # Aggregate demand
        AD = consumption + investment + G + net_exports
        
        # Apply demand shock
        demand_shock = shock_impact.get('demand', 0)
        AD *= (1 + demand_shock)
        
        # Output adjustment (partial adjustment model)
        adjustment_speed = 0.3
        Y_new = Y + adjustment_speed * (AD - Y) * self.dt
        
        # Apply supply shock to potential output
        supply_shock = shock_impact.get('supply', 0)
        self.state.potential_gdp *= (1 + supply_shock * 0.1)
        
        # Update state
        self.state.gdp = max(Y_new, 0.1 * self.state.potential_gdp)  # Floor at 10% of potential
        self.state.consumption = consumption
        self.state.investment = investment
        self.state.output_gap = (self.state.gdp - self.state.potential_gdp) / self.state.potential_gdp
        
        # GDP growth rate
        if len(self.history) > 0:
            self.state.gdp_growth = (self.state.gdp - self.history[-1].gdp) / self.history[-1].gdp
    
    def _update_labor_market(self):
        """
        Okun's Law: Δu = -β * (g_Y - g_Y*)
        
        Where:
        - Δu = change in unemployment rate
        - β = Okun coefficient (≈0.5)
        - g_Y = actual GDP growth
        - g_Y* = potential GDP growth (trend)
        """
        # Potential growth (trend)
        potential_growth = 0.025  # 2.5% annual
        
        # Okun's Law
        okun_beta = 1 / self.params.OKUN_COEFFICIENT
        gdp_gap = self.state.gdp_growth - potential_growth
        
        unemployment_change = -okun_beta * gdp_gap
        
        # Unemployment persistence
        persistence = 0.7
        new_unemployment = (
            persistence * self.state.unemployment +
            (1 - persistence) * (self.state.unemployment + unemployment_change)
        )
        
        # Bounds
        self.state.unemployment = np.clip(new_unemployment, 0.02, 0.25)
        
        # Update employment
        self.state.employment = self.state.labor_force * (1 - self.state.unemployment)
        
        # Wage dynamics (Phillips-like)
        wage_phillips = 0.5 * (self.state.natural_unemployment - self.state.unemployment)
        self.state.wage_growth = self.state.inflation + wage_phillips + 0.01  # +1% productivity
    
    def _update_inflation(self, shock_impact: Dict):
        """
        New Keynesian Phillips Curve:
        π_t = β * E[π_{t+1}] + κ * (Y - Y*)/Y* + ε
        
        With expectations and supply shocks
        """
        # Output gap effect
        output_gap_effect = self.params.PHILLIPS_SLOPE * self.state.output_gap
        
        # Expectations effect
        expectations_effect = self.params.INFLATION_PERSISTENCE * self.state.expected_inflation
        
        # Persistence
        lagged_inflation = self.state.inflation
        persistence_effect = (1 - self.params.INFLATION_PERSISTENCE) * lagged_inflation
        
        # Supply shock (cost-push)
        supply_shock = shock_impact.get('supply', 0)
        shock_effect = -supply_shock * 0.05  # Negative supply shock → higher inflation
        
        # Wage pressure
        wage_effect = 0.1 * (self.state.wage_growth - 0.03)  # Deviation from trend
        
        # New inflation rate
        new_inflation = (
            expectations_effect +
            persistence_effect +
            output_gap_effect +
            shock_effect +
            wage_effect
        )
        
        # Bounds and smoothing
        self.state.inflation = np.clip(new_inflation, -0.05, 0.30)
        
        # Update price level
        self.state.price_level *= (1 + self.state.inflation * self.dt)
        
        # Core inflation (excludes volatile components)
        self.state.core_inflation = 0.9 * self.state.core_inflation + 0.1 * self.state.inflation
    
    def _update_monetary_sector(self):
        """
        Taylor Rule for interest rate:
        i = r* + π + 0.5(π - π*) + 0.5(Y - Y*)/Y*
        
        Money market equilibrium:
        M/P = L(Y, i) = kY - hi
        """
        # Taylor Rule
        inflation_gap = self.state.inflation - 0.02  # 2% target
        
        taylor_rate = (
            self.params.NEUTRAL_RATE +
            self.state.inflation +
            self.params.TAYLOR_INFLATION_WEIGHT * inflation_gap +
            self.params.TAYLOR_OUTPUT_WEIGHT * self.state.output_gap
        )
        
        # Interest rate smoothing (central banks don't move abruptly)
        smoothing = 0.8
        self.state.interest_rate = (
            smoothing * self.state.interest_rate +
            (1 - smoothing) * taylor_rate
        )
        
        # Zero lower bound
        self.state.interest_rate = max(0.001, self.state.interest_rate)
        
        # Real interest rate
        self.state.real_interest_rate = self.state.interest_rate - self.state.expected_inflation
        
        # Money supply (endogenous under interest rate targeting)
        # M*V = P*Y → M = P*Y/V
        self.state.money_supply = (
            self.state.price_level * self.state.gdp / self.state.velocity_of_money
        )
    
    def _update_financial_sector(self):
        """
        Credit market dynamics:
        - Loan supply = f(reserves, confidence, rates)
        - Loan demand = g(investment needs, rates)
        - Default rates = h(unemployment, rates, leverage)
        """
        # Bank reserves (influenced by monetary policy)
        reserve_requirement = 0.1
        self.state.bank_reserves = self.state.money_supply * reserve_requirement
        
        # Credit supply (money multiplier)
        potential_credit = self.state.bank_reserves * self.params.CREDIT_MULTIPLIER
        confidence_adjustment = (self.state.business_confidence / 100) ** 0.5
        self.state.credit_supply = potential_credit * confidence_adjustment
        
        # Credit demand
        investment_needs = self.state.investment * 0.7  # 70% financed by credit
        rate_sensitivity = np.exp(-self.state.interest_rate * 10)  # Demand falls with rates
        self.state.credit_demand = investment_needs * rate_sensitivity
        
        # Default rate dynamics
        base_default = 0.02
        unemployment_effect = self.params.DEFAULT_SENSITIVITY_TO_UNEMPLOYMENT * (
            self.state.unemployment - self.state.natural_unemployment
        )
        rate_effect = self.params.DEFAULT_SENSITIVITY_TO_RATES * (
            self.state.interest_rate - 0.05
        )
        
        self.state.loan_default_rate = np.clip(
            base_default + unemployment_effect + rate_effect,
            0.005, 0.15
        )
    
    def _update_confidence(self):
        """
        Confidence indices with persistence and economic feedback:
        Conf_t = α * Conf_{t-1} + (1-α) * f(GDP_growth, unemployment, inflation)
        """
        # Consumer confidence
        gdp_effect = self.params.CONFIDENCE_GDP_SENSITIVITY * self.state.gdp_growth * 100
        unemployment_effect = self.params.CONFIDENCE_UNEMPLOYMENT_SENSITIVITY * (
            self.state.unemployment - self.state.natural_unemployment
        ) * 100
        inflation_effect = self.params.CONFIDENCE_INFLATION_SENSITIVITY * (
            self.state.inflation - 0.02
        ) * 100
        
        target_consumer_conf = 100 + gdp_effect + unemployment_effect + inflation_effect
        
        self.state.consumer_confidence = (
            self.params.CONFIDENCE_PERSISTENCE * self.state.consumer_confidence +
            (1 - self.params.CONFIDENCE_PERSISTENCE) * target_consumer_conf
        )
        self.state.consumer_confidence = np.clip(self.state.consumer_confidence, 20, 150)
        
        # Business confidence (more volatile, forward-looking)
        profit_proxy = self.state.gdp_growth + 0.1 * self.state.output_gap
        interest_burden = -0.5 * self.state.real_interest_rate
        target_business_conf = 100 + (profit_proxy + interest_burden) * 200
        
        self.state.business_confidence = (
            (self.params.CONFIDENCE_PERSISTENCE - 0.1) * self.state.business_confidence +
            (1.1 - self.params.CONFIDENCE_PERSISTENCE) * target_business_conf
        )
        self.state.business_confidence = np.clip(self.state.business_confidence, 20, 150)
    
    def _update_sectors(self, shock_impact: Dict):
        """
        Sector-wise GDP decomposition with differential cycle sensitivity
        """
        aggregate_growth = self.state.gdp_growth
        
        for sector, base_gdp in list(self.state.sector_gdp.items()):
            sensitivity = self.params.SECTOR_CYCLE_SENSITIVITY.get(sector, 1.0)
            
            # Sector-specific growth
            sector_growth = aggregate_growth * sensitivity
            
            # Apply sector-specific shocks
            if sector in shock_impact.get('sectors', {}):
                sector_growth += shock_impact['sectors'][sector]
            
            # Update sector GDP
            new_gdp = base_gdp * (1 + sector_growth * self.dt)
            self.state.sector_gdp[sector] = max(new_gdp, 1000)  # Minimum floor
        
        # Rescale to match aggregate GDP
        total_sector = sum(self.state.sector_gdp.values())
        if total_sector > 0:
            scale_factor = self.state.gdp / total_sector
            for sector in self.state.sector_gdp:
                self.state.sector_gdp[sector] *= scale_factor
    
    def _update_fiscal(self):
        """
        Government budget dynamics:
        - Tax revenue = τ * Y
        - Deficit = G - T
        - Debt accumulation: dD/dt = Deficit + r*D
        """
        # Tax revenue
        self.state.tax_revenue = self.state.tax_rate * self.state.gdp
        
        # Deficit
        self.state.fiscal_deficit = self.state.government_spending - self.state.tax_revenue
        
        # Debt dynamics
        interest_payments = self.state.interest_rate * self.state.public_debt
        self.state.public_debt += (self.state.fiscal_deficit + interest_payments) * self.dt
        
        # Debt-to-GDP ratio
        self.state.debt_to_gdp = self.state.public_debt / self.state.gdp if self.state.gdp > 0 else 0
    
    def _detect_cycle_phase(self):
        """
        Detect business cycle phase using growth and output gap
        """
        if len(self.history) < 4:
            return
        
        recent_growth = [h.gdp_growth for h in self.history[-4:]]
        avg_growth = np.mean(recent_growth)
        growth_trend = recent_growth[-1] - recent_growth[0]
        
        old_phase = self.state.cycle_phase
        
        if avg_growth > 0.02 and growth_trend > 0:
            self.state.cycle_phase = BusinessCyclePhase.EXPANSION
        elif avg_growth > 0 and growth_trend < 0:
            self.state.cycle_phase = BusinessCyclePhase.PEAK
        elif avg_growth < 0 and growth_trend < 0:
            self.state.cycle_phase = BusinessCyclePhase.RECESSION
        elif avg_growth < 0.01 and growth_trend > 0:
            self.state.cycle_phase = BusinessCyclePhase.TROUGH
        
        # Track phase duration
        if self.state.cycle_phase == old_phase:
            self.state.cycle_duration += 1
        else:
            self.state.cycle_duration = 1
    
    def _process_shocks(self):
        """Process active shocks with decay"""
        surviving_shocks = []
        for shock in self.active_shocks:
            # Decay intensity
            shock.current_intensity *= (1 - shock.decay_rate)
            
            # Check if shock is still active
            elapsed = self.state.tick - shock.tick_applied
            if elapsed < shock.duration and shock.current_intensity > 0.01:
                surviving_shocks.append(shock)
        
        self.active_shocks = surviving_shocks
        
        # Add queued shocks
        while self.shock_queue:
            new_shock = self.shock_queue.pop(0)
            new_shock.tick_applied = self.state.tick
            self.active_shocks.append(new_shock)
    
    def _calculate_shock_impact(self) -> Dict:
        """Calculate aggregate shock impact by type"""
        impact = {
            'supply': 0.0,
            'demand': 0.0,
            'financial': 0.0,
            'sectors': {}
        }
        
        for shock in self.active_shocks:
            effective_magnitude = shock.magnitude * shock.current_intensity
            
            if shock.shock_type == 'supply':
                impact['supply'] += effective_magnitude
            elif shock.shock_type == 'demand':
                impact['demand'] += effective_magnitude
            elif shock.shock_type == 'financial':
                impact['financial'] += effective_magnitude
            
            # Sector-specific
            for sector in shock.affected_sectors:
                if sector not in impact['sectors']:
                    impact['sectors'][sector] = 0.0
                impact['sectors'][sector] += effective_magnitude
        
        return impact
    
    def _process_policy_expiration(self):
        """Remove expired temporary policies"""
        surviving_policies = []
        for policy in self.active_policies:
            if policy.duration is not None:
                policy.duration -= 1
                if policy.duration > 0:
                    surviving_policies.append(policy)
                else:
                    # Revert policy
                    self._apply_policy_value(policy.parameter, policy.old_value)
            else:
                surviving_policies.append(policy)
        
        self.active_policies = surviving_policies
    
    def apply_shock(self, shock: EconomicShock):
        """Queue a new economic shock"""
        self.shock_queue.append(shock)
    
    def apply_policy(self, policy: PolicyAction):
        """Apply a policy change"""
        self._apply_policy_value(policy.parameter, policy.new_value)
        policy.timestamp = self.state.timestamp
        self.active_policies.append(policy)
    
    def _apply_policy_value(self, parameter: str, value: float):
        """Set a policy parameter value"""
        if hasattr(self.state, parameter):
            setattr(self.state, parameter, value)
    
    def _copy_state(self, state: MacroState) -> MacroState:
        """Deep copy of macro state"""
        return MacroState(
            gdp=state.gdp,
            gdp_growth=state.gdp_growth,
            potential_gdp=state.potential_gdp,
            output_gap=state.output_gap,
            inflation=state.inflation,
            expected_inflation=state.expected_inflation,
            core_inflation=state.core_inflation,
            price_level=state.price_level,
            unemployment=state.unemployment,
            natural_unemployment=state.natural_unemployment,
            labor_force=state.labor_force,
            employment=state.employment,
            wage_growth=state.wage_growth,
            interest_rate=state.interest_rate,
            real_interest_rate=state.real_interest_rate,
            money_supply=state.money_supply,
            velocity_of_money=state.velocity_of_money,
            government_spending=state.government_spending,
            tax_revenue=state.tax_revenue,
            tax_rate=state.tax_rate,
            fiscal_deficit=state.fiscal_deficit,
            public_debt=state.public_debt,
            debt_to_gdp=state.debt_to_gdp,
            credit_supply=state.credit_supply,
            credit_demand=state.credit_demand,
            bank_reserves=state.bank_reserves,
            reserve_ratio=state.reserve_ratio,
            loan_default_rate=state.loan_default_rate,
            consumer_confidence=state.consumer_confidence,
            business_confidence=state.business_confidence,
            consumption=state.consumption,
            investment=state.investment,
            savings_rate=state.savings_rate,
            exports=state.exports,
            imports=state.imports,
            trade_balance=state.trade_balance,
            exchange_rate=state.exchange_rate,
            sector_gdp=dict(state.sector_gdp),
            cycle_phase=state.cycle_phase,
            cycle_duration=state.cycle_duration,
            tick=state.tick,
            timestamp=state.timestamp,
        )
    
    def get_state_vector(self) -> np.ndarray:
        """Convert state to numpy vector for ML models"""
        return np.array([
            self.state.gdp / 1_000_000,  # Normalize
            self.state.gdp_growth,
            self.state.output_gap,
            self.state.inflation,
            self.state.unemployment,
            self.state.interest_rate,
            self.state.consumer_confidence / 100,
            self.state.business_confidence / 100,
            self.state.debt_to_gdp,
            self.state.loan_default_rate,
        ])
    
    def forecast(self, steps: int, scenarios: Optional[List[Dict]] = None) -> List[MacroState]:
        """Run forward simulation for forecasting"""
        # Save current state
        saved_state = self._copy_state(self.state)
        saved_history = list(self.history)
        saved_shocks = list(self.active_shocks)
        
        forecasts = []
        for _ in range(steps):
            forecasts.append(self.step())
        
        # Restore state
        self.state = saved_state
        self.history = saved_history
        self.active_shocks = saved_shocks
        
        return forecasts


class EquilibriumSolver:
    """
    General equilibrium solver for market clearing
    """
    
    @staticmethod
    def solve_goods_market(
        consumption_fn: Callable,
        investment_fn: Callable,
        government_spending: float,
        net_exports: float,
        initial_Y: float
    ) -> float:
        """
        Solve for equilibrium output: Y = C(Y) + I(Y) + G + NX
        """
        def excess_demand(Y):
            C = consumption_fn(Y)
            I = investment_fn(Y)
            AD = C + I + government_spending + net_exports
            return AD - Y
        
        Y_equilibrium = fsolve(excess_demand, initial_Y)[0]
        return max(Y_equilibrium, 0)
    
    @staticmethod
    def solve_money_market(
        money_supply: float,
        price_level: float,
        gdp: float,
        money_demand_fn: Callable
    ) -> float:
        """
        Solve for equilibrium interest rate: M/P = L(Y, i)
        """
        real_money = money_supply / price_level
        
        def excess_supply(i):
            L = money_demand_fn(gdp, i)
            return real_money - L
        
        i_equilibrium = fsolve(excess_supply, 0.05)[0]
        return np.clip(i_equilibrium, 0.001, 0.3)
    
    @staticmethod
    def solve_labor_market(
        labor_supply_fn: Callable,
        labor_demand_fn: Callable,
        initial_wage: float
    ) -> Tuple[float, float]:
        """
        Solve for equilibrium wage and employment
        """
        def excess_supply(w):
            Ls = labor_supply_fn(w)
            Ld = labor_demand_fn(w)
            return Ls - Ld
        
        w_equilibrium = fsolve(excess_supply, initial_wage)[0]
        employment = labor_demand_fn(w_equilibrium)
        return w_equilibrium, employment
