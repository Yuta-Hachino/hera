'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import BackgroundLayout from '@/components/BackgroundLayout';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useTTS } from '@/hooks/useTTS';
import { useAuth } from '@/lib/auth-context-firebase';
import { getSessionStatus, completeSession } from '@/lib/api';
import { UserProfile } from '@/lib/types';

export default function CompletePage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;
  const { user } = useAuth();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCompleting, setIsCompleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { isSpeaking, audioSrc, speak } = useTTS();

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const status = await getSessionStatus(sessionId);
        setProfile(status.user_profile);

        // ヘーラーからの完了メッセージを音声で再生（エラーは無視）
        try {
          const completionMessage =
            'お疲れさまでした。あなたの情報をしっかりと受け取りました。確認ボタンを押すと、未来の家族との素敵な体験が始まります。';
          speak(completionMessage);
        } catch (ttsErr) {
          console.warn('TTS error (ignored):', ttsErr);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'プロファイルの読み込みに失敗しました'
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, [sessionId]);

  const handleConfirm = async () => {
    setIsCompleting(true);
    setError(null);

    try {
      const response = await completeSession(sessionId, !!user);

      if (response.error) {
        setError(response.error);
        setIsCompleting(false);
        return;
      }

      setSuccessMessage(response.message);

      // 成功メッセージを音声で再生（エラーは無視）
      try {
        speak('ありがとうございました。それでは、未来の家族との時間をお楽しみください。');
      } catch (ttsErr) {
        console.warn('TTS error (ignored):', ttsErr);
      }

      // 家族との会話ページへ移動
      setTimeout(() => {
        router.push(`/family/${sessionId}`);
      }, 1500);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'セッションの完了処理に失敗しました'
      );
      setIsCompleting(false);
    }
  };

  const handleBack = () => {
    router.push(`/chat/${sessionId}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <BackgroundLayout heraText={isSpeaking ? 'お疲れ様でした！あなたの情報を確認してください。' : undefined}>
      <div className="flex flex-col h-full">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-green-500/70 to-teal-500/70 text-white p-4 backdrop-blur-sm">
          <h1 className="text-xl font-bold">情報確認</h1>
          <p className="text-sm opacity-90">収集した情報を確認してください</p>
        </div>

        {/* プロファイル表示 */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {successMessage ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">✨</div>
              <h2 className="text-2xl font-bold text-green-600 mb-2">
                {successMessage}
              </h2>
              <p className="text-gray-600">
                まもなく結果画面に移動します...
              </p>
              <LoadingSpinner />
            </div>
          ) : (
            <>
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6 border border-purple-200">
                <h2 className="text-lg font-bold text-gray-800 mb-4">
                  あなたのプロファイル
                </h2>

                {profile && (
                  <div className="space-y-3">
                    {profile.name && (
                      <ProfileItem label="お名前" value={profile.name} />
                    )}
                    {profile.age && (
                      <ProfileItem label="年齢" value={`${profile.age}歳`} />
                    )}
                    {profile.gender && (
                      <ProfileItem label="性別" value={profile.gender} />
                    )}
                    {profile.relationship_status && (
                      <ProfileItem
                        label="婚姻状態"
                        value={profile.relationship_status}
                      />
                    )}
                    {profile.income && (
                      <ProfileItem label="収入" value={profile.income} />
                    )}

                    {/* その他の情報 */}
                    {Object.entries(profile)
                      .filter(
                        ([key]) =>
                          ![
                            'name',
                            'age',
                            'gender',
                            'relationship_status',
                            'income',
                          ].includes(key)
                      )
                      .map(([key, value]) => {
                        if (
                          value &&
                          typeof value !== 'object' &&
                          value !== ''
                        ) {
                          return (
                            <ProfileItem
                              key={key}
                              label={key}
                              value={String(value)}
                            />
                          );
                        }
                        return null;
                      })}
                  </div>
                )}
              </div>

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        {/* アクションボタン */}
        {!successMessage && (
          <div className="border-t border-gray-200 p-4 space-y-2">
            <button
              onClick={handleConfirm}
              disabled={isCompleting}
              className="w-full bg-gradient-to-r from-green-500 to-teal-500 text-white font-bold py-3 px-6 rounded-lg hover:from-green-600 hover:to-teal-600 focus:outline-none focus:ring-2 focus:ring-green-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isCompleting ? (
                <span className="flex items-center justify-center">
                  <LoadingSpinner />
                  <span className="ml-2">処理中...</span>
                </span>
              ) : (
                '確認して完了する'
              )}
            </button>

            <button
              onClick={handleBack}
              disabled={isCompleting}
              className="w-full bg-gray-200 text-gray-700 font-semibold py-3 px-6 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              戻って修正する
            </button>
          </div>
        )}
      </div>
    </BackgroundLayout>
  );
}

function ProfileItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start border-b border-purple-100 pb-2">
      <span className="font-semibold text-gray-700 w-32 flex-shrink-0">
        {label}:
      </span>
      <span className="text-gray-800">{value}</span>
    </div>
  );
}
