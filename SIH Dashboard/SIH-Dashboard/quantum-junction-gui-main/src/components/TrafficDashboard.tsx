import { useState, useEffect } from "react";
import { NavigationSidebar } from "./NavigationSidebar";
import { DashboardPage } from "./pages/DashboardPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SystemConfigPage } from "./pages/SystemConfigPage";
import { useToast } from "@/hooks/use-toast";
import { useCityData } from "@/hooks/useCityData";

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
  
  // Get real-time multi-node city data from backend
  const {
    city,
    nodes,
    selectedIntersectionId,
    setSelectedIntersectionId,
    lanes,
    simulationData,
    incidents,
    ambulanceRoutes,
    isConnected,
    error,
    lastUpdateTime,
    dispatchAmbulance,
    createIncident,
    clearIncident,
  } = useCityData();

  // Convert enhanced lane data to existing LaneData format for compatibility
  const convertedLanes: LaneData[] = lanes.map((lane) => ({
    id: lane.id,
    direction: lane.direction,
    type: lane.type,
    vehicleCount: lane.vehicleCount,
    currentLight: lane.currentLight,
    timeRemaining: lane.timeRemaining,
    maxTime: lane.maxTime,
  }));

  // Show connection status and error notifications
  useEffect(() => {
    if (error) {
      toast({
        title: "Connection Error",
        description: error,
        variant: "destructive",
      });
    }
  }, [error, toast]);
  
  useEffect(() => {
    if (isConnected && lastUpdateTime) {
      toast({
        title: "🔗 Connected to Traffic System",
        description: `Receiving real-time city data (${city?.city_id || 'city'})`,
        variant: "default",
      });
    }
  }, [isConnected, lastUpdateTime, city?.city_id, toast]); // Only show once when connected

  const handleManualOverride = (laneId: string, newLight: TrafficLightState) => {
    if (controlMode === "ai") {
      setControlMode("manual");
      toast({
        title: "Manual Override Activated",
        description: "You are now controlling traffic signals manually. Note: This is a UI demo - real override would require backend integration.",
        variant: "default",
      });
    }
    
    // Note: In a real implementation, this would send a command to the backend
    // For now, this is just a UI demonstration
    console.log(`Manual override requested for ${laneId} to ${newLight}`);
    
    toast({
      title: "Manual Override",
      description: `Signal override requested for ${laneId} -> ${newLight}`,
      variant: "default",
    });
  };

  const handleEmergencyOverride = (laneId: string) => {
    setControlMode("emergency");
    setShowEmergencyPanel(false);
    
    // Note: In a real implementation, this would send an emergency command to the backend
    console.log(`Emergency override requested for ${laneId}`);
    
    toast({
      title: "🚨 Emergency Override Active",
      description: `Emergency route cleared for ${laneId}. Note: This is a UI demo - real override would require backend integration.`,
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
            lanes={convertedLanes}
            controlMode={controlMode}
            onManualOverride={handleManualOverride}
            onEmergencyOverride={handleEmergencyOverride}
            onReturnToAI={returnToAI}
            showEmergencyPanel={showEmergencyPanel}
            setShowEmergencyPanel={setShowEmergencyPanel}
            simulationData={simulationData}
            selectedIntersectionId={selectedIntersectionId}
          />
        );
      case "city": {
        const center = city?.center || { lat: 28.6139, lng: 77.2090 };
        return (
          <CityPage
            cityId={city?.city_id ?? null}
            center={center}
            nodes={nodes}
            selectedIntersectionId={selectedIntersectionId}
            onSelectIntersection={setSelectedIntersectionId}
            incidents={incidents}
            ambulanceRoutes={ambulanceRoutes}
            eventLogTail={(simulationData as any)?.event_log_tail}
            dispatchAmbulance={dispatchAmbulance}
            createIncident={createIncident}
            clearIncident={clearIncident}
          />
        );
      }
      case "cameras":
        return (
          <CamerasPage
            nodes={nodes}
            selectedIntersectionId={selectedIntersectionId}
            onSelectIntersection={setSelectedIntersectionId}
          />
        );
      case "replay":
        return <ReplayPage latestCityUpdate={(simulationData as any)?.__city_update || null} />;
      case "analytics":
        return <AnalyticsPage lanes={convertedLanes} />;
      case "system":
        return <SystemConfigPage />;
      default:
        return (
          <DashboardPage
            lanes={convertedLanes}
            controlMode={controlMode}
            onManualOverride={handleManualOverride}
            onEmergencyOverride={handleEmergencyOverride}
            onReturnToAI={returnToAI}
            showEmergencyPanel={showEmergencyPanel}
            setShowEmergencyPanel={setShowEmergencyPanel}
            simulationData={simulationData}
            selectedIntersectionId={selectedIntersectionId}
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
