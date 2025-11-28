"""
VALORA Database Models
SQLAlchemy ORM models for PostgreSQL persistence
"""

from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean, DateTime, JSON,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

Base = declarative_base()


class SimulationStatus(enum.Enum):
    """Simulation lifecycle states"""
    CREATED = "created"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(enum.Enum):
    """User roles for RBAC"""
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"
    ENTERPRISE = "enterprise"


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER)
    organization = Column(String(255))
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # API usage tracking
    api_calls_today = Column(Integer, default=0)
    api_calls_month = Column(Integer, default=0)
    
    # Relationships
    simulations = relationship("Simulation", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")


class APIKey(Base):
    """API key for programmatic access"""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    name = Column(String(100))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_used = Column(DateTime)
    
    # Usage limits
    rate_limit = Column(Integer, default=100)  # requests per minute
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


class Simulation(Base):
    """Simulation run record"""
    __tablename__ = "simulations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(SimulationStatus), default=SimulationStatus.CREATED)
    
    # Configuration
    config = Column(JSONB, default={})
    
    # Initial conditions
    initial_gdp = Column(Float, default=1000000)
    initial_inflation = Column(Float, default=0.02)
    initial_unemployment = Column(Float, default=0.05)
    
    # Agent counts
    num_consumers = Column(Integer, default=1000)
    num_firms = Column(Integer, default=200)
    num_banks = Column(Integer, default=20)
    
    # Runtime state
    current_tick = Column(Integer, default=0)
    total_ticks = Column(Integer, default=100)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    final_state = Column(JSONB)
    agent_statistics = Column(JSONB)
    
    # Relationships
    user = relationship("User", back_populates="simulations")
    snapshots = relationship("MacroSnapshot", back_populates="simulation")
    policy_actions = relationship("PolicyAction", back_populates="simulation")
    shocks = relationship("EconomicShock", back_populates="simulation")
    blocks = relationship("Block", back_populates="simulation")
    
    __table_args__ = (
        Index('ix_simulations_user_status', 'user_id', 'status'),
        Index('ix_simulations_created', 'created_at'),
    )


class MacroSnapshot(Base):
    """Macroeconomic state snapshot at each tick"""
    __tablename__ = "macro_snapshots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    
    # Core indicators
    gdp = Column(Float)
    gdp_growth = Column(Float)
    potential_gdp = Column(Float)
    output_gap = Column(Float)
    
    # Prices
    inflation = Column(Float)
    expected_inflation = Column(Float)
    price_level = Column(Float)
    
    # Labor
    unemployment = Column(Float)
    employment = Column(Float)
    wage_growth = Column(Float)
    
    # Monetary
    interest_rate = Column(Float)
    real_interest_rate = Column(Float)
    money_supply = Column(Float)
    
    # Fiscal
    tax_rate = Column(Float)
    government_spending = Column(Float)
    fiscal_deficit = Column(Float)
    debt_to_gdp = Column(Float)
    
    # Financial
    credit_supply = Column(Float)
    loan_default_rate = Column(Float)
    
    # Confidence
    consumer_confidence = Column(Float)
    business_confidence = Column(Float)
    
    # Consumption/Investment
    consumption = Column(Float)
    investment = Column(Float)
    
    # Sectoral GDP
    sector_gdp = Column(JSONB)
    
    # Cycle
    cycle_phase = Column(String(50))
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    simulation = relationship("Simulation", back_populates="snapshots")
    
    __table_args__ = (
        UniqueConstraint('simulation_id', 'tick', name='uq_snapshot_sim_tick'),
        Index('ix_snapshots_simulation_tick', 'simulation_id', 'tick'),
    )


class PolicyAction(Base):
    """Policy action record"""
    __tablename__ = "policy_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    
    policy_type = Column(String(50))  # monetary, fiscal, regulatory
    parameter = Column(String(100))
    old_value = Column(Float)
    new_value = Column(Float)
    
    reasoning = Column(Text)
    expected_impact = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    simulation = relationship("Simulation", back_populates="policy_actions")
    
    __table_args__ = (
        Index('ix_policy_actions_simulation', 'simulation_id', 'tick'),
    )


class EconomicShock(Base):
    """Economic shock record"""
    __tablename__ = "economic_shocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False)
    tick = Column(Integer, nullable=False)
    
    shock_type = Column(String(50))  # supply, demand, financial
    name = Column(String(255))
    magnitude = Column(Float)
    duration = Column(Integer)
    affected_sectors = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    simulation = relationship("Simulation", back_populates="shocks")


class Block(Base):
    """Blockchain block record"""
    __tablename__ = "blocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id"), nullable=False)
    block_number = Column(Integer, nullable=False)
    
    timestamp = Column(Float)
    previous_hash = Column(String(64))
    merkle_root = Column(String(64))
    hash = Column(String(64), unique=True)
    
    transaction_count = Column(Integer)
    transactions = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    simulation = relationship("Simulation", back_populates="blocks")
    
    __table_args__ = (
        UniqueConstraint('simulation_id', 'block_number', name='uq_block_sim_number'),
        Index('ix_blocks_hash', 'hash'),
    )


class PolicyProposal(Base):
    """Policy proposal for analysis"""
    __tablename__ = "policy_proposals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    
    parameters = Column(JSONB)
    target_inflation = Column(Float)
    target_unemployment = Column(Float)
    target_gdp_growth = Column(Float)
    
    # Analysis results
    analysis_result = Column(JSONB)
    risk_score = Column(Float)
    recommendation = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    analyzed_at = Column(DateTime)


class AnalysisReport(Base):
    """CrewAI analysis report"""
    __tablename__ = "analysis_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_id = Column(UUID(as_uuid=True), ForeignKey("simulations.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    analysis_type = Column(String(50))
    agents_involved = Column(JSONB)
    
    raw_output = Column(Text)
    structured_output = Column(JSONB)
    recommendations = Column(JSONB)
    risks_identified = Column(JSONB)
    
    confidence_score = Column(Float)
    duration_seconds = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Scenario(Base):
    """Saved simulation scenario for comparison"""
    __tablename__ = "scenarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Scenario configuration
    initial_conditions = Column(JSONB)
    shocks = Column(JSONB)
    policy_changes = Column(JSONB)
    
    # Results
    forecast_results = Column(JSONB)
    
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """System audit log"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(UUID(as_uuid=True))
    
    details = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_audit_logs_user', 'user_id', 'created_at'),
        Index('ix_audit_logs_action', 'action', 'created_at'),
    )
