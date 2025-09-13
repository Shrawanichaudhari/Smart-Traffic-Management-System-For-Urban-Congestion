import { LaneData, ControlMode, TrafficLightState } from "../TrafficDashboard";
import { EnhancedIntersectionView } from "../EnhancedIntersectionView";
import { SystemControls } from "../SystemControls";
import { EmergencyOverride } from "../EmergencyOverride";
import { TrafficMetricsGrid } from "../TrafficMetricsGrid";

interface DashboardPageProps {
  lanes: LaneData[];
  controlMode: ControlMode;
  onManualOverride: (laneId: string, newLight: TrafficLightState) => void;
  onEmergencyOverride: (laneId: string) => void;
  onReturnToAI: () => void;
  showEmergencyPanel: boolean;
  setShowEmergencyPanel: (show: boolean) => void;
}

export const DashboardPage = ({
  lanes,
  controlMode,
  onManualOverride,
  onEmergencyOverride,
  onReturnToAI,
  showEmergencyPanel,
  setShowEmergencyPanel
}: DashboardPageProps) => {
  return (
    <div className="p-6 space-y-6">
      {/* Enhanced Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-primary mb-2">
            Smart Traffic Control System
          </h1>
          <p className="text-muted-foreground">
            Main & 5th Street Intersection - Live Monitoring
          </p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Indicators */}
          <div className="flex items-center gap-2 text-sm text-success">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse"></div>
            AI Optimization Active
          </div>
          <div className="flex items-center gap-2 text-sm text-primary">
            <div className="w-2 h-2 rounded-full bg-primary"></div>
            Connected
          </div>
          
          {/* Controls */}
          <SystemControls 
            mode={controlMode}
            onReturnToAI={onReturnToAI}
          />
          
          <EmergencyOverride 
            onEmergencyActivate={() => setShowEmergencyPanel(true)}
            showPanel={showEmergencyPanel}
            onPanelClose={() => setShowEmergencyPanel(false)}
            onLaneSelect={onEmergencyOverride}
            lanes={lanes}
          />
        </div>
      </div>

      {/* Main Dashboard Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Enhanced Intersection View */}
        <div className="xl:col-span-3">
          <EnhancedIntersectionView 
            lanes={lanes}
            onManualOverride={onManualOverride}
            controlMode={controlMode}
          />
        </div>
        
        {/* Traffic Metrics */}
        <div className="xl:col-span-1">
          <TrafficMetricsGrid lanes={lanes} />
        </div>
      </div>
    </div>
  );
};