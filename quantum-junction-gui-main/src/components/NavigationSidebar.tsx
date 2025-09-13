import { useState } from "react";
import { 
  LayoutDashboard as DashboardIcon, 
  BarChart3 as AnalyticsIcon, 
  Settings as SettingsIcon, 
  ChevronLeft, 
  ChevronRight 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface NavigationSidebarProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

export const NavigationSidebar = ({ currentPage, onPageChange }: NavigationSidebarProps) => {
  console.log("NavigationSidebar: Component loaded successfully");
  const [isCollapsed, setIsCollapsed] = useState(false);

  const menuItems = [
    {
      id: "dashboard",
      label: "Dashboard", 
      IconComponent: DashboardIcon,
      description: "Traffic Control"
    },
    {
      id: "analytics",
      label: "Analytics",
      IconComponent: AnalyticsIcon,
      description: "Performance Data"
    },
    {
      id: "system",
      label: "System Config",
      IconComponent: SettingsIcon,
      description: "System Settings"
    }
  ];

  return (
    <div className={cn(
      "h-screen bg-card border-r border-border transition-all duration-300 flex flex-col",
      isCollapsed ? "w-16" : "w-64"
    )}>
      {/* Header */}
      <div className="p-4 border-b border-border flex items-center justify-between">
        {!isCollapsed && (
          <div>
            <h1 className="text-lg font-bold text-primary">Traffic Control</h1>
            <p className="text-xs text-muted-foreground">System Management</p>
          </div>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="ml-auto"
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </Button>
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 p-2">
        <div className="space-y-2">
          {menuItems.map((item) => {
            const IconComponent = item.IconComponent;
            const isActive = currentPage === item.id;
            
            return (
              <Button
                key={item.id}
                variant={isActive ? "default" : "ghost"}
                className={cn(
                  "w-full justify-start h-12 transition-all",
                  isActive && "bg-primary/20 text-primary border border-primary/30 glow-primary",
                  isCollapsed && "px-3"
                )}
                onClick={() => onPageChange(item.id)}
              >
                <IconComponent className={cn("w-5 h-5", !isCollapsed && "mr-3")} />
                {!isCollapsed && (
                  <div className="text-left">
                    <div className="font-medium">{item.label}</div>
                    <div className="text-xs text-muted-foreground">{item.description}</div>
                  </div>
                )}
              </Button>
            );
          })}
        </div>
      </nav>
    </div>
  );
};