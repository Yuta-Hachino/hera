'use client';

import { useState, useCallback, useEffect } from 'react';

type UseTTSReturn = {
  isSpeaking: boolean;
  audioSrc: string | undefined;
  speak: (text: string) => void;
  stop: () => void;
};

export function useTTS(): UseTTSReturn {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioSrc, setAudioSrc] = useState<string>();

  useEffect(() => {
    // クリーンアップ: コンポーネントアンマウント時に音声を停止
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const speak = useCallback((text: string) => {
    if (!text || typeof window === 'undefined') return;

    try {
      // 既存の音声を停止
      window.speechSynthesis.cancel();

      // Web Speech API で音声合成
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'ja-JP';
      utterance.rate = 1.0;
      utterance.pitch = 1.2;
      utterance.volume = 1.0;

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (event) => {
        console.error('TTS error:', event);
        setIsSpeaking(false);
      };

      window.speechSynthesis.speak(utterance);
    } catch (error) {
      console.error('TTS initialization error:', error);
      setIsSpeaking(false);
    }
  }, []);

  const stop = useCallback(() => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  return { isSpeaking, audioSrc, speak, stop };
}
