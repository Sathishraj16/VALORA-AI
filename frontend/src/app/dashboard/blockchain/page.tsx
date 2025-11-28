'use client';

import { useState, useEffect } from 'react';
import {
  Blocks,
  Search,
  ChevronRight,
  CheckCircle,
  XCircle,
  Hash,
  Clock,
  Users,
  FileText,
  Shield,
  RefreshCw,
  Download,
} from 'lucide-react';
import { toast } from 'sonner';
import { cn, truncateAddress, formatNumber, timeAgo } from '@/lib/utils';
import { useSimulationStore, useUIStore } from '@/lib/store';
import { blockchainApi } from '@/lib/api';

interface Block {
  index: number;
  timestamp: string;
  previous_hash: string;
  merkle_root: string;
  block_hash: string;
  nonce: number;
  event_count: number;
  events: Event[];
}

interface Event {
  event_id: string;
  event_type: string;
  timestamp: string;
  actor_id: string;
  actor_type: string;
  description: string;
  amount: number;
}

interface ChainStats {
  chain_length: number;
  total_events: number;
  is_valid: boolean;
  event_counts_by_type: Record<string, number>;
  latest_block_hash: string;
}

export default function BlockchainExplorerPage() {
  const { currentSimulation } = useSimulationStore();
  const { selectedBlock, setSelectedBlock } = useUIStore();
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [stats, setStats] = useState<ChainStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!currentSimulation?.simulation_id) {
        setLoading(false);
        return;
      }

      try {
        const [blocksRes, statsRes] = await Promise.all([
          blockchainApi.getBlocks(currentSimulation.simulation_id, { limit: 50 }),
          blockchainApi.getStats(currentSimulation.simulation_id),
        ]);

        setBlocks(blocksRes.data);
        setStats(statsRes.data);
      } catch (error) {
        console.error('Failed to fetch blockchain data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [currentSimulation?.simulation_id]);

  const handleVerifyChain = async () => {
    if (!currentSimulation) return;
    setVerifying(true);

    try {
      const response = await blockchainApi.verify(currentSimulation.simulation_id);
      if (response.data.is_valid) {
        toast.success(`Chain verified! ${response.data.verified_blocks} blocks in ${response.data.verification_time.toFixed(3)}s`);
      } else {
        toast.error(`Chain invalid! Errors: ${response.data.errors.join(', ')}`);
      }
    } catch (error) {
      toast.error('Failed to verify chain');
    } finally {
      setVerifying(false);
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    if (!currentSimulation) return;

    try {
      const response = await blockchainApi.export(currentSimulation.simulation_id, format);
      const blob = new Blob(
        [format === 'json' ? JSON.stringify(response.data.data, null, 2) : response.data.data],
        { type: format === 'json' ? 'application/json' : 'text/csv' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `valora-blockchain-${currentSimulation.simulation_id}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (error) {
      toast.error('Export failed');
    }
  };

  if (!currentSimulation) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Blocks className="w-12 h-12 text-dark-500 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">No Simulation Selected</h2>
        <p className="text-dark-400">Create or select a simulation to explore the blockchain.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    );
  }

  const filteredBlocks = searchQuery
    ? blocks.filter(
        (b) =>
          b.block_hash.toLowerCase().includes(searchQuery.toLowerCase()) ||
          b.merkle_root.toLowerCase().includes(searchQuery.toLowerCase()) ||
          b.events.some((e) => e.event_id.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : blocks;

  const activeBlock = selectedBlock !== null ? blocks.find((b) => b.index === selectedBlock) : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Blocks className="w-6 h-6 text-primary-400" />
            Blockchain Explorer
          </h1>
          <p className="text-dark-400">Immutable audit trail of all economic events</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleVerifyChain}
            disabled={verifying}
            className="btn-secondary flex items-center gap-2"
          >
            {verifying ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Shield className="w-4 h-4" />
            )}
            Verify Chain
          </button>
          <button
            onClick={() => handleExport('json')}
            className="btn-secondary flex items-center gap-2"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card-stat">
            <div className="flex items-center gap-2">
              <Hash className="w-4 h-4 text-primary-400" />
              <span className="card-stat-label">Total Blocks</span>
            </div>
            <div className="card-stat-value">{formatNumber(stats.chain_length)}</div>
          </div>
          <div className="card-stat">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-accent-400" />
              <span className="card-stat-label">Total Events</span>
            </div>
            <div className="card-stat-value">{formatNumber(stats.total_events)}</div>
          </div>
          <div className="card-stat">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-yellow-400" />
              <span className="card-stat-label">Chain Status</span>
            </div>
            <div className={cn('card-stat-value flex items-center gap-2', stats.is_valid ? 'text-accent-400' : 'text-red-400')}>
              {stats.is_valid ? (
                <>
                  <CheckCircle className="w-5 h-5" />
                  Valid
                </>
              ) : (
                <>
                  <XCircle className="w-5 h-5" />
                  Invalid
                </>
              )}
            </div>
          </div>
          <div className="card-stat">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-dark-400" />
              <span className="card-stat-label">Latest Hash</span>
            </div>
            <div className="card-stat-value font-mono text-sm">
              {truncateAddress(stats.latest_block_hash, 8, 6)}
            </div>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by block hash, merkle root, or event ID..."
          className="input-field pl-10"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Block List */}
        <div className="lg:col-span-1 space-y-2 max-h-[600px] overflow-y-auto scrollbar-hide">
          {filteredBlocks.map((block) => (
            <button
              key={block.index}
              onClick={() => setSelectedBlock(block.index)}
              className={cn(
                'w-full p-4 rounded-lg border text-left transition-all',
                selectedBlock === block.index
                  ? 'border-primary-500 bg-primary-600/10'
                  : 'border-dark-700 bg-dark-800/50 hover:border-dark-600'
              )}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono font-medium text-white">Block #{block.index}</span>
                <ChevronRight className={cn('w-4 h-4 text-dark-400 transition-transform', selectedBlock === block.index && 'rotate-90')} />
              </div>
              <div className="text-xs text-dark-400 space-y-1">
                <div className="flex justify-between">
                  <span>Events</span>
                  <span className="text-white">{block.event_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Hash</span>
                  <span className="font-mono text-dark-300">{truncateAddress(block.block_hash, 6, 4)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Time</span>
                  <span>{timeAgo(block.timestamp)}</span>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Block Details */}
        <div className="lg:col-span-2">
          {activeBlock ? (
            <div className="glass-card space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Block #{activeBlock.index}</h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-dark-400">Block Hash</span>
                    <div className="font-mono text-white break-all">{activeBlock.block_hash}</div>
                  </div>
                  <div>
                    <span className="text-dark-400">Previous Hash</span>
                    <div className="font-mono text-white break-all">{activeBlock.previous_hash}</div>
                  </div>
                  <div>
                    <span className="text-dark-400">Merkle Root</span>
                    <div className="font-mono text-white break-all">{activeBlock.merkle_root}</div>
                  </div>
                  <div>
                    <span className="text-dark-400">Nonce</span>
                    <div className="text-white">{activeBlock.nonce}</div>
                  </div>
                  <div>
                    <span className="text-dark-400">Timestamp</span>
                    <div className="text-white">{new Date(activeBlock.timestamp).toLocaleString()}</div>
                  </div>
                  <div>
                    <span className="text-dark-400">Event Count</span>
                    <div className="text-white">{activeBlock.event_count}</div>
                  </div>
                </div>
              </div>

              {/* Events in Block */}
              <div>
                <h4 className="text-md font-semibold text-white mb-3">Events</h4>
                <div className="space-y-2 max-h-[300px] overflow-y-auto">
                  {activeBlock.events.map((event) => (
                    <div
                      key={event.event_id}
                      onClick={() => setSelectedEvent(event)}
                      className={cn(
                        'p-3 rounded-lg border cursor-pointer transition-all',
                        selectedEvent?.event_id === event.event_id
                          ? 'border-accent-500 bg-accent-600/10'
                          : 'border-dark-700 bg-dark-800/30 hover:border-dark-600'
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="badge-info capitalize">{event.event_type.replace(/_/g, ' ')}</span>
                        <span className="text-xs text-dark-400">{timeAgo(event.timestamp)}</span>
                      </div>
                      <div className="text-sm text-dark-300 truncate">{event.description}</div>
                      <div className="flex items-center justify-between mt-2 text-xs text-dark-400">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {event.actor_type}: {truncateAddress(event.actor_id, 6, 4)}
                        </span>
                        <span className="font-mono">{formatNumber(event.amount)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card flex flex-col items-center justify-center h-64 text-center">
              <Blocks className="w-12 h-12 text-dark-500 mb-4" />
              <p className="text-dark-400">Select a block to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Event Type Distribution */}
      {stats?.event_counts_by_type && (
        <div className="glass-card">
          <h3 className="text-lg font-semibold text-white mb-4">Event Distribution</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {Object.entries(stats.event_counts_by_type).map(([type, count]) => (
              <div key={type} className="text-center p-3 bg-dark-800/50 rounded-lg">
                <div className="text-xs text-dark-400 capitalize mb-1">{type.replace(/_/g, ' ')}</div>
                <div className="text-xl font-bold text-white">{formatNumber(count)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
