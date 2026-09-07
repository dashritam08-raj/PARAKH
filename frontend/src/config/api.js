// ============================================================
// PARAKH API CONFIGURATION
// ============================================================
// Automatically uses the same host as the frontend.
//
// Laptop:
//   http://localhost:5173  -> http://localhost:8000
//
// LAN / Phone:
//   http://192.168.0.107:5173 -> http://192.168.0.107:8000
//
// VITE_API_URL can override this when needed.
// ============================================================

const API_PORT = 8000;

const configuredApiUrl =
  import.meta.env.VITE_API_URL?.trim();

export const API_BASE_URL =
  configuredApiUrl ||
  `${window.location.protocol}//${window.location.hostname}:${API_PORT}`;
