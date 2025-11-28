"""
VALORA Simulation Orchestrator
Coordinates economic engine, AI agents, policy system, and blockchain
"""

import asyncio
import uuid
import time
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from .economic_engine import MacroeconomicEngine, MacroState, EconomicShock, PolicyAction
from .agents import (
    ConsumerPopulation,
    FirmPopulation,
    BankingSystem,
    RegulatorSystem
)
from ..blockchain import EconomicBlockchain, BlockchainExplorer, EventType

logger = logging.getLogger(__name__)


class SimulationStatus(Enum):
    """Simulation lifecycle states"""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SimulationConfig:
    """Configuration for a simulation run"""
    # Identifiers
    simulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Unnamed Simulation"
    description: str = ""
    
    # Time settings
    total_ticks: int = 100
    tick_interval: float = 1.0  # seconds between ticks in real-time mode
    
    # Agent populations
    num_consumers: int = 1000
    num_firms: int = 200
    num_banks: int = 20
    
    # Initial conditions
    initial_gdp: float = 1_000_000.0
    initial_inflation: float = 0.02
    initial_unemployment: float = 0.05
    
    # Features
    enable_learning: bool = True
    enable_blockchain: bool = True
    enable_realtime: bool = False
    record_agent_decisions: bool = True
    
    # Random seed for reproducibility
    random_seed: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SimulationResult:
    """Results from a completed simulation"""
    simulation_id: str
    config: SimulationConfig
    final_state: MacroState
    history: List[Dict]
    agent_statistics: Dict
    policy_actions: List[Dict]
    shocks_applied: List[Dict]
    blockchain_summary: Dict
    duration_seconds: float
    total_ticks: int
    
    def to_dict(self) -> Dict:
        return {
            'simulation_id': self.simulation_id,
            'config': self.config.to_dict(),
            'final_state': self._state_to_dict(self.final_state),
            'history': self.history,
            'agent_statistics': self.agent_statistics,
            'policy_actions': self.policy_actions,
            'shocks_applied': self.shocks_applied,
            'blockchain_summary': self.blockchain_summary,
            'duration_seconds': self.duration_seconds,
            'total_ticks': self.total_ticks
        }
    
    def _state_to_dict(self, state: MacroState) -> Dict:
        return {
            'gdp': state.gdp,
            'gdp_growth': state.gdp_growth,
            'inflation': state.inflation,
            'unemployment': state.unemployment,
            'interest_rate': state.interest_rate,
            'consumer_confidence': state.consumer_confidence,
            'business_confidence': state.business_confidence,
            'debt_to_gdp': state.debt_to_gdp,
            'cycle_phase': state.cycle_phase.value,
            'tick': state.tick
        }


class SimulationOrchestrator:
    """
    Main orchestrator for economic simulations
    Coordinates all components and manages simulation lifecycle
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.simulation_id = config.simulation_id
        self.status = SimulationStatus.CREATED
        
        # Core components (initialized on start)
        self.engine: Optional[MacroeconomicEngine] = None
        self.consumers: Optional[ConsumerPopulation] = None
        self.firms: Optional[FirmPopulation] = None
        self.banks: Optional[BankingSystem] = None
        self.regulators: Optional[RegulatorSystem] = None
        self.blockchain: Optional[EconomicBlockchain] = None
        
        # State tracking
        self.current_tick = 0
        self.history: List[Dict] = []
        self.policy_actions: List[Dict] = []
        self.shocks_applied: List[Dict] = []
        
        # Callbacks for real-time updates
        self.on_tick_callbacks: List[Callable] = []
        self.on_state_change_callbacks: List[Callable] = []
        
        # Threading
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._running = False
        self._paused = False
        
        # Timing
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def initialize(self):
        """Initialize all simulation components"""
        self.status = SimulationStatus.INITIALIZING
        logger.info(f"Initializing simulation {self.simulation_id}")
        
        try:
            # Initialize economic engine
            initial_state = MacroState(
                gdp=self.config.initial_gdp,
                inflation=self.config.initial_inflation,
                unemployment=self.config.initial_unemployment
            )
            self.engine = MacroeconomicEngine(initial_state)
            
            # Initialize agent populations
            self.consumers = ConsumerPopulation(size=self.config.num_consumers)
            self.firms = FirmPopulation(size=self.config.num_firms)
            self.banks = BankingSystem(num_banks=self.config.num_banks)
            self.regulators = RegulatorSystem()
            
            # Initialize blockchain
            if self.config.enable_blockchain:
                self.blockchain = EconomicBlockchain(self.simulation_id)
                self.blockchain.record_event(
                    EventType.SIMULATION_START,
                    {
                        'config': self.config.to_dict(),
                        'initial_state': self._get_state_dict()
                    },
                    tick=0
                )
            
            logger.info(f"Simulation {self.simulation_id} initialized successfully")
            
        except Exception as e:
            self.status = SimulationStatus.FAILED
            logger.error(f"Failed to initialize simulation: {e}")
            raise
    
    def _get_state_dict(self) -> Dict:
        """Get current macro state as dictionary"""
        state = self.engine.state
        return {
            'gdp': state.gdp,
            'gdp_growth': state.gdp_growth,
            'potential_gdp': state.potential_gdp,
            'output_gap': state.output_gap,
            'inflation': state.inflation,
            'expected_inflation': state.expected_inflation,
            'unemployment': state.unemployment,
            'interest_rate': state.interest_rate,
            'real_interest_rate': state.real_interest_rate,
            'consumer_confidence': state.consumer_confidence,
            'business_confidence': state.business_confidence,
            'government_spending': state.government_spending,
            'tax_rate': state.tax_rate,
            'debt_to_gdp': state.debt_to_gdp,
            'loan_default_rate': state.loan_default_rate,
            'cycle_phase': state.cycle_phase.value,
            'tick': state.tick,
            'sector_gdp': state.sector_gdp
        }
    
    def _get_macro_dict_for_agents(self) -> Dict:
        """Get macro state formatted for agent consumption"""
        state = self.engine.state
        return {
            'gdp': state.gdp,
            'gdp_growth': state.gdp_growth,
            'output_gap': state.output_gap,
            'inflation': state.inflation,
            'expected_inflation': state.expected_inflation,
            'unemployment': state.unemployment,
            'interest_rate': state.interest_rate,
            'real_interest_rate': state.real_interest_rate,
            'wage_growth': state.wage_growth,
            'consumer_confidence': state.consumer_confidence,
            'business_confidence': state.business_confidence,
            'tax_rate': state.tax_rate,
            'credit_supply': state.credit_supply,
            'debt_to_gdp': state.debt_to_gdp
        }
    
    def step(self) -> Dict:
        """
        Execute one simulation step
        
        Order of operations:
        1. Get current macro state
        2. Regulators decide policy
        3. Banks process credit
        4. Firms produce and price
        5. Consumers spend/save
        6. Update macro dynamics
        7. Record to blockchain
        8. Notify callbacks
        """
        macro_dict = self._get_macro_dict_for_agents()
        tick = self.current_tick
        
        # 1. Regulator decisions
        policy_outputs = self.regulators.step(macro_dict, tick)
        
        # Apply policy to engine
        if policy_outputs['policy_rate'] != self.engine.state.interest_rate:
            old_rate = self.engine.state.interest_rate
            self.engine.state.interest_rate = policy_outputs['policy_rate']
            self.policy_actions.append({
                'tick': tick,
                'type': 'monetary',
                'parameter': 'interest_rate',
                'old_value': old_rate,
                'new_value': policy_outputs['policy_rate']
            })
        
        if policy_outputs['tax_rate'] != self.engine.state.tax_rate:
            old_rate = self.engine.state.tax_rate
            self.engine.state.tax_rate = policy_outputs['tax_rate']
            self.policy_actions.append({
                'tick': tick,
                'type': 'fiscal',
                'parameter': 'tax_rate',
                'old_value': old_rate,
                'new_value': policy_outputs['tax_rate']
            })
        
        self.engine.state.government_spending = policy_outputs['government_spending']
        
        # 2. Banking sector
        bank_outputs = self.banks.step(macro_dict)
        self.engine.state.credit_supply = bank_outputs['total_credit_supply']
        self.engine.state.loan_default_rate = bank_outputs['system_npl_ratio']
        
        # 3. Firm decisions
        aggregate_demand = self.engine.state.consumption + self.engine.state.investment
        firm_outputs = self.firms.step(macro_dict, aggregate_demand)
        
        # 4. Consumer decisions
        consumer_outputs = self.consumers.step(macro_dict)
        
        # 5. Update macro dynamics
        # Feed agent outputs back to engine
        self.engine.state.consumption = consumer_outputs['total_consumption']
        self.engine.state.investment = firm_outputs['total_investment']
        self.engine.state.employment = firm_outputs['total_employment']
        
        # Step the engine (differential equation updates)
        new_state = self.engine.step()
        
        # 6. Record state to history
        state_record = {
            'tick': tick,
            'timestamp': time.time(),
            'macro': self._get_state_dict(),
            'consumers': consumer_outputs,
            'firms': {
                'total_output': firm_outputs['total_output'],
                'total_employment': firm_outputs['total_employment'],
                'average_price': firm_outputs['average_price'],
                'profitable_firms': firm_outputs['profitable_firms']
            },
            'banks': {
                'credit_supply': bank_outputs['total_credit_supply'],
                'npl_ratio': bank_outputs['system_npl_ratio'],
                'capital_ratio': bank_outputs['system_capital_ratio']
            },
            'policy': {
                'interest_rate': policy_outputs['policy_rate'],
                'tax_rate': policy_outputs['tax_rate'],
                'spending': policy_outputs['government_spending']
            }
        }
        self.history.append(state_record)
        
        # 7. Record to blockchain
        if self.config.enable_blockchain and self.blockchain:
            self.blockchain.record_macro_state(state_record['macro'], tick)
            
            # Record significant policy changes
            for action in self.policy_actions:
                if action['tick'] == tick:
                    self.blockchain.record_policy_change(
                        action['type'],
                        action['parameter'],
                        action['old_value'],
                        action['new_value'],
                        policy_outputs.get('monetary_info', {}).get('reasoning', ''),
                        tick
                    )
        
        # 8. Notify callbacks
        for callback in self.on_tick_callbacks:
            try:
                callback(state_record)
            except Exception as e:
                logger.error(f"Callback error: {e}")
        
        self.current_tick += 1
        
        return state_record
    
    def apply_shock(self, shock: EconomicShock):
        """Apply an economic shock to the simulation"""
        self.engine.apply_shock(shock)
        
        shock_record = {
            'tick': self.current_tick,
            'type': shock.shock_type,
            'name': shock.name,
            'magnitude': shock.magnitude,
            'sectors': shock.affected_sectors
        }
        self.shocks_applied.append(shock_record)
        
        if self.config.enable_blockchain and self.blockchain:
            self.blockchain.record_shock(
                shock.shock_type,
                shock.name,
                shock.magnitude,
                shock.affected_sectors,
                self.current_tick
            )
        
        logger.info(f"Applied shock: {shock.name} (magnitude: {shock.magnitude})")
    
    def run(self, steps: Optional[int] = None) -> SimulationResult:
        """
        Run simulation for specified steps or until completion
        """
        if self.status == SimulationStatus.CREATED:
            self.initialize()
        
        self.status = SimulationStatus.RUNNING
        self._running = True
        self.start_time = time.time()
        
        target_ticks = steps or self.config.total_ticks
        
        logger.info(f"Starting simulation {self.simulation_id} for {target_ticks} ticks")
        
        try:
            while self._running and self.current_tick < target_ticks:
                if self._paused:
                    time.sleep(0.1)
                    continue
                
                self.step()
                
                # Real-time pacing
                if self.config.enable_realtime:
                    time.sleep(self.config.tick_interval)
                
                # Progress logging
                if self.current_tick % 10 == 0:
                    state = self.engine.state
                    logger.info(
                        f"Tick {self.current_tick}: GDP={state.gdp:.0f}, "
                        f"π={state.inflation:.2%}, u={state.unemployment:.2%}, "
                        f"i={state.interest_rate:.2%}"
                    )
            
            self.status = SimulationStatus.COMPLETED
            
        except Exception as e:
            self.status = SimulationStatus.FAILED
            logger.error(f"Simulation failed: {e}")
            raise
        
        finally:
            self._running = False
            self.end_time = time.time()
            
            if self.config.enable_blockchain and self.blockchain:
                self.blockchain.finalize()
        
        return self._build_result()
    
    async def run_async(self, steps: Optional[int] = None) -> SimulationResult:
        """Async version of run for web server integration"""
        return await asyncio.get_event_loop().run_in_executor(
            self._executor,
            lambda: self.run(steps)
        )
    
    def pause(self):
        """Pause the simulation"""
        self._paused = True
        self.status = SimulationStatus.PAUSED
        logger.info(f"Simulation {self.simulation_id} paused")
    
    def resume(self):
        """Resume paused simulation"""
        self._paused = False
        self.status = SimulationStatus.RUNNING
        logger.info(f"Simulation {self.simulation_id} resumed")
    
    def stop(self):
        """Stop the simulation"""
        self._running = False
        logger.info(f"Simulation {self.simulation_id} stopped")
    
    def _build_result(self) -> SimulationResult:
        """Build simulation result object"""
        duration = (self.end_time or time.time()) - (self.start_time or time.time())
        
        # Aggregate agent statistics
        agent_stats = {
            'consumers': {
                'total': self.config.num_consumers,
                'employed': sum(1 for c in self.consumers.consumers if c.is_employed),
                'average_wealth': sum(c.state.wealth for c in self.consumers.consumers) / max(1, self.config.num_consumers),
                'total_consumption': self.consumers.get_aggregate_demand()
            },
            'firms': {
                'total': self.config.num_firms,
                'profitable': sum(1 for f in self.firms.firms if f.profit > 0),
                'total_employment': self.firms.get_total_labor_demand(),
                'total_investment': self.firms.get_aggregate_investment()
            },
            'banks': {
                'total': len(self.banks.banks),
                'average_npl': sum(b.npl_ratio for b in self.banks.banks) / max(1, len(self.banks.banks)),
                'average_capital_ratio': sum(
                    b.capital / b.assets if b.assets > 0 else 0 
                    for b in self.banks.banks
                ) / max(1, len(self.banks.banks))
            },
            'regulators': self.regulators.get_policy_summary()
        }
        
        blockchain_summary = {}
        if self.blockchain:
            blockchain_summary = self.blockchain.get_chain_summary()
        
        return SimulationResult(
            simulation_id=self.simulation_id,
            config=self.config,
            final_state=self.engine.state,
            history=self.history,
            agent_statistics=agent_stats,
            policy_actions=self.policy_actions,
            shocks_applied=self.shocks_applied,
            blockchain_summary=blockchain_summary,
            duration_seconds=duration,
            total_ticks=self.current_tick
        )
    
    def forecast(self, horizon: int, scenarios: Optional[List[Dict]] = None) -> Dict:
        """
        Run forward forecasts under different scenarios
        """
        base_forecast = self.engine.forecast(horizon)
        
        results = {
            'base': [self._state_to_dict_simple(s) for s in base_forecast]
        }
        
        if scenarios:
            for i, scenario in enumerate(scenarios):
                # Apply scenario shocks
                for shock_config in scenario.get('shocks', []):
                    shock = EconomicShock(
                        shock_type=shock_config['type'],
                        name=shock_config['name'],
                        magnitude=shock_config['magnitude'],
                        affected_sectors=shock_config.get('sectors', []),
                        duration=shock_config.get('duration', 10)
                    )
                    self.engine.apply_shock(shock)
                
                scenario_forecast = self.engine.forecast(horizon)
                results[f'scenario_{i}'] = [
                    self._state_to_dict_simple(s) for s in scenario_forecast
                ]
        
        return results
    
    def _state_to_dict_simple(self, state: MacroState) -> Dict:
        return {
            'tick': state.tick,
            'gdp': state.gdp,
            'gdp_growth': state.gdp_growth,
            'inflation': state.inflation,
            'unemployment': state.unemployment,
            'interest_rate': state.interest_rate
        }
    
    def get_state(self) -> Dict:
        """Get current simulation state"""
        return {
            'simulation_id': self.simulation_id,
            'status': self.status.value,
            'current_tick': self.current_tick,
            'config': self.config.to_dict(),
            'macro_state': self._get_state_dict() if self.engine else None
        }
    
    def add_tick_callback(self, callback: Callable):
        """Register callback for tick updates"""
        self.on_tick_callbacks.append(callback)
    
    def get_blockchain_explorer(self) -> Optional[BlockchainExplorer]:
        """Get blockchain explorer instance"""
        if self.blockchain:
            return BlockchainExplorer(self.blockchain)
        return None


class SimulationManager:
    """
    Manages multiple simulations
    """
    
    def __init__(self):
        self.simulations: Dict[str, SimulationOrchestrator] = {}
        self._lock = threading.Lock()
    
    def create_simulation(self, config: SimulationConfig) -> str:
        """Create a new simulation"""
        with self._lock:
            orchestrator = SimulationOrchestrator(config)
            self.simulations[config.simulation_id] = orchestrator
            return config.simulation_id
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationOrchestrator]:
        """Get simulation by ID"""
        return self.simulations.get(simulation_id)
    
    def list_simulations(self) -> List[Dict]:
        """List all simulations"""
        return [
            {
                'simulation_id': sim_id,
                'name': sim.config.name,
                'status': sim.status.value,
                'current_tick': sim.current_tick
            }
            for sim_id, sim in self.simulations.items()
        ]
    
    def delete_simulation(self, simulation_id: str) -> bool:
        """Delete a simulation"""
        with self._lock:
            if simulation_id in self.simulations:
                sim = self.simulations[simulation_id]
                sim.stop()
                del self.simulations[simulation_id]
                return True
            return False
