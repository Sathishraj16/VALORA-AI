'use client';

import { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Search,
  Filter,
  ChevronDown,
  TrendingUp,
  TrendingDown,
  Activity,
  Brain,
  Wallet,
  ShoppingCart,
  Briefcase,
  Factory,
  Building2,
  Target,
  Zap,
  Eye,
  MoreVertical,
  RefreshCw,
  Download,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { api } from '@/lib/api';

interface Agent {
  id: string;
  type: 'consumer' | 'worker' | 'firm' | 'bank';
  name: string;
  wealth: number;
  income: number;
  satisfaction: number;
  riskTolerance: number;
  lastAction: string;
  lastActionTime: string;
  state: 'active' | 'idle' | 'deciding';
  decisions: number;
  createdAt: string;
}

interface AgentMetrics {
  totalAgents: number;
  activeAgents: number;
  totalWealth: number;
  averageWealth: number;
  averageSatisfaction: number;
  decisionsPerSecond: number;
  agentsByType: Record<string, number>;
}

const AGENT_TYPES = ['all', 'consumer', 'worker', 'firm', 'bank'] as const;
const SORT_OPTIONS = ['wealth', 'satisfaction', 'decisions', 'name'] as const;

const TYPE_ICONS = {
  consumer: ShoppingCart,
  worker: Briefcase,
  firm: Factory,
  bank: Building2,
};

const TYPE_COLORS = {
  consumer: '#8b5cf6',
  worker: '#f59e0b',
  firm: '#06b6d4',
  bank: '#10b981',
};

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<typeof AGENT_TYPES[number]>('all');
  const [sortBy, setSortBy] = useState<typeof SORT_OPTIONS[number]>('wealth');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const pageSize = 20;

  // Load agents data
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const [agentsRes, metricsRes] = await Promise.all([
          api.get('/agents'),
          api.get('/agents/metrics'),
        ]);
        setAgents(agentsRes.data);
        setMetrics(metricsRes.data);
      } catch (error) {
        console.error('Failed to load agents:', error);
        // Generate mock data
        setAgents(generateMockAgents(500));
        setMetrics(generateMockMetrics());
      } finally {
        setIsLoading(false);
      }
    };

    loadAgents();

    // Refresh every 5 seconds
    const interval = setInterval(loadAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  // Filter and sort agents
  const filteredAgents = useMemo(() => {
    let result = [...agents];

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.name.toLowerCase().includes(query) ||
          a.id.toLowerCase().includes(query) ||
          a.type.toLowerCase().includes(query)
      );
    }

    // Filter by type
    if (selectedType !== 'all') {
      result = result.filter((a) => a.type === selectedType);
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'wealth':
          comparison = a.wealth - b.wealth;
          break;
        case 'satisfaction':
          comparison = a.satisfaction - b.satisfaction;
          break;
        case 'decisions':
          comparison = a.decisions - b.decisions;
          break;
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });

    return result;
  }, [agents, searchQuery, selectedType, sortBy, sortOrder]);

  // Paginate
  const paginatedAgents = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredAgents.slice(start, start + pageSize);
  }, [filteredAgents, page]);

  const totalPages = Math.ceil(filteredAgents.length / pageSize);

  // Wealth distribution data for chart
  const wealthDistribution = useMemo(() => {
    const buckets = [
      { range: '0-10K', min: 0, max: 10000, count: 0 },
      { range: '10K-50K', min: 10000, max: 50000, count: 0 },
      { range: '50K-100K', min: 50000, max: 100000, count: 0 },
      { range: '100K-250K', min: 100000, max: 250000, count: 0 },
      { range: '250K-500K', min: 250000, max: 500000, count: 0 },
      { range: '500K-1M', min: 500000, max: 1000000, count: 0 },
      { range: '1M+', min: 1000000, max: Infinity, count: 0 },
    ];

    agents.forEach((agent) => {
      const bucket = buckets.find((b) => agent.wealth >= b.min && agent.wealth < b.max);
      if (bucket) bucket.count++;
    });

    return buckets;
  }, [agents]);

  // Satisfaction by type data
  const satisfactionByType = useMemo(() => {
    const typeData: Record<string, { total: number; count: number }> = {};

    agents.forEach((agent) => {
      if (!typeData[agent.type]) {
        typeData[agent.type] = { total: 0, count: 0 };
      }
      typeData[agent.type].total += agent.satisfaction;
      typeData[agent.type].count++;
    });

    return Object.entries(typeData).map(([type, data]) => ({
      type,
      satisfaction: data.total / data.count,
    }));
  }, [agents]);

  // Activity scatter data
  const activityData = useMemo(() => {
    return agents.slice(0, 100).map((agent) => ({
      wealth: agent.wealth / 1000,
      satisfaction: agent.satisfaction,
      decisions: agent.decisions,
      type: agent.type,
    }));
  }, [agents]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <Activity className="w-8 h-8 text-primary" />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Agent Population</h1>
          <p className="text-sm text-gray-500">
            Monitor and analyze economic agent behavior
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </button>
          <button className="btn-secondary flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <MetricCard
            icon={Users}
            label="Total Agents"
            value={metrics.totalAgents.toLocaleString()}
            color="#8b5cf6"
          />
          <MetricCard
            icon={Zap}
            label="Active"
            value={metrics.activeAgents.toLocaleString()}
            color="#10b981"
          />
          <MetricCard
            icon={Wallet}
            label="Total Wealth"
            value={formatCurrency(metrics.totalWealth)}
            color="#f59e0b"
          />
          <MetricCard
            icon={Wallet}
            label="Avg Wealth"
            value={formatCurrency(metrics.averageWealth)}
            color="#6366f1"
          />
          <MetricCard
            icon={Activity}
            label="Avg Satisfaction"
            value={`${metrics.averageSatisfaction.toFixed(1)}%`}
            color="#06b6d4"
          />
          <MetricCard
            icon={Brain}
            label="Decisions/sec"
            value={metrics.decisionsPerSecond.toFixed(0)}
            color="#ec4899"
          />
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Wealth Distribution */}
        <div className="glass-card">
          <h3 className="text-sm font-medium text-gray-900 mb-4">Wealth Distribution</h3>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={wealthDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="range" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Satisfaction by Type */}
        <div className="glass-card">
          <h3 className="text-sm font-medium text-gray-900 mb-4">Satisfaction by Type</h3>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={satisfactionByType} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" />
                <YAxis dataKey="type" type="category" stroke="#64748b" width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  formatter={(value: number) => `${value.toFixed(1)}%`}
                />
                <Bar dataKey="satisfaction" radius={[0, 4, 4, 0]}>
                  {satisfactionByType.map((entry, index) => (
                    <Cell
                      key={entry.type}
                      fill={TYPE_COLORS[entry.type as keyof typeof TYPE_COLORS] || '#6366f1'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Activity Scatter */}
        <div className="glass-card">
          <h3 className="text-sm font-medium text-gray-900 mb-4">Wealth vs Satisfaction</h3>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="wealth"
                  name="Wealth (K)"
                  stroke="#64748b"
                  unit="K"
                />
                <YAxis
                  dataKey="satisfaction"
                  name="Satisfaction"
                  stroke="#64748b"
                  unit="%"
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                />
                <Scatter data={activityData} fill="#6366f1">
                  {activityData.map((entry, index) => (
                    <Cell
                      key={index}
                      fill={TYPE_COLORS[entry.type as keyof typeof TYPE_COLORS] || '#6366f1'}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="glass-card p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search agents by name or ID..."
              className="w-full pl-10 pr-4 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
            />
          </div>

          {/* Type Filter */}
          <div className="flex items-center gap-1">
            {AGENT_TYPES.map((type) => (
              <button
                key={type}
                onClick={() => {
                  setSelectedType(type);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  selectedType === type
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {type === 'all' ? 'All' : type.charAt(0).toUpperCase() + type.slice(1)}
              </button>
            ))}
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as typeof SORT_OPTIONS[number])}
              className="px-3 py-1.5 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-gray-900"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  Sort by {option.charAt(0).toUpperCase() + option.slice(1)}
                </option>
              ))}
            </select>
            <button
              onClick={() => setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))}
              className="p-2 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors text-gray-600"
            >
              <ArrowUpDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Agents Table */}
      <div className="glass-card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Agent
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Wealth
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Income
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Satisfaction
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  State
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Action
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              <AnimatePresence mode="popLayout">
                {paginatedAgents.map((agent, index) => {
                  const Icon = TYPE_ICONS[agent.type];
                  const color = TYPE_COLORS[agent.type];

                  return (
                    <motion.tr
                      key={agent.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ delay: index * 0.02 }}
                      className="hover:bg-gray-50"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-8 h-8 rounded-full flex items-center justify-center"
                            style={{ backgroundColor: `${color}15` }}
                          >
                            <Icon className="w-4 h-4" style={{ color }} />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{agent.name}</p>
                            <p className="text-xs text-gray-400 font-mono">
                              {agent.id.slice(0, 8)}...
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className="px-2 py-1 rounded text-xs font-medium"
                          style={{
                            backgroundColor: `${color}15`,
                            color,
                          }}
                        >
                          {agent.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm text-gray-700">
                        {formatCurrency(agent.wealth)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-sm text-gray-700">
                        {formatCurrency(agent.income)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${agent.satisfaction}%`,
                                backgroundColor:
                                  agent.satisfaction > 70
                                    ? '#10b981'
                                    : agent.satisfaction > 40
                                    ? '#f59e0b'
                                    : '#ef4444',
                              }}
                            />
                          </div>
                          <span className="text-xs text-gray-600">{agent.satisfaction}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-center">
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              agent.state === 'active'
                                ? 'bg-green-100 text-green-700'
                                : agent.state === 'deciding'
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {agent.state}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-sm text-gray-700">{agent.lastAction}</p>
                          <p className="text-xs text-gray-400">
                            {formatRelativeTime(agent.lastActionTime)}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-1">
                          <button
                            onClick={() => setSelectedAgent(agent)}
                            className="p-1.5 hover:bg-gray-100 rounded transition-colors text-gray-500 hover:text-gray-700"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="p-1.5 hover:bg-gray-100 rounded transition-colors text-gray-500 hover:text-gray-700">
                            <MoreVertical className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  );
                })}
              </AnimatePresence>
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50">
          <p className="text-sm text-gray-500">
            Showing {(page - 1) * pageSize + 1} to{' '}
            {Math.min(page * pageSize, filteredAgents.length)} of {filteredAgents.length} agents
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-gray-500"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const pageNum = Math.max(1, Math.min(page - 2, totalPages - 4)) + i;
                if (pageNum > totalPages) return null;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-7 h-7 rounded text-sm font-medium transition-colors ${
                      page === pageNum
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
            </div>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 hover:bg-gray-200 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-gray-500"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Agent Detail Modal */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedAgent(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <AgentDetailView agent={selectedAgent} onClose={() => setSelectedAgent(null)} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Components
function MetricCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Users;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-3">
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: `${color}15` }}
        >
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-base font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
}

function AgentDetailView({
  agent,
  onClose,
}: {
  agent: Agent;
  onClose: () => void;
}) {
  const Icon = TYPE_ICONS[agent.type];
  const color = TYPE_COLORS[agent.type];

  // Generate mock activity history
  const activityHistory = Array.from({ length: 20 }, (_, i) => ({
    step: i + 1,
    wealth: agent.wealth * (0.95 + Math.random() * 0.1),
    satisfaction: agent.satisfaction * (0.9 + Math.random() * 0.2),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center"
            style={{ backgroundColor: `${color}20` }}
          >
            <Icon className="w-8 h-8" style={{ color }} />
          </div>
          <div>
            <h2 className="text-xl font-bold">{agent.name}</h2>
            <p className="text-sm text-muted-foreground font-mono">{agent.id}</p>
            <span
              className="inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium"
              style={{ backgroundColor: `${color}20`, color }}
            >
              {agent.type}
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-white/10 rounded-lg transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-white/5 rounded-xl">
          <p className="text-sm text-muted-foreground">Wealth</p>
          <p className="text-xl font-bold">{formatCurrency(agent.wealth)}</p>
        </div>
        <div className="p-4 bg-white/5 rounded-xl">
          <p className="text-sm text-muted-foreground">Income</p>
          <p className="text-xl font-bold">{formatCurrency(agent.income)}</p>
        </div>
        <div className="p-4 bg-white/5 rounded-xl">
          <p className="text-sm text-muted-foreground">Satisfaction</p>
          <p className="text-xl font-bold">{agent.satisfaction}%</p>
        </div>
        <div className="p-4 bg-white/5 rounded-xl">
          <p className="text-sm text-muted-foreground">Risk Tolerance</p>
          <p className="text-xl font-bold">{agent.riskTolerance}%</p>
        </div>
      </div>

      {/* Activity Chart */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Activity History</h3>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={activityHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="step" stroke="rgba(255,255,255,0.5)" />
              <YAxis yAxisId="left" stroke="rgba(255,255,255,0.5)" />
              <YAxis yAxisId="right" orientation="right" stroke="rgba(255,255,255,0.5)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.8)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="wealth"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
                name="Wealth"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="satisfaction"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                name="Satisfaction"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Actions */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Recent Actions</h3>
        <div className="space-y-2">
          {[
            { action: agent.lastAction, time: agent.lastActionTime },
            { action: 'Consumed goods', time: new Date(Date.now() - 60000).toISOString() },
            { action: 'Received income', time: new Date(Date.now() - 120000).toISOString() },
            { action: 'Made savings decision', time: new Date(Date.now() - 180000).toISOString() },
          ].map((item, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
            >
              <span>{item.action}</span>
              <span className="text-sm text-muted-foreground">
                {formatRelativeTime(item.time)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Utility functions
function formatCurrency(value: number): string {
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

function formatRelativeTime(isoString: string): string {
  const seconds = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

// Mock data generators
function generateMockAgents(count: number): Agent[] {
  const types: Agent['type'][] = ['consumer', 'worker', 'firm', 'bank'];
  const states: Agent['state'][] = ['active', 'idle', 'deciding'];
  const actions = [
    'Consumed goods',
    'Made investment',
    'Received income',
    'Paid taxes',
    'Applied for loan',
    'Hired worker',
    'Produced goods',
    'Adjusted prices',
  ];

  const firstNames = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Quinn', 'Avery'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Davis', 'Miller', 'Wilson'];

  return Array.from({ length: count }, (_, i) => {
    const type = types[Math.floor(Math.random() * types.length)];
    const baseWealth = type === 'bank' ? 1000000 : type === 'firm' ? 500000 : 50000;

    return {
      id: `agent-${Math.random().toString(36).substr(2, 9)}`,
      type,
      name: `${firstNames[Math.floor(Math.random() * firstNames.length)]} ${
        lastNames[Math.floor(Math.random() * lastNames.length)]
      }`,
      wealth: baseWealth * (0.2 + Math.random() * 2),
      income: baseWealth * 0.05 * (0.5 + Math.random()),
      satisfaction: Math.floor(40 + Math.random() * 50),
      riskTolerance: Math.floor(20 + Math.random() * 60),
      lastAction: actions[Math.floor(Math.random() * actions.length)],
      lastActionTime: new Date(Date.now() - Math.random() * 3600000).toISOString(),
      state: states[Math.floor(Math.random() * states.length)],
      decisions: Math.floor(Math.random() * 1000),
      createdAt: new Date(Date.now() - Math.random() * 86400000 * 30).toISOString(),
    };
  });
}

function generateMockMetrics(): AgentMetrics {
  return {
    totalAgents: 500,
    activeAgents: 387,
    totalWealth: 125000000,
    averageWealth: 250000,
    averageSatisfaction: 67.3,
    decisionsPerSecond: 1250,
    agentsByType: {
      consumer: 300,
      worker: 150,
      firm: 40,
      bank: 10,
    },
  };
}
