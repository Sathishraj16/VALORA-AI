import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api/v1';

export const api = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}${API_PREFIX}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Simulations API
export const simulationsApi = {
  list: () => api.get('/simulations'),
  get: (id: string) => api.get(`/simulations/${id}`),
  create: (data: CreateSimulationRequest) => api.post('/simulations', data),
  start: (id: string, steps?: number) => api.post(`/simulations/${id}/start`, null, { params: { steps } }),
  step: (id: string, steps?: number) => api.post(`/simulations/${id}/step`, null, { params: { steps } }),
  pause: (id: string) => api.post(`/simulations/${id}/pause`),
  stop: (id: string) => api.post(`/simulations/${id}/stop`),
  delete: (id: string) => api.delete(`/simulations/${id}`),
  getState: (id: string) => api.get(`/simulations/${id}/state`),
  getHistory: (id: string, params?: { start_tick?: number; limit?: number }) => 
    api.get(`/simulations/${id}/history`, { params }),
  applyShock: (id: string, shock: ShockRequest) => api.post(`/simulations/${id}/shock`, shock),
  getForecast: (id: string, horizon?: number) => 
    api.get(`/simulations/${id}/forecast`, { params: { horizon } }),
  getAgents: (id: string) => api.get(`/simulations/${id}/agents`),
};

// Policy API
export const policyApi = {
  analyze: (data: PolicyAnalysisRequest) => api.post('/policy/analyze', data),
  compare: (data: PolicyComparisonRequest) => api.post('/policy/compare', data),
  simulateImpact: (simulationId: string, scenario: PolicyScenario, horizon?: number) =>
    api.post('/policy/simulate-impact', scenario, { params: { simulation_id: simulationId, horizon } }),
  getDebate: (simulationId: string) => api.get(`/policy/debate/${simulationId}`),
  getTools: () => api.get('/policy/tools'),
  getHistory: (simulationId: string, limit?: number) => 
    api.get(`/policy/history/${simulationId}`, { params: { limit } }),
  optimize: (data: PolicyAnalysisRequest) => api.post('/policy/optimize', data),
};

// Blockchain API
export const blockchainApi = {
  getBlocks: (simulationId: string, params?: { start?: number; limit?: number }) =>
    api.get(`/blockchain/${simulationId}/blocks`, { params }),
  getBlock: (simulationId: string, blockIndex: number) =>
    api.get(`/blockchain/${simulationId}/blocks/${blockIndex}`),
  getStats: (simulationId: string) => api.get(`/blockchain/${simulationId}/stats`),
  verify: (simulationId: string) => api.get(`/blockchain/${simulationId}/verify`),
  searchEvents: (simulationId: string, params?: EventSearchParams) =>
    api.get(`/blockchain/${simulationId}/events`, { params }),
  getActorHistory: (simulationId: string, actorId: string) =>
    api.get(`/blockchain/${simulationId}/actor/${actorId}`),
  getEvent: (simulationId: string, eventId: string) =>
    api.get(`/blockchain/${simulationId}/event/${eventId}`),
  export: (simulationId: string, format?: string) =>
    api.get(`/blockchain/${simulationId}/export`, { params: { format } }),
  getMerkle: (simulationId: string, blockIndex: number) =>
    api.get(`/blockchain/${simulationId}/merkle/${blockIndex}`),
};

// Agents API
export const agentsApi = {
  getConsumers: (simulationId: string) => api.get(`/agents/${simulationId}/consumers`),
  listConsumers: (simulationId: string, params?: { income_class?: string; employed_only?: boolean; limit?: number }) =>
    api.get(`/agents/${simulationId}/consumers/list`, { params }),
  getFirms: (simulationId: string) => api.get(`/agents/${simulationId}/firms`),
  listFirms: (simulationId: string, params?: { sector?: string; profitable_only?: boolean; limit?: number }) =>
    api.get(`/agents/${simulationId}/firms/list`, { params }),
  getBanks: (simulationId: string) => api.get(`/agents/${simulationId}/banks`),
  listBanks: (simulationId: string, params?: { limit?: number }) =>
    api.get(`/agents/${simulationId}/banks/list`, { params }),
  getRegulator: (simulationId: string) => api.get(`/agents/${simulationId}/regulator`),
  getAgent: (simulationId: string, agentId: string) =>
    api.get(`/agents/${simulationId}/agent/${agentId}`),
  getAgentHistory: (simulationId: string, agentId: string, limit?: number) =>
    api.get(`/agents/${simulationId}/agent/${agentId}/history`, { params: { limit } }),
  getSectors: (simulationId: string) => api.get(`/agents/${simulationId}/sectors`),
};

// CrewAI API
export const crewApi = {
  analyze: (data: AnalysisRequest) => api.post('/crew/analyze', data),
  getResult: (taskId: string) => api.get(`/crew/analyze/${taskId}`),
  analyzeSync: (data: AnalysisRequest) => api.post('/crew/analyze-sync', data),
  policyBrief: (data: PolicyBriefRequest) => api.post('/crew/policy-brief', data),
  debate: (data: DebateRequest) => api.post('/crew/debate', data),
  getAgents: () => api.get('/crew/agents'),
  getTasks: (params?: { status?: string; limit?: number }) =>
    api.get('/crew/tasks', { params }),
  chat: (simulationId: string, message: string, conversationId?: string) =>
    api.post('/crew/chat', null, { params: { simulation_id: simulationId, message, conversation_id: conversationId } }),
  explain: (simulationId: string, aspect?: string) =>
    api.post(`/crew/explain/${simulationId}`, null, { params: { aspect } }),
};

// Auth API
export const authApi = {
  register: (data: RegisterRequest) => api.post('/auth/register', data),
  login: (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return axios.post(`${API_URL}${API_PREFIX}/auth/token`, formData);
  },
  refresh: (refreshToken: string) => 
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
  updateMe: (data: { name?: string; organization?: string }) =>
    api.put('/auth/me', data),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/auth/change-password', { current_password: currentPassword, new_password: newPassword }),
  createApiKey: (data: { name: string; expires_in_days?: number }) =>
    api.post('/auth/api-keys', data),
  listApiKeys: () => api.get('/auth/api-keys'),
  deleteApiKey: (keyId: string) => api.delete(`/auth/api-keys/${keyId}`),
};

// Types
export interface CreateSimulationRequest {
  name: string;
  description?: string;
  total_ticks?: number;
  num_consumers?: number;
  num_firms?: number;
  num_banks?: number;
  initial_gdp?: number;
  initial_inflation?: number;
  initial_unemployment?: number;
  enable_learning?: boolean;
  enable_blockchain?: boolean;
  enable_realtime?: boolean;
}

export interface ShockRequest {
  shock_type: 'supply' | 'demand' | 'financial' | 'external';
  name: string;
  magnitude: number;
  affected_sectors?: string[];
  duration?: number;
}

export interface PolicyAnalysisRequest {
  simulation_id: string;
  target_inflation?: number;
  target_unemployment?: number;
  target_gdp_growth?: number;
  constraints?: Record<string, any>;
}

export interface PolicyComparisonRequest {
  simulation_id: string;
  scenarios: PolicyScenario[];
  horizon?: number;
}

export interface PolicyScenario {
  name: string;
  description?: string;
  interest_rate_change?: number;
  reserve_requirement_change?: number;
  qe_amount?: number;
  tax_change?: number;
  spending_change?: number;
  target_sector?: string;
  timeline_months?: number;
}

export interface EventSearchParams {
  event_type?: string;
  actor_id?: string;
  actor_type?: string;
  min_amount?: number;
  max_amount?: number;
  start_time?: string;
  end_time?: string;
  limit?: number;
}

export interface AnalysisRequest {
  simulation_id: string;
  analysis_type: 'economic' | 'policy' | 'forecast' | 'report';
  context?: string;
  parameters?: Record<string, any>;
}

export interface PolicyBriefRequest {
  simulation_id: string;
  topic: string;
  target_audience?: string;
  include_recommendations?: boolean;
}

export interface DebateRequest {
  simulation_id: string;
  policy_question: string;
  perspectives?: string[];
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  organization?: string;
}
