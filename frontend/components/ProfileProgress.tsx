'use client';

import { InformationProgress } from '@/lib/types';

type ProfileProgressProps = {
  progress: InformationProgress;
};

const categoryLabels: Record<string, string> = {
  basic_info: '基本情報',
  relationship: 'パートナー情報',
  lifestyle: 'ライフスタイル',
  personality: '性格',
  children_info: '子ども情報',
};

export default function ProfileProgress({ progress }: ProfileProgressProps) {
  const categories = Object.entries(progress);

  if (categories.length === 0) {
    return null;
  }

  const totalCollected = categories.reduce(
    (sum, [, data]) => sum + (data?.collected || 0),
    0
  );
  const totalRequired = categories.reduce(
    (sum, [, data]) => sum + (data?.total || 0),
    0
  );
  const overallPercentage =
    totalRequired > 0 ? Math.round((totalCollected / totalRequired) * 100) : 0;

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2">
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium text-gray-600 whitespace-nowrap">
          進捗
        </span>
        <div className="flex-1">
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-gradient-to-r from-primary-500 to-pink-500 h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${overallPercentage}%` }}
            />
          </div>
        </div>
        <span className="text-xs font-bold text-primary-600 whitespace-nowrap">
          {overallPercentage}%
        </span>
      </div>

      <div className="flex gap-2 mt-1 text-xs text-gray-500">
        {categories.map(([key, data]) => {
          const collected = data?.collected || 0;
          const total = data?.total || 0;

          return (
            <span key={key} className="whitespace-nowrap">
              {categoryLabels[key] || key}: {collected}/{total}
            </span>
          );
        })}
      </div>
    </div>
  );
}
