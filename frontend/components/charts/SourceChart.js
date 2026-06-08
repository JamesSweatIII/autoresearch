import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
} from "recharts";

const COLORS = ["#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe", "#e0e7ff", "#f0abfc", "#d946ef", "#a21caf", "#f59e0b", "#10b981", "#14b8a6", "#22c55e", "#eab308", "#f97316", "#ef4444"];

export default function SourceChart({ data = {} }) {
  const entries = Object.entries(data).map(([name, value], i) => ({
    name,
    value,
    color: COLORS[i % COLORS.length],
  })).sort((a, b) => b.value - a.value);

  if (entries.length === 0) {
    return <div className="text-center py-12 text-gray-400 text-sm">No source data available yet</div>;
  }

  return (
    <div className="w-full" style={{ height: Math.max(256, Math.min(entries.length * 24 + 180, 480)) }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={entries}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {entries.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px" }}
          />
          <Legend
            layout="vertical"
            align="right"
            verticalAlign="middle"
            iconSize={10}
            wrapperStyle={{ maxHeight: 320, overflowY: "auto", paddingLeft: 12 }}
            formatter={(value) => (
              <span className="text-xs text-gray-600">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
