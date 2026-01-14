export type Direction = "north" | "south" | "east" | "west";

export interface DirectionMetrics {
  vehicle_counts: {
    car: number;
    bus: number;
    truck: number;
    bike: number;
  };
  queue_length: number;
  vehicles_crossed: number;
  avg_wait_time: number;
  emergency_vehicle_present: boolean;
}

export interface CurrentPhase {
  phase_id: number;
  active_directions: Direction[];
  status: "GREEN" | "YELLOW" | "RED" | string;
  remaining_time: number;
}

export interface OverallMetrics {
  total_vehicles_passed: number;
  avg_wait_time_all_sides: number;
  throughput: number;
  avg_speed: number;
  cycle_time: number;
}

export interface Explainability {
  policy: string;
  reason: string;
  phase_scores: Record<string, number>;
  chosen_phase: string;
  emergency_preemption: boolean;
  notes: string;
}

export interface CityNode {
  intersection_id: string;
  name: string;
  lat: number;
  lng: number;
  neighbors: string[];
  current_phase: CurrentPhase;
  overall_metrics: OverallMetrics;
  direction_metrics: Record<Direction, DirectionMetrics>;
  explainability?: Explainability | null;
}

export interface CitySnapshot {
  city_id: string;
  center: { lat: number; lng: number };
  nodes: CityNode[];
}

export interface Incident {
  incident_id: string;
  intersection_id: string;
  direction: Direction;
  incident_type: string;
  severity: number;
  created_at: string;
  status: "active" | "cleared" | string;
}

export interface AmbulanceRoute {
  route_id: string;
  from_intersection: string;
  to_intersection: string;
  created_at: string;
  eta_seconds: number;
  status: "enroute" | "arrived" | "cleared" | string;
}

export interface CityEvent {
  type: string;
  timestamp: string;
  data: Record<string, unknown>;
}

export interface CityUpdateMessage {
  type: "city_update";
  timestamp: string;
  city: CitySnapshot;
  incidents: Incident[];
  ambulance_routes: AmbulanceRoute[];
  event_log_tail: CityEvent[];
}

export interface AmbulanceRouteUpdateMessage {
  type: "ambulance_route_update";
  timestamp: string;
  route: AmbulanceRoute;
}

export interface IncidentUpdateMessage {
  type: "incident_update";
  timestamp: string;
  incident: Incident;
}

export interface PongMessage {
  type: "pong";
  timestamp: string;
}

export type CityWsMessage =
  | CityUpdateMessage
  | AmbulanceRouteUpdateMessage
  | IncidentUpdateMessage
  | PongMessage
  | { type: string; [k: string]: unknown };
