'use client';

import { useRef, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Live2DConfig } from './Live2DSettings';

// Live2DCharacterを動的インポート（SSR無効化）
const Live2DCharacter = dynamic(
  () => import('react-live2d-lipsync').then((mod) => mod.Live2DCharacter),
  { ssr: false }
);

type HeraAvatarProps = {
  text?: string; // 読み上げるテキスト
  config: Live2DConfig;
};

export default function HeraAvatar({ text, config }: HeraAvatarProps) {
  const [mounted, setMounted] = useState(false);
  const [audioVolume, setAudioVolume] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLive2DReady, setIsLive2DReady] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    setMounted(true);
    // Live2Dの準備ができるまで少し待つ
    const timer = setTimeout(() => {
      setIsLive2DReady(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // Web Speech APIによるTTS
  useEffect(() => {
    if (!mounted || !text || typeof window === 'undefined') return;

    // 前の音声を停止
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utteranceRef.current = utterance;

    // 日本語音声を選択
    const voices = window.speechSynthesis.getVoices();
    const japaneseVoice = voices.find(voice => voice.lang.startsWith('ja'));
    if (japaneseVoice) {
      utterance.voice = japaneseVoice;
    }
    utterance.lang = 'ja-JP';
    utterance.rate = 1.0;
    utterance.pitch = 1.2;
    utterance.volume = 1.0;

    utterance.onstart = () => {
      setIsSpeaking(true);
      startAudioAnalysis();
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setAudioVolume(0);
      stopAudioAnalysis();
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
      setAudioVolume(0);
      stopAudioAnalysis();
    };

    // 音声リストが読み込まれていない場合のハンドリング
    if (voices.length === 0) {
      window.speechSynthesis.onvoiceschanged = () => {
        const newVoices = window.speechSynthesis.getVoices();
        const japaneseVoice = newVoices.find(voice => voice.lang.startsWith('ja'));
        if (japaneseVoice) {
          utterance.voice = japaneseVoice;
        }
        window.speechSynthesis.speak(utterance);
      };
    } else {
      window.speechSynthesis.speak(utterance);
    }

    return () => {
      if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
      }
      stopAudioAnalysis();
    };
  }, [text, mounted]);

  // 音声分析を開始（マイク入力からの音量検出）
  const startAudioAnalysis = async () => {
    try {
      // Web Speech APIは出力音声を直接分析できないため、
      // 簡易的にランダムな口パクパターンを生成
      const simulateLipSync = () => {
        if (!isSpeaking && window.speechSynthesis.speaking) {
          // ランダムな音量値を生成（0.3〜0.8の範囲）
          const randomVolume = 0.3 + Math.random() * 0.5;
          setAudioVolume(randomVolume);
          animationFrameRef.current = requestAnimationFrame(simulateLipSync);
        } else if (!window.speechSynthesis.speaking) {
          setAudioVolume(0);
        }
      };

      setIsSpeaking(true);
      simulateLipSync();
    } catch (error) {
      console.error('Audio analysis error:', error);
      // フォールバック: 固定値で口パク
      setAudioVolume(0.5);
    }
  };

  const stopAudioAnalysis = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setAudioVolume(0);
  };

  if (!mounted || !isLive2DReady) {
    return (
      <div className="relative w-full h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-8xl mb-4 animate-pulse">👸</div>
          <p className="text-gray-700 font-semibold text-xl">ヘーラー</p>
          <p className="text-xs text-gray-500 mt-4">読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      {typeof window !== 'undefined' && (
        <Live2DCharacter
          modelPath="/live2d/lan/lan.model3.json"
          audioVolume={audioVolume}
          positionY={config.positionY}
          positionX={config.positionX}
          scale={config.scale}
          width={800}
          height={800}
          backgroundColor={0xf5e6ff}
          enableBlinking={config.enableBlinking}
          blinkInterval={config.blinkInterval}
          enableLipSync={config.enableLipSync}
          lipSyncSensitivity={config.lipSyncSensitivity}
        />
      )}
    </div>
  );
}
