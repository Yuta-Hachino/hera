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
    scale: 10.0,
    enableBlinking: true,
    blinkInterval: [3000, 5000],
    blinkDuration: 100,
    enableLipSync: true,
    lipSyncSensitivity: 1.5,
    enableBreathing: true,
    breathingSpeed: 1.0,
    breathingIntensity: 0.5,
    enableMouseTracking: true,
    trackingSmoothing: 0.1,
    trackingRange: 1.0,
    ttsVolume: 1.0,
    ttsVoice: 'ja-JP',
    showGradientBackground: false,
    backgroundImage: '/images/background.jpg',
    backgroundColor: '#ffffff',
  });

  return (
    <>
      <ResizableLayout
        topContent={
          <div
            className="w-full h-full flex items-center justify-center"
            style={{
              backgroundColor: config.backgroundImage ? 'transparent' : (config.backgroundColor || '#ffffff'),
              backgroundImage: config.backgroundImage ? `url(${config.backgroundImage})` : 'none',
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              backgroundRepeat: 'no-repeat',
              ...(config.showGradientBackground && !config.backgroundImage && {
                background: 'linear-gradient(to bottom, rgb(243 232 255), rgb(252 231 243))',
              }),
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
