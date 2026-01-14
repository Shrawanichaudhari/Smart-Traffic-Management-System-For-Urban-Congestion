// React hook for managing traffic data from backend

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiService } from '../services/apiService';
import { websocketService } from '../services/websocketService';
import { 
  SimulationData, 
  EnhancedLaneData, 
  IntersectionStatusResponse,
  AnalyticsData 
} from '../types/simulation';

interface TrafficDataState {
  // Data states
  lanes: EnhancedLaneData[];
  simulationData: SimulationData | null;
  intersectionStatus: IntersectionStatusResponse | null;
  analyticsData: AnalyticsData | null;
  
  // Connection states
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  lastUpdateTime: Date | null;
  
  // Methods
  refreshData: () => Promise<void>;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
}

export const useTrafficData = (): TrafficDataState => {
  // State management
  const [lanes, setLanes] = useState<EnhancedLaneData[]>([]);
  const [simulationData, setSimulationData] = useState<SimulationData | null>(null);
  const [intersectionStatus, setIntersectionStatus] = useState<IntersectionStatusResponse | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  
  // Refs to avoid stale closures
  const mountedRef = useRef(true);
  
  // Handle simulation data updates
  const handleSimulationUpdate = useCallback((data: SimulationData) => {
    if (!mountedRef.current) return;
    
    console.log('Received simulation update:', data.simulation_id);
    
    setSimulationData(data);
    setLastUpdateTime(new Date());
    setError(null);
    
    // Transform simulation data to lane format
    const transformedLanes = transformSimulationDataToLanes(data);
    setLanes(transformedLanes);
  }, []);
  
  // Handle WebSocket connection status
  const handleConnectionStatus = useCallback((connected: boolean) => {
    if (!mountedRef.current) return;
    
    console.log(`WebSocket connection status: ${connected}`);
    setIsConnected(connected);
    
    if (!connected) {
      setError('Connection to server lost. Attempting to reconnect...');
    } else {
      setError(null);
    }
  }, []);
  
  // Handle WebSocket errors
  const handleWebSocketError = useCallback((errorData: { error: string; timestamp: string }) => {
    if (!mountedRef.current) return;
    
    console.error('WebSocket error:', errorData.error);
    setError(`WebSocket error: ${errorData.error}`);
  }, []);
  
  // Transform simulation data to lane format for existing components
  const transformSimulationDataToLanes = (data: SimulationData): EnhancedLaneData[] => {
    const currentPhase = data.current_phase;
    const directionMetrics = data.direction_metrics;
    const lanes: EnhancedLaneData[] = [];
    
    const directionMap: { [key: string]: "north" | "south" | "east" | "west" } = {
      'north': 'north',
      'south': 'south', 
      'east': 'east',
      'west': 'west'
    };
    
    const directionShortMap: { [key: string]: string } = {
      'north': 'n',
      'south': 's',
      'east': 'e', 
      'west': 'w'
    };
    
    for (const [directionName, metrics] of Object.entries(directionMetrics)) {
      const direction = directionMap[directionName];
      if (!direction) continue;
      
      const vehicleCounts = metrics.vehicle_counts;
      const totalVehicles = Object.values(vehicleCounts).reduce((sum, count) => sum + count, 0);
      
      // Determine light state
      let lightState: "red" | "yellow" | "green" = "red";
      if (currentPhase.active_directions.includes(directionName)) {
        lightState = currentPhase.status === "YELLOW" ? "yellow" : "green";
      }
      
      lanes.push({
        id: `${directionShortMap[directionName]}-straight`,
        direction: direction,
        type: "straight",
        vehicleCount: totalVehicles,
        queueLength: metrics.queue_length,
        currentLight: lightState,
        timeRemaining: currentPhase.remaining_time,
        maxTime: 45, // Default max time
        avgWaitTime: metrics.avg_wait_time,
        vehiclesCrossed: metrics.vehicles_crossed,
        emergencyVehiclePresent: metrics.emergency_vehicle_present
      });
    }
    
    return lanes;
  };
  
  // Fetch initial data from API
  const fetchInitialData = useCallback(async () => {
    if (!mountedRef.current) return;
    
    setIsLoading(true);
    try {
      // Try to get intersection status first (optimized for React components)
      const statusData = await apiService.getIntersectionStatus();
      setIntersectionStatus(statusData);
      setLanes(statusData.lanes);
      
      // Also try to get latest simulation data
      try {
        const latestData = await apiService.getLatestSimulation();
        setSimulationData(latestData);
      } catch (simError) {
        console.log('No latest simulation data available:', simError);
      }
      
      setLastUpdateTime(new Date());
      setError(null);
    } catch (apiError) {
      console.error('Failed to fetch initial data:', apiError);
      setError('Failed to load traffic data. Please check your connection.');
      
      // Fallback: set empty lanes to avoid crashes
      setLanes([]);
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Refresh data manually
  const refreshData = useCallback(async () => {
    await fetchInitialData();
  }, [fetchInitialData]);
  
  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    websocketService.on('simulationUpdate', handleSimulationUpdate);
    websocketService.on('error', handleWebSocketError);
    websocketService.onConnectionStatus(handleConnectionStatus);
    websocketService.connect();
  }, [handleSimulationUpdate, handleWebSocketError, handleConnectionStatus]);
  
  // Disconnect from WebSocket
  const disconnectWebSocket = useCallback(() => {
    websocketService.off('simulationUpdate', handleSimulationUpdate);
    websocketService.off('error', handleWebSocketError);
    websocketService.offConnectionStatus(handleConnectionStatus);
    websocketService.disconnect();
  }, [handleSimulationUpdate, handleWebSocketError, handleConnectionStatus]);
  
  // Initialize data and connections on mount
  useEffect(() => {
    mountedRef.current = true;
    
    // Fetch initial data
    fetchInitialData();
    
    // Connect to WebSocket for real-time updates
    connectWebSocket();
    
    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      disconnectWebSocket();
    };
  }, [fetchInitialData, connectWebSocket, disconnectWebSocket]);
  
  return {
    // Data states
    lanes,
    simulationData,
    intersectionStatus,
    analyticsData,
    
    // Connection states
    isConnected,
    isLoading,
    error,
    lastUpdateTime,
    
    // Methods
    refreshData,
    connectWebSocket,
    disconnectWebSocket
  };
};
