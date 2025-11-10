/**
 * useLiveSession - Gemini Live APIセッション管理フック
 *
 * Live APIセッションの状態管理とWebSocket通信を提供するカスタムフック
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ConnectionState,
  LiveSessionManager,
  LiveSessionOptions,
  SessionConfig,
} from '@/lib/websocket';

export interface UseLiveSessionOptions {
  /** セッションID */
  sessionId: string;
  /** セッション設定 */
  config?: SessionConfig;
  /** 自動開始 */
  autoStart?: boolean;
  /** 自動再接続 */
  autoReconnect?: boolean;
}

export interface UseLiveSessionReturn {
  /** 接続状態 */
  connectionState: ConnectionState;
  /** 接続済みかどうか */
  isConnected: boolean;
  /** 最後に受信したテキストメッセージ */
  lastTextMessage: string | null;
  /** 最後に受信した音声データ（Base64） */
  lastAudioData: string | null;
  /** エラー */
  error: Error | null;
  /** セッション開始 */
  startSession: () => Promise<void>;
  /** セッション停止 */
  stopSession: () => Promise<void>;
  /** テキスト送信 */
  sendText: (text: string) => Promise<void>;
  /** 音声データ送信（Base64） */
  sendAudioChunk: (base64Data: string) => Promise<void>;
  /** セッションマネージャー（直接操作用） */
  sessionManager: LiveSessionManager | null;
}

export function useLiveSession(options: UseLiveSessionOptions): UseLiveSessionReturn {
  const { sessionId, config, autoStart = false, autoReconnect = true } = options;

  // State
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [lastTextMessage, setLastTextMessage] = useState<string | null>(null);
  const [lastAudioData, setLastAudioData] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);

  // Ref
  const sessionManagerRef = useRef<LiveSessionManager | null>(null);
  const isInitializedRef = useRef(false);

  /**
   * セッションマネージャー初期化
   */
  useEffect(() => {
    if (isInitializedRef.current) return;
    isInitializedRef.current = true;

    const sessionOptions: LiveSessionOptions = {
      sessionId,
      config,
      autoReconnect,
      handlers: {
        onConnect: () => {
          console.log('[useLiveSession] 接続成功');
          setError(null);
        },
        onDisconnect: () => {
          console.log('[useLiveSession] 切断');
        },
        onTextMessage: (text) => {
          console.log('[useLiveSession] テキスト受信:', text);
          setLastTextMessage(text);
        },
        onAudioData: (audioData) => {
          console.log('[useLiveSession] 音声データ受信:', audioData.length, 'chars');
          setLastAudioData(audioData);
        },
        onError: (err) => {
          console.error('[useLiveSession] エラー:', err);
          setError(err);
        },
        onStateChange: (state) => {
          console.log('[useLiveSession] 状態変更:', state);
          setConnectionState(state);
        },
      },
    };

    sessionManagerRef.current = new LiveSessionManager(sessionOptions);

    // 自動開始
    if (autoStart) {
      sessionManagerRef.current.start().catch((err) => {
        console.error('[useLiveSession] 自動開始失敗:', err);
        setError(err);
      });
    }

    // クリーンアップ
    return () => {
      if (sessionManagerRef.current) {
        sessionManagerRef.current.stop();
        sessionManagerRef.current = null;
      }
      isInitializedRef.current = false;
    };
  }, [sessionId, config, autoStart, autoReconnect]);

  /**
   * セッション開始
   */
  const startSession = useCallback(async () => {
    if (!sessionManagerRef.current) {
      throw new Error('Session manager not initialized');
    }

    try {
      setError(null);
      await sessionManagerRef.current.start();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * セッション停止
   */
  const stopSession = useCallback(async () => {
    if (!sessionManagerRef.current) {
      throw new Error('Session manager not initialized');
    }

    try {
      await sessionManagerRef.current.stop();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * テキスト送信
   */
  const sendText = useCallback(async (text: string) => {
    if (!sessionManagerRef.current) {
      throw new Error('Session manager not initialized');
    }

    try {
      await sessionManagerRef.current.sendText(text);
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * 音声データ送信
   */
  const sendAudioChunk = useCallback(async (base64Data: string) => {
    if (!sessionManagerRef.current) {
      throw new Error('Session manager not initialized');
    }

    try {
      await sessionManagerRef.current.sendAudioChunk(base64Data);
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  return {
    connectionState,
    isConnected: connectionState === 'connected',
    lastTextMessage,
    lastAudioData,
    error,
    startSession,
    stopSession,
    sendText,
    sendAudioChunk,
    sessionManager: sessionManagerRef.current,
  };
}

export default useLiveSession;
