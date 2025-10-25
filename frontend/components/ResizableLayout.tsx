'use client';

import { ReactNode, useState, useRef, useEffect } from 'react';

type ResizableLayoutProps = {
  topContent: ReactNode;
  bottomContent: ReactNode;
  defaultTopHeight?: number; // パーセンテージ (0-100)
};

export default function ResizableLayout({
  topContent,
  bottomContent,
  defaultTopHeight = 60,
}: ResizableLayoutProps) {
  const [topHeight, setTopHeight] = useState(defaultTopHeight);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newTopHeight = ((e.clientY - containerRect.top) / containerRect.height) * 100;

      // 最小30%、最大70%に制限
      const clampedHeight = Math.min(Math.max(newTopHeight, 30), 70);
      setTopHeight(clampedHeight);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      // ドラッグ中はテキスト選択を無効化
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'row-resize';
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
    <div ref={containerRef} className="flex flex-col h-screen bg-gray-50">
      {/* 上側コンテンツ (Live2D) */}
      <div
        style={{ height: `${topHeight}%` }}
        className="flex-shrink-0 overflow-hidden"
      >
        {topContent}
      </div>

      {/* リサイザー（ドラッグハンドル） */}
      <div
        onMouseDown={handleMouseDown}
        className={`h-1 bg-gray-300 hover:bg-primary-500 cursor-row-resize relative group transition-colors ${
          isDragging ? 'bg-primary-500' : ''
        }`}
      >
        {/* ドラッグエリアを広げるための透明な領域 */}
        <div className="absolute inset-x-0 -top-1 -bottom-1 h-3" />

        {/* ビジュアルインジケーター */}
        <div className="absolute inset-x-0 top-1/2 transform -translate-y-1/2 flex items-center justify-center">
          <div className={`h-1 w-12 rounded-full ${
            isDragging ? 'bg-primary-600' : 'bg-gray-400 group-hover:bg-primary-500'
          } transition-colors flex items-center justify-center`}>
            <div className="flex gap-0.5">
              <div className={`h-0.5 w-1 rounded-full ${
                isDragging ? 'bg-white' : 'bg-white/70'
              }`} />
              <div className={`h-0.5 w-1 rounded-full ${
                isDragging ? 'bg-white' : 'bg-white/70'
              }`} />
              <div className={`h-0.5 w-1 rounded-full ${
                isDragging ? 'bg-white' : 'bg-white/70'
              }`} />
            </div>
          </div>
        </div>
      </div>

      {/* 下側コンテンツ (チャット) */}
      <div
        style={{ height: `${100 - topHeight}%` }}
        className="flex-1 overflow-hidden"
      >
        {bottomContent}
      </div>
    </div>
  );
}
