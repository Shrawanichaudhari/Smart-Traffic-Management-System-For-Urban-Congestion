import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCityWebSocket } from "@/hooks/useCityWebSocket";
import { trafficApi } from "@/service/apiService";
import { Camera, Upload, Link as LinkIcon, Ambulance } from "lucide-react";

type Feed =
  | { id: string; kind: "file"; name: string; objectUrl: string }
  | { id: string; kind: "url"; name: string; url: string; persisted?: boolean };

export function CameraFeedsPage() {
  const { activeRoutes } = useCityWebSocket({ debug: false });

  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [streamUrl, setStreamUrl] = useState<string>("");

  // Load persisted feeds from backend (so navigation doesn't clear them)
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await trafficApi.getCameraFeeds();
        const saved = (res.data?.feeds ?? []) as Array<{ id: string; name: string; url: string }>;
        if (cancelled) return;
        setFeeds((prev) => {
          // Keep any locally-uploaded files already in state, but prepend persisted URL feeds.
          const files = prev.filter((f) => f.kind === "file");
          const urls: Feed[] = saved.map((f) => ({
            id: f.id,
            kind: "url",
            name: f.name,
            url: f.url,
            persisted: true,
          }));
          return [...urls, ...files];
        });
      } catch (e) {
        // Backend may be offline; keep UI functional with in-memory state.
        console.warn("Failed to load persisted camera feeds", e);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  // Clean up object URLs
  useEffect(() => {
    return () => {
      for (const f of feeds) {
        if (f.kind === "file") URL.revokeObjectURL(f.objectUrl);
      }
    };
  }, [feeds]);

  const banner = useMemo(() => {
    if (activeRoutes.length === 0) return null;
    return activeRoutes.map((r) => `${r.from_intersection} → ${r.to_intersection} (ETA ${r.eta_seconds}s)`).join(" • ");
  }, [activeRoutes]);

  const onAddVideoFile = async (file: File) => {
    // Best solution: upload to backend and store as a persisted URL feed.
    // Object URLs (URL.createObjectURL) are in-memory only and can disappear when you navigate.
    try {
      const res = await trafficApi.uploadCameraVideo({ name: file.name, file });
      const saved = res.data?.feed as { id: string; name: string; url: string } | undefined;
      if (saved?.id) {
        setFeeds((prev) => [
          { id: saved.id, kind: "url", name: saved.name, url: saved.url, persisted: true },
          ...prev,
        ]);
        return;
      }
    } catch (e) {
      console.warn("Failed to upload video to backend; falling back to local object URL (will not persist)", e);
    }

    // Fallback: local-only playback (will NOT persist across refresh/navigation).
    const objectUrl = URL.createObjectURL(file);
    setFeeds((prev) => [{ id: `${Date.now()}_${file.name}`, kind: "file", name: file.name, objectUrl }, ...prev]);
  };

  const onAddStreamUrl = async () => {
    const url = streamUrl.trim();
    if (!url) return;

    // Persist in backend so it survives navigation + refresh.
    try {
      const res = await trafficApi.addCameraFeed({ name: "Stream", url });
      const saved = res.data?.feed as { id: string; name: string; url: string } | undefined;
      if (saved?.id) {
        setFeeds((prev) => [
          { id: saved.id, kind: "url", name: saved.name, url: saved.url, persisted: true },
          ...prev,
        ]);
      } else {
        // Fallback to in-memory if backend response shape differs.
        setFeeds((prev) => [{ id: `${Date.now()}_url`, kind: "url", name: "Stream", url }, ...prev]);
      }
    } catch (e) {
      console.warn("Failed to persist camera feed; keeping locally", e);
      setFeeds((prev) => [{ id: `${Date.now()}_url`, kind: "url", name: "Stream", url }, ...prev]);
    }

    setStreamUrl("");
  };

  const removeFeed = async (id: string) => {
    const f = feeds.find((x) => x.id === id);

    // If it's a persisted URL feed, remove from backend as well.
    if (f?.kind === "url" && f.persisted) {
      try {
        await trafficApi.deleteCameraFeed(id);
      } catch (e) {
        console.warn("Failed to delete camera feed from backend", e);
      }
    }

    setFeeds((prev) => {
      const f2 = prev.find((x) => x.id === id);
      if (f2?.kind === "file") URL.revokeObjectURL(f2.objectUrl);
      return prev.filter((x) => x.id !== id);
    });
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Camera className="w-6 h-6" /> Camera Feeds
          </h2>
          <p className="text-sm text-muted-foreground">
            Visual confirmation panel. Supports uploaded video files or live stream URLs.
          </p>
        </div>

        {banner && (
          <Badge variant="destructive" className="flex items-center gap-2">
            <Ambulance className="w-4 h-4" /> {banner}
          </Badge>
        )}
      </div>

      <Card className="p-4">
        <Tabs defaultValue="upload">
          <TabsList>
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="w-4 h-4" /> Upload video
            </TabsTrigger>
            <TabsTrigger value="url" className="flex items-center gap-2">
              <LinkIcon className="w-4 h-4" /> Stream URL
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload" className="pt-4">
            <div className="space-y-2">
              <Label>Video file</Label>
              <Input
                type="file"
                accept="video/*"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) onAddVideoFile(f);
                  // reset input so selecting same file again works
                  e.currentTarget.value = "";
                }}
              />
              <div className="text-xs text-muted-foreground">
                Tip: upload a recorded intersection clip (YOLO output video works too).
              </div>
            </div>
          </TabsContent>

          <TabsContent value="url" className="pt-4">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-2">
              <div>
                <Label>Stream URL</Label>
                <Input
                  placeholder="http://localhost:8080/cam.mjpg  OR  https://.../video.mp4"
                  value={streamUrl}
                  onChange={(e) => setStreamUrl(e.target.value)}
                />
                <div className="text-xs text-muted-foreground mt-1">
                  MJPEG URLs render as <code>&lt;img&gt;</code>. MP4/HTTP video renders as <code>&lt;video&gt;</code>.
                </div>
              </div>
              <div className="flex items-end">
                <Button onClick={onAddStreamUrl}>Add</Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {feeds.map((f) => (
          <Card key={f.id} className="p-3">
            <div className="flex items-center justify-between gap-2">
              <div className="font-medium truncate">{f.name}</div>
              <Button size="sm" variant="ghost" onClick={() => removeFeed(f.id)}>
                Remove
              </Button>
            </div>

            <Separator className="my-2" />

            <div className="relative rounded overflow-hidden bg-black aspect-video">
              {activeRoutes.length > 0 && (
                <div className="absolute top-2 left-2 z-10">
                  <Badge variant="destructive" className="flex items-center gap-1">
                    <Ambulance className="w-3 h-3" /> emergency
                  </Badge>
                </div>
              )}

              {f.kind === "file" && (
                <video
                  src={f.objectUrl}
                  className="w-full h-full object-contain"
                  controls
                  muted
                  playsInline
                />
              )}

              {f.kind === "url" && (f.url.toLowerCase().includes(".mjpg") || f.url.toLowerCase().includes("mjpeg")) && (
                <img src={f.url} className="w-full h-full object-contain" />
              )}

              {f.kind === "url" && !(f.url.toLowerCase().includes(".mjpg") || f.url.toLowerCase().includes("mjpeg")) && (
                <video src={f.url} className="w-full h-full object-contain" controls muted playsInline />
              )}
            </div>
          </Card>
        ))}

        {feeds.length === 0 && (
          <Card className="p-6 text-sm text-muted-foreground">
            Add a video feed to start visual confirmation.
          </Card>
        )}
      </div>
    </div>
  );
}
