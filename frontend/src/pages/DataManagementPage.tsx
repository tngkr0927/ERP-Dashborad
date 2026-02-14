import { useEffect, useState } from "react";
import {
  fetchRawDataList,
  deleteRawData,
  type RawDataItem,
} from "../services/api";

export default function DataManagementPage() {
  const [items, setItems] = useState<RawDataItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 날짜 필터
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const loadData = async (start?: string, end?: string) => {
    setLoading(true);
    setError("");
    try {
      const res = await fetchRawDataList(start, end);
      setItems(res.items);
      setTotal(res.total);
    } catch {
      setError("데이터를 불러오는 데 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 첫 로드: 전체 조회
  useEffect(() => {
    loadData();
  }, []);

  const handleSearch = () => {
    loadData(startDate || undefined, endDate || undefined);
  };

  const handleDelete = async (item: RawDataItem) => {
    const msg = item.has_analysis
      ? `"${item.filename}" 데이터와 관련된 분석 결과도 함께 삭제됩니다.\n정말 삭제하시겠습니까?`
      : `"${item.filename}" 데이터를 삭제하시겠습니까?`;

    if (!window.confirm(msg)) return;

    try {
      await deleteRawData(item.id);
      setItems((prev) => prev.filter((r) => r.id !== item.id));
      setTotal((prev) => prev - 1);
    } catch {
      alert("삭제에 실패했습니다.");
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">데이터 관리</h1>

      {/* 검색 필터 */}
      <div className="flex flex-wrap items-end gap-4 rounded-lg border bg-white p-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            시작일
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">
            종료일
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={handleSearch}
          className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          조회
        </button>
        <button
          onClick={() => {
            setStartDate("");
            setEndDate("");
            loadData();
          }}
          className="rounded-lg border border-gray-300 px-5 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-50"
        >
          초기화
        </button>
        <span className="ml-auto text-sm text-gray-500">
          총 {total}건
        </span>
      </div>

      {/* 에러 */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* 데이터 테이블 */}
      <div className="overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-left text-sm">
          <thead className="border-b bg-gray-50 text-xs font-semibold uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">파일명</th>
              <th className="px-4 py-3">업로드 일시</th>
              <th className="px-4 py-3 text-center">행 수</th>
              <th className="px-4 py-3 text-center">상태</th>
              <th className="px-4 py-3 text-center">관리</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  불러오는 중...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                  데이터가 없습니다.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-600">
                    {item.id}
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-800">
                    {item.filename}
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {formatDate(item.created_at)}
                  </td>
                  <td className="px-4 py-3 text-center text-gray-600">
                    {item.row_count}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {item.has_analysis ? (
                      <span className="inline-block rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
                        분석됨
                      </span>
                    ) : (
                      <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
                        미분석
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => handleDelete(item)}
                      className="rounded bg-red-50 px-3 py-1 text-xs font-medium text-red-600 transition hover:bg-red-100"
                    >
                      삭제
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
