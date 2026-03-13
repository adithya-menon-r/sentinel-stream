/**
 * Tailwind class maps for alert pattern badges.
 * Used by AlertFeed (dashboard) and any future alert-aware component.
 */
export const PATTERN_STYLES = {
  "Suspicious Node": {
    bg: "bg-orange-500/15",
    text: "text-orange-400",
    border: "border-orange-500/30",
  },
  "Rapid Transfers": {
    bg: "bg-yellow-500/15",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
  },
};

/**
 * Tailwind class maps for event type badges.
 * Used by EventTable (investigate) and any future event-aware component.
 */
export const EVENT_TYPE_STYLES = {
  login_success: {
    bg: "bg-emerald-500/15",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
  },
  login_failed: {
    bg: "bg-red-500/15",
    text: "text-red-400",
    border: "border-red-500/30",
  },
  transfer_attempt: {
    bg: "bg-blue-500/15",
    text: "text-blue-400",
    border: "border-blue-500/30",
  },
  password_reset: {
    bg: "bg-yellow-500/15",
    text: "text-yellow-400",
    border: "border-yellow-500/30",
  },
};
