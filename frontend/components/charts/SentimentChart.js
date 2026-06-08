import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

const SENTIMENT_COLORS = { positive: "#10b981", neutral: "#6366f1", negative: "#ef4444" };

export default function SentimentChart({ data = {} }) {
  const sentimentCounts = { positive: 0, neutral: 0, negative: 0 };
  if (Array.isArray(data)) {
    data.forEach((d) => {
      const s = d.sentiment || "neutral";
      if (sentimentCounts[s] !== undefined) sentimentCounts[s]++;
    });
  }

  const chartData = Object.entries(sentimentCounts).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    fill: SENTIMENT_COLORS[name],
  }));

  if (chartData.every((d) => d.value === 0)) {
    return <div className="text-center py-12 text-gray-400 text-sm">No sentiment data available yet</div>;
  }

  return (
    <div className="w-full h-48">
      <ResponsiveContainer>
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#94a3b8" />
          <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px" }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {chartData.map((entry) => (
              <Cell key={entry.name} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
