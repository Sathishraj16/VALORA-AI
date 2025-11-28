"""
VALORA Bank Agent
RL-based bank with loan risk assessment, liquidity management, and interest rate optimization
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import random

from .base_agent import BaseAgent, AgentType, Experience


class BankType(Enum):
    """Types of banking institutions"""
    COMMERCIAL = "commercial"
    INVESTMENT = "investment"
    RETAIL = "retail"
    CENTRAL = "central"


class LoanType(Enum):
    """Types of loans"""
    CONSUMER = "consumer"
    MORTGAGE = "mortgage"
    BUSINESS = "business"
    CORPORATE = "corporate"


@dataclass
class Loan:
    """Individual loan record"""
    loan_id: str
    loan_type: LoanType
    principal: float
    interest_rate: float
    term_months: int
    remaining_balance: float
    borrower_id: str
    risk_score: float  # 0-1, higher = riskier
    is_defaulted: bool = False
    months_delinquent: int = 0


@dataclass
class BankProfile:
    """Bank characteristics"""
    bank_type: BankType
    initial_assets: float
    initial_deposits: float
    tier1_capital_ratio: float  # Regulatory capital
    risk_appetite: float  # 0-1
    market_share: float


class CreditRiskClassifier:
    """
    Simple logistic regression-style credit risk model
    In production: use XGBoost or neural network
    """
    
    def __init__(self):
        # Feature weights (pretrained-like)
        self.weights = np.array([
            -0.5,   # Debt-to-income ratio (higher = riskier)
            0.3,    # Employment stability
            -0.2,   # Interest rate (higher rate = higher risk)
            0.4,    # Credit history length
            -0.6,   # Number of delinquencies
            0.2,    # Income level
            -0.3,   # Loan-to-value ratio
            -0.4,   # Unemployment rate (macro)
        ])
        self.bias = 0.5
    
    def predict_default_probability(self, features: np.ndarray) -> float:
        """Predict probability of default"""
        logit = np.dot(features, self.weights) + self.bias
        probability = 1 / (1 + np.exp(-logit))
        return np.clip(probability, 0.001, 0.999)
    
    def update(self, features: np.ndarray, actual_default: bool, learning_rate: float = 0.01):
        """Online learning update"""
        predicted = self.predict_default_probability(features)
        error = (1 if actual_default else 0) - predicted
        gradient = error * predicted * (1 - predicted) * features
        self.weights += learning_rate * gradient


class BankAgent(BaseAgent):
    """
    Bank agent with RL for credit and liquidity decisions
    
    State Space (12 dimensions):
    - Total assets (normalized)
    - Total deposits (normalized)
    - Loan portfolio size
    - Non-performing loan ratio
    - Reserve ratio
    - Capital adequacy ratio
    - Interest rate spread
    - Macroeconomic: GDP growth
    - Macroeconomic: Unemployment
    - Macroeconomic: Inflation
    - Macroeconomic: Central bank rate
    - Liquidity coverage ratio
    
    Action Space (8 actions):
    Lending: {tighten, maintain, loosen}
    Rates: {decrease, maintain, increase}
    + special actions for stress scenarios
    
    0: Tighten lending + decrease rates
    1: Tighten lending + maintain rates
    2: Tighten lending + increase rates
    3: Maintain lending + decrease rates
    4: Maintain lending + maintain rates (status quo)
    5: Maintain lending + increase rates
    6: Loosen lending + decrease rates
    7: Loosen lending + maintain rates
    """
    
    STATE_DIM = 12
    ACTION_DIM = 8
    
    def __init__(
        self,
        agent_id: str,
        profile: Optional[BankProfile] = None,
        learning_rate: float = 0.001,
        discount_factor: float = 0.99
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.BANK,
            state_dim=self.STATE_DIM,
            action_dim=self.ACTION_DIM,
            learning_rate=learning_rate,
            discount_factor=discount_factor
        )
        
        self.profile = profile or self._generate_random_profile()
        
        # Balance sheet
        self.assets = self.profile.initial_assets
        self.deposits = self.profile.initial_deposits
        self.reserves = self.deposits * 0.1  # 10% reserve
        self.loans_outstanding = self.assets - self.reserves
        self.capital = self.assets * self.profile.tier1_capital_ratio
        
        # Loan portfolio
        self.loan_portfolio: List[Loan] = []
        self.npl_ratio = 0.02  # Non-performing loan ratio
        
        # Interest rates
        self.lending_rate = 0.08  # 8% base lending rate
        self.deposit_rate = 0.03  # 3% deposit rate
        
        # Credit standards
        self.credit_threshold = 0.3  # Max default probability for approval
        
        # Risk assessment
        self.risk_classifier = CreditRiskClassifier()
        
        # Metrics
        self.interest_income = 0
        self.interest_expense = 0
        self.net_interest_margin = 0
        self.provision_for_losses = 0
    
    def _generate_random_profile(self) -> BankProfile:
        """Generate random bank profile"""
        bank_type = random.choice([BankType.COMMERCIAL, BankType.RETAIL])
        
        if bank_type == BankType.COMMERCIAL:
            assets = random.uniform(1e9, 50e9)  # $1B - $50B
        else:
            assets = random.uniform(100e6, 5e9)  # $100M - $5B
        
        return BankProfile(
            bank_type=bank_type,
            initial_assets=assets,
            initial_deposits=assets * random.uniform(0.7, 0.9),
            tier1_capital_ratio=random.uniform(0.08, 0.15),
            risk_appetite=random.uniform(0.3, 0.7),
            market_share=random.uniform(0.01, 0.1)
        )
    
    def observe(self, macro_state: Dict) -> np.ndarray:
        """Convert macro state to bank's observation"""
        # Calculate key ratios
        if self.deposits > 0:
            reserve_ratio = self.reserves / self.deposits
        else:
            reserve_ratio = 0
        
        if self.assets > 0:
            capital_ratio = self.capital / self.assets
        else:
            capital_ratio = 0
        
        if self.loans_outstanding > 0:
            npl_amount = sum(l.remaining_balance for l in self.loan_portfolio if l.is_defaulted)
            self.npl_ratio = npl_amount / self.loans_outstanding
        
        # Interest rate spread
        spread = self.lending_rate - self.deposit_rate
        
        # Liquidity coverage ratio (simplified)
        lcr = self.reserves / (self.deposits * 0.25) if self.deposits > 0 else 0
        
        observation = np.array([
            self.assets / self.profile.initial_assets,
            self.deposits / self.profile.initial_deposits,
            self.loans_outstanding / self.assets if self.assets > 0 else 0,
            self.npl_ratio,
            reserve_ratio,
            capital_ratio,
            spread,
            macro_state.get('gdp_growth', 0.025),
            macro_state.get('unemployment', 0.05),
            macro_state.get('inflation', 0.02),
            macro_state.get('interest_rate', 0.05),
            min(lcr, 2.0),  # Cap at 200%
        ], dtype=np.float32)
        
        return observation
    
    def get_action_space(self) -> List[Dict]:
        """Define lending and rate actions"""
        actions = []
        lending_options = ['tighten', 'maintain', 'loosen']
        rate_options = ['decrease', 'maintain', 'increase']
        
        idx = 0
        for lending in lending_options[:2] + ['loosen']:
            for rate in rate_options:
                if idx >= self.ACTION_DIM:
                    break
                actions.append({
                    'id': idx,
                    'name': f'{lending}_lending_{rate}_rates',
                    'lending': lending,
                    'rate_action': rate,
                    'description': f'{lending.title()} lending standards, {rate} interest rates'
                })
                idx += 1
        
        return actions[:self.ACTION_DIM]
    
    def interpret_action(self, action_idx: int) -> Dict:
        """Convert action index to interpretable format"""
        actions = self.get_action_space()
        if action_idx < len(actions):
            return actions[action_idx]
        return actions[4]  # Default to status quo
    
    def calculate_reward(self, macro_state: Dict, action: int) -> float:
        """
        Calculate reward balancing profitability and stability
        
        Reward = α * ROA - β * NPL_penalty - γ * capital_violation + δ * stability_bonus
        """
        # Return on Assets
        if self.assets > 0:
            roa = (self.interest_income - self.interest_expense - self.provision_for_losses) / self.assets
        else:
            roa = 0
        
        # NPL penalty
        npl_penalty = max(0, self.npl_ratio - 0.03) * 10  # Penalty above 3% NPL
        
        # Capital adequacy violation
        capital_ratio = self.capital / self.assets if self.assets > 0 else 0
        if capital_ratio < 0.08:  # Below regulatory minimum
            capital_penalty = (0.08 - capital_ratio) * 20
        else:
            capital_penalty = 0
        
        # Stability bonus for maintaining healthy ratios
        if 0.08 <= capital_ratio <= 0.15 and self.npl_ratio < 0.05:
            stability_bonus = 0.3
        else:
            stability_bonus = 0
        
        reward = roa * 100 - npl_penalty - capital_penalty + stability_bonus
        return reward
    
    def assess_loan_application(
        self,
        borrower_features: Dict,
        loan_amount: float,
        loan_type: LoanType
    ) -> Tuple[bool, float, str]:
        """
        Assess a loan application
        
        Returns:
            approved: Whether loan is approved
            interest_rate: Offered rate if approved
            reasoning: Explanation
        """
        # Construct feature vector for risk model
        features = np.array([
            borrower_features.get('debt_to_income', 0.3),
            borrower_features.get('employment_stability', 0.8),
            self.lending_rate,
            borrower_features.get('credit_history_years', 5) / 30,
            borrower_features.get('delinquencies', 0) / 10,
            borrower_features.get('income', 50000) / 200000,
            borrower_features.get('loan_to_value', 0.8),
            borrower_features.get('unemployment_rate', 0.05),
        ])
        
        # Predict default probability
        default_prob = self.risk_classifier.predict_default_probability(features)
        
        # Check against credit threshold
        if default_prob > self.credit_threshold:
            return False, 0, f"Application denied: Risk score {default_prob:.2%} exceeds threshold {self.credit_threshold:.2%}"
        
        # Check capacity
        if loan_amount > self.reserves * 0.5:
            return False, 0, "Application denied: Insufficient liquidity"
        
        # Calculate risk-adjusted interest rate
        base_rate = self.lending_rate
        risk_premium = default_prob * 0.5  # Up to 50% premium for risky loans
        offered_rate = base_rate + risk_premium
        
        reasoning = f"Application approved: Risk score {default_prob:.2%}, Offered rate {offered_rate:.2%}"
        return True, offered_rate, reasoning
    
    def originate_loan(
        self,
        borrower_id: str,
        loan_type: LoanType,
        principal: float,
        interest_rate: float,
        term_months: int,
        risk_score: float
    ) -> Loan:
        """Create a new loan"""
        loan = Loan(
            loan_id=f"loan_{len(self.loan_portfolio)}_{self.agent_id}",
            loan_type=loan_type,
            principal=principal,
            interest_rate=interest_rate,
            term_months=term_months,
            remaining_balance=principal,
            borrower_id=borrower_id,
            risk_score=risk_score
        )
        
        self.loan_portfolio.append(loan)
        self.loans_outstanding += principal
        self.reserves -= principal
        
        return loan
    
    def process_loan_payments(self, macro_state: Dict):
        """Process monthly loan payments and defaults"""
        unemployment = macro_state.get('unemployment', 0.05)
        interest_rate = macro_state.get('interest_rate', 0.05)
        
        total_payments = 0
        new_defaults = 0
        
        for loan in self.loan_portfolio:
            if loan.is_defaulted:
                continue
            
            # Calculate default probability based on conditions
            base_default_prob = loan.risk_score * 0.1
            unemployment_effect = (unemployment - 0.05) * 0.5
            rate_effect = (interest_rate - 0.05) * 0.3
            
            default_prob = base_default_prob + unemployment_effect + rate_effect
            default_prob = np.clip(default_prob, 0.001, 0.5)
            
            if random.random() < default_prob:
                # Default occurs
                loan.is_defaulted = True
                new_defaults += 1
                # Write off 60% of remaining balance
                loss = loan.remaining_balance * 0.6
                self.provision_for_losses += loss
                self.capital -= loss
            else:
                # Payment received
                monthly_payment = loan.principal / loan.term_months
                interest_payment = loan.remaining_balance * loan.interest_rate / 12
                
                loan.remaining_balance -= monthly_payment
                total_payments += monthly_payment + interest_payment
                self.interest_income += interest_payment
        
        return total_payments, new_defaults
    
    def step(self, macro_state: Dict, deposit_flow: float = 0) -> Tuple[Dict, Dict]:
        """
        Execute one step of bank behavior
        """
        # Observe state
        observation = self.observe(macro_state)
        
        # Select action
        action, explanation = self.select_action(observation)
        action_info = self.interpret_action(action)
        
        # Execute lending policy change
        if action_info['lending'] == 'tighten':
            self.credit_threshold = max(0.1, self.credit_threshold - 0.05)
        elif action_info['lending'] == 'loosen':
            self.credit_threshold = min(0.5, self.credit_threshold + 0.05)
        
        # Execute rate change
        if action_info['rate_action'] == 'decrease':
            self.lending_rate = max(0.03, self.lending_rate - 0.0025)
            self.deposit_rate = max(0.01, self.deposit_rate - 0.002)
        elif action_info['rate_action'] == 'increase':
            self.lending_rate = min(0.20, self.lending_rate + 0.0025)
            self.deposit_rate = min(0.10, self.deposit_rate + 0.002)
        
        # Process deposit flows
        self.deposits += deposit_flow
        self.reserves += deposit_flow
        
        # Pay interest on deposits
        self.interest_expense = self.deposits * self.deposit_rate / 12
        
        # Process loan payments
        payments, defaults = self.process_loan_payments(macro_state)
        self.reserves += payments
        
        # Calculate metrics
        self.net_interest_margin = self.interest_income - self.interest_expense
        
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
            'credit_supply': self.reserves * 0.8,  # Available for lending
            'lending_rate': self.lending_rate,
            'deposit_rate': self.deposit_rate,
            'new_defaults': defaults,
        }
        
        info = {
            'agent_id': self.agent_id,
            'bank_type': self.profile.bank_type.value,
            'assets': self.assets,
            'deposits': self.deposits,
            'loans_outstanding': self.loans_outstanding,
            'npl_ratio': self.npl_ratio,
            'capital_ratio': self.capital / self.assets if self.assets > 0 else 0,
            'net_interest_margin': self.net_interest_margin,
            'action': action_info,
            'reward': reward,
            'explanation': explanation
        }
        
        return outputs, info
    
    def stress_test(self, scenario: Dict) -> Dict:
        """
        Run stress test under adverse scenario
        
        Scenario includes:
        - unemployment_shock: % increase in unemployment
        - gdp_shock: % decrease in GDP
        - rate_shock: % increase in rates
        """
        # Calculate stressed default rates
        base_default = self.npl_ratio
        unemployment_impact = scenario.get('unemployment_shock', 0) * 0.5
        gdp_impact = -scenario.get('gdp_shock', 0) * 0.3
        rate_impact = scenario.get('rate_shock', 0) * 0.2
        
        stressed_default = base_default + unemployment_impact + gdp_impact + rate_impact
        stressed_default = np.clip(stressed_default, 0, 0.5)
        
        # Calculate stressed losses
        stressed_losses = self.loans_outstanding * stressed_default * 0.6
        
        # Capital adequacy under stress
        stressed_capital = self.capital - stressed_losses
        stressed_capital_ratio = stressed_capital / self.assets if self.assets > 0 else 0
        
        return {
            'baseline_npl': self.npl_ratio,
            'stressed_npl': stressed_default,
            'stressed_losses': stressed_losses,
            'baseline_capital_ratio': self.capital / self.assets if self.assets > 0 else 0,
            'stressed_capital_ratio': stressed_capital_ratio,
            'passes_stress_test': stressed_capital_ratio >= 0.045,  # 4.5% minimum
            'capital_shortfall': max(0, 0.045 - stressed_capital_ratio) * self.assets
        }


class BankingSystem:
    """
    Manages the banking sector with multiple banks
    """
    
    def __init__(self, num_banks: int = 20):
        self.banks: List[BankAgent] = []
        
        for i in range(num_banks):
            bank = BankAgent(agent_id=f"bank_{i}")
            self.banks.append(bank)
    
    def step(self, macro_state: Dict) -> Dict:
        """Step all banks and return aggregate statistics"""
        total_credit = 0
        total_deposits = 0
        avg_lending_rate = 0
        total_defaults = 0
        
        for bank in self.banks:
            outputs, _ = bank.step(macro_state)
            total_credit += outputs['credit_supply']
            total_deposits += bank.deposits
            avg_lending_rate += outputs['lending_rate']
            total_defaults += outputs['new_defaults']
        
        avg_lending_rate /= len(self.banks)
        
        return {
            'total_credit_supply': total_credit,
            'total_deposits': total_deposits,
            'average_lending_rate': avg_lending_rate,
            'total_defaults': total_defaults,
            'system_npl_ratio': np.mean([b.npl_ratio for b in self.banks]),
            'system_capital_ratio': np.mean([
                b.capital / b.assets if b.assets > 0 else 0 
                for b in self.banks
            ])
        }
    
    def run_system_stress_test(self, scenario: Dict) -> Dict:
        """Run stress test on entire banking system"""
        results = []
        for bank in self.banks:
            result = bank.stress_test(scenario)
            results.append(result)
        
        return {
            'banks_tested': len(self.banks),
            'banks_passing': sum(1 for r in results if r['passes_stress_test']),
            'total_capital_shortfall': sum(r['capital_shortfall'] for r in results),
            'average_stressed_capital_ratio': np.mean([r['stressed_capital_ratio'] for r in results]),
            'worst_case_capital_ratio': min(r['stressed_capital_ratio'] for r in results),
        }
