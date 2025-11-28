'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  TrendingUp,
  Activity,
  Users,
  Building2,
  Landmark,
  DollarSign,
  Percent,
  Briefcase,
  PiggyBank,
  Zap,
  Plus,
  ArrowRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { cn, formatNumber, formatPercent, formatCompact, getCyclePhaseColor, getChangeIndicator } from '@/lib/utils';
import { useSimulationStore } from '@/lib/store';
import { simulationsApi } from '@/lib/api';

const CHART_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

interface StatCardProps {
  label: string;
  value: string | number;
  change?: number;
  icon: React.ElementType;
  format?: 'number' | 'percent' | 'currency' | 'compact';
}

function StatCard({ label, value, change, icon: Icon, format = 'number' }: StatCardProps) {
  const { direction, color } = change !== undefined ? getChangeIndicator(change) : { direction: 'neutral', color: 'text-slate-400' };
  
  const formattedValue = typeof value === 'number'
    ? format === 'percent' ? formatPercent(value) : format === 'compact' ? formatCompact(value) : formatNumber(value)
    : value;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">{label}</span>
        <Icon className="w-5 h-5 text-slate-500" />
      </div>
      <div className="text-2xl font-bold text-white">{formattedValue}</div>
      {change !== undefined && (
        <div className={cn(
          'text-sm font-medium flex items-center gap-1 mt-1',
          direction === 'up' ? 'text-emerald-400' : direction === 'down' ? 'text-red-400' : 'text-slate-400'
        )}>
          {direction === 'up' ? '↑' : direction === 'down' ? '↓' : '—'}
          <span>{formatPercent(Math.abs(change))}</span>
        </div>
      )}
    </div>
  );
}

export default function DashboardOverview() {
  const { currentSimulation, macroState, history, setMacroState, setHistory } = useSimulationStore();
  const [agentStats, setAgentStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (!currentSimulation?.simulation_id) {
        setLoading(false);
        return;
      }

      try {
        const [stateRes, historyRes, agentRes] = await Promise.all([
          simulationsApi.getState(currentSimulation.simulation_id).catch(() => null),
          simulationsApi.getHistory(currentSimulation.simulation_id, { limit: 100 }).catch(() => null),
          simulationsApi.getAgents(currentSimulation.simulation_id).catch(() => null),
        ]);

        if (stateRes?.data) {
          setMacroState(stateRes.data);
        }
        if (historyRes?.data?.history) {
          setHistory(historyRes.data.history);
        }
        if (agentRes?.data?.statistics) {
          setAgentStats(agentRes.data.statistics);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [currentSimulation?.simulation_id, setMacroState, setHistory]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    );
  }

  if (!currentSimulation) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mb-6">
          <Activity className="w-8 h-8 text-slate-500" />
        </div>
        <h2 className="text-2xl font-semibold text-white mb-3">No Simulation Selected</h2>
        <p className="text-slate-400 mb-8 max-w-md">
          Create a new simulation or select an existing one to start analyzing economic data.
        </p>
        <Link
          href="/dashboard/simulation/new"
          className="inline-flex items-center gap-2 bg-white text-slate-900 px-6 py-3 rounded-lg font-medium hover:bg-slate-100 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Create New Simulation
        </Link>
      </div>
    );
  }

  // Prepare chart data
  const chartData = history.slice(-50).map((entry) => ({
    tick: entry.tick,
    gdp: entry.macro_state?.gdp || 0,
    gdp_growth: (entry.macro_state?.gdp_growth || 0) * 100,
    inflation: (entry.macro_state?.inflation || 0) * 100,
    unemployment: (entry.macro_state?.unemployment || 0) * 100,
    interest_rate: (entry.macro_state?.interest_rate || 0) * 100,
    confidence: ((entry.macro_state?.consumer_confidence || 0) + (entry.macro_state?.business_confidence || 0)) / 2 * 100,
  }));

  const sectorData = macroState?.sector_gdp
    ? Object.entries(macroState.sector_gdp).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const prevState = history.length > 1 ? history[history.length - 2]?.macro_state : null;

  return (
    <div className="space-y-6">
      {/* Cycle Phase Banner */}
      {macroState?.cycle_phase && (
        <div className={cn(
          'bg-slate-800 border border-slate-700 rounded-xl p-4 flex items-center justify-between',
          getCyclePhaseColor(macroState.cycle_phase)
        )}>
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-indigo-400" />
            <span className="font-medium text-white">
              Economic Cycle: <span className="capitalize text-indigo-400">{macroState.cycle_phase}</span>
            </span>
          </div>
          <span className="text-sm text-slate-400">Tick {macroState.tick}</span>
        </div>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          label="GDP"
          value={macroState?.gdp || 0}
          change={prevState ? (macroState!.gdp - prevState.gdp) / prevState.gdp : undefined}
          icon={DollarSign}
          format="compact"
        />
        <StatCard
          label="GDP Growth"
          value={macroState?.gdp_growth || 0}
          change={prevState ? macroState!.gdp_growth - prevState.gdp_growth : undefined}
          icon={TrendingUp}
          format="percent"
        />
        <StatCard
          label="Inflation"
          value={macroState?.inflation || 0}
          change={prevState ? macroState!.inflation - prevState.inflation : undefined}
          icon={Percent}
          format="percent"
        />
        <StatCard
          label="Unemployment"
          value={macroState?.unemployment || 0}
          change={prevState ? macroState!.unemployment - prevState.unemployment : undefined}
          icon={Briefcase}
          format="percent"
        />
        <StatCard
          label="Interest Rate"
          value={macroState?.interest_rate || 0}
          change={prevState ? macroState!.interest_rate - prevState.interest_rate : undefined}
          icon={Landmark}
          format="percent"
        />
        <StatCard
          label="Debt/GDP"
          value={macroState?.debt_to_gdp || 0}
          change={prevState ? macroState!.debt_to_gdp - prevState.debt_to_gdp : undefined}
          icon={PiggyBank}
          format="percent"
        />
      </div>

      {/* Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* GDP & Growth Chart */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">GDP & Growth Rate</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="gdpGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="tick" stroke="#64748b" fontSize={12} />
                <YAxis yAxisId="left" stroke="#64748b" fontSize={12} />
                <YAxis yAxisId="right" orientation="right" stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    border: '1px solid rgba(71, 85, 105, 0.5)',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Area
                  yAxisId="left"
                  type="monotone"
                  dataKey="gdp"
                  stroke="#6366f1"
                  fill="url(#gdpGradient)"
                  name="GDP"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="gdp_growth"
                  stroke="#10b981"
                  strokeWidth={2}
                  dot={false}
                  name="Growth %"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Inflation & Unemployment Chart */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Inflation vs Unemployment</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="tick" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    border: '1px solid rgba(71, 85, 105, 0.5)',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="inflation"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  name="Inflation %"
                />
                <Line
                  type="monotone"
                  dataKey="unemployment"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                  name="Unemployment %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Sector Breakdown */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Sector GDP Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sectorData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name }) => name}
                >
                  {sectorData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    border: '1px solid rgba(71, 85, 105, 0.5)',
                    borderRadius: '8px',
                    color: '#fff',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confidence Metrics */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Confidence Indices</h3>
          <div className="space-y-6 mt-8">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Consumer Confidence</span>
                <span className="text-white font-medium">
                  {formatPercent(macroState?.consumer_confidence || 0)}
                </span>
              </div>
              <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-600 to-indigo-400 rounded-full transition-all duration-500"
                  style={{ width: `${(macroState?.consumer_confidence || 0) * 100}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-slate-400">Business Confidence</span>
                <span className="text-white font-medium">
                  {formatPercent(macroState?.business_confidence || 0)}
                </span>
              </div>
              <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full transition-all duration-500"
                  style={{ width: `${(macroState?.business_confidence || 0) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Agent Summary */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Agent Population</h3>
          <div className="space-y-3">
            {agentStats ? (
              <>
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Users className="w-5 h-5 text-indigo-400" />
                    <span className="text-slate-300">Consumers</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-medium">{formatNumber(agentStats.consumers?.total || 0)}</div>
                    <div className="text-xs text-slate-500">
                      {formatNumber(agentStats.consumers?.employed || 0)} employed
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Building2 className="w-5 h-5 text-emerald-400" />
                    <span className="text-slate-300">Firms</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-medium">{formatNumber(agentStats.firms?.total || 0)}</div>
                    <div className="text-xs text-slate-500">
                      {formatNumber(agentStats.firms?.profitable || 0)} profitable
                    </div>
                  </div>
                </div>
                <div className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Landmark className="w-5 h-5 text-yellow-400" />
                    <span className="text-slate-300">Banks</span>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-medium">{formatNumber(agentStats.banks?.total || 0)}</div>
                    <div className="text-xs text-slate-500">
                      {formatPercent(agentStats.banks?.average_npl || 0)} avg NPL
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-slate-500">
                <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No agent data available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
