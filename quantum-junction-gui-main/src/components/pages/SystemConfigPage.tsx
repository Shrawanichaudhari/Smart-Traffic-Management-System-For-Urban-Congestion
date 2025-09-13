import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { 
  Settings, 
  Clock, 
  Zap, 
  Shield, 
  Network, 
  Database,
  Bell,
  Monitor,
  Save,
  RefreshCw
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export const SystemConfigPage = () => {
  const { toast } = useToast();
  const [aiSensitivity, setAiSensitivity] = useState([75]);
  const [emergencyResponseTime, setEmergencyResponseTime] = useState([3]);
  const [defaultCycleTime, setDefaultCycleTime] = useState(45);
  const [maxCycleTime, setMaxCycleTime] = useState(120);
  const [minCycleTime, setMinCycleTime] = useState(15);
  
  const [settings, setSettings] = useState({
    autoOptimization: true,
    emergencyPreemption: true,
    adaptiveTiming: true,
    trafficPrediction: true,
    realTimeAdjustment: true,
    maintenanceMode: false,
    alertsEnabled: true,
    dataLogging: true
  });

  const handleSaveSettings = () => {
    toast({
      title: "Settings Saved",
      description: "System configuration has been updated successfully.",
      variant: "default",
    });
  };

  const handleResetToDefaults = () => {
    setAiSensitivity([75]);
    setEmergencyResponseTime([3]);
    setDefaultCycleTime(45);
    setMaxCycleTime(120);
    setMinCycleTime(15);
    setSettings({
      autoOptimization: true,
      emergencyPreemption: true,
      adaptiveTiming: true,
      trafficPrediction: true,
      realTimeAdjustment: true,
      maintenanceMode: false,
      alertsEnabled: true,
      dataLogging: true
    });
    
    toast({
      title: "Settings Reset",
      description: "All settings have been restored to defaults.",
      variant: "default",
    });
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl lg:text-3xl font-bold text-primary mb-2">
            System Configuration
          </h1>
          <p className="text-muted-foreground">
            Configure traffic control system parameters and preferences
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleResetToDefaults}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Reset to Defaults
          </Button>
          <Button onClick={handleSaveSettings}>
            <Save className="w-4 h-4 mr-2" />
            Save Settings
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Traffic Timing Configuration */}
        <Card className="control-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <Clock className="w-5 h-5" />
              Traffic Timing Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="default-cycle">Default Cycle Time (seconds)</Label>
              <Input
                id="default-cycle"
                type="number"
                value={defaultCycleTime}
                onChange={(e) => setDefaultCycleTime(Number(e.target.value))}
                className="bg-muted/20"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="max-cycle">Maximum Cycle Time (seconds)</Label>
              <Input
                id="max-cycle"
                type="number"
                value={maxCycleTime}
                onChange={(e) => setMaxCycleTime(Number(e.target.value))}
                className="bg-muted/20"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="min-cycle">Minimum Cycle Time (seconds)</Label>
              <Input
                id="min-cycle"
                type="number"
                value={minCycleTime}
                onChange={(e) => setMinCycleTime(Number(e.target.value))}
                className="bg-muted/20"
              />
            </div>

            <div className="space-y-3">
              <Label>AI Sensitivity Level: {aiSensitivity[0]}%</Label>
              <Slider
                value={aiSensitivity}
                onValueChange={setAiSensitivity}
                max={100}
                min={10}
                step={5}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Higher values make AI more responsive to traffic changes
              </p>
            </div>

            <div className="space-y-3">
              <Label>Emergency Response Time: {emergencyResponseTime[0]} seconds</Label>
              <Slider
                value={emergencyResponseTime}
                onValueChange={setEmergencyResponseTime}
                max={10}
                min={1}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Time to clear intersection for emergency vehicles
              </p>
            </div>
          </CardContent>
        </Card>

        {/* AI & Automation Settings */}
        <Card className="control-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <Zap className="w-5 h-5" />
              AI & Automation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries({
              autoOptimization: "Auto Optimization",
              emergencyPreemption: "Emergency Preemption",
              adaptiveTiming: "Adaptive Timing",
              trafficPrediction: "Traffic Prediction",
              realTimeAdjustment: "Real-time Adjustment"
            }).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                <div>
                  <Label htmlFor={key}>{label}</Label>
                  <p className="text-xs text-muted-foreground">
                    {key === "autoOptimization" && "Automatically optimize traffic flow"}
                    {key === "emergencyPreemption" && "Priority for emergency vehicles"}
                    {key === "adaptiveTiming" && "Adjust timing based on traffic patterns"}
                    {key === "trafficPrediction" && "Predict traffic flow changes"}
                    {key === "realTimeAdjustment" && "Real-time signal adjustments"}
                  </p>
                </div>
                <Switch
                  id={key}
                  checked={settings[key as keyof typeof settings] as boolean}
                  onCheckedChange={(checked) => 
                    setSettings(prev => ({ ...prev, [key]: checked }))
                  }
                />
              </div>
            ))}
          </CardContent>
        </Card>

        {/* System Status */}
        <Card className="control-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <Monitor className="w-5 h-5" />
              System Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 rounded-lg bg-success/20">
                <div className="text-xl font-bold text-success">Online</div>
                <div className="text-xs text-muted-foreground">System Status</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-primary/20">
                <div className="text-xl font-bold text-primary">99.8%</div>
                <div className="text-xs text-muted-foreground">Uptime</div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">CPU Usage</span>
                <Badge variant="outline" className="border-success text-success">23%</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Memory Usage</span>
                <Badge variant="outline" className="border-warning text-warning">67%</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Network Latency</span>
                <Badge variant="outline" className="border-success text-success">12ms</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Settings */}
        <Card className="control-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-primary">
              <Settings className="w-5 h-5" />
              System Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries({
              maintenanceMode: "Maintenance Mode",
              alertsEnabled: "System Alerts",
              dataLogging: "Data Logging"
            }).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                <div>
                  <Label htmlFor={key}>{label}</Label>
                  <p className="text-xs text-muted-foreground">
                    {key === "maintenanceMode" && "Disable auto-optimization for maintenance"}
                    {key === "alertsEnabled" && "Enable system alert notifications"}
                    {key === "dataLogging" && "Log traffic data for analysis"}
                  </p>
                </div>
                <Switch
                  id={key}
                  checked={settings[key as keyof typeof settings] as boolean}
                  onCheckedChange={(checked) => 
                    setSettings(prev => ({ ...prev, [key]: checked }))
                  }
                />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};