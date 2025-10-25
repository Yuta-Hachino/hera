'use client';

import { useState } from 'react';

export type Live2DConfig = {
  positionY: number;
  positionX: number;
  scale: number;
  enableBlinking: boolean;
  blinkInterval: [number, number];
  enableLipSync: boolean;
  lipSyncSensitivity: number;
};

type Live2DSettingsProps = {
  config: Live2DConfig;
  onChange: (config: Live2DConfig) => void;
};

export default function Live2DSettings({ config, onChange }: Live2DSettingsProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleChange = (key: keyof Live2DConfig, value: any) => {
    onChange({ ...config, [key]: value });
  };

  return (
    <>
      {/* 設定ボタン */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed top-4 right-4 z-50 bg-primary-500 hover:bg-primary-600 text-white rounded-full p-3 shadow-lg transition-colors"
        title="Live2D設定"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </button>

      {/* 設定パネル */}
      {isOpen && (
        <>
          {/* オーバーレイ */}
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* 設定パネル */}
          <div className="fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-50 overflow-y-auto">
            <div className="p-6">
              {/* ヘッダー */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-800">Live2D設定</h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* 設定項目 */}
              <div className="space-y-6">
                {/* 位置Y */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    縦位置 (Y): {config.positionY.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="-1"
                    max="1"
                    step="0.05"
                    value={config.positionY}
                    onChange={(e) => handleChange('positionY', parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>上</span>
                    <span>下</span>
                  </div>
                </div>

                {/* 位置X */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    横位置 (X): {config.positionX.toFixed(2)}
                  </label>
                  <input
                    type="range"
                    min="-1"
                    max="1"
                    step="0.05"
                    value={config.positionX}
                    onChange={(e) => handleChange('positionX', parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>左</span>
                    <span>右</span>
                  </div>
                </div>

                {/* スケール */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    拡大率: {config.scale.toFixed(2)}x
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.1"
                    value={config.scale}
                    onChange={(e) => handleChange('scale', parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0.5x</span>
                    <span>2.0x</span>
                  </div>
                </div>

                {/* まばたき */}
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    まばたき
                  </label>
                  <button
                    onClick={() => handleChange('enableBlinking', !config.enableBlinking)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      config.enableBlinking ? 'bg-primary-500' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        config.enableBlinking ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* まばたき間隔 */}
                {config.enableBlinking && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      まばたき間隔: {config.blinkInterval[0]}ms - {config.blinkInterval[1]}ms
                    </label>
                    <div className="space-y-2">
                      <input
                        type="range"
                        min="1000"
                        max="10000"
                        step="500"
                        value={config.blinkInterval[0]}
                        onChange={(e) =>
                          handleChange('blinkInterval', [
                            parseFloat(e.target.value),
                            config.blinkInterval[1],
                          ])
                        }
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
                      />
                      <input
                        type="range"
                        min="1000"
                        max="10000"
                        step="500"
                        value={config.blinkInterval[1]}
                        onChange={(e) =>
                          handleChange('blinkInterval', [
                            config.blinkInterval[0],
                            parseFloat(e.target.value),
                          ])
                        }
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
                      />
                    </div>
                  </div>
                )}

                {/* リップシンク */}
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">
                    リップシンク
                  </label>
                  <button
                    onClick={() => handleChange('enableLipSync', !config.enableLipSync)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      config.enableLipSync ? 'bg-primary-500' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        config.enableLipSync ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* リップシンク感度 */}
                {config.enableLipSync && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      リップシンク感度: {config.lipSyncSensitivity.toFixed(1)}
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="3"
                      step="0.1"
                      value={config.lipSyncSensitivity}
                      onChange={(e) =>
                        handleChange('lipSyncSensitivity', parseFloat(e.target.value))
                      }
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>低</span>
                      <span>高</span>
                    </div>
                  </div>
                )}

                {/* リセットボタン */}
                <button
                  onClick={() => {
                    onChange({
                      positionY: -0.2,
                      positionX: 0,
                      scale: 1.0,
                      enableBlinking: true,
                      blinkInterval: [3000, 5000],
                      enableLipSync: true,
                      lipSyncSensitivity: 1.5,
                    });
                  }}
                  className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors"
                >
                  デフォルトに戻す
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
