"""
VALORA Firm Agent
RL-based firm with demand forecasting, dynamic pricing, and production optimization
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass, field
import random
from collections import deque

from .base_agent import BaseAgent, AgentType, Experience


class FirmSector(Enum):
    """Industry sectors"""
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    TECHNOLOGY = "technology"
    RETAIL = "retail"
    CONSTRUCTION = "construction"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    ENERGY = "energy"


class FirmSize(Enum):
    """Firm size categories"""
    SMALL = "small"        # < 50 employees
    MEDIUM = "medium"      # 50-250 employees
    LARGE = "large"        # > 250 employees


@dataclass
class FirmProfile:
    """Firm characteristics"""
    sector: FirmSector
    size: FirmSize
    initial_capital: float
    initial_employees: int
    productivity: float  # Output per worker
    market_share: float  # 0-1
    debt_capacity: float
    innovation_rate: float


class DemandForecaster:
    """
    Simple LSTM-like demand forecasting using exponential smoothing
    For production: replace with actual LSTM/Transformer
    """
    
    def __init__(self, alpha: float = 0.3, beta: float = 0.1):
        self.alpha = alpha  # Level smoothing
        self.beta = beta    # Trend smoothing
        self.level = None
        self.trend = 0
        self.history = deque(maxlen=100)
    
    def update(self, demand: float):
        """Update forecast with new observation"""
        self.history.append(demand)
        
        if self.level is None:
            self.level = demand
            return
        
        # Holt's linear exponential smoothing
        old_level = self.level
        self.level = self.alpha * demand + (1 - self.alpha) * (self.level + self.trend)
        self.trend = self.beta * (self.level - old_level) + (1 - self.beta) * self.trend
    
    def forecast(self, periods: int = 1) -> float:
        """Forecast demand for future periods"""
        if self.level is None:
            return 0
        return self.level + self.trend * periods
    
    def get_forecast_confidence(self) -> float:
        """Return confidence in forecast based on data stability"""
        if len(self.history) < 5:
            return 0.3
        
        recent = list(self.history)[-10:]
        cv = np.std(recent) / (np.mean(recent) + 1e-8)  # Coefficient of variation
        
        # Lower CV = higher confidence
        return min(1.0, max(0.3, 1 - cv))


class FirmAgent(BaseAgent):
    """
    Firm agent with RL for pricing and production decisions
    
    State Space (12 dimensions):
    - Current revenue (normalized)
    - Current costs (normalized)
    - Profit margin
    - Inventory level
    - Employee count (normalized)
    - Market demand (from forecaster)
    - Competitor price level (proxy)
    - Interest rate (borrowing cost)
    - GDP growth
    - Inflation rate
    - Business confidence
    - Sector-specific indicator
    
    Action Space (9 actions - 3x3 grid):
    Pricing: {decrease 5%, maintain, increase 5%}
    Production: {reduce 20%, maintain, expand 20%}
    
    0: Price↓, Production↓
    1: Price↓, Production=
    2: Price↓, Production↑
    3: Price=, Production↓
    4: Price=, Production= (status quo)
    5: Price=, Production↑
    6: Price↑, Production↓
    7: Price↑, Production=
    8: Price↑, Production↑
    """
    
    STATE_DIM = 12
    ACTION_DIM = 9
    
    # Action mappings
    PRICE_CHANGES = [-0.05, 0.0, 0.05]  # -5%, 0%, +5%
    PRODUCTION_CHANGES = [-0.20, 0.0, 0.20]  # -20%, 0%, +20%
    
    def __init__(
        self,
        agent_id: str,
        profile: Optional[FirmProfile] = None,
        learning_rate: float = 0.001,
        discount_factor: float = 0.99
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.FIRM,
            state_dim=self.STATE_DIM,
            action_dim=self.ACTION_DIM,
            learning_rate=learning_rate,
            discount_factor=discount_factor
        )
        
        self.profile = profile or self._generate_random_profile()
        
        # Financial state
        self.capital = self.profile.initial_capital
        self.employees = self.profile.initial_employees
        self.inventory = 0.0
        self.price = 100.0  # Base price index
        self.production_rate = 1.0
        self.revenue = 0.0
        self.costs = 0.0
        self.profit = 0.0
        self.debt = 0.0
        
        # Forecasting
        self.demand_forecaster = DemandForecaster()
        self.demand_history = []
        
        # Sector parameters
        self._set_sector_parameters()
    
    def _generate_random_profile(self) -> FirmProfile:
        """Generate random firm profile"""
        sector = random.choice(list(FirmSector))
        
        size_roll = random.random()
        if size_roll < 0.6:
            size = FirmSize.SMALL
            employees = random.randint(10, 49)
            capital = random.uniform(100000, 1000000)
        elif size_roll < 0.9:
            size = FirmSize.MEDIUM
            employees = random.randint(50, 250)
            capital = random.uniform(1000000, 10000000)
        else:
            size = FirmSize.LARGE
            employees = random.randint(251, 5000)
            capital = random.uniform(10000000, 100000000)
        
        return FirmProfile(
            sector=sector,
            size=size,
            initial_capital=capital,
            initial_employees=employees,
            productivity=random.uniform(50000, 150000),  # Output per worker
            market_share=random.uniform(0.001, 0.05),
            debt_capacity=capital * random.uniform(0.3, 0.7),
            innovation_rate=random.uniform(0.01, 0.1)
        )
    
    def _set_sector_parameters(self):
        """Set sector-specific economic parameters"""
        sector_params = {
            FirmSector.MANUFACTURING: {'cycle_sensitivity': 1.2, 'labor_intensity': 0.4},
            FirmSector.SERVICES: {'cycle_sensitivity': 0.8, 'labor_intensity': 0.6},
            FirmSector.TECHNOLOGY: {'cycle_sensitivity': 1.5, 'labor_intensity': 0.3},
            FirmSector.RETAIL: {'cycle_sensitivity': 1.0, 'labor_intensity': 0.5},
            FirmSector.CONSTRUCTION: {'cycle_sensitivity': 2.0, 'labor_intensity': 0.5},
            FirmSector.FINANCE: {'cycle_sensitivity': 1.8, 'labor_intensity': 0.2},
            FirmSector.HEALTHCARE: {'cycle_sensitivity': 0.3, 'labor_intensity': 0.7},
            FirmSector.ENERGY: {'cycle_sensitivity': 0.5, 'labor_intensity': 0.2},
        }
        
        params = sector_params.get(self.profile.sector, 
                                   {'cycle_sensitivity': 1.0, 'labor_intensity': 0.5})
        self.cycle_sensitivity = params['cycle_sensitivity']
        self.labor_intensity = params['labor_intensity']
    
    def observe(self, macro_state: Dict) -> np.ndarray:
        """Convert macro state to firm's observation"""
        # Calculate current financial metrics
        total_capacity = self.employees * self.profile.productivity
        
        observation = np.array([
            self.revenue / (total_capacity + 1),  # Revenue utilization
            self.costs / (total_capacity + 1),    # Cost ratio
            self.profit / (self.revenue + 1),     # Profit margin
            self.inventory / (total_capacity * 0.5 + 1),  # Inventory ratio
            self.employees / self.profile.initial_employees,  # Employment ratio
            self.demand_forecaster.forecast() / (total_capacity + 1),  # Demand forecast
            macro_state.get('inflation', 0.02),   # Price environment
            macro_state.get('interest_rate', 0.05),  # Borrowing cost
            macro_state.get('gdp_growth', 0.025),
            macro_state.get('business_confidence', 100) / 100,
            macro_state.get('unemployment', 0.05),  # Labor availability
            self.cycle_sensitivity * macro_state.get('output_gap', 0),  # Sector cycle
        ], dtype=np.float32)
        
        return observation
    
    def get_action_space(self) -> List[Dict]:
        """Define pricing and production action combinations"""
        actions = []
        for i, (price_change, prod_change) in enumerate([
            (-0.05, -0.20), (-0.05, 0.00), (-0.05, 0.20),
            (0.00, -0.20),  (0.00, 0.00),  (0.00, 0.20),
            (0.05, -0.20),  (0.05, 0.00),  (0.05, 0.20),
        ]):
            actions.append({
                'id': i,
                'name': f'price_{price_change:+.0%}_prod_{prod_change:+.0%}',
                'price_change': price_change,
                'production_change': prod_change,
                'description': f'Change price by {price_change:+.0%}, production by {prod_change:+.0%}'
            })
        return actions
    
    def interpret_action(self, action_idx: int) -> Dict:
        """Convert action index to interpretable format"""
        return self.get_action_space()[action_idx]
    
    def calculate_reward(self, macro_state: Dict, action: int) -> float:
        """
        Calculate reward based on profit maximization with stability bonus
        
        Reward = α * profit_rate + β * market_share_change - γ * risk_penalty
        """
        # Profit component (normalized)
        if self.revenue > 0:
            profit_rate = self.profit / self.revenue
        else:
            profit_rate = -0.1  # Penalty for no revenue
        
        # Stability bonus for maintaining employment
        employment_ratio = self.employees / self.profile.initial_employees
        if 0.8 <= employment_ratio <= 1.2:
            stability_bonus = 0.2
        else:
            stability_bonus = -0.1 * abs(1 - employment_ratio)
        
        # Risk penalty for high debt
        debt_ratio = self.debt / (self.capital + 1)
        risk_penalty = max(0, debt_ratio - 0.5) * 0.5
        
        # Inventory management bonus
        optimal_inventory = self.demand_forecaster.forecast() * 0.2  # 20% of demand
        if optimal_inventory > 0:
            inventory_score = 1 - abs(self.inventory - optimal_inventory) / optimal_inventory
            inventory_score = max(-0.2, min(0.2, inventory_score * 0.2))
        else:
            inventory_score = 0
        
        reward = profit_rate + stability_bonus - risk_penalty + inventory_score
        return reward
    
    def step(self, macro_state: Dict, market_demand: float) -> Tuple[Dict, Dict]:
        """
        Execute one step of firm behavior
        
        Returns:
            outputs: Production outputs and labor decisions
            info: Decision information
        """
        # Observe state
        observation = self.observe(macro_state)
        
        # Select action
        action, explanation = self.select_action(observation)
        action_info = self.interpret_action(action)
        
        # Execute pricing decision
        price_change = action_info['price_change']
        self.price *= (1 + price_change)
        
        # Execute production decision
        prod_change = action_info['production_change']
        self.production_rate = max(0.1, self.production_rate * (1 + prod_change))
        
        # Calculate production capacity
        base_capacity = self.employees * self.profile.productivity
        actual_production = base_capacity * self.production_rate
        
        # Determine sales based on demand and price
        price_elasticity = -1.5  # Typical elasticity
        price_effect = (self.price / 100) ** price_elasticity
        effective_demand = market_demand * self.profile.market_share * price_effect
        
        # Sales = min(demand, production + inventory)
        available = actual_production + self.inventory
        sales = min(effective_demand, available)
        
        # Update inventory
        self.inventory = available - sales
        
        # Calculate financials
        self.revenue = sales * self.price
        
        # Costs: labor + capital + materials
        wage_rate = macro_state.get('wage_growth', 0.03) * 50000 + 50000  # Base wage
        labor_cost = self.employees * wage_rate * self.labor_intensity
        material_cost = actual_production * 30  # $30 per unit materials
        interest_cost = self.debt * macro_state.get('interest_rate', 0.05)
        depreciation = self.capital * 0.05  # 5% depreciation
        
        self.costs = labor_cost + material_cost + interest_cost + depreciation
        self.profit = self.revenue - self.costs
        
        # Update capital
        self.capital += self.profit * 0.5  # Retain 50% of profit
        
        # Update demand forecaster
        self.demand_forecaster.update(effective_demand)
        self.demand_history.append(effective_demand)
        
        # Employment decisions based on production needs
        target_employees = int(actual_production / self.profile.productivity)
        if prod_change < 0:
            # Layoffs
            layoffs = max(0, self.employees - target_employees)
            self.employees = max(1, self.employees - layoffs)
        elif prod_change > 0:
            # Hiring
            new_hires = max(0, target_employees - self.employees)
            self.employees += new_hires
        
        # Calculate reward
        reward = self.calculate_reward(macro_state, action)
        self.total_reward += reward
        
        # Store experience
        next_observation = self.observe(macro_state)
        experience = Experience(
            state=observation,
            action=action,
            reward=reward,
            next_state=next_observation,
            done=False
        )
        self.learn(experience)
        
        outputs = {
            'production': actual_production,
            'sales': sales,
            'employment_change': self.employees - self.profile.initial_employees,
            'price': self.price,
            'investment': max(0, self.profit * 0.3),  # 30% reinvestment
        }
        
        info = {
            'agent_id': self.agent_id,
            'sector': self.profile.sector.value,
            'size': self.profile.size.value,
            'revenue': self.revenue,
            'costs': self.costs,
            'profit': self.profit,
            'employees': self.employees,
            'inventory': self.inventory,
            'action': action_info,
            'reward': reward,
            'demand_forecast': self.demand_forecaster.forecast(),
            'forecast_confidence': self.demand_forecaster.get_forecast_confidence(),
            'explanation': explanation
        }
        
        return outputs, info
    
    def get_labor_demand(self) -> int:
        """Get current labor demand"""
        return self.employees
    
    def get_output(self) -> float:
        """Get current production output"""
        return self.employees * self.profile.productivity * self.production_rate
    
    def get_investment_demand(self) -> float:
        """Get investment spending"""
        if self.profit > 0:
            return self.profit * 0.3
        return 0


class FirmPopulation:
    """
    Manages population of heterogeneous firms across sectors
    """
    
    def __init__(self, size: int = 500, sector_distribution: Optional[Dict] = None):
        self.firms: List[FirmAgent] = []
        self.size = size
        
        # Default sector distribution
        self.sector_distribution = sector_distribution or {
            FirmSector.MANUFACTURING: 0.20,
            FirmSector.SERVICES: 0.30,
            FirmSector.TECHNOLOGY: 0.10,
            FirmSector.RETAIL: 0.15,
            FirmSector.CONSTRUCTION: 0.08,
            FirmSector.FINANCE: 0.07,
            FirmSector.HEALTHCARE: 0.05,
            FirmSector.ENERGY: 0.05,
        }
        
        self._initialize_population()
    
    def _initialize_population(self):
        """Create diverse firm population"""
        for i in range(self.size):
            # Determine sector
            roll = random.random()
            cumulative = 0
            sector = FirmSector.SERVICES
            
            for s, prob in self.sector_distribution.items():
                cumulative += prob
                if roll < cumulative:
                    sector = s
                    break
            
            # Create firm
            firm = FirmAgent(agent_id=f"firm_{i}")
            firm.profile.sector = sector
            firm._set_sector_parameters()
            
            self.firms.append(firm)
    
    def step(self, macro_state: Dict, aggregate_demand: float) -> Dict:
        """
        Step all firms and return aggregate statistics
        """
        total_output = 0
        total_employment = 0
        total_investment = 0
        sector_outputs = {s.value: 0 for s in FirmSector}
        sector_employment = {s.value: 0 for s in FirmSector}
        
        # Distribute demand across firms
        for firm in self.firms:
            firm_demand = aggregate_demand * firm.profile.market_share
            outputs, info = firm.step(macro_state, firm_demand)
            
            total_output += outputs['production']
            total_employment += firm.employees
            total_investment += outputs['investment']
            
            sector = firm.profile.sector.value
            sector_outputs[sector] += outputs['production']
            sector_employment[sector] += firm.employees
        
        return {
            'total_output': total_output,
            'total_employment': total_employment,
            'total_investment': total_investment,
            'average_price': np.mean([f.price for f in self.firms]),
            'sector_outputs': sector_outputs,
            'sector_employment': sector_employment,
            'firm_count': self.size,
            'profitable_firms': sum(1 for f in self.firms if f.profit > 0),
        }
    
    def get_sector_gdp(self) -> Dict[str, float]:
        """Calculate GDP by sector"""
        sector_gdp = {s.value: 0 for s in FirmSector}
        for firm in self.firms:
            sector_gdp[firm.profile.sector.value] += firm.revenue
        return sector_gdp
    
    def get_total_labor_demand(self) -> int:
        """Get aggregate labor demand"""
        return sum(f.get_labor_demand() for f in self.firms)
    
    def get_aggregate_investment(self) -> float:
        """Get aggregate investment"""
        return sum(f.get_investment_demand() for f in self.firms)
