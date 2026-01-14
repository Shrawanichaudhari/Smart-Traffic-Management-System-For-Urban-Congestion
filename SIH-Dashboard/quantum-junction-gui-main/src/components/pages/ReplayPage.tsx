import { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import type { CityUpdateMessage } from "@/types/city";

interface ReplayPageProps {
  latestCityUpdate?: CityUpdateMessage | null;
}

export const ReplayPage = ({ latestCityUpdate }: ReplayPageProps) => {
  const bufferRef = useRef<CityUpdateMessage[]>([]);

  const [isRecording, setIsRecording] = useState(true);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playIndex, setPlayIndex] = useState(0);

  // Record incoming updates
  useEffect(() => {
    if (!latestCityUpdate || !isRecording) return;

    bufferRef.current = [...bufferRef.current, latestCityUpdate].slice(-300);
    // Keep play index pinned to end when not playing
    if (!isPlaying) {
      setPlayIndex(bufferRef.current.length - 1);
    }
  }, [latestCityUpdate, isRecording, isPlaying]);

  // Playback timer
  useEffect(() => {
    if (!isPlaying) return;

    const t = setInterval(() => {
      setPlayIndex((idx) => {
        const next = idx + 1;
        const max = Math.max(0, bufferRef.current.length - 1);
        if (next >= max) {
          setIsPlaying(false);
          return max;
        }
        return next;
      });
    }, 500);

    return () => clearInterval(t);
  }, [isPlaying]);

  const buffer = bufferRef.current;
  const current = buffer.length ? buffer[Math.max(0, Math.min(playIndex, buffer.length - 1))] : null;

  const summary = useMemo(() => {
    if (!current) return null;
    const nodes = current.city.nodes;
    const worst = [...nodes]
      .sort((a: any, b: any) => (b.overall_metrics?.avg_wait_time_all_sides || 0) - (a.overall_metrics?.avg_wait_time_all_sides || 0))
      .slice(0, 2);
    return {
      nodeCount: nodes.length,
      topWorst: worst.map((n: any) => ({
        id: n.intersection_id,
        wait: n.overall_metrics?.avg_wait_time_all_sides,
      })),
    };
  }, [current]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-primary">Event Replay</h1>
          <p className="text-muted-foreground">Browser-side replay of recent city updates (no DB needed).</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">Buffer: {buffer.length}/300</Badge>
          <Button variant={isRecording ? "default" : "outline"} onClick={() => setIsRecording((v) => !v)}>
            {isRecording ? "Recording" : "Paused"}
          </Button>
          <Button
            variant={isPlaying ? "default" : "outline"}
            onClick={() => setIsPlaying((v) => !v)}
            disabled={buffer.length < 2}
          >
            {isPlaying ? "Stop" : "Play"}
          </Button>
        </div>
      </div>

      <Card className="control-card">
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Slider
            value={[playIndex]}
            onValueChange={(v) => {
              setIsPlaying(false);
              setPlayIndex(v[0] ?? 0);
            }}
            max={Math.max(0, buffer.length - 1)}
            step={1}
          />
          <div className="text-sm text-muted-foreground">
            {current ? `Snapshot: ${playIndex + 1}/${buffer.length} • ${current.timestamp}` : "No snapshots yet"}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="control-card">
          <CardHeader>
            <CardTitle>City summary (replayed)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {!summary ? (
              <div className="text-sm text-muted-foreground">Waiting for data…</div>
            ) : (
              <>
                <div>Nodes: {summary.nodeCount}</div>
                <div className="text-sm text-muted-foreground">Worst wait (approx):</div>
                <div className="space-y-2">
                  {summary.topWorst.map((n) => (
                    <div key={n.id} className="rounded-md border p-2">
                      <div className="font-medium">{n.id}</div>
                      <div className="text-xs text-muted-foreground">Avg wait: {n.wait}</div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>

        <Card className="control-card">
          <CardHeader>
            <CardTitle>Event tail (replayed)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(current?.event_log_tail || []).length === 0 ? (
              <div className="text-sm text-muted-foreground">No events</div>
            ) : (
              <div className="space-y-2 max-h-[360px] overflow-auto">
                {current?.event_log_tail?.map((e: any, idx: number) => (
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
  );
};
