import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { TrendingUp, Loader2 } from "lucide-react";
import { fetchRevenue } from "../../services/api";
import { formatCurrency } from "../../utils/format";

function parseMinutes(timeStr) {
  const [timePart, meridiem] = timeStr.split(" ");
  let [h, m] = timePart.split(":").map(Number);
  if (meridiem === "PM" && h !== 12) h += 12;
  if (meridiem === "AM" && h === 12) h = 0;
  return h * 60 + m;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-md px-3 py-2 shadow-lg">
      <p className="text-xs text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-cyber-emerald">
        {formatCurrency(payload[0].value)}
      </p>
    </div>
  );
}

export default function RevenueChart() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const json = await fetchRevenue();
        if (!active) return;

        const transformed = Object.entries(json)
          .map(([time, amount]) => ({ time, amount }))
          .sort((a, b) => parseMinutes(a.time) - parseMinutes(b.time));

        setData(transformed);
        setError(null);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    load();
    const interval = setInterval(load, 2000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 glow-emerald">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800">
        <TrendingUp className="w-4 h-4 text-cyber-emerald" />
        <h2 className="text-sm font-semibold text-slate-200 tracking-wide uppercase">
          Transaction Volume
        </h2>
        {loading && (
          <Loader2 className="ml-auto w-4 h-4 text-slate-500 animate-spin" />
        )}
      </div>

      {/* Chart */}
      <div className="p-4">
        {error ? (
          <div className="flex items-center justify-center h-64 text-sm text-red-400">
            Failed to load revenue data: {error}
          </div>
        ) : data.length === 0 && !loading ? (
          <div className="flex items-center justify-center h-64 text-sm text-slate-600">
            No revenue data available yet
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff9d" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00ff9d" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="time"
                tick={{ fill: "#64748b", fontSize: 11 }}
                axisLine={{ stroke: "#334155" }}
                tickLine={false}
              />
              <YAxis
                tickFormatter={(v) => formatCurrency(v, 0)}
                tick={{ fill: "#64748b", fontSize: 11 }}
                axisLine={{ stroke: "#334155" }}
                tickLine={false}
                width={80}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="#00ff9d"
                strokeWidth={2}
                fill="url(#revenueGradient)"
                dot={false}
                activeDot={{ r: 4, fill: "#00ff9d", stroke: "#0f172a", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
