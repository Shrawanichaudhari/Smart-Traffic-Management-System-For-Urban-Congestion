import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { GoogleCityMap } from "@/components/GoogleCityMap";
import type { CityNode } from "@/types/city";

interface CityPageProps {
  cityId: string | null;
  center: { lat: number; lng: number };
  nodes: CityNode[];
  selectedIntersectionId: string | null;
  onSelectIntersection: (id: string) => void;
  incidents: any[];
  ambulanceRoutes: any[];
  eventLogTail?: any[];

  // Actions
  dispatchAmbulance: (fromIntersection: string, toIntersection: string, etaSeconds?: number) => void;
  createIncident: (intersectionId: string, direction: string, incidentType?: string, severity?: number) => void;
  clearIncident: (incidentId: string) => void;
}

export const CityPage = ({
  cityId,
  center,
  nodes,
  selectedIntersectionId,
  onSelectIntersection,
  incidents,
  ambulanceRoutes,
  eventLogTail,
  dispatchAmbulance,
  createIncident,
  clearIncident,
}: CityPageProps) => {
  const [fromNode, setFromNode] = useState<string>("INT_A");
  const [toNode, setToNode] = useState<string>("INT_B");
  const [eta, setEta] = useState<number>(30);
  const [incidentDirection, setIncidentDirection] = useState<string>("east");

  const nodeOptions = useMemo(() => nodes.map((n) => n.intersection_id), [nodes]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-primary">City Control Center</h1>
          <p className="text-muted-foreground">Multi-node traffic network, corridor preemption, and incident workflow</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline">City: {cityId ?? "--"}</Badge>
          <div className="w-[260px]">
            <Select value={selectedIntersectionId ?? undefined} onValueChange={onSelectIntersection}>
              <SelectTrigger>
                <SelectValue placeholder="Select intersection" />
              </SelectTrigger>
              <SelectContent>
                {nodes.map((n) => (
                  <SelectItem key={n.intersection_id} value={n.intersection_id}>
                    {n.name} ({n.intersection_id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          <Card className="control-card">
            <CardHeader>
              <CardTitle>City Map (Google)</CardTitle>
            </CardHeader>
            <CardContent>
              <GoogleCityMap
                center={center}
                nodes={nodes}
                selectedIntersectionId={selectedIntersectionId}
                onSelectNode={onSelectIntersection}
                ambulanceRoutes={ambulanceRoutes}
              />
              <p className="text-xs text-muted-foreground mt-2">
                Corridor is shown as a red line while an ambulance route is enroute.
              </p>
            </CardContent>
          </Card>

          <Card className="control-card">
            <CardHeader>
              <CardTitle>Incident Workflow (demo)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Intersection</Label>
                  <Select value={selectedIntersectionId ?? undefined} onValueChange={onSelectIntersection}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select" />
                    </SelectTrigger>
                    <SelectContent>
                      {nodes.map((n) => (
                        <SelectItem key={n.intersection_id} value={n.intersection_id}>
                          {n.name} ({n.intersection_id})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Direction</Label>
                  <Select
                    value={incidentDirection}
                    onValueChange={(val) => {
                      setIncidentDirection(val);
                      createIncident(selectedIntersectionId ?? "INT_A", val, "accident", 2);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Choose" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="north">north</SelectItem>
                      <SelectItem value="south">south</SelectItem>
                      <SelectItem value="east">east</SelectItem>
                      <SelectItem value="west">west</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">Selecting a direction creates an accident event.</p>
                </div>

                <div className="space-y-2">
                  <Label>Quick actions</Label>
                  <Button
                    className="w-full"
                    onClick={() => createIncident(selectedIntersectionId ?? "INT_A", "east", "accident", 2)}
                  >
                    Create Accident (East)
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Active incidents</Label>
                <div className="space-y-2">
                  {(incidents || []).length === 0 ? (
                    <div className="text-sm text-muted-foreground">No active incidents</div>
                  ) : (
                    incidents.map((i: any) => (
                      <div key={i.incident_id} className="flex items-center justify-between rounded-md border p-3">
                        <div>
                          <div className="font-medium">
                            {i.incident_type} @ {i.intersection_id} ({i.direction})
                          </div>
                          <div className="text-xs text-muted-foreground">Severity: {i.severity} • {i.created_at}</div>
                        </div>
                        <Button variant="outline" onClick={() => clearIncident(i.incident_id)}>
                          Clear
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="xl:col-span-1 space-y-6">
          <Card className="control-card">
            <CardHeader>
              <CardTitle>Ambulance Corridor (Node A → Node B)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>From</Label>
                  <Select value={fromNode} onValueChange={setFromNode}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {nodeOptions.map((id) => (
                        <SelectItem key={id} value={id}>
                          {id}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>To</Label>
                  <Select value={toNode} onValueChange={setToNode}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {nodeOptions.map((id) => (
                        <SelectItem key={id} value={id}>
                          {id}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>ETA seconds</Label>
                <Input type="number" value={eta} onChange={(e) => setEta(Number(e.target.value))} />
              </div>

              <Button className="w-full" onClick={() => dispatchAmbulance(fromNode, toNode, eta)}>
                Dispatch ambulance
              </Button>

              <div className="space-y-2">
                <Label>Active routes</Label>
                {(ambulanceRoutes || []).length === 0 ? (
                  <div className="text-sm text-muted-foreground">No routes</div>
                ) : (
                  <div className="space-y-2">
                    {ambulanceRoutes.map((r: any) => (
                      <div key={r.route_id} className="rounded-md border p-3">
                        <div className="font-medium">
                          {r.from_intersection} → {r.to_intersection}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Status: {r.status} • ETA: {r.eta_seconds}s
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="control-card">
            <CardHeader>
              <CardTitle>Live Event Tail</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(eventLogTail || []).length === 0 ? (
                <div className="text-sm text-muted-foreground">No events yet</div>
              ) : (
                <div className="space-y-2 max-h-[360px] overflow-auto">
                  {eventLogTail.map((e: any, idx: number) => (
                    <div key={idx} className="text-xs rounded-md border p-2">
                      <div className="font-medium">{e.type}</div>
                      <div className="text-muted-foreground">{e.timestamp}</div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
