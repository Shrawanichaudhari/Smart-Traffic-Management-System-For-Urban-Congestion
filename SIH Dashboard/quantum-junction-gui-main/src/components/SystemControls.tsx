import { ControlMode } from "./TrafficDashboard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Bot, User, AlertTriangle } from "lucide-react";

interface SystemControlsProps {
  mode: ControlMode;
  onReturnToAI: () => void;
}

export const SystemControls = ({ mode, onReturnToAI }: SystemControlsProps) => {
  const getStatusInfo = () => {
    switch (mode) {
      case "ai":
        return {
          icon: <Bot className="w-4 h-4" />,
          text: "AI Control Active",
          variant: "default" as const,
          className: "bg-primary/20 text-primary border-primary/30"
        };
      case "manual":
        return {
          icon: <User className="w-4 h-4" />,
          text: "Manual Override",
          variant: "secondary" as const,
          className: "bg-warning/20 text-warning border-warning/30"
        };
      case "emergency":
        return {
          icon: <AlertTriangle className="w-4 h-4" />,
          text: "Emergency Override",
          variant: "destructive" as const,
          className: "bg-destructive/20 text-destructive border-destructive/30 pulse-glow"
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="flex items-center gap-3">
      <Badge 
        variant={statusInfo.variant}
        className={`${statusInfo.className} px-3 py-2 font-medium`}
      >
        {statusInfo.icon}
        <span className="ml-2">{statusInfo.text}</span>
      </Badge>
      
      {mode !== "ai" && (
        <Button
          onClick={onReturnToAI}
          variant="outline"
          size="sm"
          className="border-primary/30 text-primary hover:bg-primary/10"
        >
          <Bot className="w-4 h-4 mr-2" />
          Return to AI
        </Button>
      )}
    </div>
  );
};