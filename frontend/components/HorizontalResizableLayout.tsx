'use client';

import { ReactNode, useState, useRef, useEffect } from 'react';

type HorizontalResizableLayoutProps = {
  leftContent: ReactNode;
  rightContent: ReactNode;
  defaultLeftWidth?: number; // パーセンテージ (0-100)
};

export default function HorizontalResizableLayout({
  leftContent,
  rightContent,
  defaultLeftWidth = 50,
}: HorizontalResizableLayoutProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;

      // 最小20%、最大80%に制限
      const clampedWidth = Math.min(Math.max(newLeftWidth, 20), 80);
      setLeftWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      // ドラッグ中はテキスト選択を無効化
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isDragging]);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  return (
    <div ref={containerRef} className="flex h-screen">
      {/* 左側コンテンツ (Live2D) */}
      <div
        style={{ width: `${leftWidth}%` }}
        className="flex-shrink-0 overflow-hidden"
      >
        {leftContent}
      </div>

      {/* リサイザー（ドラッグハンドル） */}
      <div
        onMouseDown={handleMouseDown}
        className={`w-1 bg-gray-300 hover:bg-primary-500 cursor-col-resize relative group transition-colors ${
          isDragging ? 'bg-primary-500' : ''
        }`}
      >
        {/* ドラッグエリアを広げるための透明な領域 */}
        <div className="absolute inset-y-0 -left-1 -right-1 w-3" />

        {/* ビジュアルインジケーター */}
        <div className="absolute inset-y-0 left-1/2 transform -translate-x-1/2 flex items-center justify-center">
          <div className={`w-1 h-12 rounded-full ${
            isDragging ? 'bg-primary-600' : 'bg-gray-400 group-hover:bg-primary-500'
          } transition-colors flex flex-col items-center justify-center gap-0.5`}>
            <div className={`w-0.5 h-1 rounded-full ${
              isDragging ? 'bg-white' : 'bg-white/70'
            }`} />
            <div className={`w-0.5 h-1 rounded-full ${
              isDragging ? 'bg-white' : 'bg-white/70'
            }`} />
            <div className={`w-0.5 h-1 rounded-full ${
              isDragging ? 'bg-white' : 'bg-white/70'
            }`} />
          </div>
        </div>
      </div>

      {/* 右側コンテンツ (チャット) */}
      <div
        style={{ width: `${100 - leftWidth}%` }}
        className="flex-1 overflow-hidden"
      >
        {rightContent}
      </div>
    </div>
  );
}
