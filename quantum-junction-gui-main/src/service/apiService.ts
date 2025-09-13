import axios from 'axios';

const BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add error handling interceptor
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Legacy interfaces for compatibility with existing frontend
export interface EnvironmentalImpact {
  fuel_saved: number;
  co2_reduced: number;
}

export interface LiveMetrics {
  timestamp: string;
  wait_times: {
    overall_avg_wait_time: number;
    best_performance: number | null;
    worst_performance: number | null;
    detailed_data: Array<{
      intersection_id: string;
      simulation_id: string;
      avg_wait_time: number;
      total_vehicles: number;
    }>;
    total_intersections: number;
  };
  speeds: {
    overall_avg_speed: number;
    speed_data: Array<{
      intersection_id: string;
      simulation_id: string;
      avg_speed: number;
      avg_throughput: number;
      total_vehicles: number;
    }>;
  };
  environmental_impact: {
    environmental_data: Array<{
      intersection_id: string;
      simulation_id: string;
      co2_saved: number;
      fuel_saved: number;
    }>;
    total_fuel_saved: number;
    total_co2_saved: number;
  };
}

export interface PerformanceComparison {
  comparison: {
    comparison_data: {
      [mode: string]: {
        avg_wait_time: number;
        avg_throughput: number;
        avg_speed: number;
        total_fuel_saved: number;
      };
    };
  };
  emergency_handling: {
    response_time: number;
    incidents_handled: number;
  };
  generated_at: string;
}

export interface TrafficData {
  wait_times: LiveMetrics['wait_times'];
  speeds: number;
  environmental_impact: EnvironmentalImpact;
}

export const trafficApi = {
  // Health check
  checkHealth: () => api.get('/health'),
  getSystemInfo: () => api.get('/system/info'),

  // Main dashboard endpoints
  getLiveMetrics: () => api.get<LiveMetrics>('/api/v1/dashboard/live-metrics'),
  getPerformanceComparison: () => api.get<PerformanceComparison>('/api/v1/dashboard/performance-comparison'),

  // Analytics endpoints
  getWaitTimes: (params?: {
    simulation_id?: string;
    intersection_id?: string;
    time_window_hours?: number;
  }) => api.get('/api/v1/analytics/wait-times', { params }),

  getSpeeds: (params?: {
    simulation_id?: string;
    intersection_id?: string;
  }) => api.get('/api/v1/analytics/speeds', { params }),

  getEnvironmentalImpact: (params?: {
    simulation_id?: string;
    comparison_mode?: boolean;
  }) => api.get('/api/v1/analytics/environmental-impact', { params }),

  // Chart data
  getWaitTimeTrend: (simulationIds: string[], hours: number = 24) => 
    api.get('/api/v1/charts/wait-time-trend', { 
      params: { simulation_ids: simulationIds, hours }
    }),

  getPerformanceScatter: () => api.get('/api/v1/charts/performance-scatter'),

  // Data ingestion
  submitSimulationData: (data: any) => api.post('/api/v1/ingest/simulation', { data }),

  // Signal Control Endpoints
  getSignalTimings: (intersectionId?: string) => 
    api.get('/api/v1/signals/timings', { params: { intersection_id: intersectionId } }),
    
  updateSignalTiming: (laneId: string, signalState: string, duration?: number) => 
    api.post('/api/v1/signals/manual-override', {
      lane_id: laneId,
      signal_state: signalState,
      duration: duration || 30
    }),
    
  setEmergencyOverride: (laneId: string, duration?: number) => 
    api.post('/api/v1/signals/emergency-override', {
      lane_id: laneId,
      duration: duration || 60
    }),
    
  resetToAI: (intersectionId?: string) => 
    api.post('/api/v1/signals/reset-ai', { intersection_id: intersectionId }),

  // Real-time Signal Updates (for backend polling)
  postSignalUpdate: (signalData: {
    intersection_id: string;
    signals: Array<{
      lane_id: string;
      direction: string;
      type: string;
      current_light: string;
      time_remaining: number;
      max_time: number;
      vehicle_count: number;
    }>;
    timestamp: string;
  }) => api.post('/api/v1/signals/update', signalData),

  // Admin
  initializeDatabase: () => api.get('/api/v1/admin/database/init'),
};
