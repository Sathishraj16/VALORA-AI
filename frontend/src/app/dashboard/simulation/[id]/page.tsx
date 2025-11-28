'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Pause,
  StopCircle,
  FastForward,
  SkipForward,
  ArrowLeft,
  Download,
  Share2,
  Settings,
  Maximize2,
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  DollarSign,
  Percent,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Brain,
  LineChart,
  BarChart3,
  PieChart,
  Layers,
  Target,
  Gauge,
  Wallet,
  Building2,
  Factory,
  ShoppingCart,
  Briefcase,
} from 'lucide-react';
import {
  LineChart as RechartsLine,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart as RechartsPie,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Treemap,
} from 'recharts';
import { useWebSocket } from '@/lib/websocket';
import { api } from '@/lib/api';

interface SimulationState {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'completed' | 'error';
  currentStep: number;
  totalSteps: number;
  startedAt: string;
  elapsedTime: number;
  speed: number;
}

interface EconomicIndicators {
  gdp: number;
  gdpGrowth: number;
  inflation: number;
  unemployment: number;
  interestRate: number;
  consumerConfidence: number;
  businessConfidence: number;
  giniCoefficient: number;
  debtToGdp: number;
  tradeBalance: number;
}

interface AgentStats {
  total: number;
  byType: Record<string, number>;
  averageWealth: number;
  wealthDistribution: { range: string; count: number }[];
  activeDecisions: number;
  satisfactionIndex: number;
}

interface TimeSeriesData {
  step: number;
  timestamp: string;
  gdp: number;
  inflation: number;
  unemployment: number;
  interestRate: number;
  consumerSpending: number;
  investment: number;
  governmentSpending: number;
  exports: number;
  imports: number;
}

interface PolicyEvent {
  step: number;
  type: string;
  description: string;
  impact: 'positive' | 'negative' | 'neutral';
}

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#84cc16'];

export default function SimulationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const simulationId = params.id as string;
  
  const [simulation, setSimulation] = useState<SimulationState | null>(null);
  const [indicators, setIndicators] = useState<EconomicIndicators | null>(null);
  const [agentStats, setAgentStats] = useState<AgentStats | null>(null);
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesData[]>([]);
  const [policyEvents, setPolicyEvents] = useState<PolicyEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'agents' | 'sectors' | 'policy'>('overview');
  const [speed, setSpeed] = useState(1);
  const chartRef = useRef<HTMLDivElement>(null);

  // WebSocket connection for real-time updates
  const { lastMessage, isConnected, sendMessage } = useWebSocket(simulationId);

  // Process WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      const data = lastMessage;
      
      if (data.type === 'state_update' && data.state && typeof data.state === 'object') {
        const stateUpdate = data.state as Partial<SimulationState>;
        setSimulation(prev => prev ? { ...prev, ...stateUpdate } : null);
      }
      
      if (data.type === 'indicators_update' && data.indicators) {
        setIndicators(data.indicators as EconomicIndicators);
        if (data.timeSeries) {
          setTimeSeriesData(prev => {
            const newData = [...prev, data.timeSeries as TimeSeriesData];
            // Keep last 100 data points for performance
            return newData.slice(-100);
          });
        }
      }
      
      if (data.type === 'agents_update' && data.agents) {
        setAgentStats(data.agents as AgentStats);
      }
      
      if (data.type === 'policy_event' && data.event) {
        setPolicyEvents(prev => [...prev, data.event as PolicyEvent].slice(-50));
      }
    }
  }, [lastMessage]);

  // Load initial simulation data
  useEffect(() => {
    const loadSimulation = async () => {
      try {
        const response = await api.get(`/simulations/${simulationId}`);
        const data = response.data;
        
        setSimulation({
          id: data.id,
          name: data.name,
          status: data.status,
          currentStep: data.current_step || 0,
          totalSteps: data.total_steps || 1000,
          startedAt: data.started_at,
          elapsedTime: data.elapsed_time || 0,
          speed: 1,
        });
        
        setIndicators(data.current_indicators || generateMockIndicators());
        setAgentStats(data.agent_stats || generateMockAgentStats());
        setTimeSeriesData(data.time_series || generateMockTimeSeries());
        setPolicyEvents(data.policy_events || []);
        
        setIsLoading(false);
      } catch (error) {
        console.error('Failed to load simulation:', error);
        // Generate mock data for demo
        setSimulation({
          id: simulationId,
          name: 'Economic Simulation Alpha',
          status: 'running',
          currentStep: 247,
          totalSteps: 1000,
          startedAt: new Date().toISOString(),
          elapsedTime: 3600,
          speed: 1,
        });
        setIndicators(generateMockIndicators());
        setAgentStats(generateMockAgentStats());
        setTimeSeriesData(generateMockTimeSeries());
        setIsLoading(false);
      }
    };

    loadSimulation();
  }, [simulationId]);

  // Simulation control functions
  const handlePause = useCallback(() => {
    sendMessage({ action: 'pause' });
    setSimulation(prev => prev ? { ...prev, status: 'paused' } : null);
  }, [sendMessage]);

  const handleResume = useCallback(() => {
    sendMessage({ action: 'resume' });
    setSimulation(prev => prev ? { ...prev, status: 'running' } : null);
  }, [sendMessage]);

  const handleStop = useCallback(() => {
    sendMessage({ action: 'stop' });
    setSimulation(prev => prev ? { ...prev, status: 'completed' } : null);
  }, [sendMessage]);

  const handleSpeedChange = useCallback((newSpeed: number) => {
    sendMessage({ action: 'set_speed', speed: newSpeed });
    setSpeed(newSpeed);
  }, [sendMessage]);

  const handleStep = useCallback(() => {
    sendMessage({ action: 'step' });
  }, [sendMessage]);

  const exportResults = async () => {
    try {
      const response = await api.get(`/simulations/${simulationId}/export`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `simulation-${simulationId}-results.json`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export results:', error);
    }
  };

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

  if (!simulation) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <AlertTriangle className="w-12 h-12 text-yellow-500" />
        <h2 className="text-xl font-semibold">Simulation Not Found</h2>
        <button
          onClick={() => router.back()}
          className="btn-primary"
        >
          Go Back
        </button>
      </div>
    );
  }

  const progress = (simulation.currentStep / simulation.totalSteps) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-white/5 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold">{simulation.name}</h1>
            <div className="flex items-center gap-3 mt-1">
              <StatusBadge status={simulation.status} />
              <span className="text-sm text-muted-foreground">
                Step {simulation.currentStep.toLocaleString()} of {simulation.totalSteps.toLocaleString()}
              </span>
              <span className="text-sm text-muted-foreground flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatElapsedTime(simulation.elapsedTime)}
              </span>
              {isConnected && (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                  Live
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button onClick={exportResults} className="btn-secondary flex items-center gap-2">
            <Download className="w-4 h-4" />
            Export
          </button>
          <button className="btn-secondary flex items-center gap-2">
            <Share2 className="w-4 h-4" />
            Share
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="glass-card p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Simulation Progress</span>
          <span className="text-sm text-muted-foreground">{progress.toFixed(1)}%</span>
        </div>
        <div className="h-3 bg-white/5 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary to-purple-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>

        {/* Control Panel */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2">
            {simulation.status === 'running' ? (
              <button
                onClick={handlePause}
                className="p-3 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded-lg transition-colors"
              >
                <Pause className="w-5 h-5" />
              </button>
            ) : simulation.status === 'paused' ? (
              <button
                onClick={handleResume}
                className="p-3 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors"
              >
                <Play className="w-5 h-5" />
              </button>
            ) : null}
            
            <button
              onClick={handleStop}
              className="p-3 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
              disabled={simulation.status === 'completed'}
            >
              <StopCircle className="w-5 h-5" />
            </button>
            
            <button
              onClick={handleStep}
              className="p-3 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
              disabled={simulation.status !== 'paused'}
            >
              <SkipForward className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">Speed:</span>
            <div className="flex items-center gap-1">
              {[0.5, 1, 2, 5, 10].map((s) => (
                <button
                  key={s}
                  onClick={() => handleSpeedChange(s)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    speed === s
                      ? 'bg-primary text-white'
                      : 'bg-white/5 hover:bg-white/10'
                  }`}
                >
                  {s}x
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10 pb-2">
        {[
          { id: 'overview', label: 'Overview', icon: LineChart },
          { id: 'agents', label: 'Agents', icon: Users },
          { id: 'sectors', label: 'Sectors', icon: Layers },
          { id: 'policy', label: 'Policy Events', icon: Target },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-primary/20 text-primary'
                : 'hover:bg-white/5'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Key Indicators */}
            {indicators && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <IndicatorCard
                  title="GDP"
                  value={formatCurrency(indicators.gdp)}
                  change={indicators.gdpGrowth}
                  icon={DollarSign}
                />
                <IndicatorCard
                  title="Inflation"
                  value={`${indicators.inflation.toFixed(2)}%`}
                  change={indicators.inflation - 2}
                  icon={Percent}
                  inverted
                />
                <IndicatorCard
                  title="Unemployment"
                  value={`${indicators.unemployment.toFixed(2)}%`}
                  change={-indicators.unemployment + 5}
                  icon={Users}
                />
                <IndicatorCard
                  title="Interest Rate"
                  value={`${indicators.interestRate.toFixed(2)}%`}
                  change={0}
                  icon={Activity}
                />
              </div>
            )}

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* GDP & Growth Chart */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary" />
                  GDP & Growth Rate
                </h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timeSeriesData}>
                      <defs>
                        <linearGradient id="gdpGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="step" stroke="rgba(255,255,255,0.5)" />
                      <YAxis stroke="rgba(255,255,255,0.5)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="gdp"
                        stroke="#6366f1"
                        fill="url(#gdpGradient)"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Inflation & Unemployment */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-cyan-400" />
                  Inflation vs Unemployment
                </h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsLine data={timeSeriesData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="step" stroke="rgba(255,255,255,0.5)" />
                      <YAxis stroke="rgba(255,255,255,0.5)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                        }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="inflation"
                        stroke="#f59e0b"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="unemployment"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={false}
                      />
                    </RechartsLine>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* GDP Components */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <PieChart className="w-5 h-5 text-purple-400" />
                  GDP Components
                </h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={timeSeriesData.slice(-10)}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis type="number" stroke="rgba(255,255,255,0.5)" />
                      <YAxis dataKey="step" type="category" stroke="rgba(255,255,255,0.5)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                        }}
                      />
                      <Legend />
                      <Bar dataKey="consumerSpending" stackId="a" fill="#6366f1" name="Consumption" />
                      <Bar dataKey="investment" stackId="a" fill="#8b5cf6" name="Investment" />
                      <Bar dataKey="governmentSpending" stackId="a" fill="#06b6d4" name="Government" />
                      <Bar dataKey="exports" stackId="a" fill="#10b981" name="Net Exports" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Economic Health Radar */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Gauge className="w-5 h-5 text-green-400" />
                  Economic Health Index
                </h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart
                      data={
                        indicators
                          ? [
                              { metric: 'GDP Growth', value: Math.min(100, indicators.gdpGrowth * 20 + 50) },
                              { metric: 'Price Stability', value: Math.max(0, 100 - indicators.inflation * 10) },
                              { metric: 'Employment', value: Math.max(0, 100 - indicators.unemployment * 5) },
                              { metric: 'Consumer Confidence', value: indicators.consumerConfidence },
                              { metric: 'Business Confidence', value: indicators.businessConfidence },
                              { metric: 'Equality', value: Math.max(0, 100 - indicators.giniCoefficient * 100) },
                            ]
                          : []
                      }
                    >
                      <PolarGrid stroke="rgba(255,255,255,0.2)" />
                      <PolarAngleAxis dataKey="metric" stroke="rgba(255,255,255,0.5)" />
                      <PolarRadiusAxis stroke="rgba(255,255,255,0.3)" />
                      <Radar
                        name="Health"
                        dataKey="value"
                        stroke="#10b981"
                        fill="#10b981"
                        fillOpacity={0.3}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'agents' && agentStats && (
          <motion.div
            key="agents"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Agent Overview */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="glass-card p-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-primary/20 rounded-xl">
                    <Users className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Agents</p>
                    <p className="text-2xl font-bold">{agentStats.total.toLocaleString()}</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-green-500/20 rounded-xl">
                    <Wallet className="w-6 h-6 text-green-400" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Wealth</p>
                    <p className="text-2xl font-bold">{formatCurrency(agentStats.averageWealth)}</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-purple-500/20 rounded-xl">
                    <Brain className="w-6 h-6 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Active Decisions</p>
                    <p className="text-2xl font-bold">{agentStats.activeDecisions.toLocaleString()}</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-6">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-cyan-500/20 rounded-xl">
                    <Activity className="w-6 h-6 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Satisfaction</p>
                    <p className="text-2xl font-bold">{agentStats.satisfactionIndex.toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Agent Distribution by Type */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4">Agent Distribution</h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <RechartsPie>
                      <Pie
                        data={Object.entries(agentStats.byType).map(([name, value]) => ({
                          name,
                          value,
                        }))}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      >
                        {Object.keys(agentStats.byType).map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </RechartsPie>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Wealth Distribution */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4">Wealth Distribution</h3>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={agentStats.wealthDistribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="range" stroke="rgba(255,255,255,0.5)" />
                      <YAxis stroke="rgba(255,255,255,0.5)" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(0,0,0,0.8)',
                          border: '1px solid rgba(255,255,255,0.1)',
                          borderRadius: '8px',
                        }}
                      />
                      <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Agent Type Details */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4">Agent Types</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(agentStats.byType).map(([type, count], index) => {
                  const icons: Record<string, typeof Users> = {
                    Consumer: ShoppingCart,
                    Worker: Briefcase,
                    Firm: Factory,
                    Bank: Building2,
                  };
                  const Icon = icons[type] || Users;
                  
                  return (
                    <motion.div
                      key={type}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 bg-white/5 rounded-xl border border-white/10"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <div
                          className="p-2 rounded-lg"
                          style={{ backgroundColor: `${COLORS[index]}20` }}
                        >
                          <Icon className="w-5 h-5" style={{ color: COLORS[index] }} />
                        </div>
                        <span className="font-medium">{type}</span>
                      </div>
                      <p className="text-2xl font-bold">{count.toLocaleString()}</p>
                      <p className="text-sm text-muted-foreground">
                        {((count / agentStats.total) * 100).toFixed(1)}% of total
                      </p>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'sectors' && (
          <motion.div
            key="sectors"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4">Sector Performance</h3>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <Treemap
                    data={[
                      { name: 'Technology', size: 25000, growth: 5.2 },
                      { name: 'Finance', size: 22000, growth: 3.1 },
                      { name: 'Healthcare', size: 18000, growth: 4.5 },
                      { name: 'Manufacturing', size: 15000, growth: 1.8 },
                      { name: 'Energy', size: 12000, growth: -0.5 },
                      { name: 'Retail', size: 10000, growth: 2.3 },
                      { name: 'Agriculture', size: 8000, growth: 1.2 },
                      { name: 'Construction', size: 6000, growth: 2.8 },
                    ]}
                    dataKey="size"
                    aspectRatio={4 / 3}
                    stroke="rgba(255,255,255,0.2)"
                    content={<CustomTreemapContent />}
                  />
                </ResponsiveContainer>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { name: 'Technology', value: 25000, growth: 5.2, color: '#6366f1' },
                { name: 'Finance', value: 22000, growth: 3.1, color: '#8b5cf6' },
                { name: 'Healthcare', value: 18000, growth: 4.5, color: '#06b6d4' },
                { name: 'Manufacturing', value: 15000, growth: 1.8, color: '#10b981' },
              ].map((sector, index) => (
                <motion.div
                  key={sector.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="glass-card p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-medium">{sector.name}</span>
                    <span
                      className={`text-sm ${
                        sector.growth >= 0 ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {sector.growth >= 0 ? '+' : ''}
                      {sector.growth}%
                    </span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${(sector.value / 25000) * 100}%`,
                        backgroundColor: sector.color,
                      }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    {formatCurrency(sector.value * 1000000)}
                  </p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {activeTab === 'policy' && (
          <motion.div
            key="policy"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4">Policy Events Timeline</h3>
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {policyEvents.length > 0 ? (
                  policyEvents.map((event, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex gap-4 p-4 bg-white/5 rounded-xl border border-white/10"
                    >
                      <div
                        className={`p-2 rounded-lg ${
                          event.impact === 'positive'
                            ? 'bg-green-500/20'
                            : event.impact === 'negative'
                            ? 'bg-red-500/20'
                            : 'bg-gray-500/20'
                        }`}
                      >
                        {event.impact === 'positive' ? (
                          <CheckCircle className="w-5 h-5 text-green-400" />
                        ) : event.impact === 'negative' ? (
                          <AlertTriangle className="w-5 h-5 text-red-400" />
                        ) : (
                          <Activity className="w-5 h-5 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{event.type}</span>
                          <span className="text-sm text-muted-foreground">Step {event.step}</span>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{event.description}</p>
                      </div>
                    </motion.div>
                  ))
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No policy events yet</p>
                    <p className="text-sm">Policy changes will appear here as they occur</p>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Components
function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    running: 'bg-green-500/20 text-green-400',
    paused: 'bg-yellow-500/20 text-yellow-400',
    completed: 'bg-blue-500/20 text-blue-400',
    error: 'bg-red-500/20 text-red-400',
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium ${styles[status] || ''}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function IndicatorCard({
  title,
  value,
  change,
  icon: Icon,
  inverted = false,
}: {
  title: string;
  value: string;
  change: number;
  icon: typeof TrendingUp;
  inverted?: boolean;
}) {
  const isPositive = inverted ? change < 0 : change > 0;
  
  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-muted-foreground">{title}</span>
        <Icon className="w-5 h-5 text-muted-foreground" />
      </div>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-bold">{value}</span>
        <span
          className={`flex items-center gap-1 text-sm ${
            isPositive ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          {Math.abs(change).toFixed(2)}%
        </span>
      </div>
    </div>
  );
}

function CustomTreemapContent({ x, y, width, height, name, growth }: any) {
  if (width < 50 || height < 30) return null;
  
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        style={{
          fill: growth >= 0 ? `rgba(16, 185, 129, ${0.3 + growth / 10})` : `rgba(239, 68, 68, ${0.3 + Math.abs(growth) / 10})`,
          stroke: 'rgba(255,255,255,0.2)',
          strokeWidth: 1,
        }}
      />
      <text
        x={x + width / 2}
        y={y + height / 2}
        textAnchor="middle"
        dominantBaseline="middle"
        fill="white"
        fontSize={12}
        fontWeight="500"
      >
        {name}
      </text>
      <text
        x={x + width / 2}
        y={y + height / 2 + 16}
        textAnchor="middle"
        dominantBaseline="middle"
        fill={growth >= 0 ? '#10b981' : '#ef4444'}
        fontSize={10}
      >
        {growth >= 0 ? '+' : ''}{growth}%
      </text>
    </g>
  );
}

// Utility functions
function formatCurrency(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

function formatElapsedTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Mock data generators
function generateMockIndicators(): EconomicIndicators {
  return {
    gdp: 21.4e12 + Math.random() * 1e12,
    gdpGrowth: 2.3 + (Math.random() - 0.5) * 2,
    inflation: 2.1 + (Math.random() - 0.5) * 1,
    unemployment: 4.2 + (Math.random() - 0.5) * 1,
    interestRate: 5.25 + (Math.random() - 0.5) * 0.5,
    consumerConfidence: 65 + Math.random() * 20,
    businessConfidence: 70 + Math.random() * 15,
    giniCoefficient: 0.39 + (Math.random() - 0.5) * 0.1,
    debtToGdp: 123 + Math.random() * 10,
    tradeBalance: -80e9 + Math.random() * 20e9,
  };
}

function generateMockAgentStats(): AgentStats {
  return {
    total: 100000,
    byType: {
      Consumer: 70000,
      Worker: 60000,
      Firm: 5000,
      Bank: 200,
    },
    averageWealth: 85000 + Math.random() * 10000,
    wealthDistribution: [
      { range: '0-25K', count: 15000 },
      { range: '25K-50K', count: 25000 },
      { range: '50K-100K', count: 30000 },
      { range: '100K-250K', count: 20000 },
      { range: '250K-500K', count: 7000 },
      { range: '500K+', count: 3000 },
    ],
    activeDecisions: Math.floor(Math.random() * 10000),
    satisfactionIndex: 65 + Math.random() * 20,
  };
}

function generateMockTimeSeries(): TimeSeriesData[] {
  const data: TimeSeriesData[] = [];
  let gdp = 21e12;
  
  for (let i = 0; i < 50; i++) {
    gdp *= 1 + (Math.random() - 0.48) * 0.01;
    data.push({
      step: i,
      timestamp: new Date(Date.now() - (50 - i) * 60000).toISOString(),
      gdp: gdp / 1e12,
      inflation: 2 + Math.sin(i / 10) * 0.5 + (Math.random() - 0.5) * 0.3,
      unemployment: 4.5 + Math.cos(i / 15) * 0.8 + (Math.random() - 0.5) * 0.2,
      interestRate: 5.25 + Math.sin(i / 20) * 0.25,
      consumerSpending: 14 + Math.random() * 2,
      investment: 4 + Math.random() * 0.5,
      governmentSpending: 3.5 + Math.random() * 0.3,
      exports: 2.5 + Math.random() * 0.3,
      imports: 3.2 + Math.random() * 0.3,
    });
  }
  
  return data;
}
