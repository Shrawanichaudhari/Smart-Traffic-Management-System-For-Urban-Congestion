export interface CityNode {
  intersection_id: string;
  name: string;
  lat: number;
  lng: number;
  neighbors: string[];

  // Same shapes as SimulationData
  current_phase: any;
  overall_metrics: any;
  direction_metrics: any;
  explainability?: any;
}

export interface CityState {
  city_id: string;
  center: { lat: number; lng: number };
  nodes: CityNode[];
}

export interface Incident {
  incident_id: string;
  intersection_id: string;
  direction: string;
  incident_type: string;
  severity: number;
  created_at: string;
  status: string;
}

export interface AmbulanceRoute {
  route_id: string;
  from_intersection: string;
  to_intersection: string;
  created_at: string;
  eta_seconds: number;
  status: string;
}

export interface CityUpdateMessage {
  type: "city_update";
  timestamp: string;
  city: CityState;
  incidents: Incident[];
  ambulance_routes: AmbulanceRoute[];
  event_log_tail?: Array<{ type: string; timestamp: string; data: any }>;
}

export interface IncidentUpdateMessage {
  type: "incident_update";
  timestamp: string;
  incident: Incident;
}

export interface AmbulanceRouteUpdateMessage {
  type: "ambulance_route_update";
  timestamp: string;
  route: AmbulanceRoute;
}

export type CityWebSocketMessage =
  | CityUpdateMessage
  | IncidentUpdateMessage
  | AmbulanceRouteUpdateMessage
  | { type: "pong"; timestamp: string }
  | { type: "error"; timestamp: string; message?: string }; 
