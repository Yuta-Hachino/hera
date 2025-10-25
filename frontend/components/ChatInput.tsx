'use client';

import { useState, KeyboardEvent } from 'react';

type ChatInputProps = {
  onSend: (message: string) => void;
  disabled?: boolean;
};

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <div className="flex items-end gap-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="メッセージを入力してください..."
          disabled={disabled}
          rows={3}
          className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="rounded-lg bg-primary-500 px-6 py-2 text-white font-medium hover:bg-primary-600 focus:outline-none focus:ring-2 focus:ring-primary-300 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors h-[76px]"
        >
          送信
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Enterで送信、Shift+Enterで改行
      </p>
    </div>
  );
}
