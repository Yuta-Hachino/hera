'use client';

import { ReactNode, useState } from 'react';
import HeraAvatar from './HeraAvatar';
import Live2DSettings from './Live2DSettings';
import { Live2DConfig } from './Live2DSettings';

type BackgroundLayoutProps = {
  children: ReactNode;
  heraText?: string;
};

export default function BackgroundLayout({
  children,
  heraText,
}: BackgroundLayoutProps) {
  const [config, setConfig] = useState<Live2DConfig>({
    positionY: -0.1, // 上に移動
    positionX: 0,
    scale: 0.8, // 背景用にスケールを調整
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
      {/* 画面全体の背景としてLive2Dを配置 */}
      <div className="fixed inset-0 w-full h-full z-0">
        <div
          className="w-full h-full flex items-center justify-center"
          style={{
            backgroundColor: config.backgroundImage ? 'transparent' : (config.backgroundColor || '#f0f0f0'),
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
      </div>

      {/* チャットコンテンツを前面に表示 */}
      <div className="relative z-10 w-full h-screen flex flex-col">
        {children}
      </div>

      <Live2DSettings config={config} onChange={setConfig} />
    </>
  );
}
