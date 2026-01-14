import { useState } from "react";
import { LaneData } from "./TrafficDashboard";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Card, CardContent } from "@/components/ui/card";
import { AlertTriangle, Zap } from "lucide-react";

interface EmergencyOverrideProps {
  onEmergencyActivate: () => void;
  showPanel: boolean;
  onPanelClose: () => void;
  onLaneSelect: (laneId: string) => void;
  lanes: LaneData[];
}

export const EmergencyOverride = ({ 
  onEmergencyActivate, 
  showPanel, 
  onPanelClose, 
  onLaneSelect, 
  lanes 
}: EmergencyOverrideProps) => {
  const [selectedLane, setSelectedLane] = useState<string>("");

  const handleConfirm = () => {
    if (selectedLane) {
      onLaneSelect(selectedLane);
      setSelectedLane("");
    }
  };

  const groupedLanes = lanes.reduce((acc, lane) => {
    if (!acc[lane.direction]) {
      acc[lane.direction] = [];
    }
    acc[lane.direction].push(lane);
    return acc;
  }, {} as Record<string, LaneData[]>);

  return (
    <>
      {/* Emergency Button */}
      <Button
        onClick={onEmergencyActivate}
        className="emergency-btn text-white font-bold px-6 py-3 text-lg"
        size="lg"
      >
        <AlertTriangle className="w-5 h-5 mr-2" />
        EMERGENCY OVERRIDE
      </Button>

      {/* Emergency Selection Dialog */}
      <Dialog open={showPanel} onOpenChange={onPanelClose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <Zap className="w-5 h-5" />
              Emergency Override Activation
            </DialogTitle>
            <DialogDescription>
              Select the lane to clear for emergency vehicles. All other lanes will be set to RED.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {Object.entries(groupedLanes).map(([direction, directionLanes]) => (
              <Card key={direction} className="border-border/50">
                <CardContent className="p-4">
                  <h3 className="font-semibold text-primary mb-3 uppercase">
                    {direction}
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    {directionLanes.map((lane) => (
                      <Button
                        key={lane.id}
                        variant={selectedLane === lane.id ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSelectedLane(lane.id)}
                        className={`${
                          selectedLane === lane.id 
                            ? "bg-destructive text-destructive-foreground" 
                            : "border-border hover:bg-muted"
                        }`}
                      >
                        <div className="text-center">
                          <div className="text-xs font-medium">
                            {lane.type.toUpperCase()}
                          </div>
                          <div className="text-xs opacity-70">
                            🚗 ×{lane.vehicleCount}
                          </div>
                        </div>
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="flex justify-between pt-4">
            <Button variant="outline" onClick={onPanelClose}>
              Cancel
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={!selectedLane}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground"
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              Activate Emergency Override
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};