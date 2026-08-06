export type Category = "lakes" | "rivers";

export interface Station {
  voa: string;
  river: string;
  name: string;
  display_name: string | null;
  category: Category;
  lat: number | null;
  lon: number | null;
  lkv_cm: number | null;
  lnv_cm: number | null;
  kf1_cm: number | null;
  latest_measured_at: string | null;
  water_level_cm: number | null;
  discharge_m3s: number | null;
  water_temp_c: number | null;
  previous_water_level_cm: number | null;
}

export interface Measurement {
  measured_at: string;
  water_level_cm: number | null;
  discharge_m3s: number | null;
  water_temp_c: number | null;
}

export interface SoilPoint {
  location: string;
  lat: number;
  lon: number;
  measured_at: string;
  shallow_vwc: number | null;
  deep_vwc: number | null;
}
