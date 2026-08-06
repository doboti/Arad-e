"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Measurement, Station } from "@/lib/types";
import { labelFor } from "@/lib/station";

export default function StationChart({ station, history }: { station: Station; history: Measurement[] }) {
  const data = history.map((m) => ({ ...m, t: new Date(m.measured_at).getTime() }));
  const hasData = data.length > 0;
  // A single point gives Recharts nothing to size a numeric time axis by;
  // pad the domain manually rather than let it collapse to a point.
  const xDomain: [number, number] | [string, string] =
    data.length === 1 ? [data[0].t - 12 * 3600_000, data[0].t + 12 * 3600_000] : ["dataMin", "dataMax"];

  return (
    <div className="mb-8">
      <div className="mb-1 flex flex-wrap items-baseline gap-x-2">
        <h3 className="font-medium text-slate-800">{labelFor(station)}</h3>
        {station.category === "rivers" && station.discharge_m3s !== null && (
          <span className="text-sm text-slate-500">vízhozam: {Math.round(station.discharge_m3s)} m³/s</span>
        )}
      </div>
      {hasData ? (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="t"
              type="number"
              domain={xDomain}
              tickFormatter={(t: number) => new Date(t).toLocaleDateString("hu-HU", { month: "short", day: "numeric" })}
              stroke="#94a3b8"
              fontSize={12}
            />
            <YAxis stroke="#94a3b8" fontSize={12} unit=" cm" width={70} domain={["auto", "auto"]} />
            <Tooltip
              labelFormatter={(label) => new Date(Number(label)).toLocaleString("hu-HU")}
              formatter={(value) => [`${value} cm`, "Vízállás"]}
            />
            {station.lnv_cm !== null && (
              <ReferenceLine
                y={station.lnv_cm}
                stroke="#dc2626"
                strokeDasharray="4 4"
                ifOverflow="extendDomain"
                label={{ value: "LNV (történelmi max.)", position: "insideTopLeft", fontSize: 11, fill: "#dc2626" }}
              />
            )}
            {station.lkv_cm !== null && (
              <ReferenceLine
                y={station.lkv_cm}
                stroke="#d97706"
                strokeDasharray="4 4"
                ifOverflow="extendDomain"
                label={{ value: "LKV (történelmi min.)", position: "insideBottomLeft", fontSize: 11, fill: "#d97706" }}
              />
            )}
            <Line
              type="monotone"
              dataKey="water_level_cm"
              stroke="#1f77b4"
              strokeWidth={2}
              dot={{ r: 3 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-sm text-slate-400">Nincs adat az elmúlt 7 napból.</p>
      )}
    </div>
  );
}
