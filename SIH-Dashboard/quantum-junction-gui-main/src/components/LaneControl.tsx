import { useState } from "react";
import { LaneData, TrafficLightState } from "./TrafficDashboard";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Car, ArrowLeft, ArrowRight, ArrowUp, MoveUp } from "lucide-react";

interface LaneControlProps {
  lane: LaneData;
  onManualOverride: (laneId: string, newLight: TrafficLightState) => void;
  disabled?: boolean;
  orientation: "horizontal" | "vertical";
}

export const LaneControl = ({ lane, onManualOverride, disabled = false, orientation }: LaneControlProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getLaneIcon = () => {
    switch (lane.type) {
      case "left": return <ArrowLeft className="w-4 h-4" />;
      case "right": return <ArrowRight className="w-4 h-4" />;
      case "straight": return <ArrowUp className="w-4 h-4" />;
      default: return <MoveUp className="w-4 h-4" />;
    }
  };

  const getProgressColor = () => {
    switch (lane.currentLight) {
      case "green": return "progress-green";
      case "yellow": return "progress-yellow";
      case "red": return "progress-red";
    }
  };

  const progressValue = ((lane.maxTime - lane.timeRemaining) / lane.maxTime) * 100;

  return (
    <div 
      className={`control-card p-4 transition-all duration-300 cursor-pointer ${
        isExpanded ? "scale-105" : ""
      } ${disabled ? "opacity-50" : ""}`}
      onClick={() => !disabled && setIsExpanded(!isExpanded)}
    >
      {/* Lane Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {getLaneIcon()}
          <span className="text-sm font-medium text-foreground">
            {lane.type.toUpperCase()}
          </span>
        </div>
        
        {/* Traffic Light */}
        <div className="flex items-center gap-1">
          <div className={`traffic-light ${
            lane.currentLight === "red" ? "traffic-light-red" : "traffic-light-inactive"
          }`}></div>
          <div className={`traffic-light ${
            lane.currentLight === "yellow" ? "traffic-light-yellow" : "traffic-light-inactive"
          }`}></div>
          <div className={`traffic-light ${
            lane.currentLight === "green" ? "traffic-light-green" : "traffic-light-inactive"
          }`}></div>
        </div>
      </div>

      {/* Vehicle Count */}
      <div className="flex items-center gap-2 mb-3">
        <Car className="w-4 h-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">×{lane.vehicleCount}</span>
      </div>

      {/* Timer & Progress */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Time Remaining</span>
          <span className="text-sm font-mono text-foreground">{lane.timeRemaining}s</span>
        </div>
        
        <Progress 
          value={progressValue}
          className="h-2"
        />
      </div>

      {/* Manual Controls - Show when expanded and not disabled */}
      {isExpanded && !disabled && (
        <div className="mt-4 pt-3 border-t border-border">
          <div className="text-xs text-muted-foreground mb-2">Manual Override</div>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant={lane.currentLight === "red" ? "destructive" : "outline"}
              className="flex-1 h-8 text-xs bg-red-600"
              onClick={(e) => {
                e.stopPropagation();
                onManualOverride(lane.id, "red");
              }}
            >
              RED
            </Button>
            <Button
              size="sm"
              variant={lane.currentLight === "yellow" ? "default" : "outline"}
              className="flex-1 h-8 text-xs bg-warning hover:bg-warning/80"
              onClick={(e) => {
                e.stopPropagation();
                onManualOverride(lane.id, "yellow");
              }}
            >
              YLW
            </Button>
            <Button
              size="sm"
              variant={lane.currentLight === "green" ? "default" : "outline"}
              className="flex-1 h-8 text-xs bg-success hover:bg-success/80"
              onClick={(e) => {
                e.stopPropagation();
                onManualOverride(lane.id, "green");
              }}
            >
              GRN
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};