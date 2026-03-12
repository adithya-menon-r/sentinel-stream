import { Search } from "lucide-react";

export default function SearchBar({ value, onChange, onSearch, loading }) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && value.trim()) {
      onSearch();
    }
  };

  return (
    <div className="flex items-center gap-3">
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter user ID (e.g. user_42)"
          className="w-full pl-10 pr-4 py-2 rounded-md bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue/30 transition"
        />
      </div>
      <button
        onClick={onSearch}
        disabled={!value.trim() || loading}
        className="px-5 py-2 rounded-md bg-cyber-blue/15 text-cyber-blue border border-cyber-blue/30 text-sm font-medium hover:bg-cyber-blue/25 disabled:opacity-40 disabled:cursor-not-allowed transition"
      >
        {loading ? "Searching..." : "Search"}
      </button>
    </div>
  );
}
