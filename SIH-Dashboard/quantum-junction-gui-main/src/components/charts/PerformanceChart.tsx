import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Legend } from 'recharts';

const data = [
  { metric: 'Processing', ai: 35, baseline: 40 },
  { metric: 'Throughput', ai: 85, baseline: 70 },
  { metric: 'Fuel Reduction', ai: 25, baseline: 15 },
  { metric: 'CO₂ Reduction', ai: 30, baseline: 12 },
  { metric: 'Reliability', ai: 75, baseline: 68 }
];

export const PerformanceChart = () => {
  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <XAxis 
            dataKey="metric" 
            tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
            axisLine={false}
            tickLine={false}
          />
          <Legend 
            wrapperStyle={{ fontSize: '10px' }}
          />
          <Bar 
            dataKey="ai" 
            fill="hsl(var(--primary))" 
            name="AI Optimized System"
            radius={[2, 2, 0, 0]}
          />
          <Bar 
            dataKey="baseline" 
            fill="hsl(var(--muted-foreground))" 
            name="Baseline System"
            radius={[2, 2, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      
      {/* Performance Summary */}
      <div className="grid grid-cols-2 gap-4 text-xs">
        <div className="space-y-1">
          <div className="text-primary font-medium">AI Optimized System</div>
          <ul className="space-y-0.5 text-muted-foreground">
            <li>• 21.5% faster vehicle processing</li>
            <li>• 18.2% fuel consumption reduction</li>
            <li>• 94.8% system reliability</li>
          </ul>
        </div>
        <div className="space-y-1">
          <div className="text-muted-foreground font-medium">Baseline System</div>
          <ul className="space-y-0.5 text-muted-foreground">
            <li>• Standard timing sequences</li>
            <li>• No environmental optimization</li>
            <li>• 82.3% system reliability</li>
          </ul>
        </div>
      </div>
    </div>
  );
};