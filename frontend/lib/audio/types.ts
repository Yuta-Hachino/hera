/**
 * Audio Types for Gemini Live API Integration
 *
 * このファイルは音声処理に関する型定義を提供します。
 */

/**
 * 音声フォーマット
 */
export type AudioFormat = 'pcm' | 'opus' | 'mp3';

/**
 * 音声設定
 */
export interface AudioConfig {
  /** 入力サンプルレート (Hz) */
  inputSampleRate: number;
  /** 出力サンプルレート (Hz) */
  outputSampleRate: number;
  /** チャンクサイズ (ms) */
  chunkSizeMs: number;
  /** サンプル幅 (bytes) */
  sampleWidth: number;
  /** チャンネル数 (1=mono, 2=stereo) */
  channels: number;
  /** 音声フォーマット */
  format: AudioFormat;
}

/**
 * デフォルト音声設定
 */
export const DEFAULT_AUDIO_CONFIG: AudioConfig = {
  inputSampleRate: 16000,   // 16kHz (Gemini Live API input)
  outputSampleRate: 24000,  // 24kHz (Gemini Live API output)
  chunkSizeMs: 100,         // 100ms chunks
  sampleWidth: 2,           // 16-bit = 2 bytes
  channels: 1,              // mono
  format: 'pcm',
};

/**
 * 音声レコーダーの状態
 */
export type RecorderState = 'idle' | 'initializing' | 'recording' | 'paused' | 'error';

/**
 * 音声プレイヤーの状態
 */
export type PlayerState = 'idle' | 'initializing' | 'playing' | 'paused' | 'stopped' | 'error';

/**
 * 音声チャンク
 */
export interface AudioChunk {
  /** PCMデータ (Int16Array) */
  data: Int16Array;
  /** タイムスタンプ (ms) */
  timestamp: number;
  /** チャンクサイズ (bytes) */
  sizeBytes: number;
  /** 再生時間 (秒) */
  durationSec: number;
}

/**
 * 音声レコーダーのイベント
 */
export interface RecorderEvents {
  /** 音声データが利用可能になったとき */
  onDataAvailable?: (chunk: AudioChunk) => void;
  /** レコーディング開始時 */
  onStart?: () => void;
  /** レコーディング停止時 */
  onStop?: () => void;
  /** エラー発生時 */
  onError?: (error: Error) => void;
  /** 状態変更時 */
  onStateChange?: (state: RecorderState) => void;
}

/**
 * 音声プレイヤーのイベント
 */
export interface PlayerEvents {
  /** 再生開始時 */
  onStart?: () => void;
  /** 再生終了時 */
  onEnd?: () => void;
  /** エラー発生時 */
  onError?: (error: Error) => void;
  /** 状態変更時 */
  onStateChange?: (state: PlayerState) => void;
}

/**
 * 音声レコーダーのオプション
 */
export interface RecorderOptions {
  /** 音声設定 */
  config?: Partial<AudioConfig>;
  /** イベントハンドラ */
  events?: RecorderEvents;
  /** 自動ゲイン制御 */
  autoGainControl?: boolean;
  /** ノイズ抑制 */
  noiseSuppression?: boolean;
  /** エコーキャンセレーション */
  echoCancellation?: boolean;
}

/**
 * 音声プレイヤーのオプション
 */
export interface PlayerOptions {
  /** 音声設定 */
  config?: Partial<AudioConfig>;
  /** イベントハンドラ */
  events?: PlayerEvents;
  /** 音量 (0.0 - 1.0) */
  volume?: number;
}

/**
 * Web Audio API のコンテキスト情報
 */
export interface AudioContextInfo {
  /** サンプルレート */
  sampleRate: number;
  /** 状態 */
  state: AudioContextState;
  /** ベースレイテンシ */
  baseLatency: number;
  /** 出力レイテンシ */
  outputLatency?: number;
}

/**
 * マイクデバイス情報
 */
export interface MicrophoneDevice {
  /** デバイスID */
  deviceId: string;
  /** デバイス名 */
  label: string;
  /** グループID */
  groupId: string;
  /** 種類 */
  kind: MediaDeviceKind;
}

/**
 * 音声処理のメトリクス
 */
export interface AudioMetrics {
  /** 処理されたチャンク数 */
  chunksProcessed: number;
  /** 総バイト数 */
  totalBytes: number;
  /** 総再生時間 (秒) */
  totalDuration: number;
  /** 開始時刻 */
  startTime: number;
  /** 終了時刻 */
  endTime?: number;
  /** 平均レイテンシ (ms) */
  averageLatency?: number;
}

/**
 * 音声エラー
 */
export class AudioError extends Error {
  constructor(
    message: string,
    public code: AudioErrorCode,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'AudioError';
  }
}

/**
 * 音声エラーコード
 */
export enum AudioErrorCode {
  /** マイクアクセス拒否 */
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  /** マイクデバイスが見つからない */
  DEVICE_NOT_FOUND = 'DEVICE_NOT_FOUND',
  /** 初期化失敗 */
  INITIALIZATION_FAILED = 'INITIALIZATION_FAILED',
  /** 音声処理エラー */
  PROCESSING_ERROR = 'PROCESSING_ERROR',
  /** サポートされていないブラウザ */
  UNSUPPORTED_BROWSER = 'UNSUPPORTED_BROWSER',
  /** 不明なエラー */
  UNKNOWN = 'UNKNOWN',
}

/**
 * 音声処理ユーティリティの型ガード
 */
export function isAudioChunk(obj: any): obj is AudioChunk {
  return (
    obj &&
    typeof obj === 'object' &&
    obj.data instanceof Int16Array &&
    typeof obj.timestamp === 'number' &&
    typeof obj.sizeBytes === 'number' &&
    typeof obj.durationSec === 'number'
  );
}

/**
 * ブラウザが Web Audio API をサポートしているか確認
 */
export function isWebAudioSupported(): boolean {
  return !!(
    typeof window !== 'undefined' &&
    (window.AudioContext || (window as any).webkitAudioContext)
  );
}

/**
 * ブラウザが MediaRecorder をサポートしているか確認
 */
export function isMediaRecorderSupported(): boolean {
  return !!(
    typeof window !== 'undefined' &&
    window.MediaRecorder
  );
}

/**
 * ブラウザが getUserMedia をサポートしているか確認
 */
export function isGetUserMediaSupported(): boolean {
  return !!(
    typeof navigator !== 'undefined' &&
    navigator.mediaDevices &&
    navigator.mediaDevices.getUserMedia
  );
}
