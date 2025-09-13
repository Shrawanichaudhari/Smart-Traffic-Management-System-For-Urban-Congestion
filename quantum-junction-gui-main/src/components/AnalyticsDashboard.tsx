import { useState, useEffect } from "react";
import { trafficApi, LiveMetrics, PerformanceComparison } from "@/service/apiService";
import { LaneData } from "./TrafficDashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, Clock, Fuel, Leaf, Activity } from "lucide-react";

interface AnalyticsDashboardProps {
  lanes: LaneData[];
}

export const AnalyticsDashboard = ({ lanes }: AnalyticsDashboardProps) => {
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);
  const [performance, setPerformance] = useState<PerformanceComparison | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        setLoading(true);
        const [metricsResponse, performanceResponse] = await Promise.all([
          trafficApi.getLiveMetrics(),
          trafficApi.getPerformanceComparison()
        ]);

        setLiveMetrics(metricsResponse.data);
        setPerformance(performanceResponse.data);
        setError(null);
      } catch (error) {
        console.error('Error fetching analytics:', error);
        setError('Failed to fetch analytics data');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
    // Fetch data every 2 seconds for real-time updates
    const interval = setInterval(fetchAnalytics, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-4 text-center">Loading analytics...</div>;
  }

  if (error) {
    return <div className="p-4 text-center text-destructive">{error}</div>;
  }

  const metrics = [
    {
      title: "Current Throughput",
      value: `${performance?.comparison.comparison_data?.ai_mode?.avg_throughput || 0}/hr`,
      icon: <TrendingUp className="w-4 h-4" />,
      change: `${((performance?.comparison.comparison_data?.ai_mode?.avg_throughput || 0) - (performance?.comparison.comparison_data?.baseline_mode?.avg_throughput || 0)).toFixed(1)}%`,
      positive: true
    },
    {
      title: "Avg Wait Time",
      value: `${liveMetrics?.wait_times.overall_avg_wait_time.toFixed(1)}s`,
      icon: <Clock className="w-4 h-4" />,
      change: `-${Math.abs((liveMetrics?.wait_times.overall_avg_wait_time || 0) - 45).toFixed(1)}%`,
      positive: (liveMetrics?.wait_times.overall_avg_wait_time || 0) < 45
    },
    {
      title: "Fuel Saved",
      value: `${liveMetrics?.environmental_impact.total_fuel_saved.toFixed(1)}L`,
      icon: <Fuel className="w-4 h-4" />,
      change: "+15%",
      positive: true
    },
    {
      title: "CO₂ Reduced",
      value: `${liveMetrics?.environmental_impact.total_co2_saved.toFixed(1)}kg`,
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
              <div className={`text-sm font-medium ${metric.positive ? "text-success" : "text-destructive"}`}>
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
              <div className="text-2xl font-bold text-primary">{lanes.reduce((sum, lane) => sum + lane.vehicleCount, 0)}</div>
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