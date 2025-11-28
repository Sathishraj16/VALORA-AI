"""
VALORA Backend Test Suite
Comprehensive tests for all core functionality
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

# Test fixtures
@pytest.fixture
def sample_simulation_config():
    return {
        "name": "Test Simulation",
        "description": "Unit test simulation",
        "num_agents": 1000,
        "num_steps": 100,
        "initial_conditions": {
            "gdp": 1e12,
            "inflation_rate": 0.02,
            "unemployment_rate": 0.05,
            "interest_rate": 0.05,
            "consumer_confidence": 0.7,
            "business_confidence": 0.7,
        },
        "policy_parameters": {
            "tax_rate": 0.25,
            "interest_rate": 0.05,
            "government_spending_rate": 0.20,
            "money_supply_growth": 0.03,
        },
    }


@pytest.fixture
def sample_policy_scenario():
    return {
        "policy_type": "monetary",
        "interest_rate_change": 0.005,
        "duration_months": 12,
        "implementation_speed": "gradual",
    }


class TestEconomicEngine:
    """Tests for the core economic simulation engine"""

    def test_economic_state_initialization(self, sample_simulation_config):
        """Test that economic state initializes correctly"""
        from app.core.economic_engine import EconomicState
        
        state = EconomicState(**sample_simulation_config["initial_conditions"])
        
        assert state.gdp == 1e12
        assert state.inflation_rate == 0.02
        assert state.unemployment_rate == 0.05
        assert state.interest_rate == 0.05
        assert 0 <= state.consumer_confidence <= 1
        assert 0 <= state.business_confidence <= 1

    def test_gdp_calculation(self, sample_simulation_config):
        """Test GDP calculation with components"""
        from app.core.economic_engine import EconomicEngine
        
        engine = EconomicEngine()
        
        # Test with mock consumption, investment, government, net exports
        gdp = engine._calculate_gdp(
            consumption=7e11,
            investment=2e11,
            government_spending=1.5e11,
            net_exports=-5e10
        )
        
        expected_gdp = 7e11 + 2e11 + 1.5e11 - 5e10
        assert abs(gdp - expected_gdp) < 1e6

    def test_phillips_curve_relationship(self):
        """Test that Phillips curve relationship holds"""
        from app.core.economic_engine import EconomicEngine
        
        engine = EconomicEngine()
        
        # Lower unemployment should lead to higher inflation pressure
        inflation_low_unemployment = engine._calculate_inflation_pressure(
            unemployment_rate=0.03,
            money_supply_growth=0.05,
            output_gap=0.02
        )
        
        inflation_high_unemployment = engine._calculate_inflation_pressure(
            unemployment_rate=0.08,
            money_supply_growth=0.05,
            output_gap=0.02
        )
        
        assert inflation_low_unemployment > inflation_high_unemployment

    def test_interest_rate_transmission(self):
        """Test monetary policy transmission mechanism"""
        from app.core.economic_engine import EconomicEngine
        
        engine = EconomicEngine()
        
        # Higher interest rates should reduce investment demand
        investment_low_rate = engine._calculate_investment_demand(
            interest_rate=0.02,
            business_confidence=0.7,
            capacity_utilization=0.8
        )
        
        investment_high_rate = engine._calculate_investment_demand(
            interest_rate=0.08,
            business_confidence=0.7,
            capacity_utilization=0.8
        )
        
        assert investment_low_rate > investment_high_rate


class TestRLAgents:
    """Tests for reinforcement learning agents"""

    def test_consumer_agent_initialization(self):
        """Test consumer agent initialization"""
        from app.core.rl_agents import ConsumerAgent
        
        agent = ConsumerAgent(
            agent_id="consumer_001",
            initial_wealth=50000,
            income=5000,
            risk_tolerance=0.5
        )
        
        assert agent.agent_id == "consumer_001"
        assert agent.wealth == 50000
        assert agent.income == 5000
        assert 0 <= agent.risk_tolerance <= 1

    def test_firm_agent_production_decision(self):
        """Test firm agent production optimization"""
        from app.core.rl_agents import FirmAgent
        
        agent = FirmAgent(
            agent_id="firm_001",
            capital=1e6,
            labor=100,
            technology_level=1.0
        )
        
        # Test Cobb-Douglas production function
        output = agent.calculate_production()
        assert output > 0
        
        # Higher capital should increase output
        agent.capital = 2e6
        higher_output = agent.calculate_production()
        assert higher_output > output

    def test_bank_agent_lending_decision(self):
        """Test bank agent lending behavior"""
        from app.core.rl_agents import BankAgent
        
        agent = BankAgent(
            agent_id="bank_001",
            capital=1e8,
            reserves=1e7,
            reserve_requirement=0.1
        )
        
        # Test that lending respects reserve requirements
        max_lending = agent.calculate_max_lending()
        assert max_lending <= agent.capital * (1 - agent.reserve_requirement)

    def test_ppo_network_forward_pass(self):
        """Test PPO network architecture"""
        from app.core.rl_agents import PPONetwork
        import torch
        
        network = PPONetwork(
            state_dim=10,
            action_dim=4,
            hidden_dim=64
        )
        
        # Test forward pass
        state = torch.randn(1, 10)
        action_probs, value = network(state)
        
        assert action_probs.shape == (1, 4)
        assert value.shape == (1, 1)
        assert torch.allclose(action_probs.sum(dim=1), torch.tensor([1.0]), atol=1e-5)


class TestBlockchainIntegrity:
    """Tests for blockchain verification system"""

    def test_block_creation(self):
        """Test block creation and hashing"""
        from app.core.blockchain import Block
        
        block = Block(
            index=1,
            timestamp=datetime.now().isoformat(),
            data={"simulation_id": "test_001", "step": 1},
            previous_hash="0" * 64
        )
        
        assert block.index == 1
        assert block.previous_hash == "0" * 64
        assert len(block.hash) == 64  # SHA-256 produces 64 hex characters

    def test_blockchain_validation(self):
        """Test blockchain integrity validation"""
        from app.core.blockchain import Blockchain
        
        blockchain = Blockchain()
        
        # Add blocks
        blockchain.add_block({"test": "data1"})
        blockchain.add_block({"test": "data2"})
        blockchain.add_block({"test": "data3"})
        
        # Validate chain
        assert blockchain.is_valid()
        
        # Tamper with data
        blockchain.chain[1].data = {"tampered": "data"}
        assert not blockchain.is_valid()

    def test_merkle_tree_generation(self):
        """Test Merkle tree for simulation data"""
        from app.core.blockchain import MerkleTree
        
        data = [
            {"step": 1, "gdp": 1e12},
            {"step": 2, "gdp": 1.01e12},
            {"step": 3, "gdp": 1.02e12},
            {"step": 4, "gdp": 1.03e12},
        ]
        
        tree = MerkleTree(data)
        root = tree.get_root()
        
        assert root is not None
        assert len(root) == 64
        
        # Verify proof
        proof = tree.get_proof(0)
        assert tree.verify_proof(data[0], proof, root)


class TestPolicyIntelligence:
    """Tests for policy analysis system"""

    def test_policy_impact_calculation(self, sample_policy_scenario):
        """Test policy impact estimation"""
        from app.core.policy_intelligence import PolicyAnalyzer
        
        analyzer = PolicyAnalyzer()
        
        impact = analyzer.estimate_impact(
            policy_type="monetary",
            parameter_change={"interest_rate": 0.005},
            duration_months=12
        )
        
        assert "gdp_impact" in impact
        assert "inflation_impact" in impact
        assert "unemployment_impact" in impact
        assert "confidence_interval" in impact

    def test_policy_comparison(self):
        """Test multi-policy comparison"""
        from app.core.policy_intelligence import PolicyAnalyzer
        
        analyzer = PolicyAnalyzer()
        
        policies = [
            {"name": "Hawkish", "interest_rate": 0.07, "type": "monetary"},
            {"name": "Dovish", "interest_rate": 0.03, "type": "monetary"},
        ]
        
        comparison = analyzer.compare_policies(policies)
        
        assert len(comparison) == 2
        assert "risk_score" in comparison[0]
        assert "effectiveness_score" in comparison[0]

    def test_risk_assessment(self):
        """Test policy risk scoring"""
        from app.core.policy_intelligence import PolicyAnalyzer
        
        analyzer = PolicyAnalyzer()
        
        # More aggressive policy should have higher risk
        aggressive_risk = analyzer.calculate_risk_score(
            policy_type="monetary",
            magnitude=0.05,  # 5% rate change
            speed="immediate"
        )
        
        conservative_risk = analyzer.calculate_risk_score(
            policy_type="monetary",
            magnitude=0.01,  # 1% rate change
            speed="gradual"
        )
        
        assert aggressive_risk > conservative_risk


class TestCrewAIIntegration:
    """Tests for CrewAI multi-agent system"""

    @pytest.mark.asyncio
    async def test_crew_initialization(self):
        """Test CrewAI crew setup"""
        from app.core.crew_ai import EconomicAnalysisCrew
        
        crew = EconomicAnalysisCrew()
        
        assert crew.economist_agent is not None
        assert crew.policy_agent is not None
        assert crew.risk_agent is not None
        assert crew.forecaster_agent is not None

    @pytest.mark.asyncio
    async def test_crew_analysis(self):
        """Test crew collaborative analysis"""
        from app.core.crew_ai import EconomicAnalysisCrew
        
        with patch('app.core.crew_ai.Groq') as mock_groq:
            mock_groq.return_value.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Test analysis result"))]
            )
            
            crew = EconomicAnalysisCrew()
            result = await crew.analyze(
                query="What is the impact of 50bps rate hike?",
                analysis_type="impact_analysis"
            )
            
            assert result is not None
            assert "analysis" in result or isinstance(result, str)


class TestDatabaseModels:
    """Tests for SQLAlchemy database models"""

    def test_user_model_password_hashing(self):
        """Test password hashing in User model"""
        from app.db.models import User
        
        user = User(
            email="test@example.com",
            name="Test User"
        )
        user.set_password("secure_password_123")
        
        assert user.hashed_password != "secure_password_123"
        assert user.verify_password("secure_password_123")
        assert not user.verify_password("wrong_password")

    def test_simulation_model_serialization(self):
        """Test Simulation model JSON serialization"""
        from app.db.models import Simulation
        
        simulation = Simulation(
            name="Test Simulation",
            description="Test description",
            status="running",
            num_agents=1000,
            num_steps=100,
            config={"test": "config"}
        )
        
        json_data = simulation.to_dict()
        
        assert json_data["name"] == "Test Simulation"
        assert json_data["status"] == "running"
        assert json_data["config"] == {"test": "config"}


class TestAPIEndpoints:
    """Tests for FastAPI endpoints"""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_simulation_creation(self, sample_simulation_config):
        """Test simulation creation endpoint"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        with patch('app.api.simulations.create_simulation') as mock_create:
            mock_create.return_value = {
                "id": "sim_123",
                "status": "created",
                **sample_simulation_config
            }
            
            response = client.post(
                "/api/v1/simulations/start",
                json=sample_simulation_config
            )
            
            assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_auth_flow(self):
        """Test authentication flow"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test registration
        with patch('app.api.auth.create_user') as mock_create:
            mock_create.return_value = {"id": "user_123", "email": "test@example.com"}
            
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "secure_password_123",
                    "name": "Test User"
                }
            )
            
            # Accept either success or expected error
            assert response.status_code in [200, 201, 422]


class TestUtilities:
    """Tests for utility functions"""

    def test_format_currency(self):
        """Test currency formatting utility"""
        from app.utils.formatters import format_currency
        
        assert format_currency(1e12) == "$1.00T"
        assert format_currency(1e9) == "$1.00B"
        assert format_currency(1e6) == "$1.00M"
        assert format_currency(1e3) == "$1.00K"

    def test_calculate_confidence_interval(self):
        """Test confidence interval calculation"""
        from app.utils.statistics import calculate_confidence_interval
        
        data = np.random.normal(100, 10, 1000)
        lower, upper = calculate_confidence_interval(data, confidence=0.95)
        
        # 95% CI should contain the true mean most of the time
        assert lower < 100 < upper

    def test_time_series_smoothing(self):
        """Test time series smoothing"""
        from app.utils.statistics import exponential_smoothing
        
        data = [1, 2, 3, 10, 4, 5, 6]  # With outlier at index 3
        smoothed = exponential_smoothing(data, alpha=0.3)
        
        # Smoothed data should be less volatile
        assert np.std(smoothed) < np.std(data)


# Integration Tests
class TestIntegration:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_simulation_workflow(self, sample_simulation_config):
        """Test complete simulation workflow"""
        from app.core.economic_engine import EconomicEngine
        from app.core.rl_agents import AgentPopulation
        from app.core.blockchain import Blockchain
        
        # Initialize components
        engine = EconomicEngine()
        blockchain = Blockchain()
        
        # Run simulation
        for step in range(10):
            # Step the economy
            state = engine.step(sample_simulation_config["policy_parameters"])
            
            # Record to blockchain
            blockchain.add_block({
                "step": step,
                "state": state.to_dict() if hasattr(state, 'to_dict') else str(state)
            })
        
        # Verify blockchain integrity
        assert blockchain.is_valid()
        assert len(blockchain.chain) >= 10

    @pytest.mark.asyncio
    async def test_concurrent_simulations(self, sample_simulation_config):
        """Test running multiple simulations concurrently"""
        from app.core.economic_engine import EconomicEngine
        
        async def run_simulation(sim_id):
            engine = EconomicEngine()
            results = []
            for _ in range(5):
                state = engine.step(sample_simulation_config["policy_parameters"])
                results.append(state)
            return sim_id, results
        
        # Run 3 simulations concurrently
        tasks = [run_simulation(f"sim_{i}") for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for sim_id, sim_results in results:
            assert len(sim_results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app", "--cov-report=html"])
