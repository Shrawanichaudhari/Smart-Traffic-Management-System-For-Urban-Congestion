import { useMemo, useState } from "react";
import { CityMap } from "@/components/city/CityMap";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useCityWebSocket } from "@/hooks/useCityWebSocket";
import type { CityNode, Direction } from "@/types/city";
import { AlertTriangle, Ambulance, MapPin, Signal } from "lucide-react";

function sumQueue(node: CityNode) {
  return Object.values(node.direction_metrics).reduce((sum, m) => sum + (m?.queue_length ?? 0), 0);
}

function congestionLabel(queue: number) {
  if (queue >= 35) return { label: "High", variant: "destructive" as const };
  if (queue >= 18) return { label: "Medium", variant: "secondary" as const };
  return { label: "Low", variant: "outline" as const };
}

export function CityViewPage() {
  const {
    status,
    lastError,
    nodes,
    activeRoutes,
    routes,
    incidents,
    events,
    dispatchAmbulance,
    createIncident,
    clearIncident,
    clearAmbulanceRoute,
  } = useCityWebSocket({ debug: false });

  const cityCenter = useMemo(() => {
    if (nodes.length === 0) return { lat: 28.6139, lng: 77.209 };
    const avgLat = nodes.reduce((s, n) => s + n.lat, 0) / nodes.length;
    const avgLng = nodes.reduce((s, n) => s + n.lng, 0) / nodes.length;
    return { lat: avgLat, lng: avgLng };
  }, [nodes]);

  const [fromNode, setFromNode] = useState("INT_A");
  const [toNode, setToNode] = useState("INT_B");
  const [etaSeconds, setEtaSeconds] = useState("30");

  const [incidentNode, setIncidentNode] = useState("INT_A");
  const [incidentDirection, setIncidentDirection] = useState<Direction>("east");
  const [incidentType, setIncidentType] = useState("accident");
  const [incidentSeverity, setIncidentSeverity] = useState("2");

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <MapPin className="w-6 h-6" /> City View
          </h2>
          <p className="text-sm text-muted-foreground">
            Multi-node monitoring + ambulance corridor preemption (NodeA → NodeB).
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            <Badge
              variant={
                status === "connected" ? "outline" : status === "error" ? "destructive" : "secondary"
              }
            >
              WS: {status}
            </Badge>
            {activeRoutes.length > 0 && (
              <Badge variant="destructive" className="flex items-center gap-1">
                <Ambulance className="w-4 h-4" /> corridor active
              </Badge>
            )}
          </div>
          {lastError && <div className="text-xs text-red-600 max-w-[420px] text-right">{lastError}</div>}
        </div>
      </div>

      {/* Corridor banner */}
      {activeRoutes.length > 0 && (
        <Card className="p-4 border-red-300/60 bg-red-50/50">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <Ambulance className="w-6 h-6 text-red-600" />
              <div>
                <div className="font-semibold text-red-800">Emergency corridor preemption</div>
                <div className="text-sm text-red-700">
                  {activeRoutes.map((r) => (
                    <span key={r.route_id} className="mr-3">
                      {r.from_intersection} → {r.to_intersection} (ETA {r.eta_seconds}s)
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              {activeRoutes.map((r) => (
                <Button
                  key={r.route_id}
                  variant="destructive"
                  onClick={() => clearAmbulanceRoute(r.route_id)}
                >
                  Clear {r.route_id}
                </Button>
              ))}
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2">
          <CityMap center={cityCenter} nodes={nodes} routes={routes} heightClassName="h-[520px]" />
        </div>

        <div className="space-y-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div className="font-semibold flex items-center gap-2">
                <Signal className="w-4 h-4" /> Intersections
              </div>
              <Badge variant="secondary">{nodes.length}</Badge>
            </div>
            <Separator className="my-3" />
            <div className="space-y-3 max-h-[430px] overflow-auto pr-2">
              {nodes.map((n) => {
                const q = sumQueue(n);
                const c = congestionLabel(q);
                const expl = n.explainability;
                return (
                  <div key={n.intersection_id} className="p-3 rounded border bg-background">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{n.name}</div>
                      <Badge variant={c.variant}>{c.label}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {n.intersection_id} • Queue {q} • Avg wait {n.overall_metrics.avg_wait_time_all_sides}s
                    </div>

                    {expl && (
                      <div className="mt-2 text-xs">
                        <div className="text-muted-foreground">Explainability</div>
                        <div className="mt-1">
                          policy: <span className="font-medium">{expl.policy}</span> • phase:{" "}
                          <span className="font-medium">{expl.chosen_phase}</span>
                          {expl.emergency_preemption && (
                            <Badge variant="destructive" className="ml-2">
                              emergency override
                            </Badge>
                          )}
                        </div>
                        <div className="text-muted-foreground mt-1">{expl.notes}</div>
                      </div>
                    )}
                  </div>
                );
              })}
              {nodes.length === 0 && (
                <div className="text-sm text-muted-foreground">
                  Waiting for first <code>city_update</code>… start the server: <code>python start_city_websocket_server.py</code>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Controls */}
        <Card className="p-4">
          <div className="font-semibold flex items-center gap-2">
            <Ambulance className="w-4 h-4" /> Demo controls
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Trigger events to show multi-node communication and corridor creation.
          </p>

          <Separator className="my-4" />

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>From</Label>
                <Select value={fromNode} onValueChange={setFromNode}>
                  <SelectTrigger>
                    <SelectValue placeholder="From node" />
                  </SelectTrigger>
                  <SelectContent>
                    {nodes.map((n) => (
                      <SelectItem key={n.intersection_id} value={n.intersection_id}>
                        {n.intersection_id}
                      </SelectItem>
                    ))}
                    {nodes.length === 0 && <SelectItem value="INT_A">INT_A</SelectItem>}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>To</Label>
                <Select value={toNode} onValueChange={setToNode}>
                  <SelectTrigger>
                    <SelectValue placeholder="To node" />
                  </SelectTrigger>
                  <SelectContent>
                    {nodes.map((n) => (
                      <SelectItem key={n.intersection_id} value={n.intersection_id}>
                        {n.intersection_id}
                      </SelectItem>
                    ))}
                    {nodes.length === 0 && <SelectItem value="INT_B">INT_B</SelectItem>}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label>ETA (seconds)</Label>
              <Input value={etaSeconds} onChange={(e) => setEtaSeconds(e.target.value)} inputMode="numeric" />
            </div>

            <Button
              className="w-full"
              variant="destructive"
              onClick={() => dispatchAmbulance(fromNode, toNode, Math.max(5, Number(etaSeconds) || 30))}
            >
              Dispatch ambulance
            </Button>
          </div>

          <Separator className="my-4" />

          <div className="space-y-3">
            <div className="font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" /> Incident
            </div>

            <div>
              <Label>Intersection</Label>
              <Select value={incidentNode} onValueChange={setIncidentNode}>
                <SelectTrigger>
                  <SelectValue placeholder="Intersection" />
                </SelectTrigger>
                <SelectContent>
                  {nodes.map((n) => (
                    <SelectItem key={n.intersection_id} value={n.intersection_id}>
                      {n.intersection_id}
                    </SelectItem>
                  ))}
                  {nodes.length === 0 && <SelectItem value="INT_A">INT_A</SelectItem>}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Direction</Label>
                <Select value={incidentDirection} onValueChange={(v) => setIncidentDirection(v as Direction)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Direction" />
                  </SelectTrigger>
                  <SelectContent>
                    {(["north", "south", "east", "west"] as const).map((d) => (
                      <SelectItem key={d} value={d}>
                        {d}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Severity (1-5)</Label>
                <Input
                  value={incidentSeverity}
                  onChange={(e) => setIncidentSeverity(e.target.value)}
                  inputMode="numeric"
                />
              </div>
            </div>

            <div>
              <Label>Type</Label>
              <Select value={incidentType} onValueChange={setIncidentType}>
                <SelectTrigger>
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  {[
                    { v: "accident", t: "Accident" },
                    { v: "event", t: "Event" },
                    { v: "roadblock", t: "Roadblock" },
                  ].map((it) => (
                    <SelectItem key={it.v} value={it.v}>
                      {it.t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              className="w-full"
              variant="secondary"
              onClick={() =>
                createIncident(
                  incidentNode,
                  incidentDirection,
                  incidentType,
                  Math.min(5, Math.max(1, Number(incidentSeverity) || 2))
                )
              }
            >
              Create incident
            </Button>
          </div>

          {incidents.length > 0 && (
            <>
              <Separator className="my-4" />
              <div className="space-y-2">
                <div className="text-sm font-medium">Active incidents</div>
                {incidents
                  .filter((i) => i.status === "active")
                  .slice(0, 6)
                  .map((i) => (
                    <div key={i.incident_id} className="flex items-center justify-between gap-2 text-xs">
                      <div className="truncate">
                        {i.intersection_id} • {i.direction} • {i.incident_type} (sev {i.severity})
                      </div>
                      <Button size="sm" variant="outline" onClick={() => clearIncident(i.incident_id)}>
                        Clear
                      </Button>
                    </div>
                  ))}
              </div>
            </>
          )}
        </Card>

        {/* Event timeline */}
        <Card className="p-4 xl:col-span-2">
          <div className="flex items-center justify-between">
            <div className="font-semibold">Event timeline</div>
            <Badge variant="secondary">latest {events.length}</Badge>
          </div>
          <Separator className="my-3" />
          <div className="space-y-2 max-h-[360px] overflow-auto pr-2">
            {events
              .slice()
              .reverse()
              .map((e, idx) => (
                <div key={idx} className="text-sm">
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{e.type}</div>
                    <div className="text-xs text-muted-foreground">{new Date(e.timestamp).toLocaleTimeString()}</div>
                  </div>
                  <div className="text-xs text-muted-foreground truncate">
                    {JSON.stringify(e.data)}
                  </div>
                </div>
              ))}
            {events.length === 0 && (
              <div className="text-sm text-muted-foreground">No events yet.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
