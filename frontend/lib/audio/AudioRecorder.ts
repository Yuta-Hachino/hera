/**
 * AudioRecorder - マイク入力を16kHz PCMに変換
 *
 * Gemini Live API用の音声レコーダー
 * - マイクからの音声入力をキャプチャ
 * - 16kHz, 16-bit, mono PCM形式に変換
 * - リアルタイムでチャンクを生成
 */

import {
  AudioChunk,
  AudioConfig,
  AudioError,
  AudioErrorCode,
  DEFAULT_AUDIO_CONFIG,
  RecorderEvents,
  RecorderOptions,
  RecorderState,
  isGetUserMediaSupported,
  isWebAudioSupported,
} from './types';

export class AudioRecorder {
  private config: AudioConfig;
  private events: RecorderEvents;
  private state: RecorderState = 'idle';

  // Web Audio API
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private sourceNode: MediaStreamAudioSourceNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;

  // Audio constraints
  private constraints: MediaStreamConstraints;

  // Metrics
  private chunksProcessed = 0;
  private totalBytes = 0;
  private startTime = 0;

  constructor(options: RecorderOptions = {}) {
    this.config = {
      ...DEFAULT_AUDIO_CONFIG,
      ...options.config,
    };

    this.events = options.events || {};

    // マイク制約
    this.constraints = {
      audio: {
        sampleRate: this.config.inputSampleRate,
        channelCount: this.config.channels,
        echoCancellation: options.echoCancellation ?? true,
        noiseSuppression: options.noiseSuppression ?? true,
        autoGainControl: options.autoGainControl ?? true,
      },
      video: false,
    };

    this.validateBrowserSupport();
  }

  /**
   * ブラウザサポートチェック
   */
  private validateBrowserSupport(): void {
    if (!isGetUserMediaSupported()) {
      throw new AudioError(
        'このブラウザはマイク入力に対応していません',
        AudioErrorCode.UNSUPPORTED_BROWSER
      );
    }

    if (!isWebAudioSupported()) {
      throw new AudioError(
        'このブラウザはWeb Audio APIに対応していません',
        AudioErrorCode.UNSUPPORTED_BROWSER
      );
    }
  }

  /**
   * レコーダーを初期化
   */
  async initialize(): Promise<void> {
    if (this.state !== 'idle') {
      console.warn('[AudioRecorder] Already initialized');
      return;
    }

    this.setState('initializing');

    try {
      // マイクアクセス許可を要求
      this.mediaStream = await navigator.mediaDevices.getUserMedia(this.constraints);

      // AudioContext作成
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioContextClass({
        sampleRate: this.config.inputSampleRate,
      });

      // AudioContextを再開（Chromeのautoplay policy対策）
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      console.log(`[AudioRecorder] 初期化完了 (${this.audioContext.sampleRate}Hz)`);
      this.setState('idle');
    } catch (error) {
      const errorCode = (error as any).name === 'NotAllowedError'
        ? AudioErrorCode.PERMISSION_DENIED
        : AudioErrorCode.INITIALIZATION_FAILED;

      const audioError = new AudioError(
        'マイクの初期化に失敗しました',
        errorCode,
        error as Error
      );

      this.setState('error');
      this.events.onError?.(audioError);
      throw audioError;
    }
  }

  /**
   * 録音開始
   */
  async start(): Promise<void> {
    if (this.state === 'recording') {
      console.warn('[AudioRecorder] Already recording');
      return;
    }

    if (!this.audioContext || !this.mediaStream) {
      await this.initialize();
    }

    try {
      // AudioContext再開
      if (this.audioContext!.state === 'suspended') {
        await this.audioContext!.resume();
      }

      // ソースノード作成
      this.sourceNode = this.audioContext!.createMediaStreamSource(this.mediaStream!);

      // プロセッサノード作成（バッファサイズ: 4096サンプル）
      const bufferSize = 4096;
      this.processorNode = this.audioContext!.createScriptProcessor(
        bufferSize,
        this.config.channels,
        this.config.channels
      );

      // 音声処理
      this.processorNode.onaudioprocess = (event) => {
        this.processAudioData(event);
      };

      // ノード接続
      this.sourceNode.connect(this.processorNode);
      this.processorNode.connect(this.audioContext!.destination);

      // メトリクス初期化
      this.chunksProcessed = 0;
      this.totalBytes = 0;
      this.startTime = Date.now();

      this.setState('recording');
      this.events.onStart?.();
      console.log('[AudioRecorder] 録音開始');
    } catch (error) {
      const audioError = new AudioError(
        '録音の開始に失敗しました',
        AudioErrorCode.PROCESSING_ERROR,
        error as Error
      );
      this.setState('error');
      this.events.onError?.(audioError);
      throw audioError;
    }
  }

  /**
   * 録音停止
   */
  stop(): void {
    if (this.state !== 'recording') {
      console.warn('[AudioRecorder] Not recording');
      return;
    }

    try {
      // ノード切断
      if (this.processorNode) {
        this.processorNode.disconnect();
        this.processorNode.onaudioprocess = null;
        this.processorNode = null;
      }

      if (this.sourceNode) {
        this.sourceNode.disconnect();
        this.sourceNode = null;
      }

      this.setState('idle');
      this.events.onStop?.();
      console.log('[AudioRecorder] 録音停止');
      console.log(`  - チャンク数: ${this.chunksProcessed}`);
      console.log(`  - 総バイト数: ${this.totalBytes}`);
    } catch (error) {
      console.error('[AudioRecorder] 停止エラー:', error);
    }
  }

  /**
   * 音声データ処理
   */
  private processAudioData(event: AudioProcessingEvent): void {
    const inputBuffer = event.inputBuffer;
    const inputData = inputBuffer.getChannelData(0); // mono (channel 0)

    // Float32Array (-1.0 ~ 1.0) を Int16Array (-32768 ~ 32767) に変換
    const pcmData = this.float32ToInt16(inputData);

    // AudioChunk作成
    const chunk: AudioChunk = {
      data: pcmData,
      timestamp: Date.now(),
      sizeBytes: pcmData.byteLength,
      durationSec: inputBuffer.length / inputBuffer.sampleRate,
    };

    // メトリクス更新
    this.chunksProcessed++;
    this.totalBytes += chunk.sizeBytes;

    // イベント発火
    this.events.onDataAvailable?.(chunk);
  }

  /**
   * Float32Array を Int16Array に変換
   */
  private float32ToInt16(float32Array: Float32Array): Int16Array {
    const int16Array = new Int16Array(float32Array.length);

    for (let i = 0; i < float32Array.length; i++) {
      // -1.0 ~ 1.0 を -32768 ~ 32767 にスケール
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }

    return int16Array;
  }

  /**
   * リソース解放
   */
  async dispose(): Promise<void> {
    this.stop();

    // MediaStreamトラック停止
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }

    // AudioContext閉鎖
    if (this.audioContext && this.audioContext.state !== 'closed') {
      await this.audioContext.close();
      this.audioContext = null;
    }

    this.setState('idle');
    console.log('[AudioRecorder] リソース解放完了');
  }

  /**
   * 状態変更
   */
  private setState(newState: RecorderState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.events.onStateChange?.(newState);
    }
  }

  /**
   * 利用可能なマイクデバイス一覧を取得
   */
  static async getAvailableDevices(): Promise<MediaDeviceInfo[]> {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter((device) => device.kind === 'audioinput');
    } catch (error) {
      console.error('[AudioRecorder] デバイス取得エラー:', error);
      return [];
    }
  }

  // Getters
  getState(): RecorderState {
    return this.state;
  }

  getMetrics() {
    return {
      chunksProcessed: this.chunksProcessed,
      totalBytes: this.totalBytes,
      totalDuration: this.startTime > 0 ? (Date.now() - this.startTime) / 1000 : 0,
      startTime: this.startTime,
    };
  }

  getConfig(): AudioConfig {
    return { ...this.config };
  }

  isRecording(): boolean {
    return this.state === 'recording';
  }
}

export default AudioRecorder;
