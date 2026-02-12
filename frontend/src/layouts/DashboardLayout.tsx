import React from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

interface Props {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: Props) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* 좌측 사이드바 */}
      <Sidebar />

      {/* 메인 영역 */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* 상단 헤더 */}
        <Header />

        {/* 중앙 콘텐츠 */}
        <main className="flex-1 overflow-y-auto bg-gray-50 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
