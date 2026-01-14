import { useMemo } from "react";
import type { AmbulanceRoute, CityNode } from "@/types/city";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { GoogleMap, Marker, Polyline, useJsApiLoader } from "@react-google-maps/api";

function congestionColorFromQueue(queue: number) {
  if (queue >= 35) return "bg-red-500";
  if (queue >= 18) return "bg-yellow-500";
  return "bg-green-500";
}

function totalQueue(node: CityNode) {
  return Object.values(node.direction_metrics).reduce((sum, m) => sum + (m?.queue_length ?? 0), 0);
}

function GoogleCityMap(props: {
  center: { lat: number; lng: number };
  nodes: CityNode[];
  polylines: Array<{ routeId: string; path: Array<{ lat: number; lng: number }> }>;
  heightClassName?: string;
  googleMapsApiKey: string;
}) {
  const { center, nodes, polylines, heightClassName, googleMapsApiKey } = props;
  const { isLoaded } = useJsApiLoader({ googleMapsApiKey });

  if (!isLoaded) {
    return <Card className={"p-4 " + (heightClassName ?? "h-[480px]")}>Loading map…</Card>;
  }

  return (
    <Card className={"overflow-hidden " + (heightClassName ?? "h-[480px]") }>
      <GoogleMap
        mapContainerStyle={{ width: "100%", height: "100%" }}
        center={center}
        zoom={15}
        options={{
          streetViewControl: false,
          fullscreenControl: false,
          mapTypeControl: false,
        }}
      >
        {nodes.map((n) => (
          <Marker
            key={n.intersection_id}
            position={{ lat: n.lat, lng: n.lng }}
            label={{ text: n.intersection_id, color: "#111827", fontSize: "12px" }}
          />
        ))}
        {polylines.map((pl) => (
          <Polyline
            key={pl.routeId}
            path={pl.path}
            options={{ strokeColor: "#ef4444", strokeOpacity: 0.9, strokeWeight: 5 }}
          />
        ))}
      </GoogleMap>
    </Card>
  );
}

export function CityMap(props: {
  center: { lat: number; lng: number };
  nodes: CityNode[];
  routes: AmbulanceRoute[];
  heightClassName?: string;
}) {
  const { center, nodes, routes, heightClassName } = props;

  const googleMapsApiKey = (import.meta.env.VITE_GOOGLE_MAPS_API_KEY as string | undefined) ?? "";

  const routesEnroute = useMemo(
    () => routes.filter((r) => r.status === "enroute"),
    [routes]
  );

  const nodesById = useMemo(() => {
    const m = new Map<string, CityNode>();
    for (const n of nodes) m.set(n.intersection_id, n);
    return m;
  }, [nodes]);

  const polylines = useMemo(() => {
    return routesEnroute
      .map((r) => {
        const from = nodesById.get(r.from_intersection);
        const to = nodesById.get(r.to_intersection);
        if (!from || !to) return null;
        return {
          routeId: r.route_id,
          path: [
            { lat: from.lat, lng: from.lng },
            { lat: to.lat, lng: to.lng },
          ],
        };
      })
      .filter(Boolean) as { routeId: string; path: Array<{ lat: number; lng: number }> }[];
  }, [nodesById, routesEnroute]);

  const canUseGoogle = Boolean(googleMapsApiKey);

  if (canUseGoogle) {
    return (
      <GoogleCityMap
        center={center}
        nodes={nodes}
        polylines={polylines}
        heightClassName={heightClassName}
        googleMapsApiKey={googleMapsApiKey}
      />
    );
  }

  // Fallback: simple “mini-map” without external APIs.
  if (nodes.length === 0) {
    return (
      <Card className={"p-4 " + (heightClassName ?? "h-[480px]") }>
        <div className="flex flex-col gap-2">
          <Badge variant="secondary">Map fallback</Badge>
          <div className="text-sm text-muted-foreground">
            No city nodes yet. Start the city websocket server to populate the map.
          </div>
          <div className="text-xs text-muted-foreground">
            Add <code>VITE_GOOGLE_MAPS_API_KEY</code> to enable Google Maps.
          </div>
        </div>
      </Card>
    );
  }

  const latMin = Math.min(...nodes.map((n) => n.lat));
  const latMax = Math.max(...nodes.map((n) => n.lat));
  const lngMin = Math.min(...nodes.map((n) => n.lng));
  const lngMax = Math.max(...nodes.map((n) => n.lng));

  const padding = 16;

  const toXY = (lat: number, lng: number) => {
    const x = (lng - lngMin) / (lngMax - lngMin || 1);
    const y = 1 - (lat - latMin) / (latMax - latMin || 1);
    return {
      left: `calc(${padding}px + ${x * 100}% - ${padding}px)`,
      top: `calc(${padding}px + ${y * 100}% - ${padding}px)`,
    };
  };

  return (
    <Card className={"p-4 relative " + (heightClassName ?? "h-[480px]") }>
      <div className="absolute top-3 left-3 flex flex-col gap-2">
        <Badge variant="secondary">Map fallback</Badge>
        <div className="text-xs text-muted-foreground max-w-[260px]">
          Add <code>VITE_GOOGLE_MAPS_API_KEY</code> (and install <code>@react-google-maps/api</code>)
          to enable Google Maps.
        </div>
      </div>

      {/* Route lines */}
      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
        {polylines.map((pl) => {
          const a = nodesById.get(routesEnroute.find((r) => r.route_id === pl.routeId)?.from_intersection ?? "");
          const b = nodesById.get(routesEnroute.find((r) => r.route_id === pl.routeId)?.to_intersection ?? "");
          if (!a || !b) return null;

          const ax = ((a.lng - lngMin) / (lngMax - lngMin || 1)) * 100;
          const ay = (1 - (a.lat - latMin) / (latMax - latMin || 1)) * 100;
          const bx = ((b.lng - lngMin) / (lngMax - lngMin || 1)) * 100;
          const by = (1 - (b.lat - latMin) / (latMax - latMin || 1)) * 100;

          return (
            <line
              key={pl.routeId}
              x1={ax}
              y1={ay}
              x2={bx}
              y2={by}
              stroke="#ef4444"
              strokeWidth="2"
              opacity="0.9"
            />
          );
        })}
      </svg>

      {/* Nodes */}
      <div className="absolute inset-0">
        {nodes.map((n) => {
          const q = totalQueue(n);
          const pos = toXY(n.lat, n.lng);

          return (
            <div
              key={n.intersection_id}
              className="absolute"
              style={{ left: pos.left, top: pos.top, transform: "translate(-50%, -50%)" }}
              title={`${n.name} (${n.intersection_id}) queue=${q}`}
            >
              <div className="flex items-center gap-2">
                <div className={"w-3 h-3 rounded-full " + congestionColorFromQueue(q)} />
                <div className="text-xs font-medium bg-background/80 px-2 py-1 rounded border">
                  {n.intersection_id}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
