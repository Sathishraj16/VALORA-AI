"""
VALORA Blockchain Ledger
Merkle tree-based immutable audit trail for economic events and policy decisions
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import threading
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of blockchain-recorded events"""
    SIMULATION_START = "simulation_start"
    SIMULATION_STEP = "simulation_step"
    SIMULATION_END = "simulation_end"
    POLICY_CHANGE = "policy_change"
    ECONOMIC_SHOCK = "economic_shock"
    AGENT_DECISION = "agent_decision"
    MACRO_STATE = "macro_state"
    AUDIT_CHECKPOINT = "audit_checkpoint"
    CREWAI_ANALYSIS = "crewai_analysis"
    STRESS_TEST = "stress_test"
    SCENARIO_COMPARISON = "scenario_comparison"


@dataclass
class Transaction:
    """Individual transaction/event in the ledger"""
    tx_id: str
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    simulation_id: str
    tick: int
    signature: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'tx_id': self.tx_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'data': self.data,
            'simulation_id': self.simulation_id,
            'tick': self.tick,
            'signature': self.signature
        }
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of transaction"""
        tx_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()


class MerkleTree:
    """
    Merkle tree for efficient integrity verification
    """
    
    def __init__(self, transactions: List[Transaction] = None):
        self.transactions = transactions or []
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
        self.root: str = ""
        
        if transactions:
            self.build()
    
    def build(self):
        """Build Merkle tree from transactions"""
        if not self.transactions:
            self.root = hashlib.sha256(b"empty").hexdigest()
            return
        
        # Create leaf nodes
        self.leaves = [tx.compute_hash() for tx in self.transactions]
        
        # Build tree levels
        self.tree = [self.leaves]
        current_level = self.leaves
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            self.tree.append(next_level)
            current_level = next_level
        
        self.root = current_level[0] if current_level else ""
    
    def get_proof(self, tx_index: int) -> List[Dict]:
        """Get Merkle proof for a transaction"""
        if tx_index >= len(self.transactions):
            return []
        
        proof = []
        index = tx_index
        
        for level in self.tree[:-1]:
            is_left = index % 2 == 0
            sibling_index = index + 1 if is_left else index - 1
            
            if sibling_index < len(level):
                proof.append({
                    'hash': level[sibling_index],
                    'position': 'right' if is_left else 'left'
                })
            
            index //= 2
        
        return proof
    
    def verify_proof(self, tx_hash: str, proof: List[Dict], root: str) -> bool:
        """Verify a Merkle proof"""
        current_hash = tx_hash
        
        for step in proof:
            sibling = step['hash']
            if step['position'] == 'right':
                current_hash = hashlib.sha256((current_hash + sibling).encode()).hexdigest()
            else:
                current_hash = hashlib.sha256((sibling + current_hash).encode()).hexdigest()
        
        return current_hash == root


@dataclass
class Block:
    """Block in the economic blockchain"""
    block_number: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    merkle_root: str
    nonce: int = 0
    hash: str = ""
    simulation_id: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def compute_hash(self) -> str:
        """Compute block hash"""
        block_data = {
            'block_number': self.block_number,
            'timestamp': self.timestamp,
            'tx_hashes': [tx.compute_hash() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'nonce': self.nonce,
            'simulation_id': self.simulation_id
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'block_number': self.block_number,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'transaction_count': len(self.transactions),
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'hash': self.hash,
            'simulation_id': self.simulation_id,
            'metadata': self.metadata
        }


class EconomicBlockchain:
    """
    Immutable ledger for economic simulation events
    Provides proof-of-integrity without mining
    """
    
    def __init__(
        self,
        simulation_id: str,
        max_transactions_per_block: int = 100
    ):
        self.simulation_id = simulation_id
        self.max_transactions_per_block = max_transactions_per_block
        
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.tx_count = 0
        
        self._lock = threading.Lock()
        
        # Create genesis block
        self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_tx = Transaction(
            tx_id="tx_genesis",
            event_type=EventType.SIMULATION_START,
            timestamp=time.time(),
            data={
                'simulation_id': self.simulation_id,
                'version': '1.0.0',
                'created_at': datetime.utcnow().isoformat()
            },
            simulation_id=self.simulation_id,
            tick=0
        )
        
        merkle = MerkleTree([genesis_tx])
        
        genesis_block = Block(
            block_number=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0" * 64,
            merkle_root=merkle.root,
            simulation_id=self.simulation_id,
            metadata={'type': 'genesis'}
        )
        genesis_block.hash = genesis_block.compute_hash()
        
        self.chain.append(genesis_block)
    
    def add_transaction(self, transaction: Transaction) -> str:
        """Add a new transaction to pending pool"""
        with self._lock:
            self.tx_count += 1
            transaction.tx_id = f"tx_{self.simulation_id}_{self.tx_count}"
            transaction.signature = transaction.compute_hash()
            
            self.pending_transactions.append(transaction)
            
            # Auto-create block if threshold reached
            if len(self.pending_transactions) >= self.max_transactions_per_block:
                self._create_block()
            
            return transaction.tx_id
    
    def record_event(
        self,
        event_type: EventType,
        data: Dict,
        tick: int = 0
    ) -> str:
        """Convenience method to record an event"""
        tx = Transaction(
            tx_id="",  # Will be assigned
            event_type=event_type,
            timestamp=time.time(),
            data=data,
            simulation_id=self.simulation_id,
            tick=tick
        )
        return self.add_transaction(tx)
    
    def record_macro_state(self, state: Dict, tick: int) -> str:
        """Record macroeconomic state snapshot"""
        return self.record_event(
            EventType.MACRO_STATE,
            {'macro_state': state},
            tick
        )
    
    def record_policy_change(
        self,
        policy_type: str,
        parameter: str,
        old_value: float,
        new_value: float,
        reasoning: str,
        tick: int
    ) -> str:
        """Record a policy change event"""
        return self.record_event(
            EventType.POLICY_CHANGE,
            {
                'policy_type': policy_type,
                'parameter': parameter,
                'old_value': old_value,
                'new_value': new_value,
                'reasoning': reasoning
            },
            tick
        )
    
    def record_shock(
        self,
        shock_type: str,
        name: str,
        magnitude: float,
        affected_sectors: List[str],
        tick: int
    ) -> str:
        """Record an economic shock event"""
        return self.record_event(
            EventType.ECONOMIC_SHOCK,
            {
                'shock_type': shock_type,
                'name': name,
                'magnitude': magnitude,
                'affected_sectors': affected_sectors
            },
            tick
        )
    
    def record_agent_decision(
        self,
        agent_id: str,
        agent_type: str,
        action: Dict,
        reasoning: str,
        tick: int
    ) -> str:
        """Record an agent's decision"""
        return self.record_event(
            EventType.AGENT_DECISION,
            {
                'agent_id': agent_id,
                'agent_type': agent_type,
                'action': action,
                'reasoning': reasoning
            },
            tick
        )
    
    def record_crewai_analysis(
        self,
        analysis_type: str,
        agents_involved: List[str],
        result: Dict,
        tick: int
    ) -> str:
        """Record CrewAI analysis output"""
        return self.record_event(
            EventType.CREWAI_ANALYSIS,
            {
                'analysis_type': analysis_type,
                'agents_involved': agents_involved,
                'result': result
            },
            tick
        )
    
    def _create_block(self) -> Optional[Block]:
        """Create a new block from pending transactions"""
        if not self.pending_transactions:
            return None
        
        with self._lock:
            transactions = self.pending_transactions[:self.max_transactions_per_block]
            self.pending_transactions = self.pending_transactions[self.max_transactions_per_block:]
            
            # Build Merkle tree
            merkle = MerkleTree(transactions)
            
            # Create block
            new_block = Block(
                block_number=len(self.chain),
                timestamp=time.time(),
                transactions=transactions,
                previous_hash=self.chain[-1].hash,
                merkle_root=merkle.root,
                simulation_id=self.simulation_id
            )
            new_block.hash = new_block.compute_hash()
            
            self.chain.append(new_block)
            
            logger.info(f"Created block {new_block.block_number} with {len(transactions)} transactions")
            
            return new_block
    
    def finalize(self) -> Block:
        """Finalize any remaining pending transactions into a block"""
        if self.pending_transactions:
            return self._create_block()
        return self.chain[-1] if self.chain else None
    
    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """Verify entire blockchain integrity"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # Verify hash
            if current.hash != current.compute_hash():
                return False, f"Block {i} hash mismatch"
            
            # Verify chain link
            if current.previous_hash != previous.hash:
                return False, f"Block {i} previous_hash mismatch"
            
            # Verify Merkle root
            merkle = MerkleTree(current.transactions)
            if merkle.root != current.merkle_root:
                return False, f"Block {i} Merkle root mismatch"
        
        return True, None
    
    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        """Find a transaction by ID"""
        for block in self.chain:
            for tx in block.transactions:
                if tx.tx_id == tx_id:
                    return tx
        return None
    
    def get_transaction_proof(self, tx_id: str) -> Optional[Dict]:
        """Get Merkle proof for a transaction"""
        for block in self.chain:
            for i, tx in enumerate(block.transactions):
                if tx.tx_id == tx_id:
                    merkle = MerkleTree(block.transactions)
                    proof = merkle.get_proof(i)
                    return {
                        'transaction': tx.to_dict(),
                        'block_number': block.block_number,
                        'block_hash': block.hash,
                        'merkle_root': block.merkle_root,
                        'proof': proof
                    }
        return None
    
    def get_events_by_type(self, event_type: EventType) -> List[Transaction]:
        """Get all transactions of a specific type"""
        events = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.event_type == event_type:
                    events.append(tx)
        return events
    
    def get_events_by_tick_range(
        self,
        start_tick: int,
        end_tick: int
    ) -> List[Transaction]:
        """Get all transactions within a tick range"""
        events = []
        for block in self.chain:
            for tx in block.transactions:
                if start_tick <= tx.tick <= end_tick:
                    events.append(tx)
        return events
    
    def get_chain_summary(self) -> Dict:
        """Get summary of the blockchain"""
        total_transactions = sum(len(b.transactions) for b in self.chain)
        
        event_counts = {}
        for block in self.chain:
            for tx in block.transactions:
                event_type = tx.event_type.value
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'simulation_id': self.simulation_id,
            'block_count': len(self.chain),
            'total_transactions': total_transactions,
            'pending_transactions': len(self.pending_transactions),
            'event_counts': event_counts,
            'chain_valid': self.verify_chain()[0],
            'latest_block_hash': self.chain[-1].hash if self.chain else None,
            'genesis_hash': self.chain[0].hash if self.chain else None
        }
    
    def export_chain(self) -> Dict:
        """Export entire chain for persistence"""
        return {
            'simulation_id': self.simulation_id,
            'blocks': [block.to_dict() for block in self.chain],
            'pending': [tx.to_dict() for tx in self.pending_transactions]
        }
    
    def replay_to_tick(self, target_tick: int) -> List[Dict]:
        """Get all events up to a specific tick for replay"""
        events = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.tick <= target_tick:
                    events.append(tx.to_dict())
        return sorted(events, key=lambda x: (x['tick'], x['timestamp']))


class BlockchainExplorer:
    """
    API for exploring the economic blockchain
    """
    
    def __init__(self, blockchain: EconomicBlockchain):
        self.blockchain = blockchain
    
    def get_block(self, block_number: int) -> Optional[Dict]:
        """Get block by number"""
        if 0 <= block_number < len(self.blockchain.chain):
            return self.blockchain.chain[block_number].to_dict()
        return None
    
    def get_latest_blocks(self, count: int = 10) -> List[Dict]:
        """Get most recent blocks"""
        blocks = self.blockchain.chain[-count:]
        return [b.to_dict() for b in blocks]
    
    def search_transactions(
        self,
        event_type: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Search transactions with filters"""
        results = []
        
        for block in reversed(self.blockchain.chain):
            for tx in reversed(block.transactions):
                # Apply filters
                if event_type and tx.event_type.value != event_type:
                    continue
                if agent_id and tx.data.get('agent_id') != agent_id:
                    continue
                if start_tick is not None and tx.tick < start_tick:
                    continue
                if end_tick is not None and tx.tick > end_tick:
                    continue
                
                results.append({
                    **tx.to_dict(),
                    'block_number': block.block_number
                })
                
                if len(results) >= limit:
                    break
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_policy_history(self) -> List[Dict]:
        """Get all policy changes"""
        policy_txs = self.blockchain.get_events_by_type(EventType.POLICY_CHANGE)
        return [tx.to_dict() for tx in policy_txs]
    
    def get_shock_history(self) -> List[Dict]:
        """Get all recorded shocks"""
        shock_txs = self.blockchain.get_events_by_type(EventType.ECONOMIC_SHOCK)
        return [tx.to_dict() for tx in shock_txs]
    
    def verify_transaction(self, tx_id: str) -> Dict:
        """Verify a transaction exists and is valid"""
        proof = self.blockchain.get_transaction_proof(tx_id)
        if not proof:
            return {'valid': False, 'error': 'Transaction not found'}
        
        # Verify Merkle proof
        tx_hash = proof['transaction']['signature']
        merkle = MerkleTree()
        valid = merkle.verify_proof(tx_hash, proof['proof'], proof['merkle_root'])
        
        return {
            'valid': valid,
            'transaction': proof['transaction'],
            'block_number': proof['block_number'],
            'block_hash': proof['block_hash'],
            'proof': proof['proof']
        }
