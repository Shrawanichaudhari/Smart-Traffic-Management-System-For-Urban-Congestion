import { useState, useEffect } from "react";
import { NavigationSidebar } from "./NavigationSidebar";
import { DashboardPage } from "./pages/DashboardPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { SystemConfigPage } from "./pages/SystemConfigPage";
import { useToast } from "@/hooks/use-toast";
import { trafficApi, TrafficData } from "@/service/apiService";
import { Card } from "./ui/card";

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

interface SpeedData {
  avg_speed: number;
  avg_throughput: number;
  intersection_id: string;
  simulation_id: string;
  total_vehicles: number;
}

interface EnvironmentalData {
  intersection_id: string;
  simulation_id: string;
  co2_saved: number;
  fuel_saved: number;
}

interface WaitTimeDetailedData {
  intersection_id: string;
  simulation_id: string;
  avg_wait_time: number;
  total_vehicles: number;
}

interface MetricsResponse {
  environmental_impact: {
    environmental_data: EnvironmentalData[];
    total_fuel_saved: number;
    total_co2_saved: number;
  };
  speeds: {
    overall_avg_speed: number;
    speed_data: SpeedData[];
  };
  wait_times: {
    overall_avg_wait_time: number;
    best_performance: number | null;
    worst_performance: number | null;
    detailed_data: WaitTimeDetailedData[];
    total_intersections: number;
    total_simulations?: number;
  };
  timestamp: string;
}

export const TrafficDashboard = () => {
  const { toast } = useToast();
  const [controlMode, setControlMode] = useState<ControlMode>("ai");
  const [showEmergencyPanel, setShowEmergencyPanel] = useState(false);
  const [currentPage, setCurrentPage] = useState("dashboard");
  const [trafficData, setTrafficData] = useState<TrafficData | null>(null);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [connectionStatus, setConnectionStatus] = useState<"connected" | "disconnected" | "error">("disconnected");
  
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

  // Enhanced data fetching with better error handling
  const fetchRealTimeData = async () => {
    try {
      setConnectionStatus("connected");
      
      // Fetch live metrics only
      const metricsResponse = await trafficApi.getLiveMetrics();
      
      // Properly structure the metrics data
      const metricsData: MetricsResponse = {
        environmental_impact: {
          environmental_data: metricsResponse.data.environmental_impact.environmental_data || [],
          total_fuel_saved: metricsResponse.data.environmental_impact.total_fuel_saved || 0,
          total_co2_saved: metricsResponse.data.environmental_impact.total_co2_saved || 0
        },
        speeds: {
          overall_avg_speed: metricsResponse.data.speeds.overall_avg_speed || 0,
          speed_data: metricsResponse.data.speeds.speed_data || []
        },
        wait_times: {
          overall_avg_wait_time: metricsResponse.data.wait_times.overall_avg_wait_time || 0,
          best_performance: metricsResponse.data.wait_times.best_performance,
          worst_performance: metricsResponse.data.wait_times.worst_performance,
          detailed_data: metricsResponse.data.wait_times.detailed_data || [],
          total_intersections: metricsResponse.data.wait_times.total_intersections || 0,
          total_simulations: metricsResponse.data.wait_times.total_intersections || 0
        },
        timestamp: metricsResponse.data.timestamp
      };

      setMetrics(metricsData);
      
      // Update traffic data for compatibility with existing components
      setTrafficData({
        wait_times: metricsData.wait_times,
        speeds: metricsData.speeds.overall_avg_speed,
        environmental_impact: {
          fuel_saved: metricsData.environmental_impact.total_fuel_saved,
          co2_reduced: metricsData.environmental_impact.total_co2_saved
        }
      });

      // Update lanes data based on real-time metrics if available
      if (metricsData.speeds.speed_data.length > 0) {
        updateLanesFromRealData(metricsData.speeds.speed_data, metricsData.wait_times.detailed_data);
      }
      
      // Signal timing data processing removed for simplicity

      setLastUpdated(new Date().toLocaleTimeString());
      setConnectionStatus("connected");
      
    } catch (error) {
      console.error('Error fetching real-time data:', error);
      setConnectionStatus("error");
      toast({
        title: "Connection Error",
        description: "Failed to fetch real-time data. Retrying...",
        variant: "destructive",
      });
    }
  };

  // Update lane data based on real backend data
  const updateLanesFromRealData = (speedData: SpeedData[], waitTimeData: WaitTimeDetailedData[]) => {
    setLanes(prevLanes => {
      return prevLanes.map((lane, index) => {
        // Map backend data to lanes (you may need to adjust this based on your intersection mapping)
        const correspondingSpeedData = speedData[index % speedData.length];
        const correspondingWaitData = waitTimeData[index % waitTimeData.length];
        
        if (correspondingSpeedData) {
          const vehicleCount = correspondingSpeedData.total_vehicles || lane.vehicleCount;
          const avgSpeed = correspondingSpeedData.avg_speed || 0;
          
          // Simple logic: if speed is low, likely congested (red light)
          // if speed is high, likely flowing (green light)
          let newLight: TrafficLightState = lane.currentLight;
          if (controlMode === "ai") {
            if (avgSpeed < 15) {
              newLight = "red";
            } else if (avgSpeed > 25) {
              newLight = "green";
            } else {
              newLight = "yellow";
            }
          }
          
          return {
            ...lane,
            vehicleCount,
            currentLight: newLight,
            timeRemaining: newLight !== lane.currentLight ? lane.maxTime : lane.timeRemaining - 1
          };
        }
        return lane;
      });
    });
  };

  // Simplified - using only live metrics data

  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await fetchRealTimeData();
      setLoading(false);
    };

    initializeData();
    
    // Set up interval for real-time updates every 2 seconds
    const interval = setInterval(fetchRealTimeData, 2000);
    
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Simulate traffic flow changes when not using real data
    if (!metrics?.speeds.speed_data.length) {
      const trafficInterval = setInterval(() => {
        setLanes(prevLanes => {
          return prevLanes.map(lane => {
            // Increase vehicle count slightly
            const newVehicleCount = Math.max(0, lane.vehicleCount + Math.floor(Math.random() * 4) - 1);

            // Logic to change lights based on control mode and vehicle count
            if (controlMode === "ai") {
              // Simple AI: if a lane has more than 10 vehicles, turn green
              if (newVehicleCount > 10 && lane.currentLight !== "green") {
                return { ...lane, currentLight: "green", timeRemaining: lane.maxTime, vehicleCount: newVehicleCount };
              } else if (lane.currentLight === "green" && lane.timeRemaining > 0) {
                return { ...lane, timeRemaining: Math.max(0, lane.timeRemaining - 2), vehicleCount: newVehicleCount };
              } else if (lane.currentLight === "green" && lane.timeRemaining <= 0) {
                return { ...lane, currentLight: "red", timeRemaining: lane.maxTime, vehicleCount: newVehicleCount };
              } else if (lane.currentLight === "red" && lane.timeRemaining > 0) {
                return { ...lane, timeRemaining: Math.max(0, lane.timeRemaining - 2), vehicleCount: newVehicleCount };
              }
            }

            return { ...lane, vehicleCount: newVehicleCount };
          });
        });
      }, 2000);

      return () => clearInterval(trafficInterval);
    }
  }, [controlMode, metrics]);

  const handleManualOverride = async (laneId: string, newLight: TrafficLightState) => {
    if (controlMode === "ai") {
      setControlMode("manual");
      toast({
        title: "Manual Override Activated",
        description: "You are now controlling traffic signals manually.",
        variant: "default",
      });
    }
    
    try {
      // Send signal change to backend
      await trafficApi.updateSignalTiming(laneId, newLight, 30);
      
      // Update local state
      setLanes(prevLanes =>
        prevLanes.map(lane =>
          lane.id === laneId
            ? { ...lane, currentLight: newLight, timeRemaining: 30 }
            : lane
        )
      );
      
      toast({
        title: "Signal Updated",
        description: `${laneId} light changed to ${newLight.toUpperCase()}`,
        variant: "default",
      });
    } catch (error) {
      console.error('Failed to update signal:', error);
      toast({
        title: "Signal Update Failed",
        description: "Could not update signal timing. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleEmergencyOverride = async (laneId: string) => {
    setControlMode("emergency");
    setShowEmergencyPanel(false);
    
    try {
      // Send emergency override to backend
      await trafficApi.setEmergencyOverride(laneId, 60);
      
      // Update local state
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
    } catch (error) {
      console.error('Failed to set emergency override:', error);
      toast({
        title: "Emergency Override Failed",
        description: "Could not activate emergency override.",
        variant: "destructive",
      });
    }
  };

  const returnToAI = async () => {
    try {
      // Reset to AI control on backend
      await trafficApi.resetToAI("INT_001");
      
      setControlMode("ai");
      toast({
        title: "AI Control Restored",
        description: "Traffic signals returned to AI management.",
        variant: "default",
      });
    } catch (error) {
      console.error('Failed to reset to AI:', error);
      toast({
        title: "AI Reset Failed",
        description: "Could not return to AI control.",
        variant: "destructive",
      });
    }
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading real-time traffic data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex w-full">
      {/* Navigation Sidebar */}
      <NavigationSidebar 
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />
      
      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {/* Connection Status Bar */}
        <div className={`p-2 text-sm text-center ${
          connectionStatus === 'connected' ? 'bg-green-100 text-green-800' :
          connectionStatus === 'error' ? 'bg-red-100 text-red-800' :
          'bg-yellow-100 text-yellow-800'
        }`}>
          <div className="flex justify-center items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' :
              connectionStatus === 'error' ? 'bg-red-500' :
              'bg-yellow-500'
            }`}></div>
            {connectionStatus === 'connected' && `Live Data • Last updated: ${lastUpdated}`}
            {connectionStatus === 'error' && 'Connection Error • Retrying...'}
            {connectionStatus === 'disconnected' && 'Connecting to real-time data...'}
          </div>
        </div>

        {renderCurrentPage()}
      </div>
    </div>
  );
};