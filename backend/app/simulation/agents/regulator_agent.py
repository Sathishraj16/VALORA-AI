"""
VALORA Regulator Agent
PPO-based central bank and fiscal authority with inflation targeting and employment stabilization
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

from .base_agent import BaseAgent, PPOAgent, AgentType, Experience


class PolicyType(Enum):
    """Types of policy actions"""
    MONETARY = "monetary"
    FISCAL = "fiscal"
    REGULATORY = "regulatory"
    MACROPRUDENTIAL = "macroprudential"


@dataclass
class PolicyDecision:
    """A policy decision made by the regulator"""
    policy_type: PolicyType
    instrument: str
    old_value: float
    new_value: float
    reasoning: str
    confidence: float
    expected_impact: Dict[str, float]
    tick: int


class MonetaryPolicyAgent(PPOAgent):
    """
    Central bank agent using PPO for optimal monetary policy
    
    Objective: Minimize loss function L = (π - π*)² + λ(u - u*)²
    
    State Space (10 dimensions):
    - Current inflation
    - Expected inflation
    - Output gap
    - Unemployment gap (u - u*)
    - GDP growth
    - Credit growth
    - Asset prices (proxy)
    - Exchange rate
    - Previous policy rate
    - Global rate environment
    
    Action Space (continuous):
    - Interest rate change: [-0.5%, +0.5%]
    - Reserve requirement change: [-2%, +2%]
    """
    
    STATE_DIM = 10
    ACTION_DIM = 2  # Continuous: [rate_change, reserve_change]
    
    def __init__(
        self,
        agent_id: str = "central_bank",
        inflation_target: float = 0.02,
        unemployment_target: float = 0.045,
        learning_rate: float = 0.0003
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.REGULATOR,
            state_dim=self.STATE_DIM,
            action_dim=self.ACTION_DIM,
            learning_rate=learning_rate
        )
        
        self.inflation_target = inflation_target
        self.unemployment_target = unemployment_target
        
        # Policy instruments
        self.policy_rate = 0.05  # 5% initial rate
        self.reserve_requirement = 0.10  # 10%
        
        # Taylor rule parameters (for hybrid policy)
        self.taylor_inflation_weight = 1.5
        self.taylor_output_weight = 0.5
        self.neutral_rate = 0.03
        
        # Policy history
        self.policy_history: List[PolicyDecision] = []
        
        # Loss tracking for optimization
        self.loss_history = []
        self.lambda_weight = 0.5  # Weight on unemployment in loss function
    
    def observe(self, macro_state: Dict) -> np.ndarray:
        """Convert macro state to central bank's observation"""
        observation = np.array([
            macro_state.get('inflation', 0.02),
            macro_state.get('expected_inflation', 0.02),
            macro_state.get('output_gap', 0),
            macro_state.get('unemployment', 0.05) - self.unemployment_target,
            macro_state.get('gdp_growth', 0.025),
            macro_state.get('credit_growth', 0.05),
            macro_state.get('asset_price_growth', 0.03),
            macro_state.get('exchange_rate', 1.0),
            self.policy_rate,
            macro_state.get('global_rate', 0.04),
        ], dtype=np.float32)
        
        return observation
    
    def get_action_space(self) -> List[Dict]:
        """Define continuous action bounds"""
        return [
            {
                'name': 'interest_rate_change',
                'min': -0.005,  # -50 bps
                'max': 0.005,   # +50 bps
                'description': 'Change in policy interest rate'
            },
            {
                'name': 'reserve_requirement_change',
                'min': -0.02,
                'max': 0.02,
                'description': 'Change in reserve requirement'
            }
        ]
    
    def interpret_action(self, action: np.ndarray) -> Dict:
        """Convert continuous action to interpretable format"""
        return {
            'interest_rate_change': float(action[0]) * 0.005,  # Scale to [-50, +50] bps
            'reserve_requirement_change': float(action[1]) * 0.02,
            'new_policy_rate': self.policy_rate + float(action[0]) * 0.005,
            'new_reserve_requirement': self.reserve_requirement + float(action[1]) * 0.02
        }
    
    def calculate_reward(self, macro_state: Dict, action: np.ndarray) -> float:
        """
        Reward based on minimizing dual mandate loss function
        
        L = (π - π*)² + λ(u - u*)² + smoothing_penalty
        
        Reward = -L (we maximize negative loss)
        """
        inflation = macro_state.get('inflation', 0.02)
        unemployment = macro_state.get('unemployment', 0.05)
        
        # Inflation gap (squared)
        inflation_loss = (inflation - self.inflation_target) ** 2
        
        # Unemployment gap (squared)
        unemployment_loss = (unemployment - self.unemployment_target) ** 2
        
        # Total loss
        total_loss = inflation_loss + self.lambda_weight * unemployment_loss
        self.loss_history.append(total_loss)
        
        # Smoothing penalty (penalize large rate changes)
        rate_change = float(action[0]) * 0.005
        smoothing_penalty = abs(rate_change) * 0.5
        
        # Financial stability consideration
        credit_growth = macro_state.get('credit_growth', 0.05)
        if credit_growth > 0.15:  # Excessive credit growth
            stability_penalty = (credit_growth - 0.15) * 2
        else:
            stability_penalty = 0
        
        reward = -total_loss * 100 - smoothing_penalty - stability_penalty
        return reward
    
    def taylor_rule_benchmark(self, macro_state: Dict) -> float:
        """Calculate Taylor rule rate for comparison"""
        inflation = macro_state.get('inflation', 0.02)
        output_gap = macro_state.get('output_gap', 0)
        
        taylor_rate = (
            self.neutral_rate +
            inflation +
            self.taylor_inflation_weight * (inflation - self.inflation_target) +
            self.taylor_output_weight * output_gap
        )
        
        return np.clip(taylor_rate, 0.001, 0.25)
    
    def step(self, macro_state: Dict, tick: int = 0) -> Tuple[Dict, Dict]:
        """
        Execute one step of monetary policy
        """
        # Observe state
        observation = self.observe(macro_state)
        
        # Select action using PPO policy
        action, explanation = self.select_action(observation)
        action_info = self.interpret_action(action)
        
        # Store old values
        old_rate = self.policy_rate
        old_reserve = self.reserve_requirement
        
        # Apply rate change with bounds
        new_rate = old_rate + action_info['interest_rate_change']
        self.policy_rate = np.clip(new_rate, 0.001, 0.25)  # 0.1% to 25%
        
        # Apply reserve requirement change with bounds
        new_reserve = old_reserve + action_info['reserve_requirement_change']
        self.reserve_requirement = np.clip(new_reserve, 0.02, 0.25)  # 2% to 25%
        
        # Calculate reward
        reward = self.calculate_reward(macro_state, action)
        self.total_reward += reward
        
        # Get Taylor rule benchmark
        taylor_rate = self.taylor_rule_benchmark(macro_state)
        
        # Generate reasoning
        reasoning = self._generate_policy_reasoning(macro_state, action_info, taylor_rate)
        
        # Record decision
        decision = PolicyDecision(
            policy_type=PolicyType.MONETARY,
            instrument='policy_rate',
            old_value=old_rate,
            new_value=self.policy_rate,
            reasoning=reasoning,
            confidence=explanation.get('confidence', 0.8),
            expected_impact={
                'inflation_effect': -action_info['interest_rate_change'] * 0.5,
                'gdp_effect': -action_info['interest_rate_change'] * 0.3,
                'unemployment_effect': action_info['interest_rate_change'] * 0.2
            },
            tick=tick
        )
        self.policy_history.append(decision)
        
        # Store experience for PPO update
        next_observation = self.observe(macro_state)
        self.store_transition(
            observation, action, reward, next_observation, False, 0
        )
        
        # Periodic PPO update
        if len(self.trajectories) >= 64:
            self.update()
        
        outputs = {
            'policy_rate': self.policy_rate,
            'reserve_requirement': self.reserve_requirement,
            'rate_change': self.policy_rate - old_rate,
        }
        
        info = {
            'agent_id': self.agent_id,
            'policy_rate': self.policy_rate,
            'reserve_requirement': self.reserve_requirement,
            'taylor_benchmark': taylor_rate,
            'policy_deviation': self.policy_rate - taylor_rate,
            'action': action_info,
            'reward': reward,
            'loss': self.loss_history[-1] if self.loss_history else 0,
            'reasoning': reasoning,
            'explanation': explanation
        }
        
        return outputs, info
    
    def _generate_policy_reasoning(
        self,
        macro_state: Dict,
        action_info: Dict,
        taylor_rate: float
    ) -> str:
        """Generate human-readable policy reasoning"""
        inflation = macro_state.get('inflation', 0.02)
        unemployment = macro_state.get('unemployment', 0.05)
        
        lines = []
        lines.append(f"Current Economic Conditions:")
        lines.append(f"  - Inflation: {inflation:.2%} (Target: {self.inflation_target:.2%})")
        lines.append(f"  - Unemployment: {unemployment:.2%} (Target: {self.unemployment_target:.2%})")
        lines.append(f"  - Output Gap: {macro_state.get('output_gap', 0):.2%}")
        
        lines.append(f"\nPolicy Decision:")
        lines.append(f"  - New Policy Rate: {self.policy_rate:.2%}")
        lines.append(f"  - Rate Change: {action_info['interest_rate_change']*100:.0f} bps")
        lines.append(f"  - Taylor Rule Benchmark: {taylor_rate:.2%}")
        
        # Rationale
        if inflation > self.inflation_target + 0.01:
            lines.append(f"\nRationale: Inflation {(inflation-self.inflation_target)*100:.1f}pp above target warrants tighter policy.")
        elif inflation < self.inflation_target - 0.01:
            lines.append(f"\nRationale: Inflation below target, accommodative policy appropriate.")
        
        if unemployment > self.unemployment_target + 0.02:
            lines.append(f"Labor market slack suggests room for stimulus.")
        
        return "\n".join(lines)


class FiscalPolicyAgent(PPOAgent):
    """
    Fiscal authority agent for tax and spending policy
    
    State Space (10 dimensions):
    - GDP growth
    - Output gap
    - Unemployment
    - Inflation
    - Debt-to-GDP ratio
    - Deficit as % of GDP
    - Tax revenue growth
    - Consumer confidence
    - Business confidence
    - Interest payments / GDP
    
    Action Space (continuous):
    - Tax rate change: [-2%, +2%]
    - Spending change: [-5%, +5%]
    """
    
    STATE_DIM = 10
    ACTION_DIM = 2
    
    def __init__(
        self,
        agent_id: str = "fiscal_authority",
        debt_target: float = 0.60,  # 60% debt-to-GDP
        learning_rate: float = 0.0003
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.REGULATOR,
            state_dim=self.STATE_DIM,
            action_dim=self.ACTION_DIM,
            learning_rate=learning_rate
        )
        
        self.debt_target = debt_target
        
        # Policy instruments
        self.tax_rate = 0.25  # 25% average tax rate
        self.spending_level = 200000  # Base spending
        
        # Fiscal rules
        self.max_deficit = 0.03  # 3% of GDP
        self.spending_multiplier = 1.5
        
        # Policy history
        self.policy_history: List[PolicyDecision] = []
    
    def observe(self, macro_state: Dict) -> np.ndarray:
        """Convert macro state to fiscal authority's observation"""
        gdp = macro_state.get('gdp', 1000000)
        
        observation = np.array([
            macro_state.get('gdp_growth', 0.025),
            macro_state.get('output_gap', 0),
            macro_state.get('unemployment', 0.05),
            macro_state.get('inflation', 0.02),
            macro_state.get('debt_to_gdp', 0.5),
            macro_state.get('fiscal_deficit', 0) / gdp if gdp > 0 else 0,
            macro_state.get('tax_revenue_growth', 0.03),
            macro_state.get('consumer_confidence', 100) / 100,
            macro_state.get('business_confidence', 100) / 100,
            macro_state.get('interest_payments', 0) / gdp if gdp > 0 else 0,
        ], dtype=np.float32)
        
        return observation
    
    def get_action_space(self) -> List[Dict]:
        """Define fiscal action space"""
        return [
            {
                'name': 'tax_rate_change',
                'min': -0.02,
                'max': 0.02,
                'description': 'Change in average tax rate'
            },
            {
                'name': 'spending_change',
                'min': -0.05,
                'max': 0.05,
                'description': 'Percentage change in government spending'
            }
        ]
    
    def interpret_action(self, action: np.ndarray) -> Dict:
        """Convert continuous action to interpretable format"""
        tax_change = float(action[0]) * 0.02
        spending_change = float(action[1]) * 0.05
        
        return {
            'tax_rate_change': tax_change,
            'spending_change': spending_change,
            'new_tax_rate': self.tax_rate + tax_change,
            'new_spending': self.spending_level * (1 + spending_change)
        }
    
    def calculate_reward(self, macro_state: Dict, action: np.ndarray) -> float:
        """
        Reward based on stabilization and sustainability
        
        Objectives:
        1. Output stabilization
        2. Debt sustainability
        3. Counter-cyclical policy
        """
        output_gap = macro_state.get('output_gap', 0)
        debt_to_gdp = macro_state.get('debt_to_gdp', 0.5)
        unemployment = macro_state.get('unemployment', 0.05)
        
        # Stabilization reward (reduce output gap)
        stabilization_reward = -abs(output_gap) * 10
        
        # Debt sustainability penalty
        if debt_to_gdp > self.debt_target:
            debt_penalty = (debt_to_gdp - self.debt_target) * 5
        else:
            debt_penalty = 0
        
        # Counter-cyclical bonus
        action_info = self.interpret_action(action)
        if output_gap < -0.02:  # Recession
            if action_info['spending_change'] > 0 or action_info['tax_rate_change'] < 0:
                countercyclical_bonus = 0.5
            else:
                countercyclical_bonus = -0.5
        elif output_gap > 0.02:  # Overheating
            if action_info['spending_change'] < 0 or action_info['tax_rate_change'] > 0:
                countercyclical_bonus = 0.5
            else:
                countercyclical_bonus = -0.5
        else:
            countercyclical_bonus = 0
        
        reward = stabilization_reward - debt_penalty + countercyclical_bonus
        return reward
    
    def step(self, macro_state: Dict, tick: int = 0) -> Tuple[Dict, Dict]:
        """Execute one step of fiscal policy"""
        observation = self.observe(macro_state)
        action, explanation = self.select_action(observation)
        action_info = self.interpret_action(action)
        
        # Store old values
        old_tax_rate = self.tax_rate
        old_spending = self.spending_level
        
        # Apply changes with bounds
        new_tax_rate = self.tax_rate + action_info['tax_rate_change']
        self.tax_rate = np.clip(new_tax_rate, 0.10, 0.50)  # 10% to 50%
        
        new_spending = self.spending_level * (1 + action_info['spending_change'])
        self.spending_level = max(50000, new_spending)  # Minimum spending floor
        
        # Calculate reward
        reward = self.calculate_reward(macro_state, action)
        self.total_reward += reward
        
        # Generate reasoning
        reasoning = self._generate_fiscal_reasoning(macro_state, action_info)
        
        # Record decision
        decision = PolicyDecision(
            policy_type=PolicyType.FISCAL,
            instrument='tax_and_spending',
            old_value=old_tax_rate,
            new_value=self.tax_rate,
            reasoning=reasoning,
            confidence=0.8,
            expected_impact={
                'gdp_effect': action_info['spending_change'] * self.spending_multiplier,
                'deficit_effect': action_info['spending_change'] - action_info['tax_rate_change']
            },
            tick=tick
        )
        self.policy_history.append(decision)
        
        # Store experience
        next_observation = self.observe(macro_state)
        self.store_transition(observation, action, reward, next_observation, False, 0)
        
        if len(self.trajectories) >= 64:
            self.update()
        
        outputs = {
            'tax_rate': self.tax_rate,
            'government_spending': self.spending_level,
        }
        
        info = {
            'agent_id': self.agent_id,
            'tax_rate': self.tax_rate,
            'spending_level': self.spending_level,
            'action': action_info,
            'reward': reward,
            'reasoning': reasoning,
            'explanation': explanation
        }
        
        return outputs, info
    
    def _generate_fiscal_reasoning(self, macro_state: Dict, action_info: Dict) -> str:
        """Generate fiscal policy reasoning"""
        output_gap = macro_state.get('output_gap', 0)
        debt_to_gdp = macro_state.get('debt_to_gdp', 0.5)
        
        lines = []
        lines.append(f"Fiscal Assessment:")
        lines.append(f"  - Output Gap: {output_gap:.2%}")
        lines.append(f"  - Debt-to-GDP: {debt_to_gdp:.2%}")
        
        lines.append(f"\nPolicy Action:")
        lines.append(f"  - Tax Rate: {self.tax_rate:.2%} (Δ{action_info['tax_rate_change']*100:+.1f}pp)")
        lines.append(f"  - Spending: ${self.spending_level:,.0f} (Δ{action_info['spending_change']*100:+.1f}%)")
        
        if output_gap < -0.02:
            lines.append(f"\nStance: Expansionary (addressing negative output gap)")
        elif output_gap > 0.02:
            lines.append(f"\nStance: Contractionary (addressing overheating)")
        else:
            lines.append(f"\nStance: Neutral (economy near potential)")
        
        return "\n".join(lines)


class RegulatorSystem:
    """
    Integrated regulatory system combining monetary and fiscal policy
    """
    
    def __init__(self):
        self.central_bank = MonetaryPolicyAgent()
        self.fiscal_authority = FiscalPolicyAgent()
        
        # Coordination mechanism
        self.policy_coordination_enabled = True
    
    def step(self, macro_state: Dict, tick: int = 0) -> Dict:
        """Execute coordinated policy step"""
        # Monetary policy first
        monetary_outputs, monetary_info = self.central_bank.step(macro_state, tick)
        
        # Fiscal policy (may consider monetary stance)
        if self.policy_coordination_enabled:
            # Adjust fiscal response based on monetary stance
            macro_state['monetary_stance'] = (
                'tight' if monetary_outputs['rate_change'] > 0 else
                'loose' if monetary_outputs['rate_change'] < 0 else
                'neutral'
            )
        
        fiscal_outputs, fiscal_info = self.fiscal_authority.step(macro_state, tick)
        
        # Combined policy output
        return {
            'policy_rate': monetary_outputs['policy_rate'],
            'reserve_requirement': monetary_outputs['reserve_requirement'],
            'tax_rate': fiscal_outputs['tax_rate'],
            'government_spending': fiscal_outputs['government_spending'],
            'monetary_info': monetary_info,
            'fiscal_info': fiscal_info,
        }
    
    def get_policy_summary(self) -> Dict:
        """Get summary of recent policy actions"""
        return {
            'monetary': self.central_bank.get_policy_summary(),
            'fiscal': self.fiscal_authority.get_policy_summary(),
            'monetary_history': [
                {
                    'tick': d.tick,
                    'instrument': d.instrument,
                    'old_value': d.old_value,
                    'new_value': d.new_value,
                    'reasoning': d.reasoning[:200]
                }
                for d in self.central_bank.policy_history[-10:]
            ],
            'fiscal_history': [
                {
                    'tick': d.tick,
                    'instrument': d.instrument,
                    'old_value': d.old_value,
                    'new_value': d.new_value,
                }
                for d in self.fiscal_authority.policy_history[-10:]
            ]
        }
