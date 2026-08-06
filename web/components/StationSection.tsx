import type { Measurement, Station } from "@/lib/types";
import { RIVER_ORDER } from "@/lib/station";
import StationChart from "./StationChart";

export default function StationSection({
  title,
  stations,
  histories,
}: {
  title: string;
  stations: Station[];
  histories: Record<string, Measurement[]>;
}) {
  const sorted = [...stations].sort((a, b) => {
    const ra = RIVER_ORDER[a.river] ?? 99;
    const rb = RIVER_ORDER[b.river] ?? 99;
    return ra !== rb ? ra - rb : a.name.localeCompare(b.name);
  });

  return (
    <section className="mt-10">
      <h2 className="mb-4 text-xl font-semibold text-slate-900">{title}</h2>
      {sorted.length === 0 ? (
        <p className="text-sm text-slate-400">Nincs adat ehhez a szakaszhoz.</p>
      ) : (
        sorted.map((s) => <StationChart key={s.voa} station={s} history={histories[s.voa] ?? []} />)
      )}
    </section>
  );
}
