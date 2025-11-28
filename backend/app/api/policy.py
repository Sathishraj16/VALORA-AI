"""
VALORA Policy API Router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..policy.intelligence import (
    PolicyIntelligenceEngine,
    PolicyScenario,
    PolicyTool
)
from ..simulation.orchestrator import SimulationManager

router = APIRouter()

# Global manager references
simulation_manager = SimulationManager()
policy_engine = PolicyIntelligenceEngine()


class PolicyScenarioRequest(BaseModel):
    """Request to create a policy scenario"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    interest_rate_change: float = Field(default=0.0, ge=-0.05, le=0.05)
    reserve_requirement_change: float = Field(default=0.0, ge=-0.1, le=0.1)
    qe_amount: float = Field(default=0.0, ge=0, le=1000000)
    tax_change: float = Field(default=0.0, ge=-0.2, le=0.2)
    spending_change: float = Field(default=0.0, ge=-0.3, le=0.3)
    target_sector: Optional[str] = None
    timeline_months: int = Field(default=12, ge=1, le=60)


class PolicyComparisonRequest(BaseModel):
    """Request to compare policy scenarios"""
    simulation_id: str
    scenarios: List[PolicyScenarioRequest] = Field(..., min_items=2, max_items=5)
    horizon: int = Field(default=20, ge=5, le=100)


class PolicyAnalysisRequest(BaseModel):
    """Request policy analysis"""
    simulation_id: str
    target_inflation: Optional[float] = None
    target_unemployment: Optional[float] = None
    target_gdp_growth: Optional[float] = None
    constraints: Dict[str, Any] = {}


class PolicyRecommendationResponse(BaseModel):
    """Policy recommendation response"""
    recommendation_id: str
    timestamp: str
    policy_tools: List[Dict[str, Any]]
    expected_outcomes: Dict[str, float]
    risk_assessment: Dict[str, Any]
    confidence_score: float
    reasoning: str


class PolicyImpactResponse(BaseModel):
    """Policy impact response"""
    scenario_name: str
    impact_metrics: Dict[str, float]
    risk_scores: Dict[str, float]
    forecast: List[Dict[str, float]]


@router.post("/analyze", response_model=PolicyRecommendationResponse)
async def analyze_policy(request: PolicyAnalysisRequest):
    """Analyze current state and recommend policies"""
    sim = simulation_manager.get_simulation(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    # Build targets
    targets = {}
    if request.target_inflation is not None:
        targets['inflation'] = request.target_inflation
    if request.target_unemployment is not None:
        targets['unemployment'] = request.target_unemployment
    if request.target_gdp_growth is not None:
        targets['gdp_growth'] = request.target_gdp_growth
    
    if not targets:
        targets = {'inflation': 0.02, 'unemployment': 0.04, 'gdp_growth': 0.03}
    
    # Get current state
    current_state = {
        'gdp': sim.engine.state.gdp,
        'inflation': sim.engine.state.inflation,
        'unemployment': sim.engine.state.unemployment,
        'interest_rate': sim.engine.state.interest_rate,
        'gdp_growth': sim.engine.state.gdp_growth,
        'debt_to_gdp': sim.engine.state.debt_to_gdp,
        'consumer_confidence': sim.engine.state.consumer_confidence,
        'business_confidence': sim.engine.state.business_confidence
    }
    
    # Generate recommendation
    recommendation = policy_engine.recommend_policy(current_state, targets, request.constraints)
    
    return PolicyRecommendationResponse(
        recommendation_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat(),
        policy_tools=recommendation['policy_tools'],
        expected_outcomes=recommendation['expected_outcomes'],
        risk_assessment=recommendation['risk_assessment'],
        confidence_score=recommendation['confidence_score'],
        reasoning=recommendation['reasoning']
    )


@router.post("/compare")
async def compare_policies(request: PolicyComparisonRequest):
    """Compare multiple policy scenarios"""
    sim = simulation_manager.get_simulation(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    # Convert to PolicyScenario objects
    scenarios = []
    for s in request.scenarios:
        policy_tools = []
        
        if s.interest_rate_change != 0:
            policy_tools.append(PolicyTool(
                name="interest_rate",
                value=s.interest_rate_change,
                tool_type="monetary"
            ))
        
        if s.reserve_requirement_change != 0:
            policy_tools.append(PolicyTool(
                name="reserve_requirement",
                value=s.reserve_requirement_change,
                tool_type="monetary"
            ))
        
        if s.qe_amount > 0:
            policy_tools.append(PolicyTool(
                name="quantitative_easing",
                value=s.qe_amount,
                tool_type="monetary"
            ))
        
        if s.tax_change != 0:
            policy_tools.append(PolicyTool(
                name="tax_rate",
                value=s.tax_change,
                tool_type="fiscal"
            ))
        
        if s.spending_change != 0:
            policy_tools.append(PolicyTool(
                name="government_spending",
                value=s.spending_change,
                tool_type="fiscal"
            ))
        
        scenarios.append(PolicyScenario(
            name=s.name,
            description=s.description or "",
            policy_tools=policy_tools
        ))
    
    # Run comparison
    current_state = sim.engine.state.to_dict()
    comparison = policy_engine.compare_scenarios(scenarios, current_state, request.horizon)
    
    return {
        "simulation_id": request.simulation_id,
        "comparison": comparison,
        "recommendation": comparison.get('best_scenario', {})
    }


@router.post("/simulate-impact")
async def simulate_policy_impact(
    simulation_id: str,
    scenario: PolicyScenarioRequest,
    horizon: int = Query(20, ge=5, le=100)
):
    """Simulate the impact of a specific policy"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    # Create clone of current state
    import copy
    clone_state = copy.deepcopy(sim.engine.state)
    
    # Apply policy changes
    if scenario.interest_rate_change != 0:
        clone_state.interest_rate += scenario.interest_rate_change
    
    if scenario.tax_change != 0:
        clone_state.tax_rate += scenario.tax_change
    
    if scenario.spending_change != 0:
        clone_state.government_spending *= (1 + scenario.spending_change)
    
    # Simulate forward
    forecast = []
    for t in range(horizon):
        # Simplified forward simulation
        gdp_change = (
            -scenario.interest_rate_change * 0.5 +  # Contractionary effect
            scenario.spending_change * 0.3 -  # Fiscal multiplier
            scenario.tax_change * 0.2  # Tax drag
        )
        
        inflation_change = (
            scenario.spending_change * 0.15 +  # Demand pull
            scenario.qe_amount / 1000000 * 0.05 -  # Money supply effect
            scenario.interest_rate_change * 0.3  # Monetary tightening
        )
        
        unemployment_change = (
            scenario.interest_rate_change * 0.2 -  # Labor market cooling
            scenario.spending_change * 0.1 +  # Job creation
            scenario.tax_change * 0.1  # Business impact
        )
        
        forecast.append({
            'tick': sim.current_tick + t,
            'gdp': clone_state.gdp * (1 + gdp_change * (t + 1) / horizon),
            'inflation': clone_state.inflation + inflation_change * (t + 1) / horizon,
            'unemployment': max(0, clone_state.unemployment + unemployment_change * (t + 1) / horizon),
            'interest_rate': clone_state.interest_rate
        })
    
    # Risk assessment
    risk_scores = policy_engine.assess_risks({
        'gdp_impact': forecast[-1]['gdp'] / clone_state.gdp - 1,
        'inflation_impact': forecast[-1]['inflation'] - clone_state.inflation,
        'unemployment_impact': forecast[-1]['unemployment'] - clone_state.unemployment
    })
    
    return PolicyImpactResponse(
        scenario_name=scenario.name,
        impact_metrics={
            'gdp_change': (forecast[-1]['gdp'] / clone_state.gdp - 1) * 100,
            'inflation_change': (forecast[-1]['inflation'] - clone_state.inflation) * 100,
            'unemployment_change': (forecast[-1]['unemployment'] - clone_state.unemployment) * 100
        },
        risk_scores=risk_scores,
        forecast=forecast
    )


@router.get("/debate/{simulation_id}")
async def get_policy_debate(simulation_id: str):
    """Get multi-agent policy debate"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    current_state = sim.engine.state.to_dict()
    debate = policy_engine.generate_policy_debate(current_state)
    
    return {
        "simulation_id": simulation_id,
        "debate": debate
    }


@router.get("/tools")
async def list_policy_tools():
    """List available policy tools"""
    return {
        "monetary_tools": [
            {
                "name": "interest_rate",
                "description": "Federal funds rate adjustment",
                "range": [-0.05, 0.05],
                "unit": "percentage_points"
            },
            {
                "name": "reserve_requirement",
                "description": "Bank reserve requirement adjustment",
                "range": [-0.1, 0.1],
                "unit": "percentage_points"
            },
            {
                "name": "quantitative_easing",
                "description": "Asset purchase program",
                "range": [0, 1000000],
                "unit": "currency_units"
            }
        ],
        "fiscal_tools": [
            {
                "name": "tax_rate",
                "description": "Tax rate adjustment",
                "range": [-0.2, 0.2],
                "unit": "percentage_points"
            },
            {
                "name": "government_spending",
                "description": "Government spending change",
                "range": [-0.3, 0.3],
                "unit": "percentage_change"
            }
        ],
        "regulatory_tools": [
            {
                "name": "capital_requirement",
                "description": "Bank capital requirement",
                "range": [0.08, 0.15],
                "unit": "ratio"
            },
            {
                "name": "ltv_limit",
                "description": "Loan-to-value ratio limit",
                "range": [0.6, 0.95],
                "unit": "ratio"
            }
        ]
    }


@router.get("/history/{simulation_id}")
async def get_policy_history(simulation_id: str, limit: int = Query(50, ge=1, le=200)):
    """Get history of policy actions for a simulation"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Get policy history from simulation
    policy_history = []
    for entry in sim.history[-limit:]:
        if 'policy_action' in entry:
            policy_history.append({
                'tick': entry['tick'],
                'action': entry['policy_action'],
                'impact': entry.get('policy_impact', {})
            })
    
    return {
        "simulation_id": simulation_id,
        "policy_count": len(policy_history),
        "policies": policy_history
    }


@router.post("/optimize")
async def optimize_policy(request: PolicyAnalysisRequest):
    """Find optimal policy mix for given targets"""
    sim = simulation_manager.get_simulation(request.simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    targets = {}
    if request.target_inflation is not None:
        targets['inflation'] = request.target_inflation
    if request.target_unemployment is not None:
        targets['unemployment'] = request.target_unemployment
    if request.target_gdp_growth is not None:
        targets['gdp_growth'] = request.target_gdp_growth
    
    current_state = sim.engine.state.to_dict()
    
    # Optimization using gradient-free approach
    best_policy = None
    best_score = float('inf')
    
    # Grid search over policy space
    for ir in [-0.02, -0.01, 0, 0.01, 0.02]:
        for spending in [-0.1, 0, 0.1, 0.2]:
            for tax in [-0.05, 0, 0.05]:
                # Simulate policy
                scenario = PolicyScenario(
                    name="optimization_candidate",
                    description="",
                    policy_tools=[
                        PolicyTool("interest_rate", ir, "monetary"),
                        PolicyTool("government_spending", spending, "fiscal"),
                        PolicyTool("tax_rate", tax, "fiscal")
                    ]
                )
                
                forecast = policy_engine.forecast_scenario(scenario, current_state, 20)
                
                # Score against targets
                score = 0
                for key, target in targets.items():
                    if key in forecast['outcomes']:
                        score += (forecast['outcomes'][key] - target) ** 2
                
                if score < best_score:
                    best_score = score
                    best_policy = {
                        'interest_rate': ir,
                        'government_spending': spending,
                        'tax_rate': tax,
                        'forecast': forecast
                    }
    
    return {
        "simulation_id": request.simulation_id,
        "targets": targets,
        "optimal_policy": best_policy,
        "optimization_score": best_score
    }
