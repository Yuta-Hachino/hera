/**
 * WebSocket Types for Gemini Live API
 *
 * Gemini Live API用のWebSocket通信に関する型定義
 */

/**
 * WebSocket接続状態
 */
export type ConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'disconnecting'
  | 'error';

/**
 * セッション設定
 */
export interface SessionConfig {
  /** モデル名 */
  model?: string;
  /** システムインストラクション */
  systemInstruction?: string;
  /** 音声入力有効化 */
  enableAudioInput?: boolean;
  /** 音声出力有効化 */
  enableAudioOutput?: boolean;
}

/**
 * Gemini Live APIメッセージの基底型
 */
export interface BaseMessage {
  /** メッセージタイプ */
  type: string;
  /** タイムスタンプ */
  timestamp?: number;
}

/**
 * Setup メッセージ（セッション開始時に送信）
 */
export interface SetupMessage extends BaseMessage {
  type: 'setup';
  setup: {
    model?: string;
    generation_config?: {
      response_modalities?: string[];
      speech_config?: {
        voice_config?: {
          prebuilt_voice_config?: {
            voice_name?: string;
          };
        };
      };
    };
    system_instruction?: {
      parts: Array<{
        text: string;
      }>;
    };
  };
}

/**
 * Client Content メッセージ（クライアントからの入力）
 */
export interface ClientContentMessage extends BaseMessage {
  type: 'client_content';
  client_content: {
    turns: Array<{
      role: 'user';
      parts: Array<
        | { text: string }
        | { inline_data: { mime_type: string; data: string } }
      >;
    }>;
    turn_complete: boolean;
  };
}

/**
 * Realtime Input メッセージ（音声データ送信）
 */
export interface RealtimeInputMessage extends BaseMessage {
  type: 'realtime_input';
  realtime_input: {
    media_chunks: Array<{
      mime_type: 'audio/pcm';
      data: string; // Base64エンコードされたPCMデータ
    }>;
  };
}

/**
 * Server Content メッセージ（サーバーからのレスポンス）
 */
export interface ServerContentMessage extends BaseMessage {
  type: 'server_content';
  server_content: {
    model_turn: {
      parts: Array<
        | { text: string }
        | { inline_data: { mime_type: string; data: string } }
      >;
    };
    turn_complete: boolean;
  };
}

/**
 * Tool Call メッセージ（関数呼び出し）
 */
export interface ToolCallMessage extends BaseMessage {
  type: 'tool_call';
  tool_call: {
    function_calls: Array<{
      id: string;
      name: string;
      args: Record<string, any>;
    }>;
  };
}

/**
 * Tool Response メッセージ（関数実行結果）
 */
export interface ToolResponseMessage extends BaseMessage {
  type: 'tool_response';
  tool_response: {
    function_responses: Array<{
      id: string;
      name: string;
      response: Record<string, any>;
    }>;
  };
}

/**
 * Setup Complete メッセージ（セットアップ完了通知）
 */
export interface SetupCompleteMessage extends BaseMessage {
  type: 'setup_complete';
}

/**
 * すべてのメッセージ型のユニオン
 */
export type LiveAPIMessage =
  | SetupMessage
  | ClientContentMessage
  | RealtimeInputMessage
  | ServerContentMessage
  | ToolCallMessage
  | ToolResponseMessage
  | SetupCompleteMessage;

/**
 * WebSocketイベントハンドラ
 */
export interface WebSocketEventHandlers {
  /** 接続成功時 */
  onConnect?: () => void;
  /** 切断時 */
  onDisconnect?: () => void;
  /** メッセージ受信時 */
  onMessage?: (message: LiveAPIMessage) => void;
  /** テキストメッセージ受信時 */
  onTextMessage?: (text: string) => void;
  /** 音声データ受信時 */
  onAudioData?: (audioData: string) => void; // Base64
  /** Tool Call受信時 */
  onToolCall?: (toolCall: ToolCallMessage['tool_call']) => void;
  /** エラー発生時 */
  onError?: (error: Error) => void;
  /** 状態変更時 */
  onStateChange?: (state: ConnectionState) => void;
}

/**
 * LiveSessionManagerのオプション
 */
export interface LiveSessionOptions {
  /** セッションID */
  sessionId: string;
  /** セッション設定 */
  config?: SessionConfig;
  /** イベントハンドラ */
  handlers?: WebSocketEventHandlers;
  /** 自動再接続 */
  autoReconnect?: boolean;
  /** 再接続間隔（ms） */
  reconnectInterval?: number;
  /** 最大再接続試行回数 */
  maxReconnectAttempts?: number;
}

/**
 * WebSocketエラー
 */
export class WebSocketError extends Error {
  constructor(
    message: string,
    public code: WebSocketErrorCode,
    public originalError?: Error
  ) {
    super(message);
    this.name = 'WebSocketError';
  }
}

/**
 * WebSocketエラーコード
 */
export enum WebSocketErrorCode {
  /** 接続失敗 */
  CONNECTION_FAILED = 'CONNECTION_FAILED',
  /** トークン取得失敗 */
  TOKEN_FETCH_FAILED = 'TOKEN_FETCH_FAILED',
  /** メッセージ送信失敗 */
  SEND_FAILED = 'SEND_FAILED',
  /** メッセージ解析失敗 */
  PARSE_FAILED = 'PARSE_FAILED',
  /** 予期しない切断 */
  UNEXPECTED_DISCONNECT = 'UNEXPECTED_DISCONNECT',
  /** 不明なエラー */
  UNKNOWN = 'UNKNOWN',
}

/**
 * 接続メトリクス
 */
export interface ConnectionMetrics {
  /** 接続開始時刻 */
  connectTime: number;
  /** 切断時刻 */
  disconnectTime?: number;
  /** 送信メッセージ数 */
  messagesSent: number;
  /** 受信メッセージ数 */
  messagesReceived: number;
  /** 再接続試行回数 */
  reconnectAttempts: number;
  /** エラー数 */
  errorCount: number;
}
