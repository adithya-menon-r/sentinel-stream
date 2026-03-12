import { Link, useLocation } from "react-router-dom";
import { Shield, Search, LayoutDashboard } from "lucide-react";

export default function Navbar({ isConnected }) {
  const { pathname } = useLocation();

  const linkClass = (path) =>
    `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
      pathname === path
        ? "bg-slate-800 text-cyber-blue"
        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
    }`;

  return (
    <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-2 group">
            <Shield className="w-6 h-6 text-cyber-blue group-hover:drop-shadow-[0_0_6px_rgba(0,212,255,0.5)] transition" />
            <span className="text-lg font-bold tracking-tight">
              <span className="text-cyber-blue">Sentinel</span>{" "}
              <span className="text-slate-300">Stream</span>
            </span>
          </Link>

          {/* Nav Links */}
          <div className="flex items-center gap-2">
            <Link to="/" className={linkClass("/")}>
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </Link>
            <Link to="/investigate" className={linkClass("/investigate")}>
              <Search className="w-4 h-4" />
              Investigate
            </Link>

            {/* WebSocket Status */}
            <div className="ml-3 flex items-center gap-2 pl-3 border-l border-slate-800">
              <div
                className={`w-2 h-2 rounded-full ${
                  isConnected
                    ? "bg-cyber-emerald animate-pulse-glow"
                    : "bg-cyber-red"
                }`}
              />
              <span className="text-xs text-slate-500">
                {isConnected ? "LIVE" : "OFFLINE"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
