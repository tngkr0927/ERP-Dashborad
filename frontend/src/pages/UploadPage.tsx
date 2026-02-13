import { useRef, useState } from "react";
import { uploadFile, type UploadResponse } from "../services/api";

export default function UploadPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    setResult(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError("");
    setResult(null);

    try {
      const res = await uploadFile(selectedFile);
      setResult(res);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err: any) {
      setError(
        err.response?.data?.detail ?? "업로드에 실패했습니다. 다시 시도해주세요."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">데이터 업로드</h1>
      <p className="text-sm text-gray-500">
        엑셀(.xlsx) 또는 CSV 파일을 업로드하면 데이터가 자동으로 파싱되어
        저장됩니다.
      </p>

      {/* 파일 선택 영역 */}
      <div className="rounded-lg border-2 border-dashed border-gray-300 bg-white p-8 text-center">
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileChange}
          className="hidden"
          id="file-input"
        />
        <label
          htmlFor="file-input"
          className="cursor-pointer text-blue-600 hover:text-blue-800"
        >
          <div className="mb-3 text-4xl text-gray-400">&#128206;</div>
          <span className="text-sm font-medium">
            파일을 선택하세요 (.csv, .xlsx)
          </span>
        </label>
        {selectedFile && (
          <p className="mt-3 text-sm text-gray-700">
            선택된 파일: <strong>{selectedFile.name}</strong> (
            {(selectedFile.size / 1024).toFixed(1)} KB)
          </p>
        )}
      </div>

      {/* 업로드 버튼 */}
      <button
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
        className="w-full rounded-lg bg-blue-600 px-6 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-300"
      >
        {uploading ? "업로드 중..." : "업로드"}
      </button>

      {/* 성공 메시지 */}
      {result && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="font-semibold text-green-800">업로드 완료!</p>
          <p className="mt-1 text-sm text-green-700">
            파일: {result.filename} | ID: {result.id} | {result.message}
          </p>
          <p className="mt-2 text-xs text-green-600">
            이 ID({result.id})를 분석 페이지에서 사용할 수 있습니다.
          </p>
        </div>
      )}

      {/* 에러 메시지 */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}
