'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  Activity,
  LayoutDashboard,
  Play,
  Pause,
  Settings,
  ChevronRight,
  Plus,
  BarChart3,
  Users,
  Scale,
  Blocks,
  MessageSquare,
  Zap,
  Menu,
  X,
  Home,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSimulationStore, useUIStore } from '@/lib/store';
import { simulationsApi } from '@/lib/api';
import { useWebSocket } from '@/lib/websocket';
import { toast } from 'sonner';

const navItems = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard, href: '/dashboard' },
  { id: 'simulation', label: 'Simulation', icon: Activity, href: '/dashboard/simulation/new' },
  { id: 'agents', label: 'Agents', icon: Users, href: '/dashboard/agents' },
  { id: 'policy', label: 'Policy Lab', icon: Scale, href: '/dashboard/policy' },
  { id: 'blockchain', label: 'Blockchain', icon: Blocks, href: '/dashboard/blockchain' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, href: '/dashboard/analytics' },
  { id: 'crew', label: 'AI Assistant', icon: MessageSquare, href: '/dashboard/crew' },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { currentSimulation, simulations, setSimulations, setCurrentSimulation, isRunning, setIsRunning } = useSimulationStore();
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Determine active panel based on pathname
  const getActivePanel = () => {
    if (pathname === '/dashboard') return 'overview';
    const segment = pathname.split('/')[2];
    return segment || 'overview';
  };

  // WebSocket connection
  useWebSocket(currentSimulation?.simulation_id || null);

  // Fetch simulations on mount
  useEffect(() => {
    const fetchSimulations = async () => {
      try {
        const response = await simulationsApi.list();
        setSimulations(response.data);
        if (response.data.length > 0 && !currentSimulation) {
          setCurrentSimulation(response.data[0]);
        }
      } catch (error) {
        console.error('Failed to fetch simulations:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchSimulations();
  }, [setSimulations, setCurrentSimulation, currentSimulation]);

  const handleStartSimulation = async () => {
    if (!currentSimulation) return;
    try {
      await simulationsApi.start(currentSimulation.simulation_id);
      setIsRunning(true);
      toast.success('Simulation started');
    } catch (error) {
      toast.error('Failed to start simulation');
    }
  };

  const handlePauseSimulation = async () => {
    if (!currentSimulation) return;
    try {
      await simulationsApi.pause(currentSimulation.simulation_id);
      setIsRunning(false);
      toast.success('Simulation paused');
    } catch (error) {
      toast.error('Failed to pause simulation');
    }
  };

  const handleStepSimulation = async () => {
    if (!currentSimulation) return;
    try {
      await simulationsApi.step(currentSimulation.simulation_id, 1);
      toast.success('Simulation stepped');
    } catch (error) {
      toast.error('Failed to step simulation');
    }
  };

  const activePanel = getActivePanel();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar - Light Theme */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-white border-r border-gray-200 transition-all duration-300 shadow-sm',
          sidebarCollapsed ? 'w-16' : 'w-56',
          'hidden md:flex'
        )}
      >
        {/* Logo */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-gray-200">
          <Link href="/" className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-gray-900" />
            {!sidebarCollapsed && (
              <span className="text-base font-semibold text-gray-900">VALORA</span>
            )}
          </Link>
          <button
            onClick={toggleSidebar}
            className="p-1 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
          >
            <ChevronRight
              className={cn('w-4 h-4 transition-transform', sidebarCollapsed && 'rotate-180')}
            />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-all text-sm font-medium',
                activePanel === item.id && 'text-gray-900 bg-gray-100'
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {!sidebarCollapsed && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        {/* Simulation Selector */}
        {!sidebarCollapsed && (
          <div className="p-3 border-t border-gray-200">
            <label className="text-xs text-gray-500 uppercase tracking-wider mb-1.5 block font-medium">
              Active Simulation
            </label>
            <select
              value={currentSimulation?.simulation_id || ''}
              onChange={(e) => {
                const sim = simulations.find((s) => s.simulation_id === e.target.value);
                if (sim) setCurrentSimulation(sim);
              }}
              className="w-full bg-white border border-gray-300 rounded-md px-2.5 py-1.5 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
            >
              <option value="">Select simulation...</option>
              {simulations.map((sim) => (
                <option key={sim.simulation_id} value={sim.simulation_id}>
                  {sim.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Back to Home */}
        <div className="p-2 border-t border-gray-200">
          <Link
            href="/"
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-all text-sm font-medium',
            )}
          >
            <Home className="w-4 h-4 flex-shrink-0" />
            {!sidebarCollapsed && <span>Back to Home</span>}
          </Link>
        </div>
      </aside>

      {/* Mobile Menu */}
      <div
        className={cn(
          'fixed inset-0 z-50 bg-black/20 backdrop-blur-sm md:hidden transition-opacity',
          mobileMenuOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={() => setMobileMenuOpen(false)}
      >
        <div
          className={cn(
            'w-64 h-full bg-white border-r border-gray-200 transition-transform shadow-lg',
            mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
          )}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="h-14 flex items-center justify-between px-4 border-b border-gray-200">
            <Link href="/" className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-gray-900" />
              <span className="text-base font-semibold text-gray-900">VALORA</span>
            </Link>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-1 rounded hover:bg-gray-100 text-gray-500"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <nav className="py-3 px-2 space-y-0.5">
            {navItems.map((item) => (
              <Link
                key={item.id}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-all text-sm font-medium',
                  activePanel === item.id && 'text-gray-900 bg-gray-100'
                )}
              >
                <item.icon className="w-4 h-4" />
                <span>{item.label}</span>
              </Link>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main
        className={cn(
          'flex-1 min-h-screen transition-all duration-300',
          sidebarCollapsed ? 'md:ml-16' : 'md:ml-56'
        )}
      >
        {/* Top Bar - Light Theme */}
        <header className="h-14 border-b border-gray-200 bg-white sticky top-0 z-40 flex items-center justify-between px-4 md:px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 rounded hover:bg-gray-100 text-gray-500 md:hidden"
            >
              <Menu className="w-5 h-5" />
            </button>
            
            <div>
              <h1 className="text-sm font-medium text-gray-900">
                {currentSimulation?.name || 'No Simulation Selected'}
              </h1>
              {currentSimulation && (
                <div className="flex items-center gap-2 text-xs">
                  <span className={cn(
                    'px-1.5 py-0.5 rounded text-xs font-medium',
                    currentSimulation.status === 'running' ? 'bg-green-100 text-green-700' :
                    currentSimulation.status === 'paused' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-600'
                  )}>
                    {currentSimulation.status || 'idle'}
                  </span>
                  <span className="text-gray-500">
                    Tick {currentSimulation.current_tick || 0} / {currentSimulation.total_ticks || 0}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-1">
            {/* Simulation Controls */}
            {currentSimulation && (
              <>
                <button
                  onClick={handleStepSimulation}
                  className="p-2 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
                  title="Step simulation"
                >
                  <Zap className="w-4 h-4" />
                </button>
                
                {isRunning ? (
                  <button
                    onClick={handlePauseSimulation}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-yellow-100 hover:bg-yellow-200 text-yellow-700 rounded-md transition-colors text-sm font-medium"
                  >
                    <Pause className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Pause</span>
                  </button>
                ) : (
                  <button
                    onClick={handleStartSimulation}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-green-100 hover:bg-green-200 text-green-700 rounded-md transition-colors text-sm font-medium"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Start</span>
                  </button>
                )}
              </>
            )}

            <Link
              href="/dashboard/simulation/new"
              className="p-2 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
              title="New simulation"
            >
              <Plus className="w-4 h-4" />
            </Link>
            
            <Link
              href="/dashboard/settings"
              className="p-2 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <Settings className="w-4 h-4" />
            </Link>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-4 md:p-6">{children}</div>
      </main>
    </div>
  );
}
