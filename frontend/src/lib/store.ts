import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Auth Store
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, tokens: Tokens) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  setLoading: (loading: boolean) => void;
}

interface User {
  id: string;
  email: string;
  name: string;
  organization?: string;
  created_at: string;
}

interface Tokens {
  access_token: string;
  refresh_token: string;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
      login: (user, tokens) => {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        set({ user, token: tokens.access_token, isAuthenticated: true, isLoading: false });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, token: null, isAuthenticated: false, isLoading: false });
      },
      setUser: (user) => set({ user, isAuthenticated: true }),
      setToken: (token) => set({ token }),
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

// Simulation Store
interface SimulationState {
  currentSimulation: Simulation | null;
  simulations: Simulation[];
  macroState: MacroState | null;
  history: HistoryEntry[];
  isRunning: boolean;
  setCurrentSimulation: (simulation: Simulation | null) => void;
  setSimulations: (simulations: Simulation[]) => void;
  setMacroState: (state: MacroState) => void;
  addHistoryEntry: (entry: HistoryEntry) => void;
  setHistory: (history: HistoryEntry[]) => void;
  setIsRunning: (running: boolean) => void;
  clearSimulation: () => void;
}

export interface Simulation {
  simulation_id: string;
  name: string;
  status: string;
  current_tick: number;
  total_ticks: number;
  created_at?: string;
  macro_state?: MacroState;
}

export interface MacroState {
  tick: number;
  gdp: number;
  gdp_growth: number;
  inflation: number;
  unemployment: number;
  interest_rate: number;
  consumer_confidence: number;
  business_confidence: number;
  debt_to_gdp: number;
  cycle_phase: string;
  sector_gdp: Record<string, number>;
}

export interface HistoryEntry {
  tick: number;
  macro_state: MacroState;
  timestamp?: string;
}

export const useSimulationStore = create<SimulationState>()((set) => ({
  currentSimulation: null,
  simulations: [],
  macroState: null,
  history: [],
  isRunning: false,
  setCurrentSimulation: (simulation) => set({ currentSimulation: simulation }),
  setSimulations: (simulations) => set({ simulations }),
  setMacroState: (macroState) => set({ macroState }),
  addHistoryEntry: (entry) =>
    set((state) => ({ history: [...state.history, entry].slice(-500) })),
  setHistory: (history) => set({ history }),
  setIsRunning: (isRunning) => set({ isRunning }),
  clearSimulation: () =>
    set({ currentSimulation: null, macroState: null, history: [], isRunning: false }),
}));

// UI Store
interface UIState {
  sidebarCollapsed: boolean;
  activePanel: string;
  selectedAgent: string | null;
  selectedBlock: number | null;
  toggleSidebar: () => void;
  setActivePanel: (panel: string) => void;
  setSelectedAgent: (agentId: string | null) => void;
  setSelectedBlock: (blockIndex: number | null) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarCollapsed: false,
  activePanel: 'overview',
  selectedAgent: null,
  selectedBlock: null,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setActivePanel: (panel) => set({ activePanel: panel }),
  setSelectedAgent: (agentId) => set({ selectedAgent: agentId }),
  setSelectedBlock: (blockIndex) => set({ selectedBlock: blockIndex }),
}));

// Policy Store
interface PolicyState {
  recommendations: PolicyRecommendation[];
  selectedScenario: PolicyScenario | null;
  comparisonResults: ComparisonResult | null;
  addRecommendation: (rec: PolicyRecommendation) => void;
  setSelectedScenario: (scenario: PolicyScenario | null) => void;
  setComparisonResults: (results: ComparisonResult | null) => void;
  clearPolicies: () => void;
}

export interface PolicyRecommendation {
  recommendation_id: string;
  timestamp: string;
  policy_tools: PolicyTool[];
  expected_outcomes: Record<string, number>;
  risk_assessment: Record<string, any>;
  confidence_score: number;
  reasoning: string;
}

export interface PolicyTool {
  name: string;
  value: number;
  tool_type: string;
}

export interface PolicyScenario {
  name: string;
  description?: string;
  interest_rate_change?: number;
  reserve_requirement_change?: number;
  qe_amount?: number;
  tax_change?: number;
  spending_change?: number;
}

export interface ComparisonResult {
  scenarios: ScenarioResult[];
  best_scenario: string;
  reasoning: string;
}

export interface ScenarioResult {
  name: string;
  outcomes: Record<string, number>;
  risk_scores: Record<string, number>;
  overall_score: number;
}

export const usePolicyStore = create<PolicyState>()((set) => ({
  recommendations: [],
  selectedScenario: null,
  comparisonResults: null,
  addRecommendation: (rec) =>
    set((state) => ({ recommendations: [rec, ...state.recommendations].slice(0, 50) })),
  setSelectedScenario: (scenario) => set({ selectedScenario: scenario }),
  setComparisonResults: (results) => set({ comparisonResults: results }),
  clearPolicies: () =>
    set({ recommendations: [], selectedScenario: null, comparisonResults: null }),
}));

// Chat Store
interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  conversationId: string | null;
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  setConversationId: (id: string) => void;
  clearChat: () => void;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  isLoading: false,
  conversationId: null,
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setLoading: (isLoading) => set({ isLoading }),
  setConversationId: (conversationId) => set({ conversationId }),
  clearChat: () => set({ messages: [], conversationId: null }),
}));
