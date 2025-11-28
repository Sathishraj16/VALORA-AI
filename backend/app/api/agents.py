"""
VALORA Agents API Router
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..simulation.orchestrator import SimulationManager
from ..simulation.agents.consumer_agent import IncomeClass

router = APIRouter()

simulation_manager = SimulationManager()


class AgentSummary(BaseModel):
    """Agent summary response"""
    agent_id: str
    agent_type: str
    state: Dict[str, Any]


class ConsumerStats(BaseModel):
    """Consumer agent statistics"""
    total: int
    employed: int
    unemployed: int
    average_wealth: float
    average_income: float
    average_consumption: float
    by_income_class: Dict[str, int]


class FirmStats(BaseModel):
    """Firm agent statistics"""
    total: int
    profitable: int
    unprofitable: int
    average_profit: float
    average_employees: int
    total_output: float
    by_sector: Dict[str, int]


class BankStats(BaseModel):
    """Bank agent statistics"""
    total: int
    average_capital_ratio: float
    average_npl_ratio: float
    total_loans: float
    total_deposits: float


class RegulatorStats(BaseModel):
    """Regulator agent statistics"""
    current_interest_rate: float
    target_inflation: float
    policy_stance: str
    last_action: Optional[Dict[str, Any]]


@router.get("/{simulation_id}/consumers", response_model=ConsumerStats)
async def get_consumer_stats(simulation_id: str):
    """Get consumer agent statistics"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.consumers:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    consumers = sim.consumers.consumers
    employed = sum(1 for c in consumers if c.is_employed)
    
    by_income_class = {}
    for ic in IncomeClass:
        by_income_class[ic.value] = sum(1 for c in consumers if c.income_class == ic)
    
    return ConsumerStats(
        total=len(consumers),
        employed=employed,
        unemployed=len(consumers) - employed,
        average_wealth=sum(c.state.wealth for c in consumers) / max(1, len(consumers)),
        average_income=sum(c.income for c in consumers) / max(1, len(consumers)),
        average_consumption=sum(c.last_consumption for c in consumers) / max(1, len(consumers)),
        by_income_class=by_income_class
    )


@router.get("/{simulation_id}/consumers/list")
async def list_consumers(
    simulation_id: str,
    income_class: Optional[str] = None,
    employed_only: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List individual consumer agents"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.consumers:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    consumers = sim.consumers.consumers
    
    # Filter
    if income_class:
        ic = IncomeClass(income_class)
        consumers = [c for c in consumers if c.income_class == ic]
    
    if employed_only:
        consumers = [c for c in consumers if c.is_employed]
    
    # Paginate
    total = len(consumers)
    consumers = consumers[offset:offset + limit]
    
    return {
        "simulation_id": simulation_id,
        "total": total,
        "offset": offset,
        "limit": limit,
        "consumers": [
            {
                "id": c.agent_id,
                "income_class": c.income_class.value,
                "is_employed": c.is_employed,
                "income": c.income,
                "wealth": c.state.wealth,
                "consumption_rate": c.consumption_rate,
                "savings_rate": c.savings_rate
            }
            for c in consumers
        ]
    }


@router.get("/{simulation_id}/firms", response_model=FirmStats)
async def get_firm_stats(simulation_id: str):
    """Get firm agent statistics"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.firms:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    firms = sim.firms.firms
    profitable = sum(1 for f in firms if f.profit > 0)
    
    by_sector = {}
    for f in firms:
        sector = f.sector
        by_sector[sector] = by_sector.get(sector, 0) + 1
    
    return FirmStats(
        total=len(firms),
        profitable=profitable,
        unprofitable=len(firms) - profitable,
        average_profit=sum(f.profit for f in firms) / max(1, len(firms)),
        average_employees=int(sum(f.employees for f in firms) / max(1, len(firms))),
        total_output=sum(f.output for f in firms),
        by_sector=by_sector
    )


@router.get("/{simulation_id}/firms/list")
async def list_firms(
    simulation_id: str,
    sector: Optional[str] = None,
    profitable_only: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """List individual firm agents"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.firms:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    firms = sim.firms.firms
    
    # Filter
    if sector:
        firms = [f for f in firms if f.sector == sector]
    
    if profitable_only:
        firms = [f for f in firms if f.profit > 0]
    
    # Paginate
    total = len(firms)
    firms = firms[offset:offset + limit]
    
    return {
        "simulation_id": simulation_id,
        "total": total,
        "offset": offset,
        "limit": limit,
        "firms": [
            {
                "id": f.agent_id,
                "sector": f.sector,
                "employees": f.employees,
                "output": f.output,
                "profit": f.profit,
                "price_level": f.price_level,
                "inventory": f.inventory
            }
            for f in firms
        ]
    }


@router.get("/{simulation_id}/banks", response_model=BankStats)
async def get_bank_stats(simulation_id: str):
    """Get bank agent statistics"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.banks:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    banks = sim.banks.banks
    
    return BankStats(
        total=len(banks),
        average_capital_ratio=sum(b.capital_ratio for b in banks) / max(1, len(banks)),
        average_npl_ratio=sum(b.npl_ratio for b in banks) / max(1, len(banks)),
        total_loans=sum(b.total_loans for b in banks),
        total_deposits=sum(b.deposits for b in banks)
    )


@router.get("/{simulation_id}/banks/list")
async def list_banks(
    simulation_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List individual bank agents"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.banks:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    banks = sim.banks.banks[offset:offset + limit]
    
    return {
        "simulation_id": simulation_id,
        "total": len(sim.banks.banks),
        "offset": offset,
        "limit": limit,
        "banks": [
            {
                "id": b.agent_id,
                "capital_ratio": b.capital_ratio,
                "npl_ratio": b.npl_ratio,
                "total_loans": b.total_loans,
                "deposits": b.deposits,
                "interest_rate_spread": b.lending_rate - b.deposit_rate,
                "liquidity_ratio": b.liquidity_ratio
            }
            for b in banks
        ]
    }


@router.get("/{simulation_id}/regulator", response_model=RegulatorStats)
async def get_regulator_stats(simulation_id: str):
    """Get regulator agent statistics"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.regulator:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    reg = sim.regulator
    
    # Determine policy stance
    current_rate = sim.engine.state.interest_rate if sim.engine else 0.05
    target_inflation = reg.target_inflation if hasattr(reg, 'target_inflation') else 0.02
    
    if current_rate > target_inflation + 0.02:
        stance = "hawkish"
    elif current_rate < target_inflation - 0.01:
        stance = "dovish"
    else:
        stance = "neutral"
    
    return RegulatorStats(
        current_interest_rate=current_rate,
        target_inflation=target_inflation,
        policy_stance=stance,
        last_action=reg.last_action if hasattr(reg, 'last_action') else None
    )


@router.get("/{simulation_id}/agent/{agent_id}")
async def get_agent_details(simulation_id: str, agent_id: str):
    """Get details for a specific agent"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Search all agent types
    if sim.consumers:
        for c in sim.consumers.consumers:
            if c.agent_id == agent_id:
                return {
                    "agent_type": "consumer",
                    "agent_id": agent_id,
                    "state": {
                        "income_class": c.income_class.value,
                        "is_employed": c.is_employed,
                        "income": c.income,
                        "wealth": c.state.wealth,
                        "consumption_rate": c.consumption_rate,
                        "savings_rate": c.savings_rate,
                        "last_consumption": c.last_consumption
                    }
                }
    
    if sim.firms:
        for f in sim.firms.firms:
            if f.agent_id == agent_id:
                return {
                    "agent_type": "firm",
                    "agent_id": agent_id,
                    "state": {
                        "sector": f.sector,
                        "employees": f.employees,
                        "output": f.output,
                        "profit": f.profit,
                        "price_level": f.price_level,
                        "inventory": f.inventory,
                        "capacity_utilization": f.capacity_utilization if hasattr(f, 'capacity_utilization') else 0.8
                    }
                }
    
    if sim.banks:
        for b in sim.banks.banks:
            if b.agent_id == agent_id:
                return {
                    "agent_type": "bank",
                    "agent_id": agent_id,
                    "state": {
                        "capital_ratio": b.capital_ratio,
                        "npl_ratio": b.npl_ratio,
                        "total_loans": b.total_loans,
                        "deposits": b.deposits,
                        "lending_rate": b.lending_rate,
                        "deposit_rate": b.deposit_rate,
                        "liquidity_ratio": b.liquidity_ratio
                    }
                }
    
    if sim.regulator and sim.regulator.agent_id == agent_id:
        reg = sim.regulator
        return {
            "agent_type": "regulator",
            "agent_id": agent_id,
            "state": {
                "target_inflation": reg.target_inflation if hasattr(reg, 'target_inflation') else 0.02,
                "current_policy_rate": sim.engine.state.interest_rate if sim.engine else 0.05
            }
        }
    
    raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/{simulation_id}/agent/{agent_id}/history")
async def get_agent_history(
    simulation_id: str,
    agent_id: str,
    limit: int = Query(50, ge=1, le=500)
):
    """Get action history for a specific agent"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Search history for agent actions
    history = []
    for entry in sim.history[-limit:]:
        agent_actions = entry.get('agent_actions', {})
        if agent_id in agent_actions:
            history.append({
                'tick': entry['tick'],
                'action': agent_actions[agent_id]
            })
    
    return {
        "simulation_id": simulation_id,
        "agent_id": agent_id,
        "history_count": len(history),
        "history": history
    }


@router.get("/{simulation_id}/sectors")
async def get_sector_breakdown(simulation_id: str):
    """Get sector-level breakdown"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.firms:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    sectors = {}
    for firm in sim.firms.firms:
        sector = firm.sector
        if sector not in sectors:
            sectors[sector] = {
                'firm_count': 0,
                'total_employees': 0,
                'total_output': 0,
                'total_profit': 0,
                'average_price': 0
            }
        
        sectors[sector]['firm_count'] += 1
        sectors[sector]['total_employees'] += firm.employees
        sectors[sector]['total_output'] += firm.output
        sectors[sector]['total_profit'] += firm.profit
        sectors[sector]['average_price'] += firm.price_level
    
    # Calculate averages
    for sector in sectors:
        count = sectors[sector]['firm_count']
        sectors[sector]['average_price'] /= max(1, count)
        sectors[sector]['average_employees'] = sectors[sector]['total_employees'] / max(1, count)
    
    return {
        "simulation_id": simulation_id,
        "sectors": sectors
    }


@router.post("/{simulation_id}/agent/{agent_id}/learn")
async def trigger_agent_learning(simulation_id: str, agent_id: str):
    """Trigger learning update for a specific agent"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Find agent and trigger learning
    agent = None
    
    if sim.consumers:
        for c in sim.consumers.consumers:
            if c.agent_id == agent_id:
                agent = c
                break
    
    if not agent and sim.firms:
        for f in sim.firms.firms:
            if f.agent_id == agent_id:
                agent = f
                break
    
    if not agent and sim.banks:
        for b in sim.banks.banks:
            if b.agent_id == agent_id:
                agent = b
                break
    
    if not agent and sim.regulator and sim.regulator.agent_id == agent_id:
        agent = sim.regulator
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Trigger learning if method exists
    if hasattr(agent, 'learn'):
        agent.learn()
        return {"message": "Learning triggered", "agent_id": agent_id}
    
    return {"message": "Agent does not support learning", "agent_id": agent_id}
