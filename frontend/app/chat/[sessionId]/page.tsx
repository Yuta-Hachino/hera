'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import BackgroundLayout from '@/components/BackgroundLayout';
import ChatMessage from '@/components/ChatMessage';
import NovelMessage from '@/components/NovelMessage';
import ChatInput from '@/components/ChatInput';
import ProfileProgress from '@/components/ProfileProgress';
import LoadingSpinner from '@/components/LoadingSpinner';
import { sendMessage, getSessionStatus, completeSession } from '@/lib/api';
import { ConversationMessage, InformationProgress } from '@/lib/types';
import { useAuth } from '@/lib/auth-context';
import { useLiveSession } from '@/hooks/useLiveSession';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { useAudioPlayer } from '@/hooks/useAudioPlayer';
import { AudioChunk } from '@/lib/audio';

export default function ChatPage() {
  const { user } = useAuth();
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [progress, setProgress] = useState<InformationProgress>({});
  const [isComplete, setIsComplete] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCompleting, setIsCompleting] = useState(false);
  const [currentHeraText, setCurrentHeraText] = useState<string | undefined>();
  const [useNovelStyle, setUseNovelStyle] = useState(true); // ノベルゲームスタイルの切り替え
  const [lastMessageIndex, setLastMessageIndex] = useState(-1); // タイピング用

  // 🆕 Live API統合用のstate
  const [liveApiEnabled, setLiveApiEnabled] = useState(false); // Live APIモード切り替え
  const [audioInputEnabled, setAudioInputEnabled] = useState(false); // 音声入力ON/OFF（デフォルトOFF）

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 🆕 Live APIフック統合
  // 音声データをBase64に変換する関数
  const int16ArrayToBase64 = useCallback((int16Array: Int16Array): string => {
    const uint8Array = new Uint8Array(int16Array.buffer);
    let binary = '';
    for (let i = 0; i < uint8Array.byteLength; i++) {
      binary += String.fromCharCode(uint8Array[i]);
    }
    return btoa(binary);
  }, []);

  // Live APIセッション管理
  const {
    connectionState,
    isConnected,
    lastTextMessage,
    lastAudioData,
    error: liveError,
    startSession: startLiveSession,
    stopSession: stopLiveSession,
    sendText: sendLiveText,
    sendAudioChunk,
  } = useLiveSession({
    sessionId,
    config: {
      enableAudioInput: audioInputEnabled,
      enableAudioOutput: true, // 音声出力は常にON
    },
    autoStart: false, // 手動で開始
  });

  // 音声録音管理
  const {
    isRecording,
    startRecording,
    stopRecording,
    initialize: initializeRecorder,
  } = useAudioRecorder({
    onDataAvailable: useCallback(
      async (chunk: AudioChunk) => {
        // 音声チャンクをBase64エンコードしてLive APIに送信
        if (isConnected && audioInputEnabled) {
          const base64Data = int16ArrayToBase64(chunk.data);
          await sendAudioChunk(base64Data);
        }
      },
      [isConnected, audioInputEnabled, sendAudioChunk, int16ArrayToBase64]
    ),
  });

  // 音声再生管理
  const { addBase64PCM } = useAudioPlayer({
    autoInitialize: true,
  });

  // 初回ロード時にセッション状態を取得
  useEffect(() => {
    const loadSession = async () => {
      try {
        const status = await getSessionStatus(sessionId, !!user); // 認証必要
        setMessages(status.conversation_history || []);
        setProgress(status.information_progress || []);
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
  }, [sessionId, user]);

  // 🆕 Live APIからのテキストメッセージ受信処理
  useEffect(() => {
    if (lastTextMessage && liveApiEnabled) {
      const heraMessage: ConversationMessage = {
        speaker: 'hera',
        message: lastTextMessage,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, heraMessage]);
      setCurrentHeraText(lastTextMessage);
      setIsSending(false);
    }
  }, [lastTextMessage, liveApiEnabled]);

  // 🆕 Live APIからの音声データ受信処理
  useEffect(() => {
    if (lastAudioData && liveApiEnabled) {
      // Base64エンコードされた音声データを再生
      addBase64PCM(lastAudioData).catch((err) => {
        console.error('[ChatPage] 音声再生エラー:', err);
      });
    }
  }, [lastAudioData, liveApiEnabled, addBase64PCM]);

  // 🆕 Live APIエラー処理
  useEffect(() => {
    if (liveError) {
      setError(liveError.message);
      setIsSending(false);
    }
  }, [liveError]);

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
      // 🆕 Live APIモード時はWebSocket経由で送信
      if (liveApiEnabled && isConnected) {
        await sendLiveText(message);
        // Live APIからの応答はuseEffectで処理されるため、ここでは何もしない
        // isSending は useEffect で false に設定される
        return;
      }

      // 既存のHTTP通信（デフォルト）
      const response = await sendMessage(sessionId, message, !!user); // 認証はオプション

      // 家族エージェントの応答を処理
      if (response.reply && typeof response.reply === 'string') {
        // 文字列の場合、JSONとしてパースを試行
        try {
          const parsedReply = JSON.parse(response.reply);
          if (Array.isArray(parsedReply)) {
            // パース成功: 家族エージェントの配列応答
            const familyMessages: ConversationMessage[] = parsedReply.map((msg: any) => ({
              speaker: msg.speaker,
              message: msg.message,
              timestamp: new Date().toISOString(),
            }));
            setMessages((prev) => [...prev, ...familyMessages]);

            // 最初のメッセージをTTS用に設定
            if (familyMessages.length > 0) {
              setCurrentHeraText(familyMessages[0].message);
            }
          } else {
            // パース成功だが配列ではない: 通常のヘーラーメッセージ
            const heraMessage: ConversationMessage = {
              speaker: 'hera',
              message: response.reply,
              timestamp: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, heraMessage]);
            setCurrentHeraText(response.reply);
          }
        } catch (error) {
          // パース失敗: 通常のヘーラーメッセージとして処理
          const heraMessage: ConversationMessage = {
            speaker: 'hera',
            message: response.reply,
            timestamp: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, heraMessage]);
          setCurrentHeraText(response.reply);
        }
      } else if (Array.isArray(response.reply)) {
        // 既に配列形式の場合
        const familyMessages: ConversationMessage[] = response.reply.map((msg: any) => ({
          speaker: msg.speaker,
          message: msg.message,
          timestamp: new Date().toISOString(),
        }));
        setMessages((prev) => [...prev, ...familyMessages]);

        // 最初のメッセージをTTS用に設定
        if (familyMessages.length > 0) {
          setCurrentHeraText(familyMessages[0].message);
        }
      }

      // 進捗と完了状態を更新
      setProgress(response.information_progress || {});
      setIsComplete(response.profile_complete || false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'メッセージの送信に失敗しました'
      );
    } finally {
      // Live APIモード以外の場合はここでisSendingをfalseに
      if (!liveApiEnabled) {
        setIsSending(false);
      }
    }
  };

  const handleComplete = async () => {
    setIsCompleting(true);
    setError(null);
    try {
      await completeSession(sessionId, !!user); // 認証はオプション
      router.push(`/family/${sessionId}`);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : '完了処理に失敗しました。しばらくしてから再度お試しください'
      );
    } finally {
      setIsCompleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <BackgroundLayout heraText={currentHeraText}>
      <div className="flex flex-col h-full w-full">
        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-primary-500 to-pink-500 text-white p-3 flex-shrink-0">
          <h1 className="text-lg font-bold">ヘーラーとの対話</h1>
          <p className="text-xs opacity-90">
            あなたの情報を教えてください
          </p>
        </div>

        {/* 進捗バー */}
        <ProfileProgress progress={progress} />

        {/* スタイル切り替えボタンとLive APIモード切り替え */}
        <div className="px-4 py-2 flex-shrink-0 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setUseNovelStyle(!useNovelStyle)}
              className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full border border-gray-300 transition-colors"
            >
              {useNovelStyle ? '💬 チャット形式' : '📖 ノベル形式'}に切り替え
            </button>

            {/* 🆕 Live APIモード切り替え */}
            <button
              onClick={async () => {
                const newValue = !liveApiEnabled;
                setLiveApiEnabled(newValue);
                if (newValue) {
                  // Live APIモードON: セッション開始
                  try {
                    await startLiveSession();
                  } catch (err) {
                    console.error('[ChatPage] Live API開始エラー:', err);
                    setError('Live APIセッションの開始に失敗しました');
                    setLiveApiEnabled(false);
                  }
                } else {
                  // Live APIモードOFF: セッション停止
                  await stopLiveSession();
                  if (isRecording) {
                    stopRecording();
                  }
                  setAudioInputEnabled(false);
                }
              }}
              className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                liveApiEnabled
                  ? 'bg-green-100 border-green-400 hover:bg-green-200 text-green-800'
                  : 'bg-gray-100 border-gray-300 hover:bg-gray-200'
              }`}
              disabled={isSending || isCompleting}
            >
              {liveApiEnabled ? '🟢 Live API: ON' : '⚪ Live API: OFF'}
            </button>

            {/* 接続状態表示 */}
            {liveApiEnabled && (
              <span className="text-xs text-gray-600">
                {connectionState === 'connected' && '✅ 接続済み'}
                {connectionState === 'connecting' && '🔄 接続中...'}
                {connectionState === 'disconnected' && '❌ 切断'}
                {connectionState === 'error' && '⚠️ エラー'}
              </span>
            )}
          </div>

          {/* 🆕 音声入力トグル（Live APIモードON時のみ表示） */}
          {liveApiEnabled && isConnected && (
            <div className="flex items-center gap-2">
              <label className="flex items-center text-xs text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={audioInputEnabled}
                  onChange={async (e) => {
                    const newValue = e.target.checked;
                    setAudioInputEnabled(newValue);
                    if (newValue) {
                      // 音声入力ON: マイク初期化と録音開始
                      try {
                        await initializeRecorder();
                        await startRecording();
                      } catch (err) {
                        console.error('[ChatPage] 録音開始エラー:', err);
                        setError('マイクの初期化に失敗しました。マイクへのアクセス許可を確認してください。');
                        setAudioInputEnabled(false);
                      }
                    } else {
                      // 音声入力OFF: 録音停止
                      stopRecording();
                    }
                  }}
                  className="mr-2"
                  disabled={!isConnected}
                />
                <span className="select-none">
                  🎤 音声入力を有効にする{audioInputEnabled && isRecording ? '（録音中）' : ''}
                </span>
              </label>
              {!audioInputEnabled && (
                <span className="text-xs text-gray-500">
                  ※マイク許可が必要です
                </span>
              )}
            </div>
          )}
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
          <div className="px-4 py-2 flex-shrink-0">
            <button
              onClick={handleComplete}
              disabled={isCompleting}
              className="w-full bg-green-500 text-white font-semibold py-3 px-6 rounded-lg hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-300 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isCompleting ? '準備中...' : '情報収集完了 - 次へ進む'}
            </button>
          </div>
        )}

        {/* 入力フォーム */}
        <div className="p-4 flex-shrink-0">
          <ChatInput onSend={handleSend} disabled={isSending} />
        </div>
      </div>
    </BackgroundLayout>
  );
}
