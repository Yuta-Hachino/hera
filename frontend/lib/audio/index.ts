/**
 * Audio Module - Gemini Live API用の音声処理
 *
 * このモジュールは、Gemini Live API統合のための音声入出力機能を提供します。
 *
 * 主な機能:
 * - AudioRecorder: マイク入力を16kHz PCMに変換
 * - AudioPlayer: 24kHz PCM音声を再生
 * - 型定義とユーティリティ関数
 *
 * 使用例:
 * ```typescript
 * import { AudioRecorder, AudioPlayer } from '@/lib/audio';
 *
 * // 録音
 * const recorder = new AudioRecorder({
 *   events: {
 *     onDataAvailable: (chunk) => {
 *       // 音声チャンクをAPIに送信
 *       sendToAPI(chunk);
 *     }
 *   }
 * });
 * await recorder.initialize();
 * await recorder.start();
 *
 * // 再生
 * const player = new AudioPlayer();
 * await player.initialize();
 * await player.addPCMData(pcmData);
 * ```
 */

// Core classes
export { AudioRecorder } from './AudioRecorder';
export { AudioPlayer } from './AudioPlayer';

// Types
export type {
  AudioChunk,
  AudioConfig,
  AudioContextInfo,
  AudioFormat,
  AudioMetrics,
  MicrophoneDevice,
  PlayerEvents,
  PlayerOptions,
  PlayerState,
  RecorderEvents,
  RecorderOptions,
  RecorderState,
} from './types';

// Error handling
export { AudioError, AudioErrorCode } from './types';

// Constants
export { DEFAULT_AUDIO_CONFIG } from './types';

// Utility functions
export {
  isAudioChunk,
  isGetUserMediaSupported,
  isMediaRecorderSupported,
  isWebAudioSupported,
} from './types';

// Re-export default instances for convenience
export { default as AudioRecorderClass } from './AudioRecorder';
export { default as AudioPlayerClass } from './AudioPlayer';
