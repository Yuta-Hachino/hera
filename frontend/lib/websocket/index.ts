/**
 * WebSocket Module - Gemini Live API WebSocket通信
 *
 * このモジュールは、Gemini Live APIとのWebSocket通信機能を提供します。
 */

// Core class
export { LiveSessionManager } from './LiveSessionManager';

// Types
export type {
  BaseMessage,
  ClientContentMessage,
  ConnectionMetrics,
  ConnectionState,
  LiveAPIMessage,
  LiveSessionOptions,
  RealtimeInputMessage,
  ServerContentMessage,
  SessionConfig,
  SetupCompleteMessage,
  SetupMessage,
  ToolCallMessage,
  ToolResponseMessage,
  WebSocketEventHandlers,
} from './types';

// Error handling
export { WebSocketError, WebSocketErrorCode } from './types';

// Re-export default
export { default as LiveSessionManagerClass } from './LiveSessionManager';
