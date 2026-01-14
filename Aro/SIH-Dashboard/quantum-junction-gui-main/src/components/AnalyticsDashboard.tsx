import { LaneData } from "./TrafficDashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, Clock, Fuel, Leaf, Activity } from "lucide-react";

interface AnalyticsDashboardProps {
  lanes: LaneData[];
}

export const AnalyticsDashboard = ({ lanes }: AnalyticsDashboardProps) => {
  // Calculate analytics
  const totalVehicles = lanes.reduce((sum, lane) => sum + lane.vehicleCount, 0);
  const avgWaitTime = Math.round(lanes.reduce((sum, lane) => sum + lane.timeRemaining, 0) / lanes.length);
  const throughputPerHour = Math.round(totalVehicles * 12); // Assuming 5-minute cycles
  const fuelSaved = Math.round(totalVehicles * 0.2); // Liters saved vs baseline
  const co2Saved = Math.round(fuelSaved * 2.31); // kg CO2 saved

  const metrics = [
    {
      title: "Current Throughput",
      value: `${throughputPerHour}/hr`,
      icon: <TrendingUp className="w-4 h-4" />,
      change: "+12%",
      positive: true
    },
    {
      title: "Avg Wait Time",
      value: `${avgWaitTime}s`,
      icon: <Clock className="w-4 h-4" />,
      change: "-8%",
      positive: true
    },
    {
      title: "Fuel Saved",
      value: `${fuelSaved}L`,
      icon: <Fuel className="w-4 h-4" />,
      change: "+15%",
      positive: true
    },
    {
      title: "CO₂ Reduced",
      value: `${co2Saved}kg`,
      icon: <Leaf className="w-4 h-4" />,
      change: "+15%",
      positive: true
    }
  ];

  const getLaneEfficiency = (lane: LaneData) => {
    // Simple efficiency calculation based on vehicle count vs wait time
    return Math.min(100, Math.max(0, 100 - (lane.timeRemaining / lane.vehicleCount) * 5));
  };

  return (
    <div className="space-y-6">
      {/* Performance Metrics */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-primary">
            <Activity className="w-5 h-5" />
            Live Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {metrics.map((metric, index) => (
            <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
              <div className="flex items-center gap-3">
                <div className="text-primary">{metric.icon}</div>
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

      {/* Lane Efficiency */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="text-primary">Lane Efficiency</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {lanes.map((lane) => {
            const efficiency = getLaneEfficiency(lane);
            return (
              <div key={lane.id} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-foreground">
                    {lane.direction.toUpperCase()} {lane.type}
                  </span>
                  <span className="text-muted-foreground">{Math.round(efficiency)}%</span>
                </div>
                <Progress 
                  value={efficiency} 
                  className="h-2"
                />
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* System Status */}
      <Card className="control-card">
        <CardHeader>
          <CardTitle className="text-primary">System Health</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center p-3 rounded-lg bg-success/20">
              <div className="text-2xl font-bold text-success">99.8%</div>
              <div className="text-xs text-muted-foreground">Uptime</div>
            </div>
            <div className="text-center p-3 rounded-lg bg-primary/20">
              <div className="text-2xl font-bold text-primary">{totalVehicles}</div>
              <div className="text-xs text-muted-foreground">Active Vehicles</div>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">AI Response Time</span>
              <span className="text-success">12ms</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Sensor Accuracy</span>
              <span className="text-success">98.2%</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Network Latency</span>
              <span className="text-warning">45ms</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};