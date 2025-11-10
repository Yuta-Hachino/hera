/**
 * LiveSessionManager - Gemini Live API WebSocket通信管理
 *
 * Gemini Live APIとのWebSocket接続を管理するクラス
 * - Ephemeral Token取得
 * - WebSocket接続・切断
 * - メッセージ送受信
 * - 自動再接続
 */

import {
  ClientContentMessage,
  ConnectionMetrics,
  ConnectionState,
  LiveAPIMessage,
  LiveSessionOptions,
  RealtimeInputMessage,
  ServerContentMessage,
  SetupMessage,
  ToolResponseMessage,
  WebSocketError,
  WebSocketErrorCode,
  WebSocketEventHandlers,
} from './types';

export class LiveSessionManager {
  private sessionId: string;
  private config: LiveSessionOptions['config'];
  private handlers: WebSocketEventHandlers;
  private autoReconnect: boolean;
  private reconnectInterval: number;
  private maxReconnectAttempts: number;

  // WebSocket
  private ws: WebSocket | null = null;
  private wsEndpoint: string | null = null;
  private token: string | null = null;

  // State
  private state: ConnectionState = 'disconnected';
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;

  // Metrics
  private metrics: ConnectionMetrics = {
    connectTime: 0,
    messagesSent: 0,
    messagesReceived: 0,
    reconnectAttempts: 0,
    errorCount: 0,
  };

  constructor(options: LiveSessionOptions) {
    this.sessionId = options.sessionId;
    this.config = options.config || {};
    this.handlers = options.handlers || {};
    this.autoReconnect = options.autoReconnect ?? true;
    this.reconnectInterval = options.reconnectInterval ?? 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts ?? 5;
  }

  /**
   * セッション開始
   */
  async start(): Promise<void> {
    if (this.state === 'connected' || this.state === 'connecting') {
      console.warn('[LiveSession] Already connected or connecting');
      return;
    }

    try {
      this.setState('connecting');

      // Ephemeral Token取得
      await this.fetchEphemeralToken();

      // WebSocket接続
      await this.connectWebSocket();

      // Setup メッセージ送信
      await this.sendSetupMessage();

      console.log('[LiveSession] セッション開始成功');
    } catch (error) {
      console.error('[LiveSession] セッション開始失敗:', error);
      this.setState('error');
      this.handlers.onError?.(error as Error);
      throw error;
    }
  }

  /**
   * Ephemeral Token取得
   */
  private async fetchEphemeralToken(): Promise<void> {
    try {
      const response = await fetch(`/api/sessions/${this.sessionId}/ephemeral-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Token fetch failed');
      }

      const data = await response.json();
      this.token = data.token;
      this.wsEndpoint = data.ws_endpoint;

      console.log('[LiveSession] Ephemeral Token取得成功');
    } catch (error) {
      throw new WebSocketError(
        'Ephemeral Tokenの取得に失敗しました',
        WebSocketErrorCode.TOKEN_FETCH_FAILED,
        error as Error
      );
    }
  }

  /**
   * WebSocket接続
   */
  private async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.wsEndpoint) {
        reject(new Error('WebSocket endpoint not set'));
        return;
      }

      try {
        this.ws = new WebSocket(this.wsEndpoint);

        // 接続成功
        this.ws.onopen = () => {
          console.log('[LiveSession] WebSocket接続成功');
          this.setState('connected');
          this.metrics.connectTime = Date.now();
          this.reconnectAttempts = 0;
          this.handlers.onConnect?.();
          resolve();
        };

        // メッセージ受信
        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        // エラー
        this.ws.onerror = (event) => {
          console.error('[LiveSession] WebSocketエラー:', event);
          this.metrics.errorCount++;
          const error = new WebSocketError(
            'WebSocket接続エラー',
            WebSocketErrorCode.CONNECTION_FAILED
          );
          this.handlers.onError?.(error);
        };

        // 切断
        this.ws.onclose = (event) => {
          console.log('[LiveSession] WebSocket切断:', event.code, event.reason);
          this.metrics.disconnectTime = Date.now();
          this.handleDisconnect(event);
        };
      } catch (error) {
        reject(
          new WebSocketError(
            'WebSocket接続の作成に失敗しました',
            WebSocketErrorCode.CONNECTION_FAILED,
            error as Error
          )
        );
      }
    });
  }

  /**
   * Setupメッセージ送信
   */
  private async sendSetupMessage(): Promise<void> {
    const setupMessage: SetupMessage = {
      type: 'setup',
      setup: {
        model: this.config.model || 'gemini-2.0-flash-live-preview-04-09',
      },
    };

    // レスポンスモダリティ設定
    if (this.config.enableAudioOutput) {
      setupMessage.setup.generation_config = {
        response_modalities: ['TEXT', 'AUDIO'],
      };
    }

    // システムインストラクション設定
    if (this.config.systemInstruction) {
      setupMessage.setup.system_instruction = {
        parts: [{ text: this.config.systemInstruction }],
      };
    }

    await this.sendMessage(setupMessage);
    console.log('[LiveSession] Setupメッセージ送信完了');
  }

  /**
   * メッセージ送信
   */
  async sendMessage(message: LiveAPIMessage): Promise<void> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new WebSocketError(
        'WebSocketが接続されていません',
        WebSocketErrorCode.SEND_FAILED
      );
    }

    try {
      const messageStr = JSON.stringify(message);
      this.ws.send(messageStr);
      this.metrics.messagesSent++;
    } catch (error) {
      throw new WebSocketError(
        'メッセージの送信に失敗しました',
        WebSocketErrorCode.SEND_FAILED,
        error as Error
      );
    }
  }

  /**
   * テキストメッセージ送信
   */
  async sendText(text: string, turnComplete: boolean = true): Promise<void> {
    const message: ClientContentMessage = {
      type: 'client_content',
      client_content: {
        turns: [
          {
            role: 'user',
            parts: [{ text }],
          },
        ],
        turn_complete: turnComplete,
      },
    };

    await this.sendMessage(message);
  }

  /**
   * 音声データ送信（Base64エンコード済み）
   */
  async sendAudioChunk(base64Data: string): Promise<void> {
    const message: RealtimeInputMessage = {
      type: 'realtime_input',
      realtime_input: {
        media_chunks: [
          {
            mime_type: 'audio/pcm',
            data: base64Data,
          },
        ],
      },
    };

    await this.sendMessage(message);
  }

  /**
   * Tool Response送信
   */
  async sendToolResponse(responses: ToolResponseMessage['tool_response']['function_responses']): Promise<void> {
    const message: ToolResponseMessage = {
      type: 'tool_response',
      tool_response: {
        function_responses: responses,
      },
    };

    await this.sendMessage(message);
  }

  /**
   * メッセージ受信処理
   */
  private handleMessage(data: string): void {
    try {
      const message: LiveAPIMessage = JSON.parse(data);
      this.metrics.messagesReceived++;

      // 汎用ハンドラ
      this.handlers.onMessage?.(message);

      // タイプ別ハンドラ
      switch (message.type) {
        case 'server_content':
          this.handleServerContent(message as ServerContentMessage);
          break;

        case 'tool_call':
          this.handlers.onToolCall?.(message.tool_call);
          break;

        case 'setup_complete':
          console.log('[LiveSession] セットアップ完了');
          break;

        default:
          console.log('[LiveSession] 受信:', message.type);
      }
    } catch (error) {
      console.error('[LiveSession] メッセージ解析エラー:', error);
      this.metrics.errorCount++;
      this.handlers.onError?.(
        new WebSocketError(
          'メッセージの解析に失敗しました',
          WebSocketErrorCode.PARSE_FAILED,
          error as Error
        )
      );
    }
  }

  /**
   * ServerContentメッセージ処理
   */
  private handleServerContent(message: ServerContentMessage): void {
    const parts = message.server_content.model_turn.parts;

    parts.forEach((part) => {
      if ('text' in part) {
        // テキストレスポンス
        this.handlers.onTextMessage?.(part.text);
      } else if ('inline_data' in part && part.inline_data.mime_type.startsWith('audio/')) {
        // 音声データ
        this.handlers.onAudioData?.(part.inline_data.data);
      }
    });
  }

  /**
   * 切断処理
   */
  private handleDisconnect(event: CloseEvent): void {
    const wasConnected = this.state === 'connected';
    this.setState('disconnected');
    this.handlers.onDisconnect?.();

    // 自動再接続
    if (wasConnected && this.autoReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
      console.log(
        `[LiveSession] 再接続試行 ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts}`
      );
      this.scheduleReconnect();
    } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[LiveSession] 最大再接続試行回数に達しました');
      this.setState('error');
      this.handlers.onError?.(
        new WebSocketError(
          '再接続に失敗しました',
          WebSocketErrorCode.UNEXPECTED_DISCONNECT
        )
      );
    }
  }

  /**
   * 再接続スケジュール
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.metrics.reconnectAttempts++;
      this.start().catch((error) => {
        console.error('[LiveSession] 再接続失敗:', error);
      });
    }, this.reconnectInterval);
  }

  /**
   * セッション停止
   */
  async stop(): Promise<void> {
    this.setState('disconnecting');

    // 再接続タイマークリア
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    // WebSocket切断
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.close(1000, 'Normal closure');
      }
      this.ws = null;
    }

    this.setState('disconnected');
    console.log('[LiveSession] セッション停止');
  }

  /**
   * 状態変更
   */
  private setState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.handlers.onStateChange?.(newState);
    }
  }

  // Getters
  getState(): ConnectionState {
    return this.state;
  }

  isConnected(): boolean {
    return this.state === 'connected';
  }

  getMetrics(): ConnectionMetrics {
    return { ...this.metrics };
  }

  getSessionId(): string {
    return this.sessionId;
  }
}

export default LiveSessionManager;
