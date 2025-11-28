"""
VALORA Simulations API Router
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from ..simulation.orchestrator import (
    SimulationOrchestrator,
    SimulationConfig,
    SimulationManager,
    SimulationStatus
)
from ..simulation.economic_engine import EconomicShock

router = APIRouter()

# Global simulation manager
simulation_manager = SimulationManager()


# Pydantic models for API
class SimulationCreateRequest(BaseModel):
    """Request to create a new simulation"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    total_ticks: int = Field(default=100, ge=1, le=10000)
    num_consumers: int = Field(default=1000, ge=10, le=100000)
    num_firms: int = Field(default=200, ge=5, le=10000)
    num_banks: int = Field(default=20, ge=1, le=100)
    initial_gdp: float = Field(default=1000000, gt=0)
    initial_inflation: float = Field(default=0.02, ge=-0.1, le=0.5)
    initial_unemployment: float = Field(default=0.05, ge=0, le=0.5)
    enable_learning: bool = True
    enable_blockchain: bool = True
    enable_realtime: bool = False


class ShockRequest(BaseModel):
    """Request to apply an economic shock"""
    shock_type: str = Field(..., pattern="^(supply|demand|financial|external)$")
    name: str
    magnitude: float = Field(..., ge=-1.0, le=1.0)
    affected_sectors: List[str] = []
    duration: int = Field(default=10, ge=1, le=100)


class SimulationResponse(BaseModel):
    """Simulation state response"""
    simulation_id: str
    name: str
    status: str
    current_tick: int
    total_ticks: int
    macro_state: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class MacroStateResponse(BaseModel):
    """Macroeconomic state response"""
    tick: int
    gdp: float
    gdp_growth: float
    inflation: float
    unemployment: float
    interest_rate: float
    consumer_confidence: float
    business_confidence: float
    debt_to_gdp: float
    cycle_phase: str
    sector_gdp: Dict[str, float]


@router.post("/", response_model=SimulationResponse)
async def create_simulation(request: SimulationCreateRequest):
    """Create a new simulation"""
    config = SimulationConfig(
        name=request.name,
        description=request.description or "",
        total_ticks=request.total_ticks,
        num_consumers=request.num_consumers,
        num_firms=request.num_firms,
        num_banks=request.num_banks,
        initial_gdp=request.initial_gdp,
        initial_inflation=request.initial_inflation,
        initial_unemployment=request.initial_unemployment,
        enable_learning=request.enable_learning,
        enable_blockchain=request.enable_blockchain,
        enable_realtime=request.enable_realtime
    )
    
    simulation_id = simulation_manager.create_simulation(config)
    sim = simulation_manager.get_simulation(simulation_id)
    
    return SimulationResponse(
        simulation_id=simulation_id,
        name=config.name,
        status=sim.status.value,
        current_tick=sim.current_tick,
        total_ticks=config.total_ticks,
        created_at=datetime.utcnow().isoformat()
    )


@router.get("/", response_model=List[SimulationResponse])
async def list_simulations():
    """List all simulations"""
    return [
        SimulationResponse(
            simulation_id=s['simulation_id'],
            name=s['name'],
            status=s['status'],
            current_tick=s['current_tick'],
            total_ticks=0
        )
        for s in simulation_manager.list_simulations()
    ]


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str):
    """Get simulation details"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    state = sim.get_state()
    return SimulationResponse(
        simulation_id=simulation_id,
        name=sim.config.name,
        status=state['status'],
        current_tick=state['current_tick'],
        total_ticks=sim.config.total_ticks,
        macro_state=state['macro_state']
    )


@router.post("/{simulation_id}/start")
async def start_simulation(
    simulation_id: str,
    background_tasks: BackgroundTasks,
    steps: Optional[int] = Query(None, ge=1, le=10000)
):
    """Start or resume a simulation"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if sim.status == SimulationStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Simulation already running")
    
    # Initialize if needed
    if sim.status == SimulationStatus.CREATED:
        sim.initialize()
    
    # Run in background
    background_tasks.add_task(sim.run, steps)
    
    return {
        "message": "Simulation started",
        "simulation_id": simulation_id,
        "target_steps": steps or sim.config.total_ticks
    }


@router.post("/{simulation_id}/step")
async def step_simulation(simulation_id: str, steps: int = Query(1, ge=1, le=100)):
    """Execute specific number of simulation steps"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if sim.status == SimulationStatus.CREATED:
        sim.initialize()
    
    results = []
    for _ in range(steps):
        result = sim.step()
        results.append(result)
    
    return {
        "simulation_id": simulation_id,
        "steps_executed": steps,
        "current_tick": sim.current_tick,
        "results": results
    }


@router.post("/{simulation_id}/pause")
async def pause_simulation(simulation_id: str):
    """Pause a running simulation"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim.pause()
    return {"message": "Simulation paused", "simulation_id": simulation_id}


@router.post("/{simulation_id}/resume")
async def resume_simulation(simulation_id: str):
    """Resume a paused simulation"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim.resume()
    return {"message": "Simulation resumed", "simulation_id": simulation_id}


@router.post("/{simulation_id}/stop")
async def stop_simulation(simulation_id: str):
    """Stop a simulation"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    sim.stop()
    return {"message": "Simulation stopped", "simulation_id": simulation_id}


@router.get("/{simulation_id}/state", response_model=MacroStateResponse)
async def get_macro_state(simulation_id: str):
    """Get current macroeconomic state"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    state = sim.engine.state
    return MacroStateResponse(
        tick=state.tick,
        gdp=state.gdp,
        gdp_growth=state.gdp_growth,
        inflation=state.inflation,
        unemployment=state.unemployment,
        interest_rate=state.interest_rate,
        consumer_confidence=state.consumer_confidence,
        business_confidence=state.business_confidence,
        debt_to_gdp=state.debt_to_gdp,
        cycle_phase=state.cycle_phase.value,
        sector_gdp=state.sector_gdp
    )


@router.get("/{simulation_id}/history")
async def get_history(
    simulation_id: str,
    start_tick: int = Query(0, ge=0),
    end_tick: Optional[int] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get simulation history"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    history = sim.history[start_tick:end_tick][:limit]
    return {
        "simulation_id": simulation_id,
        "start_tick": start_tick,
        "count": len(history),
        "history": history
    }


@router.post("/{simulation_id}/shock")
async def apply_shock(simulation_id: str, shock: ShockRequest):
    """Apply an economic shock to the simulation"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    economic_shock = EconomicShock(
        shock_type=shock.shock_type,
        name=shock.name,
        magnitude=shock.magnitude,
        affected_sectors=shock.affected_sectors,
        duration=shock.duration
    )
    
    sim.apply_shock(economic_shock)
    
    return {
        "message": "Shock applied",
        "simulation_id": simulation_id,
        "shock": shock.dict()
    }


@router.get("/{simulation_id}/forecast")
async def get_forecast(
    simulation_id: str,
    horizon: int = Query(20, ge=1, le=100)
):
    """Get forward forecast from current state"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.engine:
        raise HTTPException(status_code=400, detail="Simulation not initialized")
    
    forecast = sim.forecast(horizon)
    return {
        "simulation_id": simulation_id,
        "current_tick": sim.current_tick,
        "forecast_horizon": horizon,
        "forecast": forecast
    }


@router.get("/{simulation_id}/agents")
async def get_agent_statistics(simulation_id: str):
    """Get agent population statistics"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    stats = {
        'consumers': {
            'total': sim.config.num_consumers,
            'employed': sum(1 for c in sim.consumers.consumers if c.is_employed) if sim.consumers else 0,
            'average_wealth': sum(c.state.wealth for c in sim.consumers.consumers) / max(1, sim.config.num_consumers) if sim.consumers else 0
        } if sim.consumers else {},
        'firms': {
            'total': sim.config.num_firms,
            'profitable': sum(1 for f in sim.firms.firms if f.profit > 0) if sim.firms else 0
        } if sim.firms else {},
        'banks': {
            'total': len(sim.banks.banks) if sim.banks else 0,
            'average_npl': sum(b.npl_ratio for b in sim.banks.banks) / max(1, len(sim.banks.banks)) if sim.banks else 0
        } if sim.banks else {}
    }
    
    return {
        "simulation_id": simulation_id,
        "statistics": stats
    }


@router.delete("/{simulation_id}")
async def delete_simulation(simulation_id: str):
    """Delete a simulation"""
    if simulation_manager.delete_simulation(simulation_id):
        return {"message": "Simulation deleted", "simulation_id": simulation_id}
    raise HTTPException(status_code=404, detail="Simulation not found")
