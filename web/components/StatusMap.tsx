"use client";

import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import type { Station } from "@/lib/types";
import { classifyStatus, labelFor, STATUS_STYLE } from "@/lib/station";

export default function StatusMap({ stations }: { stations: Station[] }) {
  const points = stations.filter(
    (s): s is Station & { lat: number; lon: number } => s.lat !== null && s.lon !== null,
  );

  return (
    <div>
      <div className="h-[420px] w-full overflow-hidden rounded-lg border border-slate-200">
        <MapContainer center={[47.16, 19.5]} zoom={7} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {points.map((s) => {
            const status = classifyStatus(s.water_level_cm, s.lkv_cm, s.lnv_cm, s.kf1_cm);
            const { color } = STATUS_STYLE[status];
            return (
              <CircleMarker
                key={s.voa}
                center={[s.lat, s.lon]}
                radius={9}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.9, weight: 1 }}
              >
                <Tooltip direction="top" offset={[0, -8]} permanent>
                  {labelFor(s)}
                </Tooltip>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-slate-600">
        {Object.values(STATUS_STYLE).map(({ color, label }) => (
          <span key={label} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
