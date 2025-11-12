/**
 * AudioPlayer - 24kHz PCM音声を再生
 *
 * Gemini Live API用の音声プレイヤー
 * - 24kHz, 16-bit, mono PCM形式の音声を再生
 * - リアルタイムストリーミング対応
 * - キューイングとバッファリング
 */

import {
  AudioChunk,
  AudioConfig,
  AudioError,
  AudioErrorCode,
  DEFAULT_AUDIO_CONFIG,
  PlayerEvents,
  PlayerOptions,
  PlayerState,
  isWebAudioSupported,
} from './types';

export class AudioPlayer {
  private config: AudioConfig;
  private events: PlayerEvents;
  private state: PlayerState = 'idle';

  // Web Audio API
  private audioContext: AudioContext | null = null;
  private gainNode: GainNode | null = null;

  // Audio queue
  private audioQueue: AudioChunk[] = [];
  private isPlaying = false;
  private currentTime = 0;

  // Volume
  private volume: number;

  // Metrics
  private chunksPlayed = 0;
  private totalBytes = 0;
  private startTime = 0;

  constructor(options: PlayerOptions = {}) {
    this.config = {
      ...DEFAULT_AUDIO_CONFIG,
      ...options.config,
    };

    this.events = options.events || {};
    this.volume = options.volume ?? 1.0;

    this.validateBrowserSupport();
  }

  /**
   * ブラウザサポートチェック
   */
  private validateBrowserSupport(): void {
    if (!isWebAudioSupported()) {
      throw new AudioError(
        'このブラウザはWeb Audio APIに対応していません',
        AudioErrorCode.UNSUPPORTED_BROWSER
      );
    }
  }

  /**
   * プレイヤーを初期化
   */
  async initialize(): Promise<void> {
    if (this.state !== 'idle') {
      console.warn('[AudioPlayer] Already initialized');
      return;
    }

    this.setState('initializing');

    try {
      // AudioContext作成
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      this.audioContext = new AudioContextClass({
        sampleRate: this.config.outputSampleRate,
      });

      // GainNode作成（音量制御用）
      this.gainNode = this.audioContext.createGain();
      this.gainNode.gain.value = this.volume;
      this.gainNode.connect(this.audioContext.destination);

      // AudioContextを再開（Chromeのautoplay policy対策）
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      console.log(`[AudioPlayer] 初期化完了 (${this.audioContext.sampleRate}Hz)`);
      this.setState('idle');
    } catch (error) {
      const audioError = new AudioError(
        'プレイヤーの初期化に失敗しました',
        AudioErrorCode.INITIALIZATION_FAILED,
        error as Error
      );
      this.setState('error');
      this.events.onError?.(audioError);
      throw audioError;
    }
  }

  /**
   * 音声チャンクを追加
   */
  async addChunk(chunk: AudioChunk): Promise<void> {
    if (!this.audioContext) {
      await this.initialize();
    }

    // キューに追加
    this.audioQueue.push(chunk);

    // 再生が停止している場合は開始
    if (!this.isPlaying) {
      await this.startPlayback();
    }
  }

  /**
   * 音声データ（Int16Array）を直接追加
   */
  async addPCMData(pcmData: Int16Array): Promise<void> {
    const chunk: AudioChunk = {
      data: pcmData,
      timestamp: Date.now(),
      sizeBytes: pcmData.byteLength,
      durationSec: pcmData.length / this.config.outputSampleRate,
    };

    await this.addChunk(chunk);
  }

  /**
   * Base64エンコードされたPCMデータを追加
   */
  async addBase64PCM(base64Data: string): Promise<void> {
    const pcmData = this.base64ToInt16Array(base64Data);
    await this.addPCMData(pcmData);
  }

  /**
   * 再生開始
   */
  private async startPlayback(): Promise<void> {
    if (this.isPlaying) {
      return;
    }

    if (!this.audioContext) {
      await this.initialize();
    }

    try {
      // AudioContext再開
      if (this.audioContext!.state === 'suspended') {
        await this.audioContext!.resume();
      }

      this.isPlaying = true;
      this.currentTime = this.audioContext!.currentTime;
      this.startTime = Date.now();
      this.chunksPlayed = 0;
      this.totalBytes = 0;

      this.setState('playing');
      this.events.onStart?.();
      console.log('[AudioPlayer] 再生開始');

      // キューを処理
      this.processQueue();
    } catch (error) {
      const audioError = new AudioError(
        '再生の開始に失敗しました',
        AudioErrorCode.PROCESSING_ERROR,
        error as Error
      );
      this.setState('error');
      this.events.onError?.(audioError);
      throw audioError;
    }
  }

  /**
   * キュー処理
   */
  private processQueue(): void {
    if (!this.isPlaying || this.audioQueue.length === 0) {
      // キューが空になったら再生終了
      if (this.isPlaying && this.audioQueue.length === 0) {
        this.stopPlayback();
      }
      return;
    }

    // 次のチャンクを取得
    const chunk = this.audioQueue.shift()!;

    // AudioBufferを作成
    const buffer = this.audioContext!.createBuffer(
      this.config.channels,
      chunk.data.length,
      this.config.outputSampleRate
    );

    // Int16ArrayをFloat32Arrayに変換してバッファに設定
    const channelData = buffer.getChannelData(0);
    this.int16ToFloat32(chunk.data, channelData);

    // BufferSourceNodeを作成
    const sourceNode = this.audioContext!.createBufferSource();
    sourceNode.buffer = buffer;
    sourceNode.connect(this.gainNode!);

    // 再生完了時のコールバック
    sourceNode.onended = () => {
      this.processQueue(); // 次のチャンクを処理
    };

    // 再生開始
    sourceNode.start(this.currentTime);
    this.currentTime += chunk.durationSec;

    // メトリクス更新
    this.chunksPlayed++;
    this.totalBytes += chunk.sizeBytes;
  }

  /**
   * 再生停止
   */
  private stopPlayback(): void {
    if (!this.isPlaying) {
      return;
    }

    this.isPlaying = false;
    this.setState('stopped');
    this.events.onEnd?.();
    console.log('[AudioPlayer] 再生停止');
    console.log(`  - チャンク数: ${this.chunksPlayed}`);
    console.log(`  - 総バイト数: ${this.totalBytes}`);
  }

  /**
   * 一時停止
   */
  async pause(): Promise<void> {
    if (this.state !== 'playing') {
      console.warn('[AudioPlayer] Not playing');
      return;
    }

    if (this.audioContext && this.audioContext.state === 'running') {
      await this.audioContext.suspend();
      this.setState('paused');
      console.log('[AudioPlayer] 一時停止');
    }
  }

  /**
   * 再開
   */
  async resume(): Promise<void> {
    if (this.state !== 'paused') {
      console.warn('[AudioPlayer] Not paused');
      return;
    }

    if (this.audioContext && this.audioContext.state === 'suspended') {
      await this.audioContext.resume();
      this.setState('playing');
      console.log('[AudioPlayer] 再開');
    }
  }

  /**
   * 完全停止（キューをクリア）
   */
  stop(): void {
    this.audioQueue = [];
    this.stopPlayback();
    this.setState('idle');
  }

  /**
   * 音量設定
   */
  setVolume(volume: number): void {
    this.volume = Math.max(0, Math.min(1, volume));
    if (this.gainNode) {
      this.gainNode.gain.value = this.volume;
    }
  }

  /**
   * Int16Array を Float32Array に変換
   */
  private int16ToFloat32(int16Array: Int16Array, float32Array: Float32Array): void {
    for (let i = 0; i < int16Array.length; i++) {
      // -32768 ~ 32767 を -1.0 ~ 1.0 にスケール
      float32Array[i] = int16Array[i] / (int16Array[i] < 0 ? 0x8000 : 0x7fff);
    }
  }

  /**
   * Base64文字列をInt16Arrayに変換
   */
  private base64ToInt16Array(base64: string): Int16Array {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return new Int16Array(bytes.buffer);
  }

  /**
   * リソース解放
   */
  async dispose(): Promise<void> {
    this.stop();

    // AudioContext閉鎖
    if (this.audioContext && this.audioContext.state !== 'closed') {
      await this.audioContext.close();
      this.audioContext = null;
    }

    this.gainNode = null;
    this.setState('idle');
    console.log('[AudioPlayer] リソース解放完了');
  }

  /**
   * 状態変更
   */
  private setState(newState: PlayerState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.events.onStateChange?.(newState);
    }
  }

  // Getters
  getState(): PlayerState {
    return this.state;
  }

  getMetrics() {
    return {
      chunksPlayed: this.chunksPlayed,
      totalBytes: this.totalBytes,
      totalDuration: this.startTime > 0 ? (Date.now() - this.startTime) / 1000 : 0,
      startTime: this.startTime,
      queueLength: this.audioQueue.length,
    };
  }

  getConfig(): AudioConfig {
    return { ...this.config };
  }

  isCurrentlyPlaying(): boolean {
    return this.state === 'playing';
  }

  getVolume(): number {
    return this.volume;
  }

  getQueueLength(): number {
    return this.audioQueue.length;
  }
}

export default AudioPlayer;
