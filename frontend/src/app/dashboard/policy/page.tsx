'use client';

import { useState, useEffect } from 'react';
import {
  Scale,
  Play,
  BarChart2,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Lightbulb,
  RefreshCw,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import { toast } from 'sonner';
import { cn, formatPercent, getRiskColor } from '@/lib/utils';
import { useSimulationStore, usePolicyStore } from '@/lib/store';
import { policyApi, type PolicyScenario } from '@/lib/api';

export default function PolicyLabPage() {
  const { currentSimulation, macroState } = useSimulationStore();
  const { recommendations, comparisonResults, addRecommendation, setComparisonResults } = usePolicyStore();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'recommend' | 'compare' | 'simulate'>('recommend');

  // Recommendation form
  const [targets, setTargets] = useState({
    inflation: 0.02,
    unemployment: 0.04,
    gdp_growth: 0.03,
  });

  // Scenario comparison
  const [scenarios, setScenarios] = useState<PolicyScenario[]>([
    { name: 'Scenario A', interest_rate_change: -0.01 },
    { name: 'Scenario B', spending_change: 0.1 },
  ]);

  // Impact simulation
  const [simulationScenario, setSimulationScenario] = useState<PolicyScenario>({
    name: 'Custom Policy',
    interest_rate_change: 0,
    spending_change: 0,
    tax_change: 0,
  });
  const [impactForecast, setImpactForecast] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!currentSimulation) {
      toast.error('No simulation selected');
      return;
    }

    setLoading(true);
    try {
      const response = await policyApi.analyze({
        simulation_id: currentSimulation.simulation_id,
        target_inflation: targets.inflation,
        target_unemployment: targets.unemployment,
        target_gdp_growth: targets.gdp_growth,
      });
      addRecommendation(response.data);
      toast.success('Policy analysis complete');
    } catch (error) {
      toast.error('Failed to analyze policy');
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!currentSimulation) {
      toast.error('No simulation selected');
      return;
    }

    setLoading(true);
    try {
      const response = await policyApi.compare({
        simulation_id: currentSimulation.simulation_id,
        scenarios,
        horizon: 20,
      });
      setComparisonResults(response.data.comparison);
      toast.success('Scenarios compared');
    } catch (error) {
      toast.error('Failed to compare scenarios');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateImpact = async () => {
    if (!currentSimulation) {
      toast.error('No simulation selected');
      return;
    }

    setLoading(true);
    try {
      const response = await policyApi.simulateImpact(
        currentSimulation.simulation_id,
        simulationScenario,
        30
      );
      setImpactForecast(response.data);
      toast.success('Impact simulation complete');
    } catch (error) {
      toast.error('Failed to simulate impact');
    } finally {
      setLoading(false);
    }
  };

  if (!currentSimulation) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <Scale className="w-12 h-12 text-dark-500 mb-4" />
        <h2 className="text-xl font-semibold text-white mb-2">No Simulation Selected</h2>
        <p className="text-dark-400">Create or select a simulation to access Policy Lab.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Scale className="w-6 h-6 text-primary-400" />
            Policy Lab
          </h1>
          <p className="text-dark-400">Analyze, compare, and simulate economic policies</p>
        </div>
      </div>

      {/* Current State Summary */}
      <div className="glass-card grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <div className="text-sm text-dark-400">Current Inflation</div>
          <div className="text-xl font-bold text-white">
            {formatPercent(macroState?.inflation || 0)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-dark-400">Current Unemployment</div>
          <div className="text-xl font-bold text-white">
            {formatPercent(macroState?.unemployment || 0)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-dark-400">GDP Growth</div>
          <div className="text-xl font-bold text-white">
            {formatPercent(macroState?.gdp_growth || 0)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-dark-400">Interest Rate</div>
          <div className="text-xl font-bold text-white">
            {formatPercent(macroState?.interest_rate || 0)}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-700">
        {(['recommend', 'compare', 'simulate'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              'px-4 py-2 font-medium transition-colors capitalize',
              activeTab === tab
                ? 'text-primary-400 border-b-2 border-primary-400'
                : 'text-dark-400 hover:text-white'
            )}
          >
            {tab === 'recommend' ? 'AI Recommendations' : tab === 'compare' ? 'Scenario Comparison' : 'Impact Simulation'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left Panel - Input */}
        <div className="space-y-6">
          {activeTab === 'recommend' && (
            <div className="glass-card">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-accent-400" />
                Target Outcomes
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-dark-400 mb-2">Target Inflation</label>
                  <div className="relative">
                    <input
                      type="number"
                      value={(targets.inflation * 100).toFixed(1)}
                      onChange={(e) =>
                        setTargets({ ...targets, inflation: parseFloat(e.target.value) / 100 })
                      }
                      className="input-field pr-8"
                      step="0.1"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400">%</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-dark-400 mb-2">Target Unemployment</label>
                  <div className="relative">
                    <input
                      type="number"
                      value={(targets.unemployment * 100).toFixed(1)}
                      onChange={(e) =>
                        setTargets({ ...targets, unemployment: parseFloat(e.target.value) / 100 })
                      }
                      className="input-field pr-8"
                      step="0.1"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400">%</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-dark-400 mb-2">Target GDP Growth</label>
                  <div className="relative">
                    <input
                      type="number"
                      value={(targets.gdp_growth * 100).toFixed(1)}
                      onChange={(e) =>
                        setTargets({ ...targets, gdp_growth: parseFloat(e.target.value) / 100 })
                      }
                      className="input-field pr-8"
                      step="0.1"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400">%</span>
                  </div>
                </div>
                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Analyze & Recommend
                </button>
              </div>
            </div>
          )}

          {activeTab === 'compare' && (
            <div className="glass-card">
              <h3 className="text-lg font-semibold text-white mb-4">Define Scenarios</h3>
              <div className="space-y-4">
                {scenarios.map((scenario, idx) => (
                  <div key={idx} className="p-4 bg-dark-800/50 rounded-lg space-y-3">
                    <input
                      type="text"
                      value={scenario.name}
                      onChange={(e) => {
                        const updated = [...scenarios];
                        updated[idx].name = e.target.value;
                        setScenarios(updated);
                      }}
                      className="input-field text-sm"
                      placeholder="Scenario name"
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-xs text-dark-400">Interest Rate Δ</label>
                        <input
                          type="number"
                          value={((scenario.interest_rate_change || 0) * 100).toFixed(1)}
                          onChange={(e) => {
                            const updated = [...scenarios];
                            updated[idx].interest_rate_change = parseFloat(e.target.value) / 100;
                            setScenarios(updated);
                          }}
                          className="input-field text-sm"
                          step="0.1"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-dark-400">Spending Δ</label>
                        <input
                          type="number"
                          value={((scenario.spending_change || 0) * 100).toFixed(1)}
                          onChange={(e) => {
                            const updated = [...scenarios];
                            updated[idx].spending_change = parseFloat(e.target.value) / 100;
                            setScenarios(updated);
                          }}
                          className="input-field text-sm"
                          step="1"
                        />
                      </div>
                    </div>
                  </div>
                ))}
                <button
                  onClick={() =>
                    setScenarios([...scenarios, { name: `Scenario ${String.fromCharCode(65 + scenarios.length)}` }])
                  }
                  className="btn-secondary w-full"
                >
                  Add Scenario
                </button>
                <button
                  onClick={handleCompare}
                  disabled={loading || scenarios.length < 2}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <BarChart2 className="w-4 h-4" />}
                  Compare Scenarios
                </button>
              </div>
            </div>
          )}

          {activeTab === 'simulate' && (
            <div className="glass-card">
              <h3 className="text-lg font-semibold text-white mb-4">Policy Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-dark-400 mb-2">Interest Rate Change</label>
                  <input
                    type="range"
                    min="-5"
                    max="5"
                    step="0.25"
                    value={(simulationScenario.interest_rate_change || 0) * 100}
                    onChange={(e) =>
                      setSimulationScenario({
                        ...simulationScenario,
                        interest_rate_change: parseFloat(e.target.value) / 100,
                      })
                    }
                    className="w-full"
                  />
                  <div className="text-center text-sm text-white">
                    {((simulationScenario.interest_rate_change || 0) * 100).toFixed(2)}%
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-dark-400 mb-2">Government Spending Change</label>
                  <input
                    type="range"
                    min="-30"
                    max="30"
                    step="1"
                    value={(simulationScenario.spending_change || 0) * 100}
                    onChange={(e) =>
                      setSimulationScenario({
                        ...simulationScenario,
                        spending_change: parseFloat(e.target.value) / 100,
                      })
                    }
                    className="w-full"
                  />
                  <div className="text-center text-sm text-white">
                    {((simulationScenario.spending_change || 0) * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-dark-400 mb-2">Tax Rate Change</label>
                  <input
                    type="range"
                    min="-20"
                    max="20"
                    step="0.5"
                    value={(simulationScenario.tax_change || 0) * 100}
                    onChange={(e) =>
                      setSimulationScenario({
                        ...simulationScenario,
                        tax_change: parseFloat(e.target.value) / 100,
                      })
                    }
                    className="w-full"
                  />
                  <div className="text-center text-sm text-white">
                    {((simulationScenario.tax_change || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <button
                  onClick={handleSimulateImpact}
                  disabled={loading}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  Simulate Impact
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Results */}
        <div className="space-y-6">
          {activeTab === 'recommend' && recommendations.length > 0 && (
            <div className="glass-card">
              <h3 className="text-lg font-semibold text-white mb-4">Latest Recommendation</h3>
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-dark-400">Confidence:</span>
                  <span className={cn('font-medium', recommendations[0].confidence_score > 0.7 ? 'text-accent-400' : 'text-yellow-400')}>
                    {formatPercent(recommendations[0].confidence_score)}
                  </span>
                </div>
                <div className="space-y-2">
                  <span className="text-sm text-dark-400">Recommended Actions:</span>
                  {recommendations[0].policy_tools.map((tool, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 bg-dark-800/50 rounded">
                      <span className="text-white capitalize">{tool.name.replace(/_/g, ' ')}</span>
                      <span className="font-mono text-accent-400">
                        {formatPercent(tool.value)}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="p-3 bg-dark-800/50 rounded-lg">
                  <p className="text-sm text-dark-300">{recommendations[0].reasoning}</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'compare' && comparisonResults && (
            <div className="glass-card">
              <h3 className="text-lg font-semibold text-white mb-4">Comparison Results</h3>
              <div className="space-y-4">
                {comparisonResults.scenarios?.map((result: any, idx: number) => (
                  <div
                    key={idx}
                    className={cn(
                      'p-4 rounded-lg border',
                      result.name === comparisonResults.best_scenario
                        ? 'border-accent-500/50 bg-accent-600/10'
                        : 'border-dark-700 bg-dark-800/50'
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">{result.name}</span>
                      {result.name === comparisonResults.best_scenario && (
                        <span className="badge-success">Recommended</span>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      {Object.entries(result.outcomes || {}).map(([key, value]: [string, any]) => (
                        <div key={key}>
                          <div className="text-dark-400 capitalize">{key}</div>
                          <div className="text-white">{formatPercent(value)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'simulate' && impactForecast && (
            <div className="glass-card">
              <h3 className="text-lg font-semibold text-white mb-4">Impact Forecast</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-dark-800/50 rounded-lg">
                    <div className="text-sm text-dark-400">GDP Impact</div>
                    <div className={cn('text-xl font-bold', impactForecast.impact_metrics?.gdp_change > 0 ? 'text-accent-400' : 'text-red-400')}>
                      {impactForecast.impact_metrics?.gdp_change > 0 ? '+' : ''}
                      {impactForecast.impact_metrics?.gdp_change?.toFixed(2)}%
                    </div>
                  </div>
                  <div className="text-center p-3 bg-dark-800/50 rounded-lg">
                    <div className="text-sm text-dark-400">Inflation Δ</div>
                    <div className="text-xl font-bold text-white">
                      {impactForecast.impact_metrics?.inflation_change > 0 ? '+' : ''}
                      {impactForecast.impact_metrics?.inflation_change?.toFixed(2)}%
                    </div>
                  </div>
                  <div className="text-center p-3 bg-dark-800/50 rounded-lg">
                    <div className="text-sm text-dark-400">Unemployment Δ</div>
                    <div className={cn('text-xl font-bold', impactForecast.impact_metrics?.unemployment_change < 0 ? 'text-accent-400' : 'text-red-400')}>
                      {impactForecast.impact_metrics?.unemployment_change > 0 ? '+' : ''}
                      {impactForecast.impact_metrics?.unemployment_change?.toFixed(2)}%
                    </div>
                  </div>
                </div>
                
                {/* Forecast Chart */}
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={impactForecast.forecast || []}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="tick" stroke="#64748b" />
                      <YAxis stroke="#64748b" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'rgba(30, 41, 59, 0.95)',
                          border: '1px solid rgba(71, 85, 105, 0.5)',
                          borderRadius: '8px',
                        }}
                      />
                      <Line type="monotone" dataKey="gdp" stroke="#6366f1" name="GDP" dot={false} />
                      <Line type="monotone" dataKey="inflation" stroke="#f59e0b" name="Inflation" dot={false} />
                      <Line type="monotone" dataKey="unemployment" stroke="#ef4444" name="Unemployment" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
