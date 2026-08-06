import type { SoilPoint, Station } from "@/lib/types";
import { labelFor } from "@/lib/station";

const HERO_STATIONS: [string, string][] = [
  ["Balaton", "Siófok"],
  ["Duna", "Budapest"],
  ["Duna", "Paks"],
  ["Tisza", "Szolnok"],
];

export default function HeroNumbers({ stations, soil }: { stations: Station[]; soil: SoilPoint[] }) {
  const heroRows = HERO_STATIONS.map(([river, name]) =>
    stations.find((s) => s.river === river && s.name === name),
  ).filter((s): s is Station => Boolean(s));

  const avgShallow =
    soil.length > 0 ? soil.reduce((sum, s) => sum + (s.shallow_vwc ?? 0), 0) / soil.length : null;

  return (
    <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-5">
      {heroRows.map((s) => {
        const delta =
          s.previous_water_level_cm !== null && s.water_level_cm !== null
            ? s.water_level_cm - s.previous_water_level_cm
            : null;
        return (
          <div key={s.voa}>
            <div className="text-sm text-slate-500">{labelFor(s)}</div>
            <div className="text-3xl font-semibold text-slate-900">
              {s.water_level_cm !== null ? `${Math.round(s.water_level_cm)} cm` : "–"}
            </div>
            {delta !== null && (
              <div className={`text-sm ${delta >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                {delta >= 0 ? "+" : ""}
                {Math.round(delta)} cm
              </div>
            )}
            <div className="text-xs text-slate-400">
              Mérve: {s.latest_measured_at ? new Date(s.latest_measured_at).toLocaleString("hu-HU") : "–"}
            </div>
          </div>
        );
      })}
      {avgShallow !== null && (
        <div>
          <div className="text-sm text-slate-500">Talajnedvesség (országos átlag)</div>
          <div className="text-3xl font-semibold text-slate-900">{Math.round(avgShallow * 100)}%</div>
          <div className="text-xs text-slate-400">{soil.length} mintaponton, felső ~9 cm</div>
        </div>
      )}
    </div>
  );
}
