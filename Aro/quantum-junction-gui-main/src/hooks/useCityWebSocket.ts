import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  CityUpdateMessage,
  CityWsMessage,
  Incident,
  CityEvent,
  AmbulanceRoute,
  AmbulanceRouteUpdateMessage,
  IncidentUpdateMessage,
  Direction,
} from "@/types/city";

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

const DEFAULT_CITY_WS_URL = "ws://localhost:8001/ws/city";

export function useCityWebSocket(options?: {
  url?: string;
  reconnectIntervalMs?: number;
  reconnectMaxAttempts?: number;
  debug?: boolean;
}) {
  const url =
    options?.url ??
    (import.meta.env.VITE_CITY_WS_URL as string | undefined) ??
    DEFAULT_CITY_WS_URL;

  const reconnectIntervalMs = options?.reconnectIntervalMs ?? 1000;
  const reconnectMaxAttempts = options?.reconnectMaxAttempts ?? 10;
  const debug = options?.debug ?? false;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);

  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [lastError, setLastError] = useState<string | null>(null);

  const [cityUpdate, setCityUpdate] = useState<CityUpdateMessage | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [routes, setRoutes] = useState<AmbulanceRoute[]>([]);
  const [events, setEvents] = useState<CityEvent[]>([]);

  const log = useCallback(
    (...args: unknown[]) => {
      if (!debug) return;
      console.log("[CityWS]", ...args);
    },
    [debug]
  );

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current) {
      window.clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const closeSocket = useCallback(() => {
    clearReconnectTimer();
    const ws = wsRef.current;
    wsRef.current = null;
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close();
    }
  }, [clearReconnectTimer]);

  const sendMessage = useCallback(
    (msg: Record<string, unknown>) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        log("sendMessage dropped (socket not open)", msg);
        return false;
      }
      ws.send(JSON.stringify(msg));
      return true;
    },
    [log]
  );

  const scheduleReconnect = useCallback(() => {
    clearReconnectTimer();

    if (reconnectAttemptRef.current >= reconnectMaxAttempts) {
      setStatus("error");
      setLastError(
        `Failed to reconnect after ${reconnectMaxAttempts} attempts. Check City WebSocket server at ${url}`
      );
      return;
    }

    const attempt = reconnectAttemptRef.current + 1;
    reconnectAttemptRef.current = attempt;
    const delay = reconnectIntervalMs * attempt;

    log(`reconnect scheduled attempt=${attempt} delayMs=${delay}`);
    setStatus("connecting");

    reconnectTimerRef.current = window.setTimeout(() => {
      connect();
    }, delay);
  }, [clearReconnectTimer, connect, log, reconnectIntervalMs, reconnectMaxAttempts, url]);

  // NOTE: connect is declared via function so scheduleReconnect can reference it.
  function connect() {
    closeSocket();
    setStatus("connecting");
    setLastError(null);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        log("connected", url);
        reconnectAttemptRef.current = 0;
        setStatus("connected");
      };

      ws.onmessage = (evt) => {
        let msg: CityWsMessage;
        try {
          msg = JSON.parse(evt.data);
        } catch {
          return;
        }

        if (msg.type === "city_update") {
          const cu = msg as CityUpdateMessage;
          setCityUpdate(cu);
          setIncidents(cu.incidents ?? []);
          setRoutes(cu.ambulance_routes ?? []);
          setEvents(cu.event_log_tail ?? []);
          return;
        }

        if (msg.type === "ambulance_route_update") {
          const { route } = msg as AmbulanceRouteUpdateMessage;
          setRoutes((prev) => {
            const filtered = prev.filter((r) => r.route_id !== route.route_id);
            return [route, ...filtered];
          });
          return;
        }

        if (msg.type === "incident_update") {
          const { incident } = msg as IncidentUpdateMessage;
          setIncidents((prev) => {
            const filtered = prev.filter((i) => i.incident_id !== incident.incident_id);
            return [incident, ...filtered];
          });
          return;
        }
      };

      ws.onerror = () => {
        setStatus("error");
        setLastError(`WebSocket error connecting to ${url}`);
      };

      ws.onclose = () => {
        log("disconnected");
        setStatus("disconnected");
        scheduleReconnect();
      };
    } catch (e) {
      setStatus("error");
      setLastError(e instanceof Error ? e.message : "Unknown websocket error");
      scheduleReconnect();
    }
  }

  useEffect(() => {
    connect();
    return () => closeSocket();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  const nodes = cityUpdate?.city?.nodes ?? [];

  const activeRoutes = useMemo(
    () => routes.filter((r) => r.status === "enroute"),
    [routes]
  );

  const actions = useMemo(
    () => ({
      dispatchAmbulance: (from: string, to: string, etaSeconds: number) =>
        sendMessage({
          type: "dispatch_ambulance",
          from_intersection: from,
          to_intersection: to,
          eta_seconds: etaSeconds,
        }),
      clearAmbulanceRoute: (routeId: string) =>
        sendMessage({ type: "clear_ambulance_route", route_id: routeId }),
      createIncident: (
        intersectionId: string,
        direction: Direction,
        incidentType: string,
        severity: number
      ) =>
        sendMessage({
          type: "incident_create",
          intersection_id: intersectionId,
          direction,
          incident_type: incidentType,
          severity,
        }),
      clearIncident: (incidentId: string) =>
        sendMessage({ type: "incident_clear", incident_id: incidentId }),
      ping: () => sendMessage({ type: "ping" }),
    }),
    [sendMessage]
  );

  return {
    url,
    status,
    lastError,
    cityUpdate,
    nodes,
    incidents,
    routes,
    activeRoutes,
    events,
    sendMessage,
    ...actions,
  };
}
