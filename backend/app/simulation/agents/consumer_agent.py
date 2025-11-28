"""
VALORA Consumer Agent
Reinforcement learning-based consumer with income classes, inflation-aware budgeting,
and unemployment risk behavior
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import random

from .base_agent import BaseAgent, AgentType, AgentState, Experience


class IncomeClass(Enum):
    """Consumer income brackets"""
    LOW = "low"           # Bottom 30%
    MIDDLE = "middle"     # Middle 50%
    HIGH = "high"         # Top 20%


@dataclass
class ConsumerProfile:
    """Individual consumer characteristics"""
    income_class: IncomeClass
    base_income: float
    risk_tolerance: float  # 0-1
    savings_preference: float  # 0-1
    employment_probability: float  # Probability of being employed
    age: int
    has_mortgage: bool = False
    has_dependents: bool = False


class ConsumerAgent(BaseAgent):
    """
    Consumer agent with Q-learning for consumption/savings decisions
    
    State Space (10 dimensions):
    - Current wealth (normalized)
    - Current income (normalized)
    - Inflation rate
    - Unemployment rate
    - Interest rate (savings return)
    - Consumer confidence index
    - Employment status (binary)
    - Price level change
    - Debt level (normalized)
    - Age factor
    
    Action Space (5 actions):
    0: Aggressive consumption (spend 90% of income)
    1: Normal consumption (spend 70% of income)
    2: Conservative consumption (spend 50% of income)
    3: Heavy saving (spend 30% of income)
    4: Emergency saving (spend only 10% of income)
    
    Reward Function:
    R = utility(consumption) - risk_penalty(savings) - inflation_loss - unemployment_penalty
    
    Where utility follows CRRA (Constant Relative Risk Aversion):
    U(C) = C^(1-σ) / (1-σ) for σ ≠ 1
    """
    
    STATE_DIM = 10
    ACTION_DIM = 5
    
    # Consumption rates for each action
    CONSUMPTION_RATES = [0.90, 0.70, 0.50, 0.30, 0.10]
    
    def __init__(
        self,
        agent_id: str,
        profile: Optional[ConsumerProfile] = None,
        learning_rate: float = 0.001,
        discount_factor: float = 0.99
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.CONSUMER,
            state_dim=self.STATE_DIM,
            action_dim=self.ACTION_DIM,
            learning_rate=learning_rate,
            discount_factor=discount_factor
        )
        
        # Consumer profile
        self.profile = profile or self._generate_random_profile()
        
        # Initialize financial state
        self.state.wealth = self.profile.base_income * 6  # 6 months savings
        self.state.income = self.profile.base_income
        self.is_employed = True
        self.debt = 0.0
        self.consumption_history = []
        
        # CRRA parameters
        self.risk_aversion = 2.0 - self.profile.risk_tolerance  # σ between 1 and 2
        
        # Income class specific parameters
        self._set_class_parameters()
    
    def _generate_random_profile(self) -> ConsumerProfile:
        """Generate randomized consumer profile"""
        # Income class distribution
        class_roll = random.random()
        if class_roll < 0.3:
            income_class = IncomeClass.LOW
            base_income = random.uniform(20000, 40000)
        elif class_roll < 0.8:
            income_class = IncomeClass.MIDDLE
            base_income = random.uniform(40000, 100000)
        else:
            income_class = IncomeClass.HIGH
            base_income = random.uniform(100000, 500000)
        
        return ConsumerProfile(
            income_class=income_class,
            base_income=base_income,
            risk_tolerance=random.uniform(0.2, 0.8),
            savings_preference=random.uniform(0.1, 0.4),
            employment_probability=random.uniform(0.85, 0.98),
            age=random.randint(22, 65),
            has_mortgage=random.random() < 0.4,
            has_dependents=random.random() < 0.35
        )
    
    def _set_class_parameters(self):
        """Set parameters based on income class"""
        if self.profile.income_class == IncomeClass.LOW:
            self.mpc = 0.95  # High marginal propensity to consume
            self.precautionary_buffer = 1.0  # months
            self.unemployment_sensitivity = 1.5
        elif self.profile.income_class == IncomeClass.MIDDLE:
            self.mpc = 0.75
            self.precautionary_buffer = 3.0
            self.unemployment_sensitivity = 1.0
        else:  # HIGH
            self.mpc = 0.55
            self.precautionary_buffer = 6.0
            self.unemployment_sensitivity = 0.5
    
    def observe(self, macro_state: Dict) -> np.ndarray:
        """
        Convert macroeconomic state to consumer's observation
        
        Consumer observes:
        1. Their own wealth relative to income
        2. Current income (may be 0 if unemployed)
        3. Inflation rate
        4. Unemployment rate (affects job security perception)
        5. Interest rate (savings return)
        6. Consumer confidence
        7. Employment status
        8. Recent price changes
        9. Debt burden
        10. Age/retirement proximity
        """
        # Update employment status based on unemployment rate
        unemployment_rate = macro_state.get('unemployment', 0.05)
        if self.is_employed:
            # Probability of losing job increases with unemployment
            layoff_prob = unemployment_rate * self.unemployment_sensitivity * 0.1
            self.is_employed = random.random() > layoff_prob
        else:
            # Probability of finding job
            hire_prob = (1 - unemployment_rate) * 0.3
            self.is_employed = random.random() < hire_prob
        
        # Update income
        if self.is_employed:
            # Wage growth adjustment
            wage_growth = macro_state.get('wage_growth', 0.03)
            self.state.income = self.profile.base_income * (1 + wage_growth)
        else:
            # Unemployment benefits (40% of income)
            self.state.income = self.profile.base_income * 0.4
        
        # Construct observation vector
        observation = np.array([
            self.state.wealth / (self.profile.base_income * 12),  # Wealth in years of income
            self.state.income / self.profile.base_income,  # Income ratio
            macro_state.get('inflation', 0.02),
            macro_state.get('unemployment', 0.05),
            macro_state.get('interest_rate', 0.05),
            macro_state.get('consumer_confidence', 100) / 100,
            1.0 if self.is_employed else 0.0,
            macro_state.get('gdp_growth', 0.025),  # Price trend proxy
            self.debt / max(self.state.income, 1),  # Debt-to-income
            (65 - self.profile.age) / 43,  # Years to retirement normalized
        ], dtype=np.float32)
        
        return observation
    
    def get_action_space(self) -> List[Dict]:
        """Define consumption action space"""
        return [
            {
                'id': 0,
                'name': 'aggressive_consumption',
                'consumption_rate': 0.90,
                'description': 'Spend 90% of income on consumption'
            },
            {
                'id': 1,
                'name': 'normal_consumption',
                'consumption_rate': 0.70,
                'description': 'Spend 70% of income on consumption'
            },
            {
                'id': 2,
                'name': 'conservative_consumption',
                'consumption_rate': 0.50,
                'description': 'Spend 50% of income on consumption'
            },
            {
                'id': 3,
                'name': 'heavy_saving',
                'consumption_rate': 0.30,
                'description': 'Spend only 30% of income, save rest'
            },
            {
                'id': 4,
                'name': 'emergency_mode',
                'consumption_rate': 0.10,
                'description': 'Minimal spending, maximum saving'
            }
        ]
    
    def interpret_action(self, action_idx: int) -> Dict:
        """Convert action index to interpretable format"""
        actions = self.get_action_space()
        return actions[action_idx]
    
    def calculate_reward(self, macro_state: Dict, action: int) -> float:
        """
        Calculate reward using CRRA utility with penalties
        
        Reward = CRRA_Utility(consumption) 
               - inflation_penalty 
               - unemployment_risk_penalty 
               + savings_security_bonus
        """
        consumption_rate = self.CONSUMPTION_RATES[action]
        consumption = self.state.income * consumption_rate
        savings = self.state.income * (1 - consumption_rate)
        
        # CRRA utility of consumption
        if consumption > 0:
            if self.risk_aversion == 1:
                utility = np.log(consumption)
            else:
                utility = (consumption ** (1 - self.risk_aversion)) / (1 - self.risk_aversion)
            # Normalize utility to reasonable scale
            utility = utility / 1000
        else:
            utility = -10  # Strong penalty for zero consumption
        
        # Inflation penalty (erodes savings value)
        inflation = macro_state.get('inflation', 0.02)
        inflation_penalty = inflation * savings / self.profile.base_income * 0.5
        
        # Unemployment risk penalty (should save more if unemployment high)
        unemployment = macro_state.get('unemployment', 0.05)
        natural_unemployment = 0.045
        
        # If unemployment is high and not saving enough, penalize
        if unemployment > natural_unemployment and action < 2:
            risk_penalty = (unemployment - natural_unemployment) * 10 * self.unemployment_sensitivity
        else:
            risk_penalty = 0
        
        # Savings security bonus (having adequate buffer)
        buffer_months = self.state.wealth / self.profile.base_income * 12
        target_buffer = self.precautionary_buffer
        if buffer_months >= target_buffer:
            security_bonus = 0.5
        else:
            security_bonus = -0.5 * (target_buffer - buffer_months) / target_buffer
        
        # Total reward
        reward = utility - inflation_penalty - risk_penalty + security_bonus
        
        return reward
    
    def step(self, macro_state: Dict) -> Tuple[float, Dict]:
        """
        Execute one step of consumer behavior
        
        Returns:
            consumption: Amount consumed
            info: Decision information for explainability
        """
        # Observe state
        observation = self.observe(macro_state)
        
        # Select action
        action, explanation = self.select_action(observation)
        
        # Execute action
        consumption_rate = self.CONSUMPTION_RATES[action]
        consumption = self.state.income * consumption_rate
        savings = self.state.income - consumption
        
        # Update wealth
        interest_rate = macro_state.get('interest_rate', 0.05)
        inflation = macro_state.get('inflation', 0.02)
        real_return = interest_rate - inflation
        
        self.state.wealth = self.state.wealth * (1 + real_return / 4) + savings  # Quarterly
        self.consumption_history.append(consumption)
        
        # Calculate reward
        reward = self.calculate_reward(macro_state, action)
        self.total_reward += reward
        
        # Store experience for learning
        next_observation = self.observe(macro_state)
        experience = Experience(
            state=observation,
            action=action,
            reward=reward,
            next_state=next_observation,
            done=False
        )
        self.learn(experience)
        
        # Decision info
        info = {
            'agent_id': self.agent_id,
            'income_class': self.profile.income_class.value,
            'is_employed': self.is_employed,
            'consumption': consumption,
            'savings': savings,
            'wealth': self.state.wealth,
            'action': self.interpret_action(action),
            'reward': reward,
            'explanation': explanation
        }
        
        return consumption, info
    
    def get_aggregate_demand(self) -> float:
        """Get this consumer's contribution to aggregate demand"""
        if self.consumption_history:
            return self.consumption_history[-1]
        return self.state.income * 0.7  # Default consumption
    
    def respond_to_tax_change(self, old_rate: float, new_rate: float):
        """Adjust behavior in response to tax rate change"""
        tax_change = new_rate - old_rate
        
        # Disposable income effect
        income_effect = -tax_change * self.profile.base_income
        
        # Adjust base income for tax
        self.profile.base_income *= (1 - tax_change)
        
        # Higher taxes may increase precautionary saving
        if tax_change > 0:
            self.mpc *= 0.95  # Reduce consumption propensity
    
    def respond_to_interest_rate_change(self, old_rate: float, new_rate: float):
        """Adjust behavior in response to interest rate change"""
        rate_change = new_rate - old_rate
        
        # Higher rates incentivize saving
        if rate_change > 0:
            self.mpc *= 0.98
            self.profile.savings_preference = min(0.5, self.profile.savings_preference + 0.02)
        else:
            self.mpc *= 1.02
            self.profile.savings_preference = max(0.05, self.profile.savings_preference - 0.02)


class ConsumerPopulation:
    """
    Manages a population of heterogeneous consumers
    """
    
    def __init__(self, size: int = 1000, income_distribution: Optional[Dict] = None):
        self.consumers: List[ConsumerAgent] = []
        self.size = size
        
        # Default income distribution
        self.income_distribution = income_distribution or {
            IncomeClass.LOW: 0.30,
            IncomeClass.MIDDLE: 0.50,
            IncomeClass.HIGH: 0.20
        }
        
        self._initialize_population()
    
    def _initialize_population(self):
        """Create diverse consumer population"""
        for i in range(self.size):
            # Determine income class
            roll = random.random()
            cumulative = 0
            income_class = IncomeClass.MIDDLE
            
            for ic, prob in self.income_distribution.items():
                cumulative += prob
                if roll < cumulative:
                    income_class = ic
                    break
            
            # Create profile
            if income_class == IncomeClass.LOW:
                base_income = random.uniform(20000, 40000)
            elif income_class == IncomeClass.MIDDLE:
                base_income = random.uniform(40000, 100000)
            else:
                base_income = random.uniform(100000, 500000)
            
            profile = ConsumerProfile(
                income_class=income_class,
                base_income=base_income,
                risk_tolerance=random.uniform(0.2, 0.8),
                savings_preference=random.uniform(0.1, 0.4),
                employment_probability=random.uniform(0.85, 0.98),
                age=random.randint(22, 65),
                has_mortgage=random.random() < 0.4,
                has_dependents=random.random() < 0.35
            )
            
            consumer = ConsumerAgent(
                agent_id=f"consumer_{i}",
                profile=profile
            )
            self.consumers.append(consumer)
    
    def step(self, macro_state: Dict) -> Dict:
        """
        Step all consumers and return aggregate statistics
        """
        total_consumption = 0
        total_savings = 0
        employed_count = 0
        class_consumption = {ic.value: 0 for ic in IncomeClass}
        class_counts = {ic.value: 0 for ic in IncomeClass}
        
        for consumer in self.consumers:
            consumption, info = consumer.step(macro_state)
            total_consumption += consumption
            total_savings += consumer.state.wealth
            
            if consumer.is_employed:
                employed_count += 1
            
            class_key = consumer.profile.income_class.value
            class_consumption[class_key] += consumption
            class_counts[class_key] += 1
        
        # Calculate averages
        avg_consumption_by_class = {}
        for ic in IncomeClass:
            if class_counts[ic.value] > 0:
                avg_consumption_by_class[ic.value] = class_consumption[ic.value] / class_counts[ic.value]
            else:
                avg_consumption_by_class[ic.value] = 0
        
        return {
            'total_consumption': total_consumption,
            'average_consumption': total_consumption / self.size,
            'total_savings': total_savings,
            'average_savings': total_savings / self.size,
            'employment_rate': employed_count / self.size,
            'consumption_by_class': avg_consumption_by_class,
            'consumer_count': self.size
        }
    
    def get_aggregate_demand(self) -> float:
        """Get total consumer demand"""
        return sum(c.get_aggregate_demand() for c in self.consumers)
    
    def apply_policy(self, policy_type: str, old_value: float, new_value: float):
        """Apply policy change to all consumers"""
        for consumer in self.consumers:
            if policy_type == 'tax_rate':
                consumer.respond_to_tax_change(old_value, new_value)
            elif policy_type == 'interest_rate':
                consumer.respond_to_interest_rate_change(old_value, new_value)
