import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  fetchRawDataList,
  runAnalysis,
  type RawDataItem,
  type AnalyzeResponse,
} from "../services/api";

export default function AnalyzePage() {
  const [rawDataList, setRawDataList] = useState<RawDataItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [userPrompt, setUserPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState("");

  // 페이지 진입 시 업로드된 데이터 목록 로드
  useEffect(() => {
    fetchRawDataList()
      .then((res) => setRawDataList(res.items))
      .catch(() => {});
  }, []);

  const handleAnalyze = async () => {
    if (!selectedId) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await runAnalysis(selectedId as number, userPrompt);
      setResult(res);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ?? "분석에 실패했습니다. 다시 시도해주세요."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">AI 분석 실행</h1>
      <p className="text-sm text-gray-500">
        업로드된 데이터를 선택하고, Gemini AI에게 분석을 요청하세요.
      </p>

      {/* 데이터 선택 + 프롬프트 입력 */}
      <div className="space-y-4 rounded-lg border bg-white p-6">
        {/* 드롭다운 */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            분석할 데이터 선택
          </label>
          <select
            value={selectedId}
            onChange={(e) =>
              setSelectedId(e.target.value ? Number(e.target.value) : "")
            }
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">-- 데이터를 선택하세요 --</option>
            {rawDataList.map((item) => (
              <option key={item.id} value={item.id}>
                [ID: {item.id}] {item.filename} ({item.row_count}행)
              </option>
            ))}
          </select>
        </div>

        {/* 프롬프트 */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            추가 지시사항 (선택)
          </label>
          <textarea
            value={userPrompt}
            onChange={(e) => setUserPrompt(e.target.value)}
            placeholder="예: 월별 매출 추이를 분석해줘, 비용 항목별로 비교해줘..."
            rows={3}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* 분석 버튼 */}
        <button
          onClick={handleAnalyze}
          disabled={!selectedId || loading}
          className="w-full rounded-lg bg-indigo-600 px-6 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-300"
        >
          {loading ? "분석 중... (Gemini AI 처리 대기)" : "분석 실행"}
        </button>
      </div>

      {/* 로딩 표시 */}
      {loading && (
        <div className="flex items-center justify-center rounded-lg border bg-white p-12">
          <div className="text-center">
            <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600"></div>
            <p className="text-sm text-gray-500">
              Gemini AI가 데이터를 분석하고 있습니다...
            </p>
          </div>
        </div>
      )}

      {/* 분석 결과 */}
      {result && (
        <div className="space-y-4">
          {/* 요약 */}
          <div className="rounded-lg border bg-white p-6">
            <h2 className="mb-3 text-lg font-semibold text-gray-800">
              분석 요약
            </h2>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700">
              {result.summary}
            </p>
          </div>

          {/* 차트 */}
          {result.chart_data && result.chart_data.length > 0 && (
            <div className="rounded-lg border bg-white p-6">
              <h2 className="mb-4 text-lg font-semibold text-gray-800">
                시각화
              </h2>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={result.chart_data}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* 에러 */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}
