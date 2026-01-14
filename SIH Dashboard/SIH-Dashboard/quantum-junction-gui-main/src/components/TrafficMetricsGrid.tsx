import { LaneData } from "./TrafficDashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  TrendingUp, 
  Clock, 
  Car, 
  Activity, 
  Zap,
  AlertTriangle,
  CheckCircle,
  Users
} from "lucide-react";

interface TrafficMetricsGridProps {
  lanes: LaneData[];
}

export const TrafficMetricsGrid = ({ lanes }: TrafficMetricsGridProps) => {
  // Calculate comprehensive metrics
  const totalVehicles = lanes.reduce((sum, lane) => sum + lane.vehicleCount, 0);
  const avgWaitTime = Math.round(lanes.reduce((sum, lane) => sum + lane.timeRemaining, 0) / lanes.length);
  const throughputPerHour = Math.round(totalVehicles * 12);
  
  // Traffic density analysis
  const highDensityLanes = lanes.filter(lane => lane.vehicleCount > 10).length;
  const mediumDensityLanes = lanes.filter(lane => lane.vehicleCount >= 5 && lane.vehicleCount <= 10).length;
  const lowDensityLanes = lanes.filter(lane => lane.vehicleCount < 5).length;
  
  // Performance indicators
  const activeLanes = lanes.filter(lane => lane.currentLight === "green").length;
  const congestionLevel = Math.min(100, (totalVehicles / (lanes.length * 15)) * 100);
  const systemEfficiency = Math.max(0, 100 - congestionLevel);
  
  // Peak direction analysis
  const directionTotals = {
    north: lanes.filter(l => l.direction === "north").reduce((sum, l) => sum + l.vehicleCount, 0),
    south: lanes.filter(l => l.direction === "south").reduce((sum, l) => sum + l.vehicleCount, 0),
    east: lanes.filter(l => l.direction === "east").reduce((sum, l) => sum + l.vehicleCount, 0),
    west: lanes.filter(l => l.direction === "west").reduce((sum, l) => sum + l.vehicleCount, 0)
  };
  const peakDirection = Object.entries(directionTotals).reduce((a, b) => a[1] > b[1] ? a : b)[0];

  const metrics = [
    {
      title: "Current Throughput",
      value: `${throughputPerHour}/hr`,
      icon: <TrendingUp className="w-4 h-4" />,
      change: "+12%",
      positive: true,
      color: "primary"
    },
    {
      title: "System Efficiency", 
      value: `${Math.round(systemEfficiency)}%`,
      icon: <Zap className="w-4 h-4" />,
      change: "+8%",
      positive: true,
      color: "success"
    },
    {
      title: "Active Lanes",
      value: `${activeLanes}/${lanes.length}`,
      icon: <Activity className="w-4 h-4" />,
      change: "Normal",
      positive: true,
      color: "primary"
    },
    {
      title: "Avg Wait Time",
      value: `${avgWaitTime}s`,
      icon: <Clock className="w-4 h-4" />,
      change: "-5%",
      positive: true,
      color: "success"
    }
  ];

  const getColorClass = (color: string) => {
    switch (color) {
      case "success": return "text-success";
      case "warning": return "text-warning";
      case "destructive": return "text-destructive";
      default: return "text-primary";
    }
  };

  return (
    <div className="space-y-6">
      {/* Live Performance Metrics */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <Activity className="w-5 h-5" />
            Live Metrics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {metrics.map((metric, index) => (
            <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
              <div className="flex items-center gap-3">
                <div className={getColorClass(metric.color)}>{metric.icon}</div>
                <div>
                  <div className="text-sm text-muted-foreground">{metric.title}</div>
                  <div className="text-lg font-semibold text-foreground">{metric.value}</div>
                </div>
              </div>
              <div className={`text-sm font-medium ${
                metric.positive ? "text-success" : "text-destructive"
              }`}>
                {metric.change}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Traffic Density Analysis */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <Car className="w-5 h-5" />
            Traffic Density
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">High Density</span>
              <Badge variant="destructive">{highDensityLanes} lanes</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Medium Density</span>
              <Badge variant="outline" className="border-warning text-warning">{mediumDensityLanes} lanes</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Low Density</span>
              <Badge variant="outline" className="border-success text-success">{lowDensityLanes} lanes</Badge>
            </div>
          </div>
          
          <div className="pt-4 border-t border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-muted-foreground">Overall Congestion</span>
              <span className="text-sm font-medium">{Math.round(congestionLevel)}%</span>
            </div>
            <Progress 
              value={congestionLevel} 
              className="h-3"
            />
          </div>
        </CardContent>
      </Card>

      {/* Peak Direction Analysis */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <Users className="w-5 h-5" />
            Direction Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {Object.entries(directionTotals).map(([direction, count]) => (
              <div key={direction} className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground capitalize">
                  {direction}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{count} vehicles</span>
                  {direction === peakDirection && (
                    <Badge variant="outline" className="border-warning text-warning">
                      Peak
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          <div className="pt-4 border-t border-border">
            <div className="text-center p-3 rounded-lg bg-primary/20">
              <div className="text-lg font-bold text-primary capitalize">{peakDirection}</div>
              <div className="text-xs text-muted-foreground">Highest Traffic Direction</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Status */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <CheckCircle className="w-5 h-5" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 rounded-lg bg-success/20">
              <div className="text-xl font-bold text-success">99.8%</div>
              <div className="text-xs text-muted-foreground">Uptime</div>
            </div>
            <div className="text-center p-3 rounded-lg bg-primary/20">
              <div className="text-xl font-bold text-primary">{totalVehicles}</div>
              <div className="text-xs text-muted-foreground">Total Vehicles</div>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">AI Response</span>
              <span className="text-success">12ms</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Sensor Accuracy</span>
              <span className="text-success">98.2%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Network Status</span>
              <span className="text-success">Connected</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};