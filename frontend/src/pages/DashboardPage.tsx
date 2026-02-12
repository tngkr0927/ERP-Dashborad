import PlaceholderWidget from "../components/PlaceholderWidget";

/**
 * 대시보드 메인 페이지.
 *
 * CSS Grid 2x2 레이아웃으로 위젯을 배치합니다.
 *
 * TODO: PlaceholderWidget을 실제 Recharts 차트 컴포넌트(예: ChartWidget.tsx)로
 *       교체하세요. fetchDashboard()로 받은 데이터를 각 위젯에 전달하면 됩니다.
 */

const widgets = [
  {
    title: "차트 영역 A (준비 중)",
    description: "매출 추이 등의 라인/바 차트가 들어갈 자리입니다.",
  },
  {
    title: "차트 영역 B (준비 중)",
    description: "비용 분석 등의 파이/도넛 차트가 들어갈 자리입니다.",
  },
  {
    title: "데이터 그리드 영역 C (준비 중)",
    description: "원본 데이터 테이블이 들어갈 자리입니다.",
  },
  {
    title: "KPI 영역 D (준비 중)",
    description: "핵심 지표 카드가 들어갈 자리입니다.",
  },
];

export default function DashboardPage() {
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      {/* TODO: 나중에 Recharts 컴포넌트는 여기에 넣으세요 */}
      {widgets.map((w) => (
        <PlaceholderWidget
          key={w.title}
          title={w.title}
          description={w.description}
        />
      ))}
    </div>
  );
}
