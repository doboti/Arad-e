import type { Station } from "./types";

export function labelFor(s: Pick<Station, "display_name" | "river" | "name">): string {
  return s.display_name ?? `${s.river} – ${s.name}`;
}

export type Status = "flood" | "normal" | "low" | "critical";

// Mirrors dashboard/app.py's classify_status: uses the official I. fokozatú
// flood-alert level (kf1) when vizugy.hu publishes one, otherwise falls back
// to the station's position between its historical min (LKV) and max (LNV).
// The 35%/12% cutoffs aren't an official standard, just a reasonable default
// absent real defense-stage data for every station.
export function classifyStatus(
  level: number | null,
  lkv: number | null,
  lnv: number | null,
  kf1: number | null,
): Status {
  if (level === null) return "normal";
  if (kf1 !== null && level >= kf1) return "flood";
  if (lkv === null || lnv === null || lnv <= lkv) return "normal";
  const position = (level - lkv) / (lnv - lkv);
  if (position >= 0.35) return "normal";
  if (position >= 0.12) return "low";
  return "critical";
}

export const STATUS_STYLE: Record<Status, { color: string; label: string }> = {
  flood: { color: "#1f77b4", label: "Áradás" },
  normal: { color: "#2ca02c", label: "Normál" },
  low: { color: "#f1c40f", label: "Alacsony" },
  critical: { color: "#e74c3c", label: "Kritikus aszály / kiszáradás" },
};

export const RIVER_ORDER: Record<string, number> = { Balaton: 0, Duna: 1, Tisza: 2 };
