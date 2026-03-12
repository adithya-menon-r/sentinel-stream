import { User, Hash, DollarSign, Loader2 } from "lucide-react";
import { formatCurrency } from "../../utils/format";

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <span className="text-xs uppercase tracking-wider text-slate-500">
          {label}
        </span>
      </div>
      <p className={`text-2xl font-bold font-mono ${color}`}>{value}</p>
    </div>
  );
}

export default function UserProfile({ profile, loading }) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="rounded-lg border border-slate-800 bg-slate-900/60 p-5 animate-pulse"
          >
            <div className="h-3 w-20 bg-slate-800 rounded mb-4" />
            <div className="h-7 w-28 bg-slate-800 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard
        icon={User}
        label="User ID"
        value={profile.user_id}
        color="text-cyber-blue"
      />
      <StatCard
        icon={Hash}
        label="Total Transactions"
        value={profile.total_tx_count.toLocaleString()}
        color="text-cyber-emerald"
      />
      <StatCard
        icon={DollarSign}
        label="Total Volume"
        value={formatCurrency(profile.total_tx_sum_usd)}
        color="text-cyber-yellow"
      />
    </div>
  );
}
