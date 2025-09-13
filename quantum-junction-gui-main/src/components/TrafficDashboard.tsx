import { useState, useEffect } from "react";
import { NavigationSidebar } from "./NavigationSidebar";
import { DashboardPage } from "./pages/DashboardPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SystemConfigPage } from "./pages/SystemConfigPage";
import { useToast } from "@/hooks/use-toast";

export type TrafficLightState = "red" | "yellow" | "green";
export type ControlMode = "ai" | "manual" | "emergency";

export interface LaneData {
  id: string;
  direction: "north" | "south" | "east" | "west";
  type: "straight" | "left" | "right";
  vehicleCount: number;
  currentLight: TrafficLightState;
  timeRemaining: number;
  maxTime: number;
}

export const TrafficDashboard = () => {
  const { toast } = useToast();
  const [controlMode, setControlMode] = useState<ControlMode>("ai");
  const [showEmergencyPanel, setShowEmergencyPanel] = useState(false);
  const [currentPage, setCurrentPage] = useState("dashboard");
  
  // Sample lane data - in real app this would come from sensors/API
  const [lanes, setLanes] = useState<LaneData[]>([
    // North lanes
    { id: "n-straight", direction: "north", type: "straight", vehicleCount: 8, currentLight: "green", timeRemaining: 25, maxTime: 30 },
   
    // South lanes
    { id: "s-straight", direction: "south", type: "straight", vehicleCount: 12, currentLight: "red", timeRemaining: 35, maxTime: 45 },
    
    
    // East lanes  
    { id: "e-straight", direction: "east", type: "straight", vehicleCount: 15, currentLight: "red", timeRemaining: 15, maxTime: 45 },
    
    
    // West lanes
    { id: "w-straight", direction: "west", type: "straight", vehicleCount: 9, currentLight: "red", timeRemaining: 20, maxTime: 45 },
    
  ]);

  useEffect(() => {
    // Simulate traffic flow changes
    const trafficInterval = setInterval(() => {
      setLanes(prevLanes => {
        return prevLanes.map(lane => {
          // Increase vehicle count slightly
          const newVehicleCount = Math.max(0, lane.vehicleCount + Math.floor(Math.random() * 4) - 1);

          // Logic to change lights based on control mode and vehicle count
          if (controlMode === "ai") {
            // Simple AI: if a lane has more than 10 vehicles, turn green
            if (newVehicleCount > 10 && lane.currentLight !== "green") {
              return { ...lane, currentLight: "green", timeRemaining: lane.maxTime };
            } else if (lane.currentLight === "green" && lane.timeRemaining > 0) {
              return { ...lane, timeRemaining: lane.timeRemaining - 1 };
            } else if (lane.currentLight === "green") {
              return { ...lane, currentLight: "red", timeRemaining: lane.maxTime };
            }
          }

          return { ...lane, vehicleCount: newVehicleCount };
        });
      });
    }, 5000); // Update every 5 seconds

    return () => clearInterval(trafficInterval);
  }, [controlMode]);

  const handleManualOverride = (laneId: string, newLight: TrafficLightState) => {
    if (controlMode === "ai") {
      setControlMode("manual");
      toast({
        title: "Manual Override Activated",
        description: "You are now controlling traffic signals manually.",
        variant: "default",
      });
    }
    
    setLanes(prevLanes =>
      prevLanes.map(lane =>
        lane.id === laneId
          ? { ...lane, currentLight: newLight, timeRemaining: 30 }
          : lane
      )
    );
  };

  const handleEmergencyOverride = (laneId: string) => {
    setControlMode("emergency");
    setShowEmergencyPanel(false);
    
    setLanes(prevLanes =>
      prevLanes.map(lane => ({
        ...lane,
        currentLight: lane.id === laneId ? "green" : "red",
        timeRemaining: lane.id === laneId ? 60 : 60
      }))
    );
    
    toast({
      title: "🚨 Emergency Override Active",
      description: `Emergency route cleared for ${laneId}`,
      variant: "destructive",
    });
  };

  const returnToAI = () => {
    setControlMode("ai");
    toast({
      title: "AI Control Restored",
      description: "Traffic signals returned to AI management.",
      variant: "default",
    });
  };

  const renderCurrentPage = () => {
    switch (currentPage) {
      case "dashboard":
        return (
          <DashboardPage
            lanes={lanes}
            controlMode={controlMode}
            onManualOverride={handleManualOverride}
            onEmergencyOverride={handleEmergencyOverride}
            onReturnToAI={returnToAI}
            showEmergencyPanel={showEmergencyPanel}
            setShowEmergencyPanel={setShowEmergencyPanel}
          />
        );
      case "analytics":
        return <AnalyticsPage lanes={lanes} />;
      case "system":
        return <SystemConfigPage />;
      default:
        return (
          <DashboardPage
            lanes={lanes}
            controlMode={controlMode}
            onManualOverride={handleManualOverride}
            onEmergencyOverride={handleEmergencyOverride}
            onReturnToAI={returnToAI}
            showEmergencyPanel={showEmergencyPanel}
            setShowEmergencyPanel={setShowEmergencyPanel}
          />
        );
    }
  };

  return (
    <div className="min-h-screen flex w-full">
      {/* Navigation Sidebar */}
      <NavigationSidebar 
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {renderCurrentPage()}
      </div>
    </div>
  );
};
