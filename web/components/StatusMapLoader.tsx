"use client";

import dynamic from "next/dynamic";
import type { Station } from "@/lib/types";

// Leaflet touches `window`, so it can only run in the browser. `ssr: false`
// on next/dynamic is only allowed from inside a Client Component (Next.js
// 16 errors if it's called from a Server Component), hence this wrapper.
const StatusMap = dynamic(() => import("./StatusMap"), {
  ssr: false,
  loading: () => <div className="h-[420px] animate-pulse rounded-lg bg-slate-100" />,
});

export default function StatusMapLoader({ stations }: { stations: Station[] }) {
  return <StatusMap stations={stations} />;
}
