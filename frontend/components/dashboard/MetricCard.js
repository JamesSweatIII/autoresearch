export default function MetricCard({ label, value, icon, trend, color = "primary" }) {
  const colorMap = {
    primary: "bg-primary-50 text-primary-700",
    green: "bg-green-50 text-green-700",
    blue: "bg-blue-50 text-blue-700",
    purple: "bg-purple-50 text-purple-700",
    orange: "bg-orange-50 text-orange-700",
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {trend && (
            <p className={`text-xs mt-1 ${trend.startsWith("+") ? "text-green-600" : "text-red-600"}`}>
              {trend}
            </p>
          )}
        </div>
        {icon && (
          <div className={`p-3 rounded-lg ${colorMap[color] || colorMap.primary}`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
