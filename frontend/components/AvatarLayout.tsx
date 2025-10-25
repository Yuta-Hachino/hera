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
  });

  return (
    <>
      <ResizableLayout
        leftContent={
          <div className="w-full h-full bg-gradient-to-b from-purple-100 to-pink-100 flex items-center justify-center">
            <HeraAvatar text={heraText} config={config} />
          </div>
        }
        rightContent={
          <div className="w-full h-full flex flex-col bg-white shadow-lg">
            {children}
          </div>
        }
        defaultLeftWidth={33}
      />
      <Live2DSettings config={config} onChange={setConfig} />
    </>
  );
}
