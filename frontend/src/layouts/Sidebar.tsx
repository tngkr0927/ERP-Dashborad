const menuItems = [
  { label: "대시보드", href: "#" },
  { label: "데이터 업로드", href: "#upload" },
  { label: "분석 실행", href: "#analyze" },
  { label: "데이터 관리", href: "#management" },
];

export default function Sidebar() {
  const currentHash = window.location.hash || "#";

  return (
    <aside className="flex w-56 flex-col bg-gray-900 text-gray-100">
      <div className="flex h-14 items-center justify-center border-b border-gray-700 text-lg font-bold tracking-wide">
        ERP Dashboard
      </div>
      <nav className="mt-4 flex-1 space-y-1 px-3">
        {menuItems.map((item) => {
          const isActive = currentHash === item.href;
          return (
            <a
              key={item.label}
              href={item.href}
              className={`block rounded px-3 py-2 text-sm transition ${
                isActive
                  ? "bg-blue-600 font-semibold text-white"
                  : "hover:bg-gray-700"
              }`}
            >
              {item.label}
            </a>
          );
        })}
      </nav>
    </aside>
  );
}
