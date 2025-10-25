'use client';

type ChatMessageProps = {
  speaker: 'user' | 'hera';
  message: string;
  timestamp?: string;
};

export default function ChatMessage({
  speaker,
  message,
  timestamp,
}: ChatMessageProps) {
  const isUser = speaker === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 animate-fade-in`}
    >
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary-500 text-white rounded-br-none'
            : 'bg-gray-200 text-gray-800 rounded-bl-none'
        }`}
      >
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
