import type { Measurement, SoilPoint, Station } from "./types";

const API_BASE = process.env.API_BASE_URL ?? "http://localhost:8000";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`);
  }
  return res.json();
}

export function fetchStations(): Promise<Station[]> {
  return getJSON<Station[]>("/api/stations");
}

export function fetchHistory(voa: string, days = 7): Promise<Measurement[]> {
  return getJSON<Measurement[]>(`/api/stations/${voa}/history?days=${days}`);
}

export function fetchSoilMoisture(): Promise<SoilPoint[]> {
  return getJSON<SoilPoint[]>("/api/soil-moisture");
}
