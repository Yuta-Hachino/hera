'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import BackgroundLayout from '@/components/BackgroundLayout';
import ChatMessage from '@/components/ChatMessage';
import NovelMessage from '@/components/NovelMessage';
import ChatInput from '@/components/ChatInput';
import LoadingSpinner from '@/components/LoadingSpinner';
import { useTTS } from '@/hooks/useTTS';
import {
  getFamilyStatus,
  sendFamilyMessage,
} from '@/lib/api';
import { ConversationMessage } from '@/lib/types';

export default function FamilyConversationPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [tripInfo, setTripInfo] = useState<Record<string, any>>({});
  const [isConversationComplete, setConversationComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useNovelStyle, setUseNovelStyle] = useState(true);
  const [lastMessageIndex, setLastMessageIndex] = useState(-1);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { speak } = useTTS();

  useEffect(() => {
    const loadFamilyConversation = async () => {
      try {
        const status = await getFamilyStatus(sessionId);
        const history = status.conversation_history || [];
        const mapped: ConversationMessage[] = history.map((entry) => ({
          speaker: entry.speaker || 'family',
          message: entry.message || '',
          timestamp: entry.timestamp,
        }));
        setMessages(mapped);
        setTripInfo(status.family_trip_info || {});
        setConversationComplete(status.conversation_complete || false);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : '家族との会話履歴の取得に失敗しました'
        );
      } finally {
        setIsLoading(false);
      }
    };

    loadFamilyConversation();
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    if (messages.length > lastMessageIndex + 1) {
      setLastMessageIndex(messages.length - 1);
    }
  }, [messages, lastMessageIndex]);

  const handleSend = async (message: string) => {
    setIsSending(true);
    setError(null);

    const userMessage: ConversationMessage = {
      speaker: 'user',
      message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const response = await sendFamilyMessage(sessionId, message);
      const replies = response.reply || [];
      const mappedReplies: ConversationMessage[] = replies.map((reply) => ({
        speaker: reply.speaker || 'family',
        message: reply.message || '',
        timestamp: new Date().toISOString(),
      }));

      setMessages((prev) => [...prev, ...mappedReplies]);

      if (mappedReplies.length > 0) {
        speak(mappedReplies[0].message);
      }

      setTripInfo(response.family_trip_info || {});
      setConversationComplete(response.conversation_complete || false);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : '家族エージェントへのメッセージ送信に失敗しました'
      );
    } finally {
      setIsSending(false);
    }
  };

  const handleFinish = () => {
    router.push('/');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <BackgroundLayout>
      <div className="flex flex-col h-full w-full">
        <div className="bg-gradient-to-r from-amber-500 to-pink-500 text-white p-3 flex-shrink-0">
          <h1 className="text-lg font-bold">未来の家族との会話</h1>
          <p className="text-xs opacity-90">
            家族みんながあなたの話を楽しみにしています
          </p>
        </div>

        <div className="px-4 py-2 flex-shrink-0">
          <button
            onClick={() => setUseNovelStyle(!useNovelStyle)}
            className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full border border-gray-300 transition-colors"
          >
            {useNovelStyle ? '💬 チャット形式' : '📖 ノベル形式'}に切り替え
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-8">
              <p>「お帰りなさい！」家族があなたを待っています。</p>
              <p className="text-sm mt-2">メッセージを送って未来の家族と会話を始めましょう。</p>
            </div>
          )}

          {useNovelStyle ? (
            messages.map((msg, idx) => (
              <NovelMessage
                key={`${msg.speaker}-${idx}`}
                speaker={msg.speaker}
                message={msg.message}
                timestamp={msg.timestamp}
                isTyping={idx === lastMessageIndex && msg.speaker !== 'user'}
                typingSpeed={20}
              />
            ))
          ) : (
            messages.map((msg, idx) => (
              <ChatMessage key={`${msg.speaker}-${idx}`} {...msg} />
            ))
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-gray-100 bg-white/80 backdrop-blur-sm px-4 py-3 flex-shrink-0">
          <h2 className="text-xs font-semibold text-gray-600 mb-2">旅行プランメモ</h2>
          <div className="text-xs text-gray-700 space-y-1">
            <p>
              <span className="font-semibold">行きたい場所: </span>
              {tripInfo?.destination || '未定'}
            </p>
            <p>
              <span className="font-semibold">やりたいこと: </span>
              {(tripInfo?.activities && tripInfo.activities.length > 0)
                ? tripInfo.activities.join('、')
                : '未定'}
            </p>
          </div>
        </div>

        <div className="p-4 flex-shrink-0 space-y-2">
          {isConversationComplete && (
            <button
              onClick={handleFinish}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white font-bold py-3 px-6 rounded-lg hover:from-green-600 hover:to-emerald-600 focus:outline-none focus:ring-2 focus:ring-emerald-300 transition-colors"
            >
              素敵な時間をありがとう！ホームに戻る
            </button>
          )}

          <ChatInput onSend={handleSend} disabled={isSending} placeholder="家族へのメッセージを入力してください..." />
        </div>
      </div>
    </BackgroundLayout>
  );
}
