import { LaneData } from "../TrafficDashboard";
import { AnalyticsSidebar } from "../AnalyticsSidebar";

interface AnalyticsPageProps {
  lanes: LaneData[];
}

export const AnalyticsPage = ({ lanes }: AnalyticsPageProps) => {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl lg:text-3xl font-bold text-primary mb-2">
          Advanced Analytics
        </h1>
        <p className="text-muted-foreground">
          Comprehensive traffic performance analysis and reporting
        </p>
      </div>
      
      <AnalyticsSidebar lanes={lanes} />
    </div>
  );
};