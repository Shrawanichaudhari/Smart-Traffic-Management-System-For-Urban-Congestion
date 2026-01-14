import { useState } from "react";
import { LaneData, TrafficLightState, ControlMode } from "./TrafficDashboard";
import { LaneControl } from "./LaneControl";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  ArrowUp, 
  ArrowDown, 
  ArrowLeft, 
  ArrowRight, 
  Settings, 
  Timer,
  PlayCircle,
  PauseCircle,
  RefreshCw
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface EnhancedIntersectionViewProps {
  lanes: LaneData[];
  onManualOverride: (laneId: string, newLight: TrafficLightState) => void;
  controlMode: ControlMode;
}

export const EnhancedIntersectionView = ({ 
  lanes, 
  onManualOverride, 
  controlMode 
}: EnhancedIntersectionViewProps) => {
  const { toast } = useToast();
  const [selectedDirection, setSelectedDirection] = useState<string>("north");
  const [phaseTime, setPhaseTime] = useState(30);
  const [cycleTime, setCycleTime] = useState(120);
  const [isTimingPaused, setIsTimingPaused] = useState(false);

  const getLanesByDirection = (direction: string) => 
    lanes.filter(lane => lane.direction === direction);

  const getDirectionIcon = (direction: string) => {
    switch (direction) {
      case "north": return <ArrowUp className="w-5 h-5" />;
      case "south": return <ArrowDown className="w-5 h-5" />;
      case "east": return <ArrowRight className="w-5 h-5" />;
      case "west": return <ArrowLeft className="w-5 h-5" />;
      default: return null;
    }
  };

  const directions = ["north", "south", "east", "west"];

  const handlePhaseTimeUpdate = () => {
    toast({
      title: "Phase Time Updated",
      description: `${selectedDirection.toUpperCase()} direction phase set to ${phaseTime} seconds`,
      variant: "default",
    });
  };

  const handleCycleTimeUpdate = () => {
    toast({
      title: "Cycle Time Updated", 
      description: `Total cycle time set to ${cycleTime} seconds`,
      variant: "default",
    });
  };

  const toggleTiming = () => {
    setIsTimingPaused(!isTimingPaused);
    toast({
      title: isTimingPaused ? "Timing Resumed" : "Timing Paused",
      description: isTimingPaused ? "Signal timing has resumed" : "Signal timing has been paused",
      variant: "default",
    });
  };

  return (
    <div className="space-y-6">
      {/* Intersection Control Header */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-primary glow-primary"></div>
            Enhanced 4-Way Intersection Control
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              controlMode === "ai" ? "bg-primary/20 text-primary" :
              controlMode === "manual" ? "bg-warning/20 text-warning" :
              "bg-destructive/20 text-destructive"
            }`}>
              {controlMode.toUpperCase()} MODE
            </div>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Main Control Tabs */}
      <Tabs defaultValue="intersection" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="intersection">Intersection View</TabsTrigger>
          <TabsTrigger value="timing">Timing Control</TabsTrigger>
          <TabsTrigger value="remote">Remote Control</TabsTrigger>
        </TabsList>

        {/* Intersection View Tab */}
        <TabsContent value="intersection">
          <Card className="control-card">
            <CardContent className="p-6">
              {/* Intersection Grid */}
              <div className="grid grid-cols-3 gap-6 max-w-5xl mx-auto">
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
                  <div className="w-40 h-40 border-4 border-primary/30 rounded-lg flex items-center justify-center bg-muted/20 relative">
                    <div className="text-center">
                      <div className="w-10 h-10 bg-primary/20 rounded-full mx-auto mb-2 flex items-center justify-center">
                        <div className="w-6 h-6 bg-primary/40 rounded-full"></div>
                      </div>
                      <span className="text-xs text-muted-foreground">INTERSECTION</span>
                    </div>
                    {/* Traffic flow indicators */}
                    <div className="absolute inset-0 opacity-30">
                      <div className="absolute top-2 left-1/2 w-1 h-8 bg-primary/60 transform -translate-x-1/2"></div>
                      <div className="absolute bottom-2 left-1/2 w-1 h-8 bg-primary/60 transform -translate-x-1/2"></div>
                      <div className="absolute left-2 top-1/2 h-1 w-8 bg-primary/60 transform -translate-y-1/2"></div>
                      <div className="absolute right-2 top-1/2 h-1 w-8 bg-primary/60 transform -translate-y-1/2"></div>
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
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timing Control Tab */}
        <TabsContent value="timing">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="control-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-primary">
                  <Timer className="w-5 h-5" />
                  Phase Time Management
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="direction">Select Direction</Label>
                  <Select value={selectedDirection} onValueChange={setSelectedDirection}>
                    <SelectTrigger className="bg-muted/20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {directions.map(direction => (
                        <SelectItem key={direction} value={direction}>
                          <div className="flex items-center gap-2">
                            {getDirectionIcon(direction)}
                            {direction.toUpperCase()}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="phase-time">Phase Duration (seconds)</Label>
                  <Input
                    id="phase-time"
                    type="number"
                    value={phaseTime}
                    onChange={(e) => setPhaseTime(Number(e.target.value))}
                    className="bg-muted/20"
                    min="10"
                    max="180"
                  />
                </div>

                <Button onClick={handlePhaseTimeUpdate} className="w-full">
                  <Settings className="w-4 h-4 mr-2" />
                  Update Phase Time
                </Button>
              </CardContent>
            </Card>

            <Card className="control-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-primary">
                  <RefreshCw className="w-5 h-5" />
                  Cycle Management
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="cycle-time">Total Cycle Time (seconds)</Label>
                  <Input
                    id="cycle-time"
                    type="number"
                    value={cycleTime}
                    onChange={(e) => setCycleTime(Number(e.target.value))}
                    className="bg-muted/20"
                    min="60"
                    max="300"
                  />
                </div>

                <div className="flex gap-2">
                  <Button onClick={handleCycleTimeUpdate} className="flex-1">
                    Update Cycle
                  </Button>
                  <Button 
                    onClick={toggleTiming} 
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    {isTimingPaused ? (
                      <PlayCircle className="w-4 h-4" />
                    ) : (
                      <PauseCircle className="w-4 h-4" />
                    )}
                    {isTimingPaused ? "Resume" : "Pause"}
                  </Button>
                </div>

                <div className="mt-4 p-3 bg-muted/20 rounded-lg">
                  <div className="text-sm text-muted-foreground mb-2">Current Status</div>
                  <div className="text-lg font-semibold text-foreground">
                    {isTimingPaused ? "Timing Paused" : "Active Cycle"}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Remote Control Tab */}
        <TabsContent value="remote">
          <Card className="control-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-primary">
                <Settings className="w-5 h-5" />
                Remote Signal Control
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                {directions.map(direction => {
                  const directionLanes = getLanesByDirection(direction);
                  return (
                    <div key={direction} className="space-y-4">
                      <div className="flex items-center gap-2 text-primary font-medium">
                        {getDirectionIcon(direction)}
                        <span>{direction.toUpperCase()}</span>
                      </div>
                      <div className="space-y-2">
                        {directionLanes.map(lane => (
                          <div key={lane.id} className="p-3 bg-muted/20 rounded-lg">
                            <div className="text-xs text-muted-foreground mb-1">
                              {lane.type.toUpperCase()}
                            </div>
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant={lane.currentLight === "red" ? "destructive" : "outline"}
                                onClick={() => onManualOverride(lane.id, "red")}
                                className="flex-1 h-8 text-xs"
                              >
                                RED
                              </Button>
                              <Button
                                size="sm"
                                variant={lane.currentLight === "yellow" ? "default" : "outline"}
                                onClick={() => onManualOverride(lane.id, "yellow")}
                                className="flex-1 h-8 text-xs bg-warning/20 border-warning text-warning hover:bg-warning/30"
                              >
                                YLW
                              </Button>
                              <Button
                                size="sm"
                                variant={lane.currentLight === "green" ? "default" : "outline"}
                                onClick={() => onManualOverride(lane.id, "green")}
                                className="flex-1 h-8 text-xs bg-success/20 border-success text-success hover:bg-success/30"
                              >
                                GRN
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};