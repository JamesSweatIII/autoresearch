import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const COLORS = ["#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe", "#e0e7ff", "#f0abfc", "#d946ef", "#a21caf"];

export default function KeywordChart({ data = {} }) {
  const chartData = Object.entries(data).map(([name, value], i) => ({
    name: name.length > 12 ? name.slice(0, 12) + "..." : name,
    fullName: name,
    value,
    fill: COLORS[i % COLORS.length],
  })).sort((a, b) => b.value - a.value).slice(0, 12);

  if (chartData.length === 0) {
    return <div className="text-center py-12 text-gray-400 text-sm">No keyword data available yet</div>;
  }

  return (
    <div className="w-full h-72">
      <ResponsiveContainer>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis type="number" tick={{ fontSize: 11 }} stroke="#94a3b8" />
          <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} stroke="#94a3b8" width={90} />
          <Tooltip
            contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px" }}
            formatter={(value, _name, props) => [value, props.payload.fullName]}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
