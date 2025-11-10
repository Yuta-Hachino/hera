"""
Audio Utilities for Gemini Live API

このモジュールは音声データ処理のユーティリティ関数を提供します。

主な機能:
- PCMデータのバリデーションと変換
- 音声チャンクの分割・結合
- Base64エンコード/デコード
- サンプルレート変換（将来的に拡張可能）

音声フォーマット仕様:
- 入力: Raw PCM, 16kHz, 16-bit, mono, little-endian
- 出力: Raw PCM, 24kHz, 16-bit, mono, little-endian
"""

import base64
import struct
from typing import List, Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


# 音声フォーマット定数
AUDIO_FORMAT_PCM = 'pcm'
INPUT_SAMPLE_RATE = 16000  # 16kHz
OUTPUT_SAMPLE_RATE = 24000  # 24kHz
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes
CHANNELS = 1  # mono
CHUNK_SIZE_MS = 100  # 100ms chunks


def validate_pcm_data(data: bytes, sample_rate: int = INPUT_SAMPLE_RATE) -> bool:
    """
    PCMデータの妥当性を検証

    Args:
        data: PCMデータ（bytes）
        sample_rate: サンプルレート（Hz）

    Returns:
        bool: 妥当な場合True
    """
    if not isinstance(data, bytes):
        logger.error(f"PCMデータは bytes 型である必要があります: {type(data)}")
        return False

    if len(data) == 0:
        logger.warning("PCMデータが空です")
        return False

    # 16-bit PCMの場合、データサイズは2の倍数である必要がある
    if len(data) % SAMPLE_WIDTH != 0:
        logger.error(f"PCMデータサイズが不正です: {len(data)} bytes（2の倍数である必要があります）")
        return False

    # サンプル数を計算
    num_samples = len(data) // SAMPLE_WIDTH
    logger.debug(f"PCMデータ検証OK: {len(data)} bytes, {num_samples} samples")

    return True


def pcm_to_base64(pcm_data: bytes) -> str:
    """
    PCMデータをBase64文字列に変換

    Args:
        pcm_data: PCMデータ（bytes）

    Returns:
        str: Base64エンコードされた文字列
    """
    return base64.b64encode(pcm_data).decode('utf-8')


def base64_to_pcm(base64_str: str) -> bytes:
    """
    Base64文字列をPCMデータに変換

    Args:
        base64_str: Base64エンコードされた文字列

    Returns:
        bytes: PCMデータ
    """
    return base64.b64decode(base64_str)


def split_audio_chunks(
    pcm_data: bytes,
    chunk_duration_ms: int = CHUNK_SIZE_MS,
    sample_rate: int = INPUT_SAMPLE_RATE
) -> List[bytes]:
    """
    PCMデータを指定時間のチャンクに分割

    Args:
        pcm_data: PCMデータ（bytes）
        chunk_duration_ms: チャンク長（ミリ秒）
        sample_rate: サンプルレート（Hz）

    Returns:
        List[bytes]: チャンクのリスト
    """
    # チャンクサイズを計算（bytes）
    chunk_size_samples = (sample_rate * chunk_duration_ms) // 1000
    chunk_size_bytes = chunk_size_samples * SAMPLE_WIDTH

    chunks = []
    offset = 0

    while offset < len(pcm_data):
        chunk = pcm_data[offset:offset + chunk_size_bytes]
        chunks.append(chunk)
        offset += chunk_size_bytes

    logger.debug(f"音声データを{len(chunks)}個のチャンクに分割（各{chunk_duration_ms}ms）")
    return chunks


def merge_audio_chunks(chunks: List[bytes]) -> bytes:
    """
    音声チャンクを結合

    Args:
        chunks: チャンクのリスト

    Returns:
        bytes: 結合されたPCMデータ
    """
    merged = b''.join(chunks)
    logger.debug(f"{len(chunks)}個のチャンクを結合: {len(merged)} bytes")
    return merged


def get_audio_duration(pcm_data: bytes, sample_rate: int = INPUT_SAMPLE_RATE) -> float:
    """
    PCMデータの再生時間を計算

    Args:
        pcm_data: PCMデータ（bytes）
        sample_rate: サンプルレート（Hz）

    Returns:
        float: 再生時間（秒）
    """
    num_samples = len(pcm_data) // SAMPLE_WIDTH
    duration_sec = num_samples / sample_rate
    return duration_sec


def pcm_bytes_to_int16_array(pcm_data: bytes) -> List[int]:
    """
    PCMバイトデータをint16配列に変換

    Args:
        pcm_data: PCMデータ（bytes）

    Returns:
        List[int]: int16サンプル値のリスト
    """
    num_samples = len(pcm_data) // SAMPLE_WIDTH
    samples = struct.unpack(f'<{num_samples}h', pcm_data)  # little-endian int16
    return list(samples)


def int16_array_to_pcm_bytes(samples: List[int]) -> bytes:
    """
    int16配列をPCMバイトデータに変換

    Args:
        samples: int16サンプル値のリスト

    Returns:
        bytes: PCMデータ
    """
    return struct.pack(f'<{len(samples)}h', *samples)  # little-endian int16


def normalize_pcm_volume(pcm_data: bytes, target_amplitude: float = 0.8) -> bytes:
    """
    PCMデータの音量を正規化

    Args:
        pcm_data: PCMデータ（bytes）
        target_amplitude: 目標振幅（0.0-1.0）

    Returns:
        bytes: 正規化されたPCMデータ
    """
    samples = pcm_bytes_to_int16_array(pcm_data)

    # 最大振幅を計算
    max_amplitude = max(abs(s) for s in samples)

    if max_amplitude == 0:
        logger.warning("音声データが無音です（振幅=0）")
        return pcm_data

    # 正規化係数を計算
    target_max = int(32767 * target_amplitude)  # int16の最大値は32767
    scale_factor = target_max / max_amplitude

    # 正規化
    normalized_samples = [int(s * scale_factor) for s in samples]

    # クリッピング（-32768 ~ 32767）
    clipped_samples = [max(-32768, min(32767, s)) for s in normalized_samples]

    logger.debug(f"音量正規化: max_amplitude={max_amplitude} -> {target_max}")
    return int16_array_to_pcm_bytes(clipped_samples)


def detect_silence(
    pcm_data: bytes,
    threshold: int = 500,
    sample_rate: int = INPUT_SAMPLE_RATE
) -> bool:
    """
    音声データが無音かどうかを判定

    Args:
        pcm_data: PCMデータ（bytes）
        threshold: 無音判定の閾値（絶対値）
        sample_rate: サンプルレート（Hz）

    Returns:
        bool: 無音の場合True
    """
    samples = pcm_bytes_to_int16_array(pcm_data)

    # 平均振幅を計算
    avg_amplitude = sum(abs(s) for s in samples) / len(samples)

    is_silent = avg_amplitude < threshold
    logger.debug(f"無音検出: avg_amplitude={avg_amplitude:.1f}, threshold={threshold}, silent={is_silent}")

    return is_silent


def create_silence(duration_ms: int, sample_rate: int = OUTPUT_SAMPLE_RATE) -> bytes:
    """
    指定時間の無音PCMデータを生成

    Args:
        duration_ms: 無音の長さ（ミリ秒）
        sample_rate: サンプルレート（Hz）

    Returns:
        bytes: 無音PCMデータ
    """
    num_samples = (sample_rate * duration_ms) // 1000
    silence = bytes(num_samples * SAMPLE_WIDTH)  # all zeros
    logger.debug(f"無音データ生成: {duration_ms}ms, {len(silence)} bytes")
    return silence


# 音声フォーマット情報取得
def get_audio_format_info(sample_rate: int = INPUT_SAMPLE_RATE) -> dict:
    """
    音声フォーマット情報を取得

    Args:
        sample_rate: サンプルレート（Hz）

    Returns:
        dict: フォーマット情報
    """
    return {
        'format': AUDIO_FORMAT_PCM,
        'sample_rate': sample_rate,
        'sample_width': SAMPLE_WIDTH,
        'channels': CHANNELS,
        'encoding': 'linear16',
        'endianness': 'little',
    }


# エクスポート用の便利関数
def prepare_audio_chunk_for_api(pcm_data: bytes) -> dict:
    """
    音声チャンクをAPI送信用に準備

    Args:
        pcm_data: PCMデータ（bytes）

    Returns:
        dict: API送信用のデータ
    """
    if not validate_pcm_data(pcm_data):
        raise ValueError("無効なPCMデータです")

    return {
        'data': pcm_to_base64(pcm_data),
        'format': get_audio_format_info(),
        'size_bytes': len(pcm_data),
        'duration_sec': get_audio_duration(pcm_data),
    }


if __name__ == "__main__":
    # テスト実行
    print("=" * 60)
    print("Audio Utils Test")
    print("=" * 60)

    # テスト用の音声データ生成（1秒の無音）
    test_silence = create_silence(1000, INPUT_SAMPLE_RATE)
    print(f"✅ 無音データ生成: {len(test_silence)} bytes")

    # バリデーション
    is_valid = validate_pcm_data(test_silence)
    print(f"✅ PCMデータ検証: {is_valid}")

    # チャンク分割
    chunks = split_audio_chunks(test_silence, chunk_duration_ms=100)
    print(f"✅ チャンク分割: {len(chunks)}個のチャンク")

    # Base64変換
    base64_data = pcm_to_base64(test_silence)
    print(f"✅ Base64エンコード: {len(base64_data)} chars")

    decoded_data = base64_to_pcm(base64_data)
    print(f"✅ Base64デコード: {len(decoded_data)} bytes")

    # 再生時間計算
    duration = get_audio_duration(test_silence)
    print(f"✅ 再生時間: {duration:.2f}秒")

    # 無音検出
    is_silent = detect_silence(test_silence)
    print(f"✅ 無音検出: {is_silent}")

    print("=" * 60)
    print("✅ すべてのテストが成功しました！")
    print("=" * 60)
