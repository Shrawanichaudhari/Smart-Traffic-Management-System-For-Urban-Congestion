import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { websocketService } from "@/services/websocketService";
import type {
  CityUpdateMessage,
  CityState,
  CityNode,
  Incident,
  AmbulanceRoute,
} from "@/types/city";
import type { EnhancedLaneData, SimulationData } from "@/types/simulation";

interface CityDataState {
  city: CityState | null;
  latestCityUpdate: CityUpdateMessage | null;
  nodes: CityNode[];
  selectedIntersectionId: string | null;
  setSelectedIntersectionId: (id: string) => void;

  // Data for existing lane-based UI
  lanes: EnhancedLaneData[];
  simulationData: SimulationData | null;

  // Alerts/workflows
  incidents: Incident[];
  ambulanceRoutes: AmbulanceRoute[];

  // Connection
  isConnected: boolean;
  error: string | null;
  lastUpdateTime: Date | null;

  // Actions
  dispatchAmbulance: (fromIntersection: string, toIntersection: string, etaSeconds?: number) => void;
  createIncident: (intersectionId: string, direction: string, incidentType?: string, severity?: number) => void;
  clearIncident: (incidentId: string) => void;
}

const dirShortMap: Record<string, string> = {
  north: "n",
  south: "s",
  east: "e",
  west: "w",
};

export const useCityData = (): CityDataState => {
  const mountedRef = useRef(true);

  const [city, setCity] = useState<CityState | null>(null);
  const [latestCityUpdate, setLatestCityUpdate] = useState<CityUpdateMessage | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [ambulanceRoutes, setAmbulanceRoutes] = useState<AmbulanceRoute[]>([]);

  const [selectedIntersectionId, setSelectedIntersectionId] = useState<string | null>(null);

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);

  const handleCityUpdate = useCallback((msg: CityUpdateMessage) => {
    if (!mountedRef.current) return;

    setLatestCityUpdate(msg);
    setCity(msg.city);
    setIncidents(msg.incidents || []);
    setAmbulanceRoutes(msg.ambulance_routes || []);
    setLastUpdateTime(new Date());
    setError(null);

    // Initialize selection once.
    if (!selectedIntersectionId && msg.city?.nodes?.length) {
      setSelectedIntersectionId(msg.city.nodes[0].intersection_id);
    }
  }, [selectedIntersectionId]);

  const handleConnectionStatus = useCallback((connected: boolean) => {
    if (!mountedRef.current) return;
    setIsConnected(connected);
    setError(connected ? null : "Connection lost. Trying to reconnect...");
  }, []);

  const handleError = useCallback((payload: any) => {
    if (!mountedRef.current) return;
    setError(payload?.error || "WebSocket error");
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    websocketService.on("cityUpdate", handleCityUpdate);
    websocketService.on("error", handleError);
    websocketService.onConnectionStatus(handleConnectionStatus);
    websocketService.connect();

    return () => {
      mountedRef.current = false;
      websocketService.off("cityUpdate", handleCityUpdate);
      websocketService.off("error", handleError);
      websocketService.offConnectionStatus(handleConnectionStatus);
      websocketService.disconnect();
    };
  }, [handleCityUpdate, handleError, handleConnectionStatus]);

  const nodes = city?.nodes || [];

  const selectedNode: CityNode | undefined = useMemo(() => {
    if (!selectedIntersectionId) return undefined;
    return nodes.find((n) => n.intersection_id === selectedIntersectionId);
  }, [nodes, selectedIntersectionId]);

  const lanes: EnhancedLaneData[] = useMemo(() => {
    if (!selectedNode) return [];

    const currentPhase = selectedNode.current_phase;
    const directionMetrics = selectedNode.direction_metrics;

    const result: EnhancedLaneData[] = [];
    for (const [directionName, metrics] of Object.entries(directionMetrics)) {
      const short = dirShortMap[directionName];
      if (!short) continue;

      const vehicleCounts: any = metrics.vehicle_counts;
      const totalVehicles = Object.values(vehicleCounts).reduce((sum: number, count: any) => sum + Number(count), 0);

      let lightState: "red" | "yellow" | "green" = "red";
      if (currentPhase.active_directions.includes(directionName)) {
        lightState = currentPhase.status === "YELLOW" ? "yellow" : "green";
      }

      result.push({
        id: `${short}-straight`,
        direction: directionName as any,
        type: "straight",
        vehicleCount: totalVehicles,
        queueLength: metrics.queue_length,
        currentLight: lightState,
        timeRemaining: currentPhase.remaining_time,
        maxTime: 45,
        avgWaitTime: metrics.avg_wait_time,
        vehiclesCrossed: metrics.vehicles_crossed,
        emergencyVehiclePresent: metrics.emergency_vehicle_present,
      });
    }

    return result;
  }, [selectedNode]);

  const simulationData: SimulationData | null = useMemo(() => {
    if (!selectedNode || !city) return null;

    // Bridge format so existing components can still render.
    return {
      simulation_id: city.city_id,
      timestamp: new Date().toISOString(),
      intersection_id: selectedNode.intersection_id,
      current_phase: selectedNode.current_phase,
      direction_metrics: selectedNode.direction_metrics as any,
      overall_metrics: selectedNode.overall_metrics,
      explainability: selectedNode.explainability as any,
    } as any;
  }, [city, selectedNode]);

  const dispatchAmbulance = useCallback(
    (fromIntersection: string, toIntersection: string, etaSeconds?: number) => {
      websocketService.send({
        type: "dispatch_ambulance",
        from_intersection: fromIntersection,
        to_intersection: toIntersection,
        eta_seconds: etaSeconds ?? 30,
      });
    },
    []
  );

  const createIncident = useCallback(
    (intersectionId: string, direction: string, incidentType?: string, severity?: number) => {
      websocketService.send({
        type: "incident_create",
        intersection_id: intersectionId,
        direction,
        incident_type: incidentType ?? "accident",
        severity: severity ?? 2,
      });
    },
    []
  );

  const clearIncident = useCallback((incidentId: string) => {
    websocketService.send({ type: "incident_clear", incident_id: incidentId });
  }, []);

  return {
    city,
    latestCityUpdate,
    nodes,
    selectedIntersectionId,
    setSelectedIntersectionId,
    lanes,
    simulationData,
    incidents,
    ambulanceRoutes,
    isConnected,
    error,
    lastUpdateTime,
    dispatchAmbulance,
    createIncident,
    clearIncident,
  };
};
