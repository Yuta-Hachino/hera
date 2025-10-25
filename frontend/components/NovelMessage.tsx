'use client';

import { useState, useEffect } from 'react';

type NovelMessageProps = {
  speaker: string;
  speakerColor?: string;
  message: string;
  timestamp?: string;
  isTyping?: boolean;
  typingSpeed?: number;
  avatar?: string;
};

const speakerColors: Record<string, string> = {
  hera: 'text-purple-600',
  user: 'text-blue-600',
  child: 'text-pink-600',
  partner: 'text-green-600',
  family: 'text-orange-600',
  // 日本語のロール名
  '妻': 'text-rose-600',
  '夫': 'text-cyan-600',
  'パートナー': 'text-green-600',
  '娘': 'text-pink-500',
  '息子': 'text-blue-500',
  '長男': 'text-blue-600',
  '次男': 'text-blue-500',
  '長女': 'text-pink-600',
  '次女': 'text-pink-500',
  default: 'text-gray-700',
};

const speakerNames: Record<string, string> = {
  hera: 'ヘーラー',
  user: 'あなた',
  child: '子ども',
  partner: 'パートナー',
  family: '家族',
  // 英語のロール名を日本語に変換
  wife: '妻',
  husband: '夫',
  daughter: '娘',
  son: '息子',
};

export default function NovelMessage({
  speaker,
  speakerColor,
  message,
  timestamp,
  isTyping = false,
  typingSpeed = 30,
  avatar,
}: NovelMessageProps) {
  const [displayedText, setDisplayedText] = useState(isTyping ? '' : message);
  const [currentIndex, setCurrentIndex] = useState(0);

  // タイピングアニメーション
  useEffect(() => {
    if (isTyping && currentIndex < message.length) {
      const timer = setTimeout(() => {
        setDisplayedText(message.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, typingSpeed);

      return () => clearTimeout(timer);
    }
  }, [isTyping, currentIndex, message, typingSpeed]);

  // 新しいメッセージが来たらリセット
  useEffect(() => {
    if (isTyping) {
      setDisplayedText('');
      setCurrentIndex(0);
    } else {
      setDisplayedText(message);
    }
  }, [message, isTyping]);

  // speakerNamesに定義があればそれを使用、なければspeaker自体をそのまま表示（日本語のロール名にも対応）
  const displayName = speakerNames[speaker.toLowerCase()] || speakerNames[speaker] || speaker;
  const nameColor = speakerColor || speakerColors[speaker.toLowerCase()] || speakerColors[speaker] || speakerColors.default;

  return (
    <div className="animate-fade-in mb-6">
      {/* メッセージボックス */}
      <div className="bg-white/40 backdrop-blur-sm rounded-lg shadow-lg p-6 border border-gray-200">
        {/* スピーカー名前とアバター */}
        <div className="flex items-center mb-3">
          {avatar && (
            <div className="w-10 h-10 rounded-full overflow-hidden mr-3 border-2 border-white shadow-sm">
              <img
                src={avatar}
                alt={displayName}
                className="w-full h-full object-cover"
              />
            </div>
          )}
          <div className="flex-1">
            <div className="flex items-baseline">
              <span className={`font-bold text-lg ${nameColor}`}>
                {displayName}
              </span>
              {timestamp && (
                <span className="text-xs text-gray-400 ml-3">
                  {new Date(timestamp).toLocaleTimeString('ja-JP', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* メッセージテキスト */}
        <div className="ml-13">
          <p className="text-gray-800 leading-relaxed whitespace-pre-wrap text-base">
            {displayedText}
            {isTyping && currentIndex < message.length && (
              <span className="inline-block w-2 h-4 bg-gray-600 animate-pulse ml-1" />
            )}
          </p>
        </div>
      </div>
    </div>
  );
}