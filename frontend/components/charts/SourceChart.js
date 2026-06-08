import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
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
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={entries}
            cx="50%"
            cy="50%"
            innerRadius={50}
            outerRadius={100}
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
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
