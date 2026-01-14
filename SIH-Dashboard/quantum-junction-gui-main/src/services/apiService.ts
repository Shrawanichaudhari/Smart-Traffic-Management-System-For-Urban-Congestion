// API service for communicating with FastAPI backend

import { 
  SimulationData, 
  IntersectionStatusResponse, 
  AnalyticsData, 
  TimeSeriesData 
} from '../types/simulation';

// Configuration (Vite uses import.meta.env; keep process.env fallback for legacy builds)
const API_BASE_URL =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_BASE_URL) ||
  (typeof process !== 'undefined' && (process as any).env?.REACT_APP_API_BASE_URL) ||
  'http://localhost:8000';

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // Generic fetch method with error handling
  private async fetchData<T>(url: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${this.baseUrl}${url}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API call failed for ${url}:`, error);
      throw error;
    }
  }

  // Health check
  async checkHealth(): Promise<{ status: string; database: string; timestamp: string }> {
    return this.fetchData('/health');
  }

  // Get latest simulation data
  async getLatestSimulation(): Promise<SimulationData> {
    return this.fetchData('/api/simulation/latest');
  }

  // Get simulation by ID
  async getSimulationById(simulationId: string): Promise<SimulationData> {
    return this.fetchData(`/api/simulation/${simulationId}`);
  }

  // Get simulation history
  async getSimulationHistory(
    simulationId: string, 
    hours: number = 24, 
    intervalMinutes: number = 5
  ): Promise<TimeSeriesData> {
    return this.fetchData(
      `/api/simulation/${simulationId}/history?hours=${hours}&interval_minutes=${intervalMinutes}`
    );
  }

  // Get intersection status (optimized for React components)
  async getIntersectionStatus(): Promise<IntersectionStatusResponse> {
    return this.fetchData('/api/dashboard/intersection-status');
  }

  // Get live metrics for dashboard
  async getLiveMetrics(): Promise<{
    timestamp: string;
    wait_times: any;
    speeds: any;
    environmental_impact: any;
  }> {
    return this.fetchData('/api/v1/dashboard/live-metrics');
  }

  // Get performance comparison data
  async getPerformanceComparison(): Promise<{
    comparison: any;
    emergency_handling: any;
    generated_at: string;
  }> {
    return this.fetchData('/api/v1/dashboard/performance-comparison');
  }

  // Analytics endpoints
  async getWaitTimeAnalytics(
    simulationId?: string,
    intersectionId?: string,
    timeWindowHours?: number
  ): Promise<AnalyticsData> {
    const params = new URLSearchParams();
    if (simulationId) params.append('simulation_id', simulationId);
    if (intersectionId) params.append('intersection_id', intersectionId);
    if (timeWindowHours) params.append('time_window_hours', timeWindowHours.toString());
    
    const queryString = params.toString();
    const url = `/api/v1/analytics/wait-times${queryString ? `?${queryString}` : ''}`;
    
    return this.fetchData(url);
  }

  async getBaselineVsAIComparison(
    intersectionId?: string,
    timeWindowHours: number = 24,
    metric: string = 'wait_time'
  ): Promise<any> {
    const params = new URLSearchParams();
    if (intersectionId) params.append('intersection_id', intersectionId);
    params.append('time_window_hours', timeWindowHours.toString());
    params.append('metric', metric);
    
    return this.fetchData(`/api/v1/analytics/comparison/baseline-vs-ai?${params.toString()}`);
  }

  async getEnvironmentalImpact(simulationId?: string, comparisonMode: boolean = false): Promise<any> {
    const params = new URLSearchParams();
    if (simulationId) params.append('simulation_id', simulationId);
    params.append('comparison_mode', comparisonMode.toString());
    
    return this.fetchData(`/api/v1/analytics/environmental-impact?${params.toString()}`);
  }

  async getEmergencyHandlingReport(
    simulationId?: string,
    timeWindowHours?: number
  ): Promise<any> {
    const params = new URLSearchParams();
    if (simulationId) params.append('simulation_id', simulationId);
    if (timeWindowHours) params.append('time_window_hours', timeWindowHours.toString());
    
    const queryString = params.toString();
    const url = `/api/v1/analytics/emergency-handling${queryString ? `?${queryString}` : ''}`;
    
    return this.fetchData(url);
  }

  // Chart data endpoints
  async getWaitTimeTrendData(simulationIds: string[], hours: number = 24): Promise<any> {
    const params = new URLSearchParams();
    simulationIds.forEach(id => params.append('simulation_ids', id));
    params.append('hours', hours.toString());
    
    return this.fetchData(`/api/v1/charts/wait-time-trend?${params.toString()}`);
  }

  async getPerformanceScatterData(
    metricX: string = 'avg_wait_time',
    metricY: string = 'throughput',
    timeWindowHours: number = 24
  ): Promise<any> {
    const params = new URLSearchParams();
    params.append('metric_x', metricX);
    params.append('metric_y', metricY);
    params.append('time_window_hours', timeWindowHours.toString());
    
    return this.fetchData(`/api/v1/charts/performance-scatter?${params.toString()}`);
  }

  // Ingest simulation data (for testing purposes)
  async ingestSimulationData(data: SimulationData): Promise<any> {
    return this.fetchData('/api/v1/ingest/simulation', {
      method: 'POST',
      body: JSON.stringify({ data }),
    });
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;