'use client';

type ChatMessageProps = {
  speaker: string; // 'user' | 'hera' | 'あゆみ' | 'たかし' など
  message: string;
  timestamp?: string;
};

export default function ChatMessage({
  speaker,
  message,
  timestamp,
}: ChatMessageProps) {
  const isUser = speaker === 'user';
  const isHera = speaker === 'hera';
  const isFamily = !isUser && !isHera; // 家族メンバー

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}
    >
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 backdrop-blur-sm ${
          isUser
            ? 'bg-primary-500 bg-opacity-60 text-white rounded-br-none'
            : isHera
            ? 'bg-gray-200 bg-opacity-60 text-gray-800 rounded-bl-none'
            : 'bg-green-200 bg-opacity-60 text-green-800 rounded-bl-none' // 家族メンバーは一律グリーン
        }`}
      >
        {/* 家族メンバーの場合は名前を表示 */}
        {isFamily && (
          <div className="text-xs font-semibold mb-1 opacity-80">
            {speaker}
          </div>
        )}
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        {timestamp && (
          <p
            className={`text-xs mt-1 ${
              isUser ? 'text-purple-100' : 'text-gray-500'
            }`}
          >
            {new Date(timestamp).toLocaleTimeString('ja-JP', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>
        )}
      </div>
    </div>
  );
}
