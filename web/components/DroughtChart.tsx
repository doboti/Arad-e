"use client";

import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SoilPoint } from "@/lib/types";

const SHALLOW_LABEL = "Felső réteg (~0–9 cm)";
const DEEP_LABEL = "Mélyebb réteg (~9–81 cm)";

export default function DroughtChart({ soil }: { soil: SoilPoint[] }) {
  if (soil.length === 0) {
    return <p className="text-sm text-slate-400">Nincs talajnedvesség-adat.</p>;
  }

  const data = [...soil]
    .sort((a, b) => (a.shallow_vwc ?? 0) - (b.shallow_vwc ?? 0)) // driest first
    .map((s) => ({
      location: s.location,
      [SHALLOW_LABEL]: s.shallow_vwc !== null ? Math.round(s.shallow_vwc * 1000) / 10 : null,
      [DEEP_LABEL]: s.deep_vwc !== null ? Math.round(s.deep_vwc * 1000) / 10 : null,
    }));

  const latest = soil.reduce((max, s) => (s.measured_at > max ? s.measured_at : max), soil[0].measured_at);

  return (
    <div>
      <ResponsiveContainer width="100%" height={340}>
        <BarChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="location" stroke="#94a3b8" fontSize={12} />
          <YAxis stroke="#94a3b8" fontSize={12} unit="%" />
          <Tooltip />
          <Legend />
          <Bar dataKey={SHALLOW_LABEL} fill="#c47f17" />
          <Bar dataKey={DEEP_LABEL} fill="#1f77b4" />
        </BarChart>
      </ResponsiveContainer>
      <p className="mt-2 text-xs text-slate-400">
        Open-Meteo modellezett talajnedvesség-adatai néhány mintaponton - tájékoztató jellegű, nem hivatalos
        aszálytérkép. Mérve: {new Date(latest).toLocaleString("hu-HU")}
      </p>
    </div>
  );
}
