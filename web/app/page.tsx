import DroughtChart from "@/components/DroughtChart";
import HeroNumbers from "@/components/HeroNumbers";
import StationSection from "@/components/StationSection";
import StatusMapLoader from "@/components/StatusMapLoader";
import { fetchHistory, fetchSoilMoisture, fetchStations } from "@/lib/api";
import type { Measurement } from "@/lib/types";

export default async function Home() {
  const [stations, soil] = await Promise.all([fetchStations(), fetchSoilMoisture()]);

  const histories: Record<string, Measurement[]> = {};
  await Promise.all(
    stations.map(async (s) => {
      histories[s.voa] = await fetchHistory(s.voa, 7);
    }),
  );

  const lakes = stations.filter((s) => s.category === "lakes");
  const rivers = stations.filter((s) => s.category === "rivers");

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="flex items-center gap-2 text-3xl font-bold text-slate-900">💧 Hol a víz?</h1>
      <p className="mt-1 text-slate-500">Valós idejű hazai víz- és aszályfigyelő - MVP</p>

      {stations.length === 0 ? (
        <p className="mt-8 rounded-md bg-amber-50 px-4 py-3 text-amber-800">
          Nincs még adat. Futtasd az <code>etl/run.py</code> szkriptet, hogy legyen mit megjeleníteni.
        </p>
      ) : (
        <>
          <div className="mt-8">
            <HeroNumbers stations={stations} soil={soil} />
          </div>

          <section className="mt-10">
            <h2 className="mb-4 text-xl font-semibold text-slate-900">Országos helyzetkép</h2>
            <StatusMapLoader stations={stations} />
          </section>

          <StationSection title="Nagy tavaink" stations={lakes} histories={histories} />
          <StationSection title="Folyók és vízgyűjtők" stations={rivers} histories={histories} />

          <section className="mt-10 mb-16">
            <h2 className="mb-4 text-xl font-semibold text-slate-900">Aszály és talajnedvesség</h2>
            <DroughtChart soil={soil} />
          </section>
        </>
      )}
    </main>
  );
}
