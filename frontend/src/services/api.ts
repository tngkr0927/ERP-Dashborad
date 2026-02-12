import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export interface DashboardResult {
  id: number;
  analyzed_at: string;
  analysis_type: string;
  result_data: Record<string, unknown>;
}

export async function fetchDashboard(
  limit = 10,
): Promise<DashboardResult[]> {
  const res = await api.get<{ results: DashboardResult[] }>("/dashboard", {
    params: { limit },
  });
  return res.data.results;
}

export async function uploadData(
  sourceSystem: string,
  payload: Record<string, unknown>,
) {
  return api.post("/upload", { source_system: sourceSystem, payload });
}

export async function runAnalysis(
  analysisType = "dummy",
  sourceSystem?: string,
) {
  return api.post("/analyze", {
    analysis_type: analysisType,
    source_system: sourceSystem ?? null,
  });
}

export default api;
