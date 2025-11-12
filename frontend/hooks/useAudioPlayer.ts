/**
 * useAudioPlayer - 音声再生管理フック
 *
 * AudioPlayerの状態管理とライフサイクルを提供するカスタムフック
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { AudioPlayer, PlayerState } from '@/lib/audio';

export interface UseAudioPlayerOptions {
  /** 音量（0.0 - 1.0） */
  volume?: number;
  /** エラーコールバック */
  onError?: (error: Error) => void;
  /** 自動初期化 */
  autoInitialize?: boolean;
}

export interface UseAudioPlayerReturn {
  /** 再生状態 */
  playerState: PlayerState;
  /** 再生中かどうか */
  isPlaying: boolean;
  /** エラー */
  error: Error | null;
  /** 初期化 */
  initialize: () => Promise<void>;
  /** PCMデータ追加（Int16Array） */
  addPCMData: (pcmData: Int16Array) => Promise<void>;
  /** Base64 PCMデータ追加 */
  addBase64PCM: (base64Data: string) => Promise<void>;
  /** 一時停止 */
  pause: () => Promise<void>;
  /** 再開 */
  resume: () => Promise<void>;
  /** 停止（キュークリア） */
  stop: () => void;
  /** 音量設定 */
  setVolume: (volume: number) => void;
  /** リソース解放 */
  dispose: () => Promise<void>;
  /** プレイヤーインスタンス */
  player: AudioPlayer | null;
}

export function useAudioPlayer(options: UseAudioPlayerOptions = {}): UseAudioPlayerReturn {
  const { volume = 1.0, onError, autoInitialize = true } = options;

  // State
  const [playerState, setPlayerState] = useState<PlayerState>('idle');
  const [error, setError] = useState<Error | null>(null);

  // Ref
  const playerRef = useRef<AudioPlayer | null>(null);
  const isInitializedRef = useRef(false);

  /**
   * プレイヤー初期化
   */
  useEffect(() => {
    if (isInitializedRef.current) return;

    // AudioPlayer作成
    playerRef.current = new AudioPlayer({
      volume,
      events: {
        onError: (err) => {
          console.error('[useAudioPlayer] エラー:', err);
          setError(err);
          onError?.(err);
        },
        onStateChange: (state) => {
          setPlayerState(state);
        },
      },
    });

    isInitializedRef.current = true;

    // 自動初期化
    if (autoInitialize) {
      playerRef.current.initialize().catch((err) => {
        console.error('[useAudioPlayer] 自動初期化失敗:', err);
        setError(err);
      });
    }

    // クリーンアップ
    return () => {
      if (playerRef.current) {
        playerRef.current.dispose();
        playerRef.current = null;
      }
      isInitializedRef.current = false;
    };
  }, [volume, onError, autoInitialize]);

  /**
   * 初期化
   */
  const initialize = useCallback(async () => {
    if (!playerRef.current) {
      throw new Error('Player not created');
    }

    try {
      setError(null);
      await playerRef.current.initialize();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * PCMデータ追加
   */
  const addPCMData = useCallback(async (pcmData: Int16Array) => {
    if (!playerRef.current) {
      throw new Error('Player not created');
    }

    try {
      setError(null);
      await playerRef.current.addPCMData(pcmData);
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * Base64 PCMデータ追加
   */
  const addBase64PCM = useCallback(async (base64Data: string) => {
    if (!playerRef.current) {
      throw new Error('Player not created');
    }

    try {
      setError(null);
      await playerRef.current.addBase64PCM(base64Data);
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * 一時停止
   */
  const pause = useCallback(async () => {
    if (!playerRef.current) {
      throw new Error('Player not created');
    }

    try {
      await playerRef.current.pause();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * 再開
   */
  const resume = useCallback(async () => {
    if (!playerRef.current) {
      throw new Error('Player not created');
    }

    try {
      await playerRef.current.resume();
    } catch (err) {
      setError(err as Error);
      throw err;
    }
  }, []);

  /**
   * 停止
   */
  const stop = useCallback(() => {
    if (!playerRef.current) {
      throw new Error('Player not created');
    }

    playerRef.current.stop();
  }, []);

  /**
   * 音量設定
   */
  const setVolumeCallback = useCallback((newVolume: number) => {
    if (!playerRef.current) {
      throw new Error('Player not created');
    }

    playerRef.current.setVolume(newVolume);
  }, []);

  /**
   * リソース解放
   */
  const dispose = useCallback(async () => {
    if (!playerRef.current) {
      return;
    }

    await playerRef.current.dispose();
  }, []);

  return {
    playerState,
    isPlaying: playerState === 'playing',
    error,
    initialize,
    addPCMData,
    addBase64PCM,
    pause,
    resume,
    stop,
    setVolume: setVolumeCallback,
    dispose,
    player: playerRef.current,
  };
}

export default useAudioPlayer;
