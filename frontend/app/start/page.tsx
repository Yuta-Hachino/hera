'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createSession } from '@/lib/api';
import LoadingSpinner from '@/components/LoadingSpinner';
import { withAuth } from '@/lib/with-auth';

function StartPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const session = await createSession();
      router.push(`/chat/${session.session_id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'セッションの作成に失敗しました'
      );
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-purple-100 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl p-8 md:p-12">
        <div className="text-center">
          {/* タイトル */}
          <h1 className="text-4xl md:text-5xl font-bold text-gray-800 mb-4">
            AIファミリー・シミュレーター
          </h1>
          <p className="text-xl text-primary-600 font-semibold mb-8">
            未来の家族を体験
          </p>

          {/* 説明文 */}
          <div className="text-left space-y-4 mb-10 text-gray-700">
            <p className="leading-relaxed">
              このアプリケーションは、AI家族愛の神「ヘーラー（Hera）」との対話を通じて、
              あなたの未来の家族像を描き出します。
            </p>
            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <h2 className="font-semibold text-primary-700 mb-2">
                体験できること：
              </h2>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start">
                  <span className="text-primary-500 mr-2">✓</span>
                  <span>AIエージェント「ヘーラー」との自然な対話</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-500 mr-2">✓</span>
                  <span>Live2Dアバターが話しかけてくる没入体験</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-500 mr-2">✓</span>
                  <span>あなたに合わせた家族の未来ストーリー生成</span>
                </li>
                <li className="flex items-start">
                  <span className="text-primary-500 mr-2">✓</span>
                  <span>子どもを持つ未来をポジティブに体験</span>
                </li>
              </ul>
            </div>
            <p className="text-sm text-gray-600">
              所要時間：約10〜15分
            </p>
          </div>

          {/* エラー表示 */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* 開始ボタン */}
          <button
            onClick={handleStart}
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-primary-500 to-pink-500 text-white font-bold py-4 px-8 rounded-xl text-lg hover:from-primary-600 hover:to-pink-600 focus:outline-none focus:ring-4 focus:ring-primary-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <LoadingSpinner />
                <span className="ml-2">準備中...</span>
              </span>
            ) : (
              '体験を始める'
            )}
          </button>

          <p className="text-xs text-gray-500 mt-6">
            ※ このアプリケーションで収集した情報は、体験の提供のみに使用されます
          </p>
        </div>
      </div>
    </div>
  );
}

export default withAuth(StartPage);
