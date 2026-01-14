import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { AlertTriangle, Clock, CheckCircle, Activity, Settings, Download, FileText } from "lucide-react";

interface EmergencyEvent {
  id: string;
  vehicleId: string;
  status: "active" | "cleared";
  clearedTime: string;
  duration?: string;
}

const emergencyEvents: EmergencyEvent[] = [
  { id: "E001", vehicleId: "Emergency Vehicle #E001", status: "cleared", clearedTime: "7.2s", duration: "05:42:49" },
  { id: "E002", vehicleId: "Emergency Vehicle #E002", status: "cleared", clearedTime: "9.8s", duration: "06:59:49" },
  { id: "E003", vehicleId: "Emergency Vehicle #E003", status: "active", clearedTime: "", duration: "06:37:04" }
];

export const EmergencyEventsPanel = () => {
  return (
    <div className="space-y-4">
      {/* Recent Emergency Events */}
      <Card className="control-card">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm text-primary">Recent Emergency Events</CardTitle>
        </CardHeader>
        <CardContent className="p-4 pt-0 space-y-3">
          {emergencyEvents.map((event) => (
            <div key={event.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  event.status === "active" ? "bg-warning pulse-glow" : "bg-success"
                }`}></div>
                <div>
                  <div className="text-sm font-medium text-foreground">{event.vehicleId}</div>
                  <div className="text-xs text-muted-foreground">
                    {event.status === "active" ? `In progress • ${event.duration}` : `Cleared in ${event.clearedTime} • ${event.duration}`}
                  </div>
                </div>
              </div>
              <Badge variant={event.status === "active" ? "secondary" : "outline"} className="text-xs">
                {event.status === "active" ? "Active" : "Cleared"}
              </Badge>
            </div>
          ))}
          
          <Button variant="link" size="sm" className="w-full text-primary">
            View All Events
          </Button>
        </CardContent>
      </Card>

      {/* Emergency Management Console */}
      <Card className="control-card">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm text-primary">
            <Settings className="w-4 h-4" />
            Emergency Management Console
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4 pt-0 space-y-4">
          {/* Emergency Override Controls */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-medium text-foreground">
              <AlertTriangle className="w-3 h-3" />
              EMERGENCY OVERRIDE CONTROLS
            </div>
            
            <Button 
              variant="destructive" 
              size="sm" 
              className="w-full justify-start"
            >
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 border border-white rounded-sm"></div>
                EMERGENCY STOP - ALL RED
              </div>
            </Button>
            
            <div className="flex items-center gap-2 text-xs text-warning">
              <div className="w-3 h-3 bg-warning rounded-sm"></div>
              Emergency Vehicle Priority
            </div>
          </div>

          <Separator className="bg-border/50" />

          {/* Manual Phase Control */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-medium text-foreground">
              <Activity className="w-3 h-3" />
              MANUAL PHASE CONTROL
            </div>
            
            <select className="w-full p-2 rounded bg-muted border border-border text-xs text-muted-foreground">
              <option>Select Traffic Phase...</option>
              <option>North-South Green</option>
              <option>East-West Green</option>
              <option>All Red</option>
            </select>
            
            <Button variant="outline" size="sm" className="w-full text-xs">
              <Settings className="w-3 h-3 mr-2" />
              Apply Manual Override
            </Button>
          </div>

          <Separator className="bg-border/50" />

          {/* System Configuration */}
          <div className="space-y-3">
            <div className="text-xs font-medium text-foreground">
              <Settings className="w-3 h-3 inline mr-2" />
              SYSTEM CONFIGURATION
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Emergency Vehicle Priority System</span>
                <div className="w-2 h-2 rounded-full bg-success"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">AI Traffic Optimization</span>
                <div className="w-2 h-2 rounded-full bg-success"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Audio Alert System</span>
                <div className="w-2 h-2 rounded-full bg-muted"></div>
              </div>
            </div>
          </div>

          <Separator className="bg-border/50" />

          {/* System Reports */}
          <div className="space-y-3">
            <div className="text-xs font-medium text-foreground">SYSTEM REPORTS</div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1 text-xs">
                <Download className="w-3 h-3 mr-1" />
                Export KPIs
              </Button>
              <Button variant="outline" size="sm" className="flex-1 text-xs">
                <FileText className="w-3 h-3 mr-1" />
                Generate Report
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};