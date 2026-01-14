// Types for simulation data from backend API

export interface VehicleCounts {
  car: number;
  bus: number;
  truck: number;
  bike: number;
}

export interface DirectionMetrics {
  vehicle_counts: VehicleCounts;
  queue_length: number;
  vehicles_crossed: number;
  avg_wait_time: number;
  emergency_vehicle_present: boolean;
}

export interface CurrentPhase {
  phase_id: number;
  active_directions: string[];
  status: "GREEN" | "YELLOW" | "RED";
  remaining_time: number;
}

export interface OverallMetrics {
  total_vehicles_passed: number;
  avg_wait_time_all_sides: number;
  throughput: number;
  avg_speed: number;
  cycle_time: number;
}

export interface SimulationData {
  simulation_id: string;
  timestamp: string;
  intersection_id: string;
  current_phase: CurrentPhase;
  direction_metrics: {
    [direction: string]: DirectionMetrics;
  };
  overall_metrics: OverallMetrics;

  // Optional explainability payload (why the controller made a decision)
  explainability?: any;
}

// Enhanced lane data that matches existing React component expectations
export interface EnhancedLaneData {
  id: string;
  direction: "north" | "south" | "east" | "west";
  type: "straight" | "left" | "right";
  vehicleCount: number;
  queueLength: number;
  currentLight: "red" | "yellow" | "green";
  timeRemaining: number;
  maxTime: number;
  avgWaitTime: number;
  vehiclesCrossed: number;
  emergencyVehiclePresent: boolean;
}

// API response for intersection status
export interface IntersectionStatusResponse {
  timestamp: string;
  simulation_id: string;
  intersection_id: string;
  lanes: EnhancedLaneData[];
  current_phase: CurrentPhase;
  overall_metrics: OverallMetrics;
}

// WebSocket message types
export interface WebSocketMessage {
  type: "simulation_update" | "connection_status" | "error";
  data?: SimulationData;
  timestamp: string;
  message?: string;
}

// Analytics data types
export interface AnalyticsData {
  wait_times: {
    [direction: string]: number;
  };
  environmental_impact: {
    fuel_saved: number;
    co2_saved: number;
    percentage_improvement: number;
  };
  comparison_data: {
    baseline: {
      avg_wait_time: number;
      throughput: number;
      avg_speed: number;
    };
    ai_optimized: {
      avg_wait_time: number;
      throughput: number;
      avg_speed: number;
    };
  };
}

// Chart data types
export interface ChartDataPoint {
  timestamp: string;
  value: number;
  metric: string;
}

export interface TimeSeriesData {
  simulation_id: string;
  metric: string;
  data_points: ChartDataPoint[];
  time_window_hours: number;
}