/**
 * Placeholder 위젯 컴포넌트.
 *
 * TODO: 실제 차트를 추가할 때 이 컴포넌트를 Recharts 기반 위젯으로 교체하세요.
 *       예시:
 *         import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
 *         <BarChart data={data}> ... </BarChart>
 *
 *       또는 이 컴포넌트의 children 영역에 차트를 렌더링하도록 확장할 수 있습니다.
 */

interface Props {
  title: string;
  description?: string;
}

export default function PlaceholderWidget({ title, description }: Props) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 bg-white p-6 shadow-sm">
      <p className="text-base font-medium text-gray-500">{title}</p>
      {description && (
        <p className="mt-1 text-sm text-gray-400">{description}</p>
      )}
    </div>
  );
}
