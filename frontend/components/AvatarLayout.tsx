'use client';

import { ReactNode, useState } from 'react';
import HeraAvatar from './HeraAvatar';
import ResizableLayout from './ResizableLayout';
import Live2DSettings, { Live2DConfig } from './Live2DSettings';

type AvatarLayoutProps = {
  children: ReactNode;
  heraText?: string;
};

export default function AvatarLayout({
  children,
  heraText,
}: AvatarLayoutProps) {
  const [config, setConfig] = useState<Live2DConfig>({
    positionY: -0.2,
    positionX: 0,
    scale: 1.0,
    enableBlinking: true,
    blinkInterval: [3000, 5000],
    enableLipSync: true,
    lipSyncSensitivity: 1.5,
    ttsVolume: 1.0,
    ttsVoice: 'ja-JP',
  });

  return (
    <>
      <ResizableLayout
        topContent={
          <div
            className="w-full h-full flex items-center justify-center"
            style={{
              background: 'linear-gradient(to bottom, rgb(243 232 255), rgb(252 231 243))',
              backgroundImage: 'url(/images/background.jpg)',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
          >
            <HeraAvatar text={heraText} config={config} />
          </div>
        }
        bottomContent={
          <div className="w-full h-full flex flex-col bg-white shadow-lg">
            {children}
          </div>
        }
        defaultTopHeight={60}
      />
      <Live2DSettings config={config} onChange={setConfig} />
    </>
  );
}
