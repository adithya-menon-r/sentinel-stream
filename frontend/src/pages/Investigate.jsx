import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import SearchBar from "../features/investigate/SearchBar";
import UserProfile from "../features/investigate/UserProfile";
import EventTable from "../features/investigate/EventTable";
import { fetchUserProfile, fetchUserHistory } from "../services/api";

export default function Investigate() {
  const [query, setQuery] = useState("");
  const [profile, setProfile] = useState(null);
  const [events, setEvents] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSearch() {
    const userId = query.trim();
    if (!userId) return;

    setLoading(true);
    setError(null);
    setProfile(null);
    setEvents(null);

    try {
      const [profileData, historyData] = await Promise.all([
        fetchUserProfile(userId),
        fetchUserHistory(userId),
      ]);

      if (profileData === null || historyData === null) {
        setError("User not found");
        return;
      }

      setProfile(profileData);
      setEvents(historyData.events || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-200">
          User Investigation
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Look up a user ID to view their risk profile and recent event logs.
        </p>
      </div>

      {/* Search */}
      <SearchBar
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
        loading={loading}
      />

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <span className="text-sm text-red-400">{error}</span>
        </div>
      )}

      {/* Profile Cards */}
      <UserProfile profile={profile} loading={loading} />

      {/* Event History */}
      {(events || loading) && (
        <div>
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Recent Events
          </h2>
          <EventTable events={events} loading={loading} />
        </div>
      )}
    </div>
  );
}
