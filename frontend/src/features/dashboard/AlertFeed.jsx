import { Terminal } from "lucide-react";
import { PATTERN_STYLES } from "../../constants/alerts";

function PatternBadge({ pattern }) {
  const style = PATTERN_STYLES[pattern] || {
    bg: "bg-slate-500/15",
    text: "text-slate-400",
    border: "border-slate-500/30",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-semibold border ${style.bg} ${style.text} ${style.border}`}
    >
      {pattern}
    </span>
  );
}

export default function AlertFeed({ alerts }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 glow-blue">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800">
        <Terminal className="w-4 h-4 text-cyber-blue" />
        <h2 className="text-sm font-semibold text-slate-200 tracking-wide uppercase">
          Incoming Alerts
        </h2>
        <span className="ml-auto text-xs text-slate-500 font-mono">
          {alerts.length} events
        </span>
      </div>

      {/* Scrollable feed */}
      <div className="alert-feed overflow-y-auto max-h-[420px] p-2 space-y-1">
        {alerts.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-slate-600 text-sm">
            <span className="font-mono">Waiting for alerts...</span>
          </div>
        ) : (
          alerts.map((alert, i) => (
            <div
              key={`${alert.ts}-${alert.entity}-${i}`}
              className="animate-alert-in flex items-start gap-3 px-3 py-2 rounded-md bg-slate-800/40 hover:bg-slate-800/70 transition-colors font-mono text-xs"
            >
              <span className="text-slate-500 shrink-0 w-16">{alert.ts}</span>
              <PatternBadge pattern={alert.pattern} />
              <span className="text-cyber-blue shrink-0">{alert.entity}</span>
              <span className="text-slate-400 truncate">{alert.detail}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
