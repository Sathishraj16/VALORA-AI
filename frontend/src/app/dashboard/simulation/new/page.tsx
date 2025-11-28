'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Play, Settings2, Zap, RefreshCw, Users, Building, Landmark, TrendingUp } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import { simulationsApi } from '@/lib/api';
import { useSimulationStore } from '@/lib/store';
import { cn } from '@/lib/utils';

interface FormState {
  name: string;
  description: string;
  total_ticks: number;
  num_consumers: number;
  num_firms: number;
  num_banks: number;
  initial_gdp: number;
  initial_inflation: number;
  initial_unemployment: number;
  enable_learning: boolean;
  enable_blockchain: boolean;
  enable_realtime: boolean;
}

export default function NewSimulationPage() {
  const router = useRouter();
  const { setCurrentSimulation, setSimulations, simulations } = useSimulationStore();
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<FormState>({
    name: 'New Simulation',
    description: '',
    total_ticks: 100,
    num_consumers: 1000,
    num_firms: 200,
    num_banks: 20,
    initial_gdp: 1000000,
    initial_inflation: 0.02,
    initial_unemployment: 0.05,
    enable_learning: true,
    enable_blockchain: true,
    enable_realtime: true,
  });

  const updateForm = (key: keyof FormState, value: any) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await simulationsApi.create(form);
      const newSimulation = response.data;
      
      setSimulations([...simulations, newSimulation]);
      setCurrentSimulation(newSimulation);
      
      toast.success('Simulation created successfully!');
      router.push('/dashboard');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create simulation');
    } finally {
      setLoading(false);
    }
  };

  const presets = [
    {
      name: 'Small Economy',
      description: 'Quick simulations for testing',
      icon: '🏘️',
      values: { num_consumers: 100, num_firms: 20, num_banks: 5, total_ticks: 50 },
    },
    {
      name: 'Medium Economy',
      description: 'Balanced simulation',
      icon: '🏙️',
      values: { num_consumers: 1000, num_firms: 200, num_banks: 20, total_ticks: 100 },
    },
    {
      name: 'Large Economy',
      description: 'Comprehensive model',
      icon: '🌆',
      values: { num_consumers: 10000, num_firms: 2000, num_banks: 100, total_ticks: 500 },
    },
    {
      name: 'Crisis Scenario',
      description: 'High unemployment',
      icon: '⚠️',
      values: { initial_unemployment: 0.12, initial_inflation: 0.08, initial_gdp: 800000 },
    },
  ];

  const applyPreset = (preset: typeof presets[0]) => {
    setForm((prev) => ({ ...prev, ...preset.values }));
    toast.success(`Applied "${preset.name}" preset`);
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Link
          href="/dashboard"
          className="p-2 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-white">Create New Simulation</h1>
          <p className="text-slate-400">Configure your economic digital twin</p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <button
              onClick={() => setStep(s)}
              className={cn(
                'w-10 h-10 rounded-full font-medium transition-all',
                step === s
                  ? 'bg-indigo-600 text-white'
                  : step > s
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                  : 'bg-slate-700/50 text-slate-400'
              )}
            >
              {s}
            </button>
            {s < 3 && (
              <div className={cn(
                'w-24 h-0.5 mx-2',
                step > s ? 'bg-emerald-500/50' : 'bg-slate-700'
              )} />
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {/* Step 1: Basic Info */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="glass-card">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-indigo-400" />
                Basic Configuration
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Simulation Name
                  </label>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => updateForm('name', e.target.value)}
                    className="input-field-dark"
                    placeholder="Enter simulation name"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={form.description}
                    onChange={(e) => updateForm('description', e.target.value)}
                    className="input-field-dark resize-none"
                    rows={3}
                    placeholder="Describe your simulation scenario..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Simulation Duration (Ticks)
                  </label>
                  <input
                    type="number"
                    value={form.total_ticks}
                    onChange={(e) => updateForm('total_ticks', parseInt(e.target.value))}
                    className="input-field-dark"
                    min={1}
                    max={10000}
                  />
                  <p className="text-xs text-slate-500 mt-1">Each tick represents one economic cycle</p>
                </div>
              </div>
            </div>

            {/* Quick Presets */}
            <div className="glass-card">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" />
                Quick Presets
              </h2>
              
              <div className="grid grid-cols-2 gap-3">
                {presets.map((preset) => (
                  <button
                    key={preset.name}
                    type="button"
                    onClick={() => applyPreset(preset)}
                    className="p-4 rounded-lg border border-slate-700 hover:border-indigo-500/50 hover:bg-slate-800/50 transition-all text-left group"
                  >
                    <div className="text-2xl mb-2">{preset.icon}</div>
                    <div className="font-medium text-white group-hover:text-indigo-400 transition-colors">{preset.name}</div>
                    <div className="text-sm text-slate-400">{preset.description}</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="btn-primary"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Agent Configuration */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="glass-card">
              <h2 className="text-lg font-semibold text-white mb-6">Agent Population</h2>
              
              <div className="space-y-6">
                <div className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg">
                  <div className="w-12 h-12 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <Users className="w-6 h-6 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-white mb-1">Consumers</label>
                    <p className="text-xs text-slate-400 mb-2">Individual economic agents that consume and work</p>
                    <input
                      type="number"
                      value={form.num_consumers}
                      onChange={(e) => updateForm('num_consumers', parseInt(e.target.value))}
                      className="input-field-dark"
                      min={10}
                      max={100000}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg">
                  <div className="w-12 h-12 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                    <Building className="w-6 h-6 text-emerald-400" />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-white mb-1">Firms</label>
                    <p className="text-xs text-slate-400 mb-2">Companies that produce goods and employ workers</p>
                    <input
                      type="number"
                      value={form.num_firms}
                      onChange={(e) => updateForm('num_firms', parseInt(e.target.value))}
                      className="input-field-dark"
                      min={5}
                      max={10000}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg">
                  <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Landmark className="w-6 h-6 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-white mb-1">Banks</label>
                    <p className="text-xs text-slate-400 mb-2">Financial institutions that manage credit and deposits</p>
                    <input
                      type="number"
                      value={form.num_banks}
                      onChange={(e) => updateForm('num_banks', parseInt(e.target.value))}
                      className="input-field-dark"
                      min={1}
                      max={100}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-card">
              <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                Initial Economic Conditions
              </h2>
              
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Initial GDP</label>
                  <input
                    type="number"
                    value={form.initial_gdp}
                    onChange={(e) => updateForm('initial_gdp', parseFloat(e.target.value))}
                    className="input-field-dark"
                    min={100000}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Inflation Rate</label>
                  <div className="relative">
                    <input
                      type="number"
                      value={(form.initial_inflation * 100).toFixed(1)}
                      onChange={(e) => updateForm('initial_inflation', parseFloat(e.target.value) / 100)}
                      className="input-field-dark pr-8"
                      step="0.1"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">%</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Unemployment Rate</label>
                  <div className="relative">
                    <input
                      type="number"
                      value={(form.initial_unemployment * 100).toFixed(1)}
                      onChange={(e) => updateForm('initial_unemployment', parseFloat(e.target.value) / 100)}
                      className="input-field-dark pr-8"
                      step="0.1"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <button type="button" onClick={() => setStep(1)} className="btn-secondary">
                Back
              </button>
              <button type="button" onClick={() => setStep(3)} className="btn-primary">
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Features */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="glass-card">
              <h2 className="text-lg font-semibold text-white mb-6">Advanced Features</h2>
              
              <div className="space-y-4">
                <label className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                      <span className="text-xl">🧠</span>
                    </div>
                    <div>
                      <div className="font-medium text-white">Agent Learning (RL)</div>
                      <div className="text-sm text-slate-400">
                        Agents use reinforcement learning to optimize behavior
                      </div>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={form.enable_learning}
                    onChange={(e) => updateForm('enable_learning', e.target.checked)}
                    className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-indigo-500 focus:ring-indigo-500"
                  />
                </label>
                
                <label className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                      <span className="text-xl">⛓️</span>
                    </div>
                    <div>
                      <div className="font-medium text-white">Blockchain Ledger</div>
                      <div className="text-sm text-slate-400">
                        Immutable Merkle tree for all economic transactions
                      </div>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={form.enable_blockchain}
                    onChange={(e) => updateForm('enable_blockchain', e.target.checked)}
                    className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-indigo-500 focus:ring-indigo-500"
                  />
                </label>
                
                <label className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors cursor-pointer">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                      <span className="text-xl">📡</span>
                    </div>
                    <div>
                      <div className="font-medium text-white">Real-time Streaming</div>
                      <div className="text-sm text-slate-400">
                        WebSocket streaming for live simulation updates
                      </div>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={form.enable_realtime}
                    onChange={(e) => updateForm('enable_realtime', e.target.checked)}
                    className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-indigo-500 focus:ring-indigo-500"
                  />
                </label>
              </div>
            </div>

            {/* Summary */}
            <div className="glass-card">
              <h2 className="text-lg font-semibold text-white mb-4">Summary</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-slate-400">Name</div>
                  <div className="text-white font-medium">{form.name}</div>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-slate-400">Duration</div>
                  <div className="text-white font-medium">{form.total_ticks} ticks</div>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-slate-400">Total Agents</div>
                  <div className="text-white font-medium">{(form.num_consumers + form.num_firms + form.num_banks).toLocaleString()}</div>
                </div>
                <div className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-slate-400">Initial GDP</div>
                  <div className="text-white font-medium">${form.initial_gdp.toLocaleString()}</div>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <button type="button" onClick={() => setStep(2)} className="btn-secondary">
                Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-accent flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Create Simulation
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}
