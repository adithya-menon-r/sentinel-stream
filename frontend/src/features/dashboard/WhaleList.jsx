import { Crown, DollarSign } from "lucide-react";
import { formatCurrency } from "../../utils/format";

export default function WhaleList({ whales }) {
  return (
    <div className="h-full flex flex-col rounded-lg border border-slate-800 bg-slate-900/60 glow-blue">
      {/* Header */}
      <div className="shrink-0 flex items-center gap-2 px-4 py-3 border-b border-slate-800">
        <Crown className="w-4 h-4 text-cyber-gold" />
        <h2 className="text-sm font-semibold text-slate-200 tracking-wide uppercase">
          Whale Leaderboard
        </h2>
        <span className="ml-auto text-xs text-slate-500 font-mono">
          Top 10
        </span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto max-h-[420px] p-2 space-y-1">
        {whales.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-slate-600 text-sm font-mono">
            Loading transactors...
          </div>
        ) : (
          whales.map((whale, i) => (
            <div
              key={whale.user_id}
              className="flex items-center gap-3 px-3 py-2 rounded-md bg-slate-800/40 hover:bg-slate-800/70 transition-colors font-mono text-xs"
            >
              <span className="w-4 text-slate-500">{i + 1}.</span>
              <span className="text-cyber-blue font-semibold grow">{whale.user_id}</span>
              <div className="flex items-center gap-1 text-cyber-gold">
                <DollarSign className="w-3 h-3" />
                <span>{whale.total_amount}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
