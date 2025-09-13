import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';

const data = [
  { condition: 'High Traffic', aiSuccess: 89, aiFailure: 11, baselineSuccess: 67, baselineFailure: 33 },
  { condition: 'Medium Traffic', aiSuccess: 93, aiFailure: 7, baselineSuccess: 76, baselineFailure: 24 },
  { condition: 'Low Traffic', aiSuccess: 97, aiFailure: 3, baselineSuccess: 91, baselineFailure: 9 }
];

export const TrafficConditionsChart = () => {
  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
          <XAxis 
            dataKey="condition" 
            tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis 
            tick={{ fontSize: 10, fill: 'hsl(var(--muted-foreground))' }}
            axisLine={false}
            tickLine={false}
            domain={[0, 100]}
          />
          <Bar dataKey="aiSuccess" stackId="ai" fill="hsl(var(--success))" />
          <Bar dataKey="aiFailure" stackId="ai" fill="hsl(var(--destructive))" />
          <Bar dataKey="baselineSuccess" stackId="baseline" fill="hsl(var(--success))" opacity={0.6} />
          <Bar dataKey="baselineFailure" stackId="baseline" fill="hsl(var(--destructive))" opacity={0.6} />
        </BarChart>
      </ResponsiveContainer>

      {/* Contingency Analysis Results */}
      <div className="space-y-3">
        <div className="text-xs font-medium text-foreground">Contingency Analysis Results</div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-1 text-muted-foreground">Traffic Level</th>
                <th className="text-center p-1 text-primary">AI Success</th>
                <th className="text-center p-1 text-destructive">AI Failure</th>
                <th className="text-center p-1 text-muted-foreground">Baseline Success</th>
                <th className="text-center p-1 text-muted-foreground">Baseline Failure</th>
                <th className="text-center p-1 text-accent">Chi-Square</th>
              </tr>
            </thead>
            <tbody className="space-y-1">
              <tr>
                <td className="p-1 text-foreground">High Traffic</td>
                <td className="text-center p-1 text-success">89%</td>
                <td className="text-center p-1 text-destructive">11%</td>
                <td className="text-center p-1 text-muted-foreground">67%</td>
                <td className="text-center p-1 text-muted-foreground">33%</td>
                <td className="text-center p-1 text-accent">χ² = 15.8</td>
              </tr>
              <tr>
                <td className="p-1 text-foreground">Medium Traffic</td>
                <td className="text-center p-1 text-success">93%</td>
                <td className="text-center p-1 text-destructive">7%</td>
                <td className="text-center p-1 text-muted-foreground">76%</td>
                <td className="text-center p-1 text-muted-foreground">24%</td>
                <td className="text-center p-1 text-accent">χ² = 12.1</td>
              </tr>
              <tr>
                <td className="p-1 text-foreground">Low Traffic</td>
                <td className="text-center p-1 text-success">97%</td>
                <td className="text-center p-1 text-destructive">3%</td>
                <td className="text-center p-1 text-muted-foreground">91%</td>
                <td className="text-center p-1 text-muted-foreground">9%</td>
                <td className="text-center p-1 text-accent">χ² = 4.1</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="text-xs text-success bg-success/10 p-2 rounded">
          * All Chi-square values significant at p &lt; 0.05, indicating statistically significant performance differences.
        </div>
      </div>
    </div>
  );
};