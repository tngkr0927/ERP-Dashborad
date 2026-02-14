import axios from "axios";

const api = axios.create({
  baseURL: "/api",
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RawDataItem {
  id: number;
  filename: string;
  created_at: string;
  row_count: number;
  has_analysis: boolean;
}

export interface RawDataListResponse {
  items: RawDataItem[];
  total: number;
}

export interface UploadResponse {
  id: number;
  filename: string;
  message: string;
}

export interface AnalyzeResponse {
  id: number;
  raw_data_id: number;
  summary: string;
  chart_data: { label: string; value: number }[];
}

export interface DashboardResult {
  id: number;
  raw_data_id: number;
  analyzed_at: string;
  summary: string;
  chart_data: { label: string; value: number }[];
}

// ---------------------------------------------------------------------------
// API 함수
// ---------------------------------------------------------------------------

/** 엑셀/CSV 파일 업로드 */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await api.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

/** 원본 데이터 목록 조회 */
export async function fetchRawDataList(
  startDate?: string,
  endDate?: string,
): Promise<RawDataListResponse> {
  const params: Record<string, string> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  const res = await api.get<RawDataListResponse>("/raw-data", { params });
  return res.data;
}

/** 원본 데이터 삭제 */
export async function deleteRawData(id: number): Promise<void> {
  await api.delete(`/raw-data/${id}`);
}

/** Gemini AI 분석 실행 */
export async function runAnalysis(
  rawDataId: number,
  userPrompt: string = "",
): Promise<AnalyzeResponse> {
  const res = await api.post<AnalyzeResponse>("/analyze", {
    raw_data_id: rawDataId,
    user_prompt: userPrompt,
  });
  return res.data;
}

/** 대시보드 결과 조회 */
export async function fetchDashboard(
  limit = 10,
): Promise<DashboardResult[]> {
  const res = await api.get<{ results: DashboardResult[] }>("/dashboard", {
    params: { limit },
  });
  return res.data.results;
}

export default api;
