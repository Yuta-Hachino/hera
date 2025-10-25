'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import AvatarLayout from '@/components/AvatarLayout';
import ChatMessage from '@/components/ChatMessage';
import NovelMessage from '@/components/NovelMessage';
import ChatInput from '@/components/ChatInput';
import ProfileProgress from '@/components/ProfileProgress';
import LoadingSpinner from '@/components/LoadingSpinner';
import { sendMessage, getSessionStatus } from '@/lib/api';
import { ConversationMessage, InformationProgress } from '@/lib/types';

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [progress, setProgress] = useState<InformationProgress>({});
  const [isComplete, setIsComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentHeraText, setCurrentHeraText] = useState<string | undefined>();
  const [useNovelStyle, setUseNovelStyle] = useState(true); // ノベルゲームスタイルの切り替え
  const [lastMessageIndex, setLastMessageIndex] = useState(-1); // タイピング用

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 初回ロード時にセッション状態を取得
  useEffect(() => {
    const loadSession = async () => {
      try {
        const status = await getSessionStatus(sessionId);
        setMessages(status.conversation_history || []);
        setProgress(status.information_progress || {});
        setIsComplete(status.profile_complete || false);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'セッションの読み込みに失敗しました'
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadSession();
  }, [sessionId]);

  // メッセージが追加されたら最下部にスクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    // 新しいメッセージがある場合、lastMessageIndexを更新
    if (messages.length > lastMessageIndex + 1) {
      setLastMessageIndex(messages.length - 1);
    }
  }, [messages]);

  const handleSend = async (message: string) => {
    setIsSending(true);
    setError(null);

    // ユーザーメッセージを即座に表示
    const userMessage: ConversationMessage = {
      speaker: 'user',
      message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await sendMessage(sessionId, message);

      // Heraの応答を表示
      const heraMessage: ConversationMessage = {
        speaker: 'hera',
        message: response.reply,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, heraMessage]);

      // 音声で応答を再生（リップシンク）
      setCurrentHeraText(response.reply);

      // 進捗と完了状態を更新
      setProgress(response.information_progress || {});
      setIsComplete(response.profile_complete || false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'メッセージの送信に失敗しました'
      );
    } finally {
      setIsSending(false);
    }
  };

  const handleComplete = () => {
    router.push(`/complete/${sessionId}`);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AvatarLayout heraText={currentHeraText}>
      <div className="flex flex-col h-full">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-primary-500 to-pink-500 text-white p-3">
          <h1 className="text-lg font-bold">ヘーラーとの対話</h1>
          <p className="text-xs opacity-90">
            あなたの情報を教えてください
          </p>
        </div>

        {/* 進捗バー */}
        <ProfileProgress progress={progress} />

        {/* スタイル切り替えボタン */}
        <div className="px-4 py-2 bg-gray-50 border-b">
          <button
            onClick={() => setUseNovelStyle(!useNovelStyle)}
            className="text-xs bg-white hover:bg-gray-100 px-3 py-1 rounded-full border border-gray-300 transition-colors"
          >
            {useNovelStyle ? '💬 チャット形式' : '📖 ノベル形式'}に切り替え
          </button>
        </div>

        {/* チャット履歴 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              <p>ヘーラーがあなたをお待ちしています。</p>
              <p className="text-sm mt-2">メッセージを送信して対話を始めましょう。</p>
            </div>
          )}

          {useNovelStyle ? (
            // ノベルゲームスタイル表示
            messages.map((msg, idx) => (
              <NovelMessage
                key={idx}
                speaker={msg.speaker}
                message={msg.message}
                timestamp={msg.timestamp}
                isTyping={idx === lastMessageIndex && msg.speaker === 'hera'}
                typingSpeed={25}
              />
            ))
          ) : (
            // 従来のチャットスタイル表示
            messages.map((msg, idx) => (
              <ChatMessage key={idx} {...msg} />
            ))
          )}

          {isSending && (
            useNovelStyle ? (
              <NovelMessage
                speaker="hera"
                message="考え中..."
                isTyping={false}
              />
            ) : (
              <div className="flex justify-start mb-4">
                <div className="bg-gray-200 rounded-2xl px-4 py-3 rounded-bl-none">
                  <LoadingSpinner />
                </div>
              </div>
            )
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 完了ボタン */}
        {isComplete && (
          <div className="px-4 py-2 bg-green-50 border-t border-green-200">
            <button
              onClick={handleComplete}
              className="w-full bg-green-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-300 transition-colors"
            >
              情報収集完了 - 次へ進む
            </button>
          </div>
        )}

        {/* 入力フォーム */}
        <ChatInput onSend={handleSend} disabled={isSending} />
      </div>
    </AvatarLayout>
  );
}
