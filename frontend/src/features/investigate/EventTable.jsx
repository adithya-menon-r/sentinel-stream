import { Loader2 } from "lucide-react";
import { EVENT_TYPE_STYLES } from "../../constants/alerts";
import { formatCurrency } from "../../utils/format";

function TypeBadge({ type }) {
  const style = EVENT_TYPE_STYLES[type] || {
    bg: "bg-slate-500/15",
    text: "text-slate-400",
    border: "border-slate-500/30",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${style.bg} ${style.text} ${style.border}`}
    >
      {type}
    </span>
  );
}

function formatAmount(value) {
  const num = parseFloat(value);
  if (!num || num <= 0) return "—";
  return formatCurrency(num);
}

export default function EventTable({ events, loading }) {
  if (loading) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-8">
        <div className="flex items-center justify-center gap-2 text-slate-500">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading event history...</span>
        </div>
      </div>
    );
  }

  if (!events) return null;

  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-8 text-center text-sm text-slate-500">
        No events found for this user.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-800/40">
              {["Timestamp", "Type", "Amount", "IP Address", "Device", "Status"].map(
                (col) => (
                  <th
                    key={col}
                    className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wider"
                  >
                    {col}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {events.map((event, i) => (
              <tr
                key={`${event.timestamp}-${i}`}
                className="hover:bg-slate-800/30 transition-colors"
              >
                <td className="px-4 py-3 font-mono text-slate-300 whitespace-nowrap">
                  {event.timestamp}
                </td>
                <td className="px-4 py-3">
                  <TypeBadge type={event.type} />
                </td>
                <td className="px-4 py-3 font-mono text-slate-300">
                  {formatAmount(event.amount)}
                </td>
                <td className="px-4 py-3 font-mono text-slate-400">
                  {event.ip}
                </td>
                <td className="px-4 py-3 font-mono text-slate-400 text-xs">
                  {event.device}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`text-xs font-semibold ${
                      event.status === "SUCCESS"
                        ? "text-emerald-400"
                        : "text-red-400"
                    }`}
                  >
                    {event.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
