import { useEffect, useMemo, useRef } from "react";
import type { CityNode, AmbulanceRoute } from "@/types/city";

declare global {
  interface Window {
    google?: any;
  }
}

function loadGoogleMaps(apiKey: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.google?.maps) {
      resolve();
      return;
    }

    const existing = document.querySelector("script[data-google-maps]");
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject(new Error("Failed to load Google Maps")));
      return;
    }

    const script = document.createElement("script");
    script.dataset.googleMaps = "true";
    script.async = true;
    script.defer = true;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(apiKey)}`;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Maps"));
    document.head.appendChild(script);
  });
}

interface GoogleCityMapProps {
  center: { lat: number; lng: number };
  nodes: CityNode[];
  selectedIntersectionId?: string | null;
  onSelectNode?: (id: string) => void;
  ambulanceRoutes?: AmbulanceRoute[];
}

export const GoogleCityMap = ({
  center,
  nodes,
  selectedIntersectionId,
  onSelectNode,
  ambulanceRoutes = [],
}: GoogleCityMapProps) => {
  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const polylinesRef = useRef<any[]>([]);

  const apiKey = (import.meta as any).env?.VITE_GOOGLE_MAPS_API_KEY as string | undefined;

  const nodeById = useMemo(() => {
    const m = new Map<string, CityNode>();
    nodes.forEach((n) => m.set(n.intersection_id, n));
    return m;
  }, [nodes]);

  useEffect(() => {
    if (!mapDivRef.current) return;

    // Without a key, render a placeholder.
    if (!apiKey) {
      return;
    }

    let cancelled = false;

    loadGoogleMaps(apiKey)
      .then(() => {
        if (cancelled) return;

        if (!mapRef.current) {
          mapRef.current = new window.google.maps.Map(mapDivRef.current, {
            center,
            zoom: 15,
            mapTypeId: "roadmap",
            disableDefaultUI: false,
          });
        }

        // Clear old markers
        markersRef.current.forEach((m) => m.setMap(null));
        markersRef.current = [];

        nodes.forEach((n) => {
          const isSelected = selectedIntersectionId && n.intersection_id === selectedIntersectionId;

          const marker = new window.google.maps.Marker({
            map: mapRef.current,
            position: { lat: n.lat, lng: n.lng },
            title: `${n.name} (${n.intersection_id})`,
            label: {
              text: n.intersection_id.replace("INT_", ""),
              color: isSelected ? "#ffffff" : "#111827",
              fontWeight: "bold",
            },
            icon: isSelected
              ? {
                  path: window.google.maps.SymbolPath.CIRCLE,
                  scale: 12,
                  fillColor: "#2563eb",
                  fillOpacity: 1,
                  strokeColor: "#ffffff",
                  strokeWeight: 2,
                }
              : {
                  path: window.google.maps.SymbolPath.CIRCLE,
                  scale: 10,
                  fillColor: "#f59e0b",
                  fillOpacity: 0.9,
                  strokeColor: "#111827",
                  strokeWeight: 1,
                },
          });

          marker.addListener("click", () => {
            onSelectNode?.(n.intersection_id);
          });

          markersRef.current.push(marker);
        });

        // Clear old polylines
        polylinesRef.current.forEach((p) => p.setMap(null));
        polylinesRef.current = [];

        // Draw ambulance corridor lines
        ambulanceRoutes
          .filter((r) => r.status === "enroute")
          .forEach((r) => {
            const from = nodeById.get(r.from_intersection);
            const to = nodeById.get(r.to_intersection);
            if (!from || !to) return;

            const line = new window.google.maps.Polyline({
              map: mapRef.current,
              path: [
                { lat: from.lat, lng: from.lng },
                { lat: to.lat, lng: to.lng },
              ],
              geodesic: true,
              strokeColor: "#ef4444",
              strokeOpacity: 0.9,
              strokeWeight: 5,
            });
            polylinesRef.current.push(line);
          });
      })
      .catch(() => {
        // Ignore, placeholder will show below.
      });

    return () => {
      cancelled = true;
    };
  }, [apiKey, center, nodes, selectedIntersectionId, onSelectNode, ambulanceRoutes, nodeById]);

  if (!apiKey) {
    return (
      <div className="h-[420px] rounded-md border border-border bg-muted/20 flex items-center justify-center p-6 text-sm text-muted-foreground">
        Google Maps API key not set. Create a `.env.local` file with `VITE_GOOGLE_MAPS_API_KEY=...`.
      </div>
    );
  }

  return <div ref={mapDivRef} className="h-[420px] w-full rounded-md border border-border" />;
};
