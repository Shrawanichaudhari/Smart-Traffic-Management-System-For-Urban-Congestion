import { LaneData, TrafficLightState, ControlMode } from "./TrafficDashboard";
import { LaneControl } from "./LaneControl";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from "lucide-react";

interface IntersectionViewProps {
  lanes: LaneData[];
  onManualOverride: (laneId: string, newLight: TrafficLightState) => void;
  controlMode: ControlMode;
}

export const IntersectionView = ({ lanes, onManualOverride, controlMode }: IntersectionViewProps) => {
  const getLanesByDirection = (direction: string) => 
    lanes.filter(lane => lane.direction === direction);

  const getDirectionIcon = (direction: string) => {
    switch (direction) {
      case "north": return <ArrowUp className="w-6 h-6" />;
      case "south": return <ArrowDown className="w-6 h-6" />;
      case "east": return <ArrowRight className="w-6 h-6" />;
      case "west": return <ArrowLeft className="w-6 h-6" />;
      default: return null;
    }
  };

  return (
    <div className="control-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-3 h-3 rounded-full bg-primary glow-primary"></div>
        <h2 className="text-xl font-semibold text-foreground">
          4-Way Intersection Control
        </h2>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
          controlMode === "ai" ? "bg-primary/20 text-primary" :
          controlMode === "manual" ? "bg-warning/20 text-warning" :
          "bg-destructive/20 text-destructive"
        }`}>
          {controlMode.toUpperCase()} MODE
        </div>
      </div>

      {/* Intersection Grid */}
      <div className="grid grid-cols-3 gap-4 max-w-4xl mx-auto">
        {/* Top Row - North */}
        <div></div>
        <div className="space-y-4">
          <div className="flex items-center justify-center gap-2 text-primary font-medium">
            {getDirectionIcon("north")}
            <span>NORTH</span>
          </div>
          <div className="space-y-3">
            {getLanesByDirection("north").map(lane => (
              <LaneControl
                key={lane.id}
                lane={lane}
                onManualOverride={onManualOverride}
                disabled={controlMode === "emergency"}
                orientation="vertical"
              />
            ))}
          </div>
        </div>
        <div></div>

        {/* Middle Row - West & Center & East */}
        <div className="space-y-4">
          <div className="flex items-center justify-center gap-2 text-primary font-medium">
            {getDirectionIcon("west")}
            <span>WEST</span>
          </div>
          <div className="space-y-3">
            {getLanesByDirection("west").map(lane => (
              <LaneControl
                key={lane.id}
                lane={lane}
                onManualOverride={onManualOverride}
                disabled={controlMode === "emergency"}
                orientation="horizontal"
              />
            ))}
          </div>
        </div>

        {/* Center Intersection */}
        <div className="flex items-center justify-center">
          <div className="w-32 h-32 border-4 border-primary/30 rounded-lg flex items-center justify-center bg-muted/20">
            <div className="text-center">
              <div className="w-8 h-8 bg-primary/20 rounded-full mx-auto mb-2"></div>
              <span className="text-xs text-muted-foreground">INTERSECTION</span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-center gap-2 text-primary font-medium">
            {getDirectionIcon("east")}
            <span>EAST</span>
          </div>
          <div className="space-y-3">
            {getLanesByDirection("east").map(lane => (
              <LaneControl
                key={lane.id}
                lane={lane}
                onManualOverride={onManualOverride}
                disabled={controlMode === "emergency"}
                orientation="horizontal"
              />
            ))}
          </div>
        </div>

        {/* Bottom Row - South */}
        <div></div>
        <div className="space-y-4">
          <div className="space-y-3">
            {getLanesByDirection("south").map(lane => (
              <LaneControl
                key={lane.id}
                lane={lane}
                onManualOverride={onManualOverride}
                disabled={controlMode === "emergency"}
                orientation="vertical"
              />
            ))}
          </div>
          <div className="flex items-center justify-center gap-2 text-primary font-medium">
            {getDirectionIcon("south")}
            <span>SOUTH</span>
          </div>
        </div>
        <div></div>
      </div>
    </div>
  );
};