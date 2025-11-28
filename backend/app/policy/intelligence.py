"""
VALORA Policy Intelligence Engine
Multi-agent debate, risk scoring, scenario comparison, and forecasting
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Policy risk levels"""
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    SEVERE = "severe"


class PolicyCategory(Enum):
    """Categories of policy interventions"""
    MONETARY_EXPANSION = "monetary_expansion"
    MONETARY_CONTRACTION = "monetary_contraction"
    FISCAL_STIMULUS = "fiscal_stimulus"
    FISCAL_AUSTERITY = "fiscal_austerity"
    REGULATORY_TIGHTENING = "regulatory_tightening"
    REGULATORY_LOOSENING = "regulatory_loosening"
    EMERGENCY_INTERVENTION = "emergency_intervention"


@dataclass
class PolicyProposal:
    """A proposed policy intervention"""
    proposal_id: str
    name: str
    description: str
    category: PolicyCategory
    
    # Policy parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Target changes
    target_inflation: Optional[float] = None
    target_unemployment: Optional[float] = None
    target_gdp_growth: Optional[float] = None
    
    # Constraints
    max_deficit_increase: Optional[float] = None
    max_debt_increase: Optional[float] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "system"
    
    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'parameters': self.parameters,
            'target_inflation': self.target_inflation,
            'target_unemployment': self.target_unemployment,
            'target_gdp_growth': self.target_gdp_growth,
            'max_deficit_increase': self.max_deficit_increase,
            'max_debt_increase': self.max_debt_increase,
            'created_at': self.created_at,
            'created_by': self.created_by
        }


@dataclass
class ImpactForecast:
    """Forecasted impact of a policy"""
    horizon: str  # "1y", "3y", "5y"
    gdp_impact: float
    gdp_confidence_interval: Tuple[float, float]
    inflation_impact: float
    inflation_confidence_interval: Tuple[float, float]
    unemployment_impact: float
    unemployment_confidence_interval: Tuple[float, float]
    debt_impact: float
    probability_of_recession: float
    probability_of_overheating: float


@dataclass
class RiskAssessment:
    """Risk assessment for a policy"""
    overall_risk: RiskLevel
    risk_score: float  # 0-100
    
    # Component risks
    inflation_risk: float
    deflation_risk: float
    recession_risk: float
    overheating_risk: float
    financial_stability_risk: float
    fiscal_sustainability_risk: float
    
    # Specific concerns
    concerns: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)


@dataclass
class DebatePosition:
    """An agent's position in policy debate"""
    agent_name: str
    agent_role: str  # "hawk", "dove", "neutral", "analyst"
    stance: str  # "support", "oppose", "conditional"
    
    # Arguments
    supporting_arguments: List[str] = field(default_factory=list)
    opposing_arguments: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    
    confidence: float = 0.8
    priority_concerns: List[str] = field(default_factory=list)


@dataclass
class PolicyAnalysis:
    """Complete analysis of a policy proposal"""
    proposal: PolicyProposal
    risk_assessment: RiskAssessment
    impact_forecasts: Dict[str, ImpactForecast]  # keyed by horizon
    debate_positions: List[DebatePosition]
    
    # Recommendations
    recommendation: str  # "implement", "modify", "reject", "delay"
    recommended_modifications: List[str] = field(default_factory=list)
    implementation_timeline: Optional[str] = None
    
    # Executive summary
    executive_summary: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'proposal': self.proposal.to_dict(),
            'risk_assessment': {
                'overall_risk': self.risk_assessment.overall_risk.value,
                'risk_score': self.risk_assessment.risk_score,
                'inflation_risk': self.risk_assessment.inflation_risk,
                'recession_risk': self.risk_assessment.recession_risk,
                'concerns': self.risk_assessment.concerns,
                'mitigations': self.risk_assessment.mitigations
            },
            'impact_forecasts': {
                horizon: {
                    'gdp_impact': f.gdp_impact,
                    'inflation_impact': f.inflation_impact,
                    'unemployment_impact': f.unemployment_impact,
                    'probability_of_recession': f.probability_of_recession
                }
                for horizon, f in self.impact_forecasts.items()
            },
            'debate_summary': [
                {
                    'agent': p.agent_name,
                    'stance': p.stance,
                    'key_argument': p.supporting_arguments[0] if p.supporting_arguments else p.opposing_arguments[0] if p.opposing_arguments else ""
                }
                for p in self.debate_positions
            ],
            'recommendation': self.recommendation,
            'recommended_modifications': self.recommended_modifications,
            'executive_summary': self.executive_summary
        }


class PolicyDebateEngine:
    """
    Multi-agent debate system for policy analysis
    Simulates different economic perspectives
    """
    
    def __init__(self):
        # Define debate agents with different perspectives
        self.debate_agents = [
            {
                'name': 'Inflation Hawk',
                'role': 'hawk',
                'priority': 'price_stability',
                'bias': {'inflation': -2.0, 'unemployment': 0.5}
            },
            {
                'name': 'Employment Dove',
                'role': 'dove',
                'priority': 'full_employment',
                'bias': {'inflation': 0.5, 'unemployment': -2.0}
            },
            {
                'name': 'Fiscal Conservative',
                'role': 'conservative',
                'priority': 'debt_sustainability',
                'bias': {'deficit': -2.0, 'spending': -1.5}
            },
            {
                'name': 'Growth Advocate',
                'role': 'growth',
                'priority': 'economic_growth',
                'bias': {'gdp_growth': 2.0, 'investment': 1.5}
            },
            {
                'name': 'Financial Stability Officer',
                'role': 'stability',
                'priority': 'financial_stability',
                'bias': {'credit_growth': -1.0, 'leverage': -1.5}
            },
            {
                'name': 'Neutral Analyst',
                'role': 'neutral',
                'priority': 'balanced_assessment',
                'bias': {}
            }
        ]
    
    def generate_debate(
        self,
        proposal: PolicyProposal,
        macro_state: Dict,
        impact_forecasts: Dict[str, ImpactForecast]
    ) -> List[DebatePosition]:
        """Generate debate positions from all agents"""
        positions = []
        
        for agent in self.debate_agents:
            position = self._generate_position(
                agent, proposal, macro_state, impact_forecasts
            )
            positions.append(position)
        
        return positions
    
    def _generate_position(
        self,
        agent: Dict,
        proposal: PolicyProposal,
        macro_state: Dict,
        impact_forecasts: Dict[str, ImpactForecast]
    ) -> DebatePosition:
        """Generate a single agent's debate position"""
        
        supporting = []
        opposing = []
        conditions = []
        
        # Get 1-year forecast
        forecast_1y = impact_forecasts.get('1y')
        
        # Inflation Hawk perspective
        if agent['role'] == 'hawk':
            if proposal.category in [PolicyCategory.MONETARY_EXPANSION, PolicyCategory.FISCAL_STIMULUS]:
                if macro_state.get('inflation', 0.02) > 0.025:
                    opposing.append("Current inflation already above target; stimulus risks price instability")
                    opposing.append("Inflation expectations may become unanchored")
                else:
                    conditions.append("Support contingent on inflation staying below 3%")
                    supporting.append("Limited inflation risk given current slack")
            elif proposal.category in [PolicyCategory.MONETARY_CONTRACTION]:
                supporting.append("Rate increase will anchor inflation expectations")
                supporting.append("Preemptive tightening prevents larger corrections later")
        
        # Employment Dove perspective
        elif agent['role'] == 'dove':
            unemployment = macro_state.get('unemployment', 0.05)
            if proposal.category in [PolicyCategory.MONETARY_EXPANSION, PolicyCategory.FISCAL_STIMULUS]:
                if unemployment > 0.055:
                    supporting.append(f"Unemployment at {unemployment:.1%} requires demand support")
                    supporting.append("Labor market slack justifies accommodation")
                else:
                    conditions.append("Monitor for signs of labor market overheating")
            elif proposal.category in [PolicyCategory.MONETARY_CONTRACTION]:
                opposing.append("Premature tightening risks employment gains")
                opposing.append("Wait for clearer signs of wage-price spiral")
        
        # Fiscal Conservative perspective
        elif agent['role'] == 'conservative':
            debt_to_gdp = macro_state.get('debt_to_gdp', 0.5)
            if proposal.category == PolicyCategory.FISCAL_STIMULUS:
                if debt_to_gdp > 0.8:
                    opposing.append(f"Debt-to-GDP at {debt_to_gdp:.0%} leaves no fiscal space")
                    opposing.append("Bond market confidence at risk")
                else:
                    conditions.append("Implement with clear sunset provisions")
                    conditions.append("Identify offsetting spending cuts")
            elif proposal.category == PolicyCategory.FISCAL_AUSTERITY:
                supporting.append("Fiscal consolidation improves long-term sustainability")
                supporting.append("Reduced crowding out benefits private investment")
        
        # Growth Advocate perspective
        elif agent['role'] == 'growth':
            gdp_growth = macro_state.get('gdp_growth', 0.025)
            if proposal.category in [PolicyCategory.FISCAL_STIMULUS, PolicyCategory.MONETARY_EXPANSION]:
                if gdp_growth < 0.02:
                    supporting.append("Below-trend growth requires policy support")
                    supporting.append("Multiplier effects boost long-term potential")
                else:
                    conditions.append("Target investment rather than consumption")
            elif proposal.category in [PolicyCategory.FISCAL_AUSTERITY, PolicyCategory.MONETARY_CONTRACTION]:
                if gdp_growth < 0.015:
                    opposing.append("Contractionary policy risks recession")
                else:
                    conditions.append("Phase in gradually to avoid demand shock")
        
        # Financial Stability perspective
        elif agent['role'] == 'stability':
            credit_growth = macro_state.get('credit_growth', 0.05)
            npl_ratio = macro_state.get('loan_default_rate', 0.02)
            
            if proposal.category == PolicyCategory.MONETARY_EXPANSION:
                if credit_growth > 0.1:
                    opposing.append("Easy money fueling excessive credit growth")
                    opposing.append("Asset price inflation risks financial stability")
                else:
                    conditions.append("Complement with macroprudential measures")
            elif proposal.category == PolicyCategory.REGULATORY_TIGHTENING:
                supporting.append("Stronger buffers improve system resilience")
                supporting.append("Counter-cyclical measures appropriate")
        
        # Neutral Analyst perspective
        elif agent['role'] == 'neutral':
            if forecast_1y:
                if forecast_1y.probability_of_recession > 0.3:
                    supporting.append("Analysis suggests elevated recession risk warrants action")
                if abs(forecast_1y.inflation_impact) > 0.02:
                    conditions.append("Monitor inflation closely given significant projected impact")
            supporting.append("Policy consistent with current economic conditions")
            conditions.append("Recommend quarterly policy review")
        
        # Determine overall stance
        if len(supporting) > len(opposing):
            stance = "support"
        elif len(opposing) > len(supporting):
            stance = "oppose"
        else:
            stance = "conditional"
        
        return DebatePosition(
            agent_name=agent['name'],
            agent_role=agent['role'],
            stance=stance,
            supporting_arguments=supporting,
            opposing_arguments=opposing,
            conditions=conditions,
            confidence=0.7 + 0.3 * (len(supporting) + len(opposing)) / 5,
            priority_concerns=[agent['priority']]
        )


class ImpactForecaster:
    """
    Multi-horizon policy impact forecasting with confidence intervals
    """
    
    def __init__(self):
        # Impact coefficients based on economic literature
        self.coefficients = {
            PolicyCategory.MONETARY_EXPANSION: {
                'gdp': 0.02,      # +2% GDP impact per 100bp rate cut
                'inflation': 0.005,  # +0.5pp inflation
                'unemployment': -0.003  # -0.3pp unemployment
            },
            PolicyCategory.MONETARY_CONTRACTION: {
                'gdp': -0.015,
                'inflation': -0.008,
                'unemployment': 0.004
            },
            PolicyCategory.FISCAL_STIMULUS: {
                'gdp': 0.015,  # Multiplier ~1.5
                'inflation': 0.003,
                'unemployment': -0.005
            },
            PolicyCategory.FISCAL_AUSTERITY: {
                'gdp': -0.01,
                'inflation': -0.002,
                'unemployment': 0.003
            }
        }
        
        # Horizon decay factors (impact diminishes over time)
        self.horizon_factors = {
            '1y': 1.0,
            '3y': 0.6,
            '5y': 0.3
        }
    
    def forecast(
        self,
        proposal: PolicyProposal,
        macro_state: Dict
    ) -> Dict[str, ImpactForecast]:
        """Generate impact forecasts for multiple horizons"""
        forecasts = {}
        
        base_coeffs = self.coefficients.get(proposal.category, {})
        
        # Policy intensity factor
        intensity = self._calculate_intensity(proposal)
        
        for horizon, factor in self.horizon_factors.items():
            # Base impacts
            gdp_impact = base_coeffs.get('gdp', 0) * intensity * factor
            inflation_impact = base_coeffs.get('inflation', 0) * intensity * factor
            unemployment_impact = base_coeffs.get('unemployment', 0) * intensity * factor
            
            # Adjust for current conditions
            current_output_gap = macro_state.get('output_gap', 0)
            if current_output_gap < -0.02:  # Recession
                gdp_impact *= 1.3  # Larger multiplier in slack
                unemployment_impact *= 1.2
            elif current_output_gap > 0.02:  # Overheating
                inflation_impact *= 1.5
                gdp_impact *= 0.7
            
            # Confidence intervals (widen with horizon)
            uncertainty = 0.01 * (1 + 0.5 * float(horizon[0]))
            
            # Probability calculations
            prob_recession = self._calculate_recession_probability(
                macro_state, gdp_impact
            )
            prob_overheating = self._calculate_overheating_probability(
                macro_state, inflation_impact
            )
            
            forecasts[horizon] = ImpactForecast(
                horizon=horizon,
                gdp_impact=gdp_impact,
                gdp_confidence_interval=(gdp_impact - uncertainty, gdp_impact + uncertainty),
                inflation_impact=inflation_impact,
                inflation_confidence_interval=(
                    inflation_impact - uncertainty/2,
                    inflation_impact + uncertainty/2
                ),
                unemployment_impact=unemployment_impact,
                unemployment_confidence_interval=(
                    unemployment_impact - uncertainty/2,
                    unemployment_impact + uncertainty/2
                ),
                debt_impact=self._calculate_debt_impact(proposal, macro_state, horizon),
                probability_of_recession=prob_recession,
                probability_of_overheating=prob_overheating
            )
        
        return forecasts
    
    def _calculate_intensity(self, proposal: PolicyProposal) -> float:
        """Calculate policy intensity from parameters"""
        intensity = 1.0
        
        params = proposal.parameters
        if 'rate_change' in params:
            intensity *= abs(params['rate_change']) / 0.0025  # Normalize to 25bp
        if 'spending_change' in params:
            intensity *= abs(params['spending_change']) / 0.05  # Normalize to 5%
        
        return max(0.5, min(2.0, intensity))
    
    def _calculate_recession_probability(
        self,
        macro_state: Dict,
        gdp_impact: float
    ) -> float:
        """Calculate probability of recession given policy impact"""
        current_growth = macro_state.get('gdp_growth', 0.025)
        projected_growth = current_growth + gdp_impact
        
        # Simple logistic probability
        if projected_growth >= 0.02:
            return 0.05
        elif projected_growth >= 0:
            return 0.10 + (0.02 - projected_growth) * 10
        else:
            return min(0.9, 0.30 + abs(projected_growth) * 20)
    
    def _calculate_overheating_probability(
        self,
        macro_state: Dict,
        inflation_impact: float
    ) -> float:
        """Calculate probability of overheating"""
        current_inflation = macro_state.get('inflation', 0.02)
        projected_inflation = current_inflation + inflation_impact
        
        if projected_inflation <= 0.03:
            return 0.05
        elif projected_inflation <= 0.05:
            return 0.10 + (projected_inflation - 0.03) * 10
        else:
            return min(0.9, 0.30 + (projected_inflation - 0.05) * 20)
    
    def _calculate_debt_impact(
        self,
        proposal: PolicyProposal,
        macro_state: Dict,
        horizon: str
    ) -> float:
        """Calculate impact on debt-to-GDP ratio"""
        current_debt = macro_state.get('debt_to_gdp', 0.5)
        
        if proposal.category == PolicyCategory.FISCAL_STIMULUS:
            # Stimulus increases debt
            return 0.02 * float(horizon[0])
        elif proposal.category == PolicyCategory.FISCAL_AUSTERITY:
            # Austerity reduces debt
            return -0.015 * float(horizon[0])
        else:
            # Monetary policy has indirect effect
            return 0.005 * float(horizon[0])


class RiskScorer:
    """
    Comprehensive risk scoring for policies
    """
    
    def assess(
        self,
        proposal: PolicyProposal,
        macro_state: Dict,
        impact_forecasts: Dict[str, ImpactForecast]
    ) -> RiskAssessment:
        """Generate comprehensive risk assessment"""
        
        concerns = []
        mitigations = []
        
        # Get 1-year forecast for primary assessment
        forecast = impact_forecasts.get('1y')
        
        # Inflation risk
        current_inflation = macro_state.get('inflation', 0.02)
        projected_inflation = current_inflation + (forecast.inflation_impact if forecast else 0)
        
        if projected_inflation > 0.05:
            inflation_risk = 0.9
            concerns.append(f"High inflation risk: projected {projected_inflation:.1%}")
        elif projected_inflation > 0.03:
            inflation_risk = 0.6
            concerns.append("Moderate inflation pressure expected")
        else:
            inflation_risk = 0.2
        
        # Deflation risk
        if projected_inflation < 0:
            deflation_risk = 0.8
            concerns.append("Deflation risk with negative projected inflation")
        elif projected_inflation < 0.01:
            deflation_risk = 0.4
        else:
            deflation_risk = 0.1
        
        # Recession risk
        recession_risk = forecast.probability_of_recession if forecast else 0.2
        if recession_risk > 0.4:
            concerns.append(f"Elevated recession probability: {recession_risk:.0%}")
        
        # Overheating risk
        overheating_risk = forecast.probability_of_overheating if forecast else 0.1
        if overheating_risk > 0.3:
            concerns.append("Risk of economic overheating")
        
        # Financial stability risk
        credit_growth = macro_state.get('credit_growth', 0.05)
        npl_ratio = macro_state.get('loan_default_rate', 0.02)
        
        if proposal.category == PolicyCategory.MONETARY_EXPANSION and credit_growth > 0.10:
            financial_risk = 0.7
            concerns.append("Loose policy may fuel credit bubble")
        elif npl_ratio > 0.05:
            financial_risk = 0.6
            concerns.append("Banking sector stress elevated")
        else:
            financial_risk = 0.2
        
        # Fiscal sustainability risk
        debt_to_gdp = macro_state.get('debt_to_gdp', 0.5)
        forecast_5y = impact_forecasts.get('5y')
        
        projected_debt = debt_to_gdp + (forecast_5y.debt_impact if forecast_5y else 0)
        
        if projected_debt > 1.0:
            fiscal_risk = 0.9
            concerns.append(f"Unsustainable debt trajectory: {projected_debt:.0%} of GDP")
        elif projected_debt > 0.8:
            fiscal_risk = 0.6
            concerns.append("Fiscal space narrowing")
        else:
            fiscal_risk = 0.2
        
        # Generate mitigations
        if inflation_risk > 0.5:
            mitigations.append("Include automatic inflation triggers for policy reversal")
        if recession_risk > 0.4:
            mitigations.append("Prepare contingency stimulus measures")
        if financial_risk > 0.5:
            mitigations.append("Complement with macroprudential tightening")
        if fiscal_risk > 0.5:
            mitigations.append("Implement medium-term fiscal framework")
        
        # Calculate overall risk score
        risk_score = (
            inflation_risk * 0.25 +
            deflation_risk * 0.10 +
            recession_risk * 0.25 +
            overheating_risk * 0.10 +
            financial_risk * 0.15 +
            fiscal_risk * 0.15
        ) * 100
        
        # Determine risk level
        if risk_score >= 70:
            overall_risk = RiskLevel.SEVERE
        elif risk_score >= 55:
            overall_risk = RiskLevel.HIGH
        elif risk_score >= 40:
            overall_risk = RiskLevel.ELEVATED
        elif risk_score >= 25:
            overall_risk = RiskLevel.MODERATE
        else:
            overall_risk = RiskLevel.LOW
        
        return RiskAssessment(
            overall_risk=overall_risk,
            risk_score=risk_score,
            inflation_risk=inflation_risk,
            deflation_risk=deflation_risk,
            recession_risk=recession_risk,
            overheating_risk=overheating_risk,
            financial_stability_risk=financial_risk,
            fiscal_sustainability_risk=fiscal_risk,
            concerns=concerns,
            mitigations=mitigations
        )


class PolicyIntelligenceEngine:
    """
    Main policy intelligence system
    Integrates forecasting, risk assessment, and debate
    """
    
    def __init__(self):
        self.forecaster = ImpactForecaster()
        self.risk_scorer = RiskScorer()
        self.debate_engine = PolicyDebateEngine()
        
        # Policy history for versioning
        self.policy_history: List[PolicyAnalysis] = []
        self.policy_versions: Dict[str, List[PolicyProposal]] = {}
    
    def analyze_policy(
        self,
        proposal: PolicyProposal,
        macro_state: Dict
    ) -> PolicyAnalysis:
        """
        Complete analysis of a policy proposal
        """
        logger.info(f"Analyzing policy: {proposal.name}")
        
        # Generate impact forecasts
        impact_forecasts = self.forecaster.forecast(proposal, macro_state)
        
        # Assess risks
        risk_assessment = self.risk_scorer.assess(
            proposal, macro_state, impact_forecasts
        )
        
        # Generate debate
        debate_positions = self.debate_engine.generate_debate(
            proposal, macro_state, impact_forecasts
        )
        
        # Determine recommendation
        recommendation = self._determine_recommendation(
            risk_assessment, debate_positions
        )
        
        # Generate modifications if needed
        modifications = self._generate_modifications(
            proposal, risk_assessment, macro_state
        )
        
        # Create executive summary
        summary = self._generate_executive_summary(
            proposal, risk_assessment, impact_forecasts, recommendation
        )
        
        analysis = PolicyAnalysis(
            proposal=proposal,
            risk_assessment=risk_assessment,
            impact_forecasts=impact_forecasts,
            debate_positions=debate_positions,
            recommendation=recommendation,
            recommended_modifications=modifications,
            executive_summary=summary
        )
        
        # Store in history
        self.policy_history.append(analysis)
        
        # Version tracking
        if proposal.name not in self.policy_versions:
            self.policy_versions[proposal.name] = []
        self.policy_versions[proposal.name].append(proposal)
        
        return analysis
    
    def _determine_recommendation(
        self,
        risk: RiskAssessment,
        positions: List[DebatePosition]
    ) -> str:
        """Determine overall recommendation"""
        
        # Count stances
        support = sum(1 for p in positions if p.stance == 'support')
        oppose = sum(1 for p in positions if p.stance == 'oppose')
        conditional = sum(1 for p in positions if p.stance == 'conditional')
        
        # Risk threshold
        if risk.overall_risk == RiskLevel.SEVERE:
            return "reject"
        
        if risk.overall_risk == RiskLevel.HIGH:
            if support > oppose + conditional:
                return "modify"
            else:
                return "reject"
        
        if support > oppose:
            if conditional > 0:
                return "implement"
            return "implement"
        elif oppose > support:
            return "delay"
        else:
            return "modify"
    
    def _generate_modifications(
        self,
        proposal: PolicyProposal,
        risk: RiskAssessment,
        macro_state: Dict
    ) -> List[str]:
        """Generate recommended policy modifications"""
        mods = []
        
        if risk.inflation_risk > 0.5:
            mods.append("Reduce policy magnitude by 25%")
            mods.append("Add inflation circuit breaker at 4%")
        
        if risk.recession_risk > 0.4:
            if proposal.category in [PolicyCategory.MONETARY_CONTRACTION, PolicyCategory.FISCAL_AUSTERITY]:
                mods.append("Phase in over 4 quarters instead of immediate")
                mods.append("Include automatic stabilizer provisions")
        
        if risk.fiscal_sustainability_risk > 0.5:
            mods.append("Include sunset clause after 2 years")
            mods.append("Pair with medium-term fiscal consolidation plan")
        
        if risk.financial_stability_risk > 0.5:
            mods.append("Complement with countercyclical capital buffer")
        
        return mods
    
    def _generate_executive_summary(
        self,
        proposal: PolicyProposal,
        risk: RiskAssessment,
        forecasts: Dict[str, ImpactForecast],
        recommendation: str
    ) -> str:
        """Generate executive summary"""
        forecast_1y = forecasts.get('1y')
        
        summary = f"""
POLICY ANALYSIS: {proposal.name}
{'='*50}

RECOMMENDATION: {recommendation.upper()}

OVERVIEW:
{proposal.description}

PROJECTED IMPACT (1-Year):
• GDP Growth: {forecast_1y.gdp_impact:+.1%} ({forecast_1y.gdp_confidence_interval[0]:+.1%} to {forecast_1y.gdp_confidence_interval[1]:+.1%})
• Inflation: {forecast_1y.inflation_impact:+.1%}
• Unemployment: {forecast_1y.unemployment_impact:+.1%}
• Recession Probability: {forecast_1y.probability_of_recession:.0%}

RISK ASSESSMENT:
• Overall Risk: {risk.overall_risk.value.upper()} (Score: {risk.risk_score:.0f}/100)
• Key Concerns: {'; '.join(risk.concerns[:3]) if risk.concerns else 'None identified'}

KEY MITIGATIONS:
{chr(10).join(f'• {m}' for m in risk.mitigations[:3]) if risk.mitigations else '• None required'}
"""
        return summary.strip()
    
    def compare_scenarios(
        self,
        proposals: List[PolicyProposal],
        macro_state: Dict
    ) -> Dict:
        """Compare multiple policy scenarios"""
        analyses = [self.analyze_policy(p, macro_state) for p in proposals]
        
        comparison = {
            'scenarios': [],
            'best_for_growth': None,
            'best_for_stability': None,
            'lowest_risk': None
        }
        
        best_growth = -float('inf')
        best_stability = float('inf')
        lowest_risk = float('inf')
        
        for analysis in analyses:
            forecast = analysis.impact_forecasts.get('1y')
            
            scenario_data = {
                'name': analysis.proposal.name,
                'recommendation': analysis.recommendation,
                'risk_score': analysis.risk_assessment.risk_score,
                'gdp_impact': forecast.gdp_impact if forecast else 0,
                'inflation_impact': forecast.inflation_impact if forecast else 0,
                'unemployment_impact': forecast.unemployment_impact if forecast else 0
            }
            comparison['scenarios'].append(scenario_data)
            
            if forecast:
                if forecast.gdp_impact > best_growth:
                    best_growth = forecast.gdp_impact
                    comparison['best_for_growth'] = analysis.proposal.name
                
                volatility = abs(forecast.inflation_impact) + abs(forecast.unemployment_impact)
                if volatility < best_stability:
                    best_stability = volatility
                    comparison['best_for_stability'] = analysis.proposal.name
            
            if analysis.risk_assessment.risk_score < lowest_risk:
                lowest_risk = analysis.risk_assessment.risk_score
                comparison['lowest_risk'] = analysis.proposal.name
        
        return comparison
    
    def get_policy_history(self, policy_name: Optional[str] = None) -> List[Dict]:
        """Get policy analysis history"""
        if policy_name:
            return [
                a.to_dict() for a in self.policy_history 
                if a.proposal.name == policy_name
            ]
        return [a.to_dict() for a in self.policy_history[-20:]]
    
    def rollback_policy(self, policy_name: str, version: int = -1) -> Optional[PolicyProposal]:
        """Get a previous version of a policy"""
        versions = self.policy_versions.get(policy_name, [])
        if versions and abs(version) <= len(versions):
            return versions[version]
        return None
