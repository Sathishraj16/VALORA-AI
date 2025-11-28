"""
VALORA Blockchain API Router
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..blockchain.ledger import (
    EconomicBlockchain,
    BlockchainExplorer,
    EconomicEvent,
    EventType
)
from ..simulation.orchestrator import SimulationManager

router = APIRouter()

# Global references
simulation_manager = SimulationManager()


class EventResponse(BaseModel):
    """Blockchain event response"""
    event_id: str
    event_type: str
    timestamp: str
    actor_id: str
    actor_type: str
    description: str
    data: Dict[str, Any]
    amount: float


class BlockResponse(BaseModel):
    """Block response"""
    index: int
    timestamp: str
    previous_hash: str
    merkle_root: str
    block_hash: str
    nonce: int
    event_count: int
    events: List[EventResponse]


class ChainStatsResponse(BaseModel):
    """Blockchain statistics response"""
    chain_length: int
    total_events: int
    is_valid: bool
    event_counts_by_type: Dict[str, int]
    latest_block_hash: str


class VerificationResponse(BaseModel):
    """Chain verification response"""
    is_valid: bool
    errors: List[str]
    verified_blocks: int
    verification_time: float


@router.get("/{simulation_id}/blocks", response_model=List[BlockResponse])
async def get_blocks(
    simulation_id: str,
    start: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """Get blocks from the blockchain"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    blocks = sim.blockchain.chain[start:start + limit]
    
    return [
        BlockResponse(
            index=block.index,
            timestamp=block.timestamp.isoformat(),
            previous_hash=block.previous_hash,
            merkle_root=block.merkle_root,
            block_hash=block.hash,
            nonce=block.nonce,
            event_count=len(block.events),
            events=[
                EventResponse(
                    event_id=e.event_id,
                    event_type=e.event_type.value,
                    timestamp=e.timestamp.isoformat(),
                    actor_id=e.actor_id,
                    actor_type=e.actor_type,
                    description=e.description,
                    data=e.data,
                    amount=e.amount
                )
                for e in block.events
            ]
        )
        for block in blocks
    ]


@router.get("/{simulation_id}/blocks/{block_index}", response_model=BlockResponse)
async def get_block(simulation_id: str, block_index: int):
    """Get a specific block"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    if block_index < 0 or block_index >= len(sim.blockchain.chain):
        raise HTTPException(status_code=404, detail="Block not found")
    
    block = sim.blockchain.chain[block_index]
    
    return BlockResponse(
        index=block.index,
        timestamp=block.timestamp.isoformat(),
        previous_hash=block.previous_hash,
        merkle_root=block.merkle_root,
        block_hash=block.hash,
        nonce=block.nonce,
        event_count=len(block.events),
        events=[
            EventResponse(
                event_id=e.event_id,
                event_type=e.event_type.value,
                timestamp=e.timestamp.isoformat(),
                actor_id=e.actor_id,
                actor_type=e.actor_type,
                description=e.description,
                data=e.data,
                amount=e.amount
            )
            for e in block.events
        ]
    )


@router.get("/{simulation_id}/stats", response_model=ChainStatsResponse)
async def get_chain_stats(simulation_id: str):
    """Get blockchain statistics"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    explorer = BlockchainExplorer(sim.blockchain)
    stats = explorer.get_statistics()
    
    return ChainStatsResponse(
        chain_length=stats['chain_length'],
        total_events=stats['total_events'],
        is_valid=stats['chain_valid'],
        event_counts_by_type=stats['events_by_type'],
        latest_block_hash=sim.blockchain.chain[-1].hash if sim.blockchain.chain else ""
    )


@router.get("/{simulation_id}/verify", response_model=VerificationResponse)
async def verify_chain(simulation_id: str):
    """Verify blockchain integrity"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    import time
    start_time = time.time()
    
    is_valid, errors = sim.blockchain.verify_chain()
    
    verification_time = time.time() - start_time
    
    return VerificationResponse(
        is_valid=is_valid,
        errors=errors,
        verified_blocks=len(sim.blockchain.chain),
        verification_time=verification_time
    )


@router.get("/{simulation_id}/events")
async def search_events(
    simulation_id: str,
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    actor_type: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """Search events in the blockchain"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    explorer = BlockchainExplorer(sim.blockchain)
    
    # Build filters
    filters = {}
    if event_type:
        filters['event_type'] = EventType(event_type)
    if actor_id:
        filters['actor_id'] = actor_id
    if actor_type:
        filters['actor_type'] = actor_type
    if min_amount is not None:
        filters['min_amount'] = min_amount
    if max_amount is not None:
        filters['max_amount'] = max_amount
    if start_time:
        filters['start_time'] = datetime.fromisoformat(start_time)
    if end_time:
        filters['end_time'] = datetime.fromisoformat(end_time)
    
    events = explorer.search_events(**filters)[:limit]
    
    return {
        "simulation_id": simulation_id,
        "count": len(events),
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "timestamp": e.timestamp.isoformat(),
                "actor_id": e.actor_id,
                "actor_type": e.actor_type,
                "description": e.description,
                "data": e.data,
                "amount": e.amount
            }
            for e in events
        ]
    }


@router.get("/{simulation_id}/actor/{actor_id}")
async def get_actor_history(
    simulation_id: str,
    actor_id: str,
    limit: int = Query(50, ge=1, le=500)
):
    """Get all events for a specific actor"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    explorer = BlockchainExplorer(sim.blockchain)
    history = explorer.get_actor_history(actor_id)[:limit]
    
    return {
        "simulation_id": simulation_id,
        "actor_id": actor_id,
        "event_count": len(history),
        "events": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "timestamp": e.timestamp.isoformat(),
                "description": e.description,
                "data": e.data,
                "amount": e.amount
            }
            for e in history
        ]
    }


@router.get("/{simulation_id}/event/{event_id}")
async def get_event(simulation_id: str, event_id: str):
    """Get a specific event by ID"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    explorer = BlockchainExplorer(sim.blockchain)
    
    # Search for event
    for block in sim.blockchain.chain:
        for event in block.events:
            if event.event_id == event_id:
                proof = explorer.get_merkle_proof(event_id)
                return {
                    "event": {
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "actor_id": event.actor_id,
                        "actor_type": event.actor_type,
                        "description": event.description,
                        "data": event.data,
                        "amount": event.amount
                    },
                    "block_index": block.index,
                    "block_hash": block.hash,
                    "merkle_proof": proof
                }
    
    raise HTTPException(status_code=404, detail="Event not found")


@router.get("/{simulation_id}/export")
async def export_chain(
    simulation_id: str,
    format: str = Query("json", pattern="^(json|csv)$")
):
    """Export blockchain data"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    if format == "json":
        data = []
        for block in sim.blockchain.chain:
            data.append({
                "index": block.index,
                "timestamp": block.timestamp.isoformat(),
                "previous_hash": block.previous_hash,
                "merkle_root": block.merkle_root,
                "hash": block.hash,
                "nonce": block.nonce,
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type.value,
                        "timestamp": e.timestamp.isoformat(),
                        "actor_id": e.actor_id,
                        "actor_type": e.actor_type,
                        "description": e.description,
                        "data": e.data,
                        "amount": e.amount
                    }
                    for e in block.events
                ]
            })
        return {"format": "json", "data": data}
    
    else:  # CSV
        lines = ["event_id,event_type,timestamp,actor_id,actor_type,amount,block_index,block_hash"]
        for block in sim.blockchain.chain:
            for event in block.events:
                lines.append(
                    f"{event.event_id},{event.event_type.value},{event.timestamp.isoformat()},"
                    f"{event.actor_id},{event.actor_type},{event.amount},{block.index},{block.hash}"
                )
        return {"format": "csv", "data": "\n".join(lines)}


@router.get("/{simulation_id}/merkle/{block_index}")
async def get_merkle_tree(simulation_id: str, block_index: int):
    """Get Merkle tree structure for a block"""
    sim = simulation_manager.get_simulation(simulation_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    if not sim.blockchain:
        raise HTTPException(status_code=400, detail="Blockchain not initialized")
    
    if block_index < 0 or block_index >= len(sim.blockchain.chain):
        raise HTTPException(status_code=404, detail="Block not found")
    
    block = sim.blockchain.chain[block_index]
    
    # Get event hashes
    from ..blockchain.ledger import MerkleTree
    import hashlib
    
    event_hashes = []
    for event in block.events:
        event_json = json.dumps({
            'event_id': event.event_id,
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'actor_id': event.actor_id,
            'data': event.data,
            'amount': event.amount
        }, sort_keys=True)
        event_hash = hashlib.sha256(event_json.encode()).hexdigest()
        event_hashes.append({
            'event_id': event.event_id,
            'hash': event_hash
        })
    
    return {
        "block_index": block_index,
        "merkle_root": block.merkle_root,
        "event_count": len(block.events),
        "event_hashes": event_hashes
    }


import json
