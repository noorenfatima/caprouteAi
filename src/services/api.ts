export const API_BASE_URL = ((import.meta as any).env?.VITE_API_BASE_URL as string | undefined) || 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export type RouteRequest = {
  amount: number;
  source_country: string;
  destination_country: string;
  purpose: string;
  business_size: string;
  priority: string;
  currency_handling: string;
};

export type RouteSummary = {
  label?: string;
  path: string[];
  path_display: string;
  total_cost_usd: number;
  total_time_hrs: number;
  compliance_score: number;
  breakdown: Record<string, unknown>;
};

export type OptimizeResponse = {
  request: RouteRequest;
  recommended_route: RouteSummary;
  direct_route: { path: string[]; path_display: string };
  comparisons: { best: RouteSummary; fastest: RouteSummary; safest: RouteSummary };
  fx_risk?: FXRiskResponse;
  map_url?: string | null;
};

export type CompareResponse = {
  routes: RouteSummary[];
};

export type SimulationRequest = RouteRequest & {
  adjust_tax_pct?: number;
  adjust_fx_pct?: number;
};

export type SimulationResponse = {
  scenario: SimulationRequest;
  route: RouteSummary;
  simulation: {
    adjusted_tax: number;
    adjusted_fx_loss: number;
    compliance_cost: number;
    total_cost_usd: number;
    estimated_time_hrs: number;
    risk_score: 'Low' | 'Medium' | 'High';
  };
};

export type FXRiskResponse = {
  fx_risk_score: number;
  risk_label: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  annualised_vol_pct: number;
  max_drawdown_pct: number;
  method: string;
  interpretation: string;
};

export type ExplainRequest = {
  source_country: string;
  destination_country: string;
  amount: number;
  purpose: string;
  recommended_path: string[];
  total_cost_usd: number;
  total_time_hrs: number;
  compliance_score: number;
  fx_risk_score: number;
  fx_risk_label: string;
  fx_interpretation: string;
};

export type ExplainResponse = {
  explanation: string;
  model: string;
};

export type DashboardResponse = {
  metrics: {
    total_routes_analyzed: number;
    avg_cost_reduction_pct: number;
    efficiency_score: number;
  };
  active_nodes: string[];
  recent_routes: Array<{
    id: string;
    destination: string;
    asset_class: string;
    cost_save: string;
    score: string;
    status: string;
  }>;
  recommended_routes: RouteSummary[];
};

export type InsightsResponse = {
  costDistribution: Array<{ name: string; value: number }>;
  topRoutes: Array<{ path: string; volume: string; avgCost: string }>;
  riskHeatmap: Array<{ region: string; risk: string; score: number }>;
};

export type AssetResponse = Array<{ id: string; name: string; type: string; symbol: string }>;

export const optimizeRoute = (params: RouteRequest) =>
  request<OptimizeResponse>('/optimize-route', {
    method: 'POST',
    body: JSON.stringify(params),
  });

export const compareRoutes = (params: RouteRequest) =>
  request<CompareResponse>('/compare-routes', {
    method: 'POST',
    body: JSON.stringify(params),
  });

export const simulateScenario = (params: SimulationRequest) =>
  request<SimulationResponse>('/simulate', {
    method: 'POST',
    body: JSON.stringify(params),
  });

export const getFXRisk = (params: { source_country: string; destination_country: string }) =>
  request<FXRiskResponse>('/fx-risk', {
    method: 'POST',
    body: JSON.stringify(params),
  });

export const explainRoute = (params: ExplainRequest) =>
  request<ExplainResponse>('/explain-route', {
    method: 'POST',
    body: JSON.stringify(params),
  });

export type TTSResponse = {
  audio_base64: string;
};

export const textToSpeech = (text: string) =>
  request<TTSResponse>('/text-to-speech', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });

export const getDashboard = () => request<DashboardResponse>('/dashboard');

export const getInsights = () => request<InsightsResponse>('/insights');

export const getAssets = () => request<AssetResponse>('/assets');

export const getHistory = (limit = 5) => request<{ entries: DashboardResponse['recent_routes']; total: number }>(`/history?limit=${limit}`);

export const getModelInfo = () => request('/model-info');
