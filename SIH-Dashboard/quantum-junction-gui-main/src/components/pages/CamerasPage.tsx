import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { CityNode } from "@/types/city";

type SourceType = "file" | "url";

interface FeedConfig {
  sourceType: SourceType;
  url?: string;
  fileUrl?: string;
}

const DIRECTIONS = ["north", "south", "east", "west"] as const;

interface CamerasPageProps {
  nodes: CityNode[];
  selectedIntersectionId: string | null;
  onSelectIntersection: (id: string) => void;
}

export const CamerasPage = ({ nodes, selectedIntersectionId, onSelectIntersection }: CamerasPageProps) => {
  const [feeds, setFeeds] = useState<Record<string, FeedConfig>>(() => ({
    north: { sourceType: "file" },
    south: { sourceType: "file" },
    east: { sourceType: "file" },
    west: { sourceType: "file" },
  }));

  const selectedNode = useMemo(
    () => nodes.find((n) => n.intersection_id === selectedIntersectionId),
    [nodes, selectedIntersectionId]
  );

  const setFeed = (dir: string, patch: Partial<FeedConfig>) => {
    setFeeds((prev) => ({
      ...prev,
      [dir]: { ...prev[dir], ...patch },
    }));
  };

  const onPickFile = (dir: string, file?: File | null) => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    setFeed(dir, { fileUrl: url, sourceType: "file" });
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-primary">Live Camera Verification</h1>
          <p className="text-muted-foreground">
            Demo mode: use local video files now; add stream URLs when available.
          </p>
        </div>
        <div className="w-[280px]">
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

      <Card className="control-card">
        <CardHeader>
          <CardTitle>Selected node: {selectedNode ? `${selectedNode.name} (${selectedNode.intersection_id})` : "--"}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {DIRECTIONS.map((dir) => {
              const cfg = feeds[dir];
              const previewUrl = cfg.sourceType === "file" ? cfg.fileUrl : cfg.url;

              return (
                <div key={dir} className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="font-medium capitalize">{dir} camera</div>
                    <Select value={cfg.sourceType} onValueChange={(v) => setFeed(dir, { sourceType: v as SourceType })}>
                      <SelectTrigger className="w-[140px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="file">File</SelectItem>
                        <SelectItem value="url">URL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {cfg.sourceType === "file" ? (
                    <div className="space-y-2">
                      <Label>Choose MP4/WEBM file</Label>
                      <Input
                        type="file"
                        accept="video/*"
                        onChange={(e) => onPickFile(dir, e.target.files?.[0])}
                      />
                      <p className="text-xs text-muted-foreground">
                        Tip: use small clips (10–30s) for fast testing.
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Label>Stream URL (HTTP)</Label>
                      <Input
                        placeholder="https://... (mp4/webm/mjpeg)"
                        value={cfg.url || ""}
                        onChange={(e) => setFeed(dir, { url: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground">
                        RTSP does not play directly in browsers. For RTSP cameras you typically need a proxy converting
                        RTSP → HLS/MJPEG.
                      </p>
                    </div>
                  )}

                  <div className="rounded-md border border-border bg-muted/10 p-2">
                    {previewUrl ? (
                      cfg.sourceType === "url" && previewUrl.toLowerCase().includes(".mjpg") ? (
                        <img src={previewUrl} className="w-full h-[220px] object-cover rounded" />
                      ) : (
                        <video
                          src={previewUrl}
                          className="w-full h-[220px] object-cover rounded"
                          controls
                          muted
                          playsInline
                        />
                      )
                    ) : (
                      <div className="h-[220px] flex items-center justify-center text-sm text-muted-foreground">
                        No feed selected
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
