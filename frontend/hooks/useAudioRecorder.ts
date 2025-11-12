/**
 * useAudioRecorder - 音声録音管理フック
 *
 * AudioRecorderの状態管理とライフサイクルを提供するカスタムフック
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { AudioRecorder, AudioChunk, RecorderState } from '@/lib/audio';

export interface UseAudioRecorderOptions {
  /** 録音データコールバック */
  onDataAvailable?: (chunk: AudioChunk) => void;
  /** エラーコールバック */
  onError?: (error: Error) => void;
  /** 自動初期化 */
  autoInitialize?: boolean;
}

export interface UseAudioRecorderReturn {
  /** 録音状態 */
  recorderState: RecorderState;
  /** 録音中かどうか */
  isRecording: boolean;
  /** エラー */
  error: Error | null;
  /** 初期化 */
  initialize: () => Promise<void>;
  /** 録音開始 */
  startRecording: () => Promise<void>;
  /** 録音停止 */
  stopRecording: () => void;
  /** リソース解放 */
  dispose: () => Promise<void>;
  /** レコーダーインスタンス */
  recorder: AudioRecorder | null;
}

export function useAudioRecorder(
  options: UseAudioRecorderOptions = {}
): UseAudioRecorderReturn {
  const { onDataAvailable, onError, autoInitialize = false } = options;

  // State
  const [recorderState, setRecorderState] = useState<RecorderState>('idle');
  const [error, setError] = useState<Error | null>(null);

  // Ref
  const recorderRef = useRef<AudioRecorder | null>(null);
  const isInitializedRef = useRef(false);

  /**
   * レコーダー初期化
   */
  useEffect(() => {
    if (isInitializedRef.current) return;

    // AudioRecorder作成
    recorderRef.current = new AudioRecorder({
      events: {
        onDataAvailable: (chunk) => {
          onDataAvailable?.(chunk);
        },
        onError: (err) => {
          console.error('[useAudioRecorder] エラー:', err);
          setError(err);
          onError?.(err);
        },
        onStateChange: (state) => {
          setRecorderState(state);
        },
      },
    });

    isInitializedRef.current = true;

    // 自動初期化
    if (autoInitialize) {
      recorderRef.current.initialize().catch((err) => {
        console.error('[useAudioRecorder] 自動初期化失敗:', err);
        setError(err);
      });
    }

    // クリーンアップ
    return () => {
      if (recorderRef.current) {
        recorderRef.current.dispose();
        recorderRef.current = null;
      }
      isInitializedRef.current = false;
    };
  }, [onDataAvailable, onError, autoInitialize]);

  /**
   * 初期化
   */
  const initialize = useCallback(async () => {
    if (!recorderRef.current) {
      throw new Error('Recorder not created');
    }

    try {
      setError(null);
      await recorderRef.current.initialize();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * 録音開始
   */
  const startRecording = useCallback(async () => {
    if (!recorderRef.current) {
      throw new Error('Recorder not created');
    }

    try {
      setError(null);
      await recorderRef.current.start();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * 録音停止
   */
  const stopRecording = useCallback(() => {
    if (!recorderRef.current) {
      throw new Error('Recorder not created');
    }

    recorderRef.current.stop();
  }, []);

  /**
   * リソース解放
   */
  const dispose = useCallback(async () => {
    if (!recorderRef.current) {
      return;
    }

    await recorderRef.current.dispose();
  }, []);

  return {
    recorderState,
    isRecording: recorderState === 'recording',
    error,
    initialize,
    startRecording,
    stopRecording,
    dispose,
    recorder: recorderRef.current,
  };
}

export default useAudioRecorder;
