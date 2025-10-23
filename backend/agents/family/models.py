"""家族エージェント用データモデル"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Persona:
    """家族メンバーのペルソナ（AIエージェントの人格設定）

    Attributes:
        name: 家族メンバーの名前（例: 未来の妻、未来の娘）
        role: 役割（例: 妻、夫、娘、息子）
        speaking_style: 話し方の特徴（例: 優しく穏やかな口調）
        traits: 性格特性のリスト（例: ["思いやりがある", "協調性が高い"]）
        goals: 家族に対する願いや目標
        background: 背景情報や人物像の説明
        history: 過去のエピソードや思い出のリスト
    """
    name: str
    role: str
    speaking_style: str
    traits: List[str]
    goals: str
    background: str
    history: List[Dict[str, Any]] = field(default_factory=list)
